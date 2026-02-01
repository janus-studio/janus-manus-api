import logging
import asyncio
from http.client import responses
from time import sleep
from typing import Optional

from markdownify import markdownify
from playwright.async_api import Playwright, Browser, Page, async_playwright

from app.domain.external.brower import Browser as BrowserProtocol
from app.domain.external.llm import LLM
from app.domain.models.tool_result import ToolResult
from app.infrastructure.external.browser.playwright_browser_fun import (
    GET_VISIBLE_CONTENT_FUNC,
    GET_INTERACTIVE_ELEMENTS_FUNC,
    INJECT_CONSOLE_LOGS_FUNC
)

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

    async def _extract_content(self):
        """提取当前页面可见内容"""
        await self._ensure_page()
        content = await self.page.evaluate(GET_VISIBLE_CONTENT_FUNC)
        markdown_content = markdownify(content)

        max_content_length = min(len(markdown_content), 50000)

        if self.llm:
            response = await self.llm.invoke([{
                'role': 'system',
                'content': '你是一个专业的Markdown文档提取器，负责从HTML内容中提取所有信息并转换为Markdown格式。'
            }, {
                'role': 'user',
                'content': markdown_content[:max_content_length]
            }])
            return response.get('content', '')
        else:
            return markdown_content[:max_content_length]

    async def _extract_interactive_elements(self):
        """提取当前页面所有可交互元素"""
        await self._ensure_page()

        # 清除当前页面上的缓存可交互元素列表
        self.page.interactive_elements_cache = []

        interactive_elements = await self.page.evaluate(GET_INTERACTIVE_ELEMENTS_FUNC)
        self.page.interactive_elements_cache = interactive_elements

        # 格式化可交互元素
        formatted_elements = []
        for element in interactive_elements:
            formatted_elements.append(
                f'{element["index"]}:<{element["tag"]}>{element["text"]}</{element["tag"]}>')
        return formatted_elements

    async def _get_element_by_id(self, index: int) -> Optional[Any]:
        """根据索引/id获取可交互元素"""
        if (
                not hasattr(self.page, 'interactive_elements_cache') or
                not self.page.interactive_elements_cache or
                index >= len(self.page.interactive_elements_cache)
        ):
            return None

        selector = f'[data-manus-id="manus-element-{index}"]'
        return await self.page.query_selector(selector)

    async def click(
            self,
            index: Optional[int] = None,
            coordinate_x: Optional[float] = None,
            coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        await self._ensure_page()

        if coordinate_x is not None and coordinate_y is not None:
            await self.page.mouse.click(coordinate_x, coordinate_y)
        elif index is not None:
            try:
                element = await self._get_element_by_id(index)
                if not element:
                    return ToolResult(success=False, message=f'使用索引 {index} 查找元素失败')

                is_visible = await self.page.evaluate("""(element) => {
                    if (!element) return false;
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    return !(
                        rect.width === 0 ||
                        rect.height === 0 ||
                        style.visibility === 'hidden' ||
                        style.display === 'none' ||
                        style.opacity === '0'
                    )
                }""", element)

                if not is_visible:
                    # 尝试将页面滚动到该元素的位置
                    await self.page.evaluate("""
                    (element) => {
                        if (!element) return;
                        element.scrollIntoView({
                            block: 'center',
                            behavior: 'smooth'
                        });
                    }
                    """, element)
                    await asyncio.sleep(1)

                await element.click(timeout=5000)
            except Exception as e:
                return ToolResult(success=False, message=f'点击元素出错：{e}')

        return ToolResult(success=True)

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

    async def navigate(self, url: str) -> ToolResult:
        await self._ensure_page()
        try:

            self.page.interactive_elements_cache = []

            await self.page.goto(url)
            return ToolResult(
                success=True,
                data={'interactive_elements': await self._extract_interactive_elements()}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f'浏览器导航到 {url} 失败: {e}'
            )

    async def view_page(self) -> ToolResult:
        await self._ensure_page()
        await self.wait_for_page_load()

        interactive_elements = await self._extract_interactive_elements()
        return ToolResult(
            success=True,
            data={
                'interactive_elements': interactive_elements,
                'content': await self._extract_content()
            }
        )

    async def input(
            self,
            text: str,
            press_enter: bool,
            index: Optional[int] = None,
            coordinate_x: Optional[float] = None,
            coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        await self._ensure_page()

        if coordinate_x is not None and coordinate_y is not None:
            await self.page.mouse.click(coordinate_x, coordinate_y)
            await self.page.keyboard.type(text)
        elif index is not None:
            try:
                element = await self._get_element_by_id(index)
                if not element:
                    return ToolResult(
                        success=False,
                        message=f'浏览器输入文本失败: 元素索引 {index} 不存在'
                    )
                try:
                    await element.fill('')
                    await element.type(text)
                except Exception as e:
                    # 如果填充失败，则尝试点击后输入文本
                    await element.click()
                    await element.type(text)
                    
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f'浏览器输入文本失败: {e}'
                )

        if press_enter:
            await self.page.keyboard.press('Enter')

        return ToolResult(success=True)

    async def move_mouse(self, coordinate_x: float,
                         coordinate_y: float) -> ToolResult:
        await self._ensure_page()
        await self.page.mouse.move(coordinate_x, coordinate_y)
        return ToolResult(success=True)

    async def press_key(self, key: str) -> ToolResult:
        await self._ensure_page()
        await self.page.keyboard.press(key)
        return ToolResult(success=True)

    async def select_option(self, index: int, option: int) -> ToolResult:
        await self._ensure_page()
        try:
            element = await self._get_element_by_id(index)
            if not element:
                return ToolResult(
                    success=False,
                    message=f'浏览器选择选项失败: 元素索引 {index} 不存在'
                )

            await element.select_option(index=option)
            return ToolResult(success=True)

        except Exception as e:
            return ToolResult(
                success=False,
                message=f'浏览器选择选项失败: {e}'
            )

    async def restart(self, url):
        """重启浏览器并导航到指定URL"""
        await self.cleanup()
        await self.navigate(url)

    async def scroll_up(self, to_top: Optional[bool] = None) -> ToolResult:
        """向上滚动浏览器一个屏幕或整个页面"""
        await self._ensure_page()
        if to_top:
            await self.page.evaluate('window.scrollTo(0, 0)')
        else:
            await self.page.evaluate('window.scrollBy(0, -window.innerHeight)')

        return ToolResult(success=True)

    async def scroll_down(self, to_bottom: Optional[bool] = None) -> ToolResult:
        """向下滚动浏览器一个屏幕或整个页面"""
        await self._ensure_page()
        if to_bottom:
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        else:
            await self.page.evaluate('window.scrollBy(0, window.innerHeight)')

        return ToolResult(success=True)

    async def screenshot(self, full_page: Optional[bool] = None) -> bytes:
        """获取当前页面截图"""
        await self._ensure_page()

        screenshot_options = {
            'full_page': full_page,
            'type': 'png',
        }

        return await self.page.screenshot(**screenshot_options)

    async def console_exec(self, javascript: str) -> ToolResult:
        """在浏览器控制台执行JavaScript代码"""
        await self._ensure_page()

        try:
            await self.page.evaluate(INJECT_CONSOLE_LOGS_FUNC)
        except Exception as e:
            logger.warning(f'注入 window.console.logs 失败: {e}')

        try:
            result = await self.page.evaluate(javascript)
            return ToolResult(success=True, data={'result': result})
        except Exception as e:
            return ToolResult(
                success=False,
                message=f'浏览器控制台执行JavaScript代码失败: {e}'
            )

    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """查看浏览器控制台输出"""
        await self._ensure_page()

        try:
            console_outputs = await self.page.evaluate('() => window.console.logs || []')
            if max_lines is not None:
                console_outputs = console_outputs[-max_lines:]
            return ToolResult(success=True, data={'logs': console_outputs})

        except Exception as e:
            return ToolResult(
                success=False,
                message=f'浏览器控制台查看输出失败: {e}'
            )
