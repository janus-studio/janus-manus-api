import logging
import asyncio
from typing import Optional

from playwright.async_api import Playwright, Browser, Page, async_playwright

from app.domain.external.brower import Browser as BrowserProtocol
from app.domain.external.llm import LLM

logger = logging.getLogger(__name__)


class PlaywrightBrowser(BrowserProtocol):
    def __init__(self, cdp_url: str, llm: Optional[LLM] = None):
        self.llm = llm

        self.cdp_url = cdp_url
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def _ensure_browser(self):
        if not self.browser or not self.page:
            if not self.initialize():
                raise Exception('Playwright 浏览器初始化失败')

    async def _ensure_page(self):
        await self._ensure_browser()

        if not self.page:
            self.page = await self.browser.new_page()
        else:
            contexts = self.browser.contexts
            if contexts:
                default_context = contexts[0]
                pages = default_context.pages
                if pages:
                    latest_page = pages[-1]
                    if self.page != latest_page:
                        self.page = latest_page

    async def initialize(self):
        max_retries = 5
        retry_interval = 1

        for attempt in range(max_retries):
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)

                contexts = self.browser.contexts

                if contexts and len(contexts[0].pages) == 1:
                    page = contexts[0].pages[0]
                    if (
                            not page.url or
                            page.url == 'about:blank' or
                            page.url == 'chrome://newtab/' or
                            page.url == 'chrome://new-tab-page/'
                    ):
                        self.page = page
                    else:
                        self.page = await contexts[0].new_page()

                else:
                    # 上下文不存在或者不唯一，则表示数据被污染，重新创建上下文
                    contexts = contexts[0] if contexts else self.browser.new_context()
                    self.page = await contexts.new_page()

                return True

            except Exception as e:
                await self.cleanup()

                if attempt == max_retries - 1:
                    logger.error(f'Playwright 浏览器初始化失败（已重试{max_retries}次）: {e}')
                    return False

                retry_interval = min(retry_interval * 2, 10)
                logger.warning(
                    f'Playwright 浏览器初始化失败（已重试{attempt + 1}次）: {e}，等待{retry_interval}秒后重试')
                await asyncio.sleep(retry_interval)

    async def cleanup(self):
        try:
            if self.browser:
                contexts = self.browser.contexts
                if contexts:
                    for context in contexts:
                        pages = context.pages
                        if pages:
                            for page in pages:
                                if page.is_closed():
                                    continue
                                await page.close()

            if self.page and not self.page.is_closed():
                await self.page.close()

            if self.browser:
                await self.browser.close()

            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f'Playwright 浏览器清理失败: {e}')
        finally:
            self.playwright = None
            self.browser = None
            self.page = None

    async def wait_for_page_load(self, timeout: int = 15):
        await self._ensure_page()
        start_time = asyncio.get_event_loop().time()
        check_interval = 5

        while asyncio.get_event_loop().time() - start_time < timeout:
            is_completed = await self.page.evaluate('() => document.readyState === "complete"')
            if is_completed:
                return True

            await asyncio.sleep(check_interval)

        return False
