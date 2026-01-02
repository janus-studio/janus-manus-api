from .base import BaseTool, tool
from app.domain.external.brower import Browser
from app.domain.models.tool_result import ToolResult


class BrowserTool(BaseTool):
    name: str = 'browser'

    def __init__(self, browser: Browser):
        super().__init__()
        self.browser = browser

    @tool(
        name='browser_view',
        description='查看当前浏览器页面内容，用于确认已打开页面的最新状态',
        parameters={},
        required=[]
    )
    async def browser_view(self) -> ToolResult:
        """查看当前浏览器页面内容"""
        return await self.browser.view_page()

    @tool(
        name='browser_navigate',
        description='导航到指定URL，用于打开新页面或跳转到已打开页面的其他位置',
        parameters={
            'url': {
                'type': 'string',
                'description': '要导航到的完整URL地址'
            }
        },
        required=['url']
    )
    async def browser_navigate(self, url: str) -> ToolResult:
        """导航到指定URL"""
        return await self.browser.navigate(url)

    @tool(
        name='browser_restart',
        description='重启浏览器并导航至指定URL，用于清除当前会话状态或解决浏览器异常问题',
        parameters={
            'url': {
                'type': 'string',
                'description': '要导航到的完整URL地址'
            }
        },
        required=['url']
    )
    async def browser_restart(self, url: str) -> ToolResult:
        """重启浏览器"""
        return await self.browser.restart(url=url)

    @tool(
        name='browser_click',
        description='点击页面上的指定元素，用于触发交互操作',
        parameters={
            'index': {
                'type': 'integer',
                'description': '(可选)要点击的元素索引'
            },
            'coordinate_x': {
                'type': 'integer',
                'description': '(可选)要点击的元素的X坐标'
            },
            'coordinate_y': {
                'type': 'integer',
                'description': '(可选)要点击的元素的Y坐标'
            }
        },
        required=[]
    )
    async def browser_click(self, index: int, coordinate_x: int, coordinate_y: int) -> ToolResult:
        """点击页面上的指定元素"""
        return await self.browser.click(
            index=index, coordinate_x=coordinate_x, coordinate_y=coordinate_y)

    @tool(
        name='browser_input',
        description='覆盖浏览器当前页面可编辑区域的文本内容(input/textarea输入框)，在需要填充输入框时使用',
        parameters={
            'index': {
                'type': 'integer',
                'description': '(可选)要输入文本的元素索引'
            },
            'coordinate_x': {
                'type': 'integer',
                'description': '(可选)要输入文本的元素的X坐标'
            },
            'coordinate_y': {
                'type': 'integer',
                'description': '(可选)要输入文本的元素的Y坐标'
            },
            'text': {
                'type': 'string',
                'description': '要输入的文本内容'
            },
            'press_enter': {
                'type': 'boolean',
                'description': '是否在输入完成后按下Enter键'
            }
        },
        required=['text', 'press_enter']
    )
    async def browser_input(
            self, index: int, coordinate_x: int,
            coordinate_y: int, text: str, press_enter: bool) -> ToolResult:
        """在页面上的指定元素中输入文本"""
        return await self.browser.input(
            index=index, coordinate_x=coordinate_x,
            coordinate_y=coordinate_y, text=text, press_enter=press_enter
        )

    @tool(
        name='browser_move_mouse',
        description='移动鼠标到指定坐标，用于模拟用户鼠标移动操作',
        parameters={
            'coordinate_x': {
                'type': 'integer',
                'description': '要移动鼠标到的X坐标'
            },
            'coordinate_y': {
                'type': 'integer',
                'description': '要移动鼠标到的Y坐标'
            }
        },
        required=['coordinate_x', 'coordinate_y']
    )
    async def browser_move_mouse(self, coordinate_x: int, coordinate_y: int) -> ToolResult:
        """移动鼠标到指定坐标"""
        return await self.browser.move_mouse(
            coordinate_x=coordinate_x, coordinate_y=coordinate_y
        )

    @tool(
        name='browser_press_key',
        description='模拟按下指定键盘键，用于触发键盘操作',
        parameters={
            'key': {
                'type': 'string',
                'description': '要模拟按下的键盘键，例如"a"、"Enter"等，支持多个键同时按下，例如"Ctrl+A"'
            }
        },
        required=['key']
    )
    async def browser_press_key(self, key: str) -> ToolResult:
        """模拟按下指定键盘键"""
        return await self.browser.press_key(key=key)

    @tool(
        name='browser_select_option',
        description='选择下拉列表中的指定选项，用于模拟用户选择操作',
        parameters={
            'index': {
                'type': 'integer',
                'description': '要操作的下拉列表元素的索引（序号）'
            },
            'option': {
                'type': 'integer',
                'description': '要选择的选项序号，从0开始（下拉框里的第几项）'
            }
        },
        required=['index', 'option']
    )
    async def browser_select_option(self, index: int, option: int) -> ToolResult:
        """选择下拉列表中的指定选项"""
        return await self.browser.select_option(index=index, option=option)

    @tool(
        name='browser_scroll_up',
        description='向上滚动浏览器页面，用于查看上方内容或返回页面顶部',
        parameters={
            'to_top': {
                'type': 'boolean',
                'description': '(可选)是否滚动到页面顶部，而非向上滚动一页'
            }
        },
        required=[]
    )
    async def browser_scroll_up(self, to_top: bool) -> ToolResult:
        """向上滚动浏览器页面"""
        return await self.browser.scroll_up(to_top=to_top)

    @tool(
        name='browser_scroll_down',
        description='向下滚动浏览器页面，用于查看下方内容',
        parameters={
            'to_bottom': {
                'type': 'boolean',
                'description': '(可选)是否滚动到页面底部，而非向下滚动一页'
            }
        },
        required=[]
    )
    async def browser_scroll_down(self, to_bottom: bool) -> ToolResult:
        """向下滚动浏览器页面"""
        return await self.browser.scroll_down(to_bottom=to_bottom)

    @tool(
        name='browser_console_exec',
        description='在浏览器控制台执行JavaScript代码，用于调试或执行浏览器操作',
        parameters={
            'javascript': {
                'type': 'string',
                'description': '要在浏览器控制台执行的JavaScript代码，请注意运行时环境为浏览器控制台'
            }
        },
        required=['javascript']
    )
    async def browser_console_exec(self, javascript: str) -> ToolResult:
        """在浏览器控制台执行JavaScript代码"""
        return await self.browser.console_exec(javascript=javascript)

    @tool(
        name='browser_console_view',
        description='查看浏览器控制台输出，用于检查JavaScript日志或调试页面错误',
        parameters={
            'max_lines': {
                'type': 'integer',
                'description': '(可选)要查看的最大行数，默认查看所有输出'
            }
        },
        required=[]
    )
    async def browser_console_view(self, max_lines: int) -> ToolResult:
        """查看浏览器控制台输出"""
        return await self.browser.console_view(max_lines=max_lines)
