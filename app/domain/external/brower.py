from typing import Protocol, Optional
from app.domain.models.tool_result import ToolResult


class Browser(Protocol):
    async def view_page(self) -> ToolResult:
        """获取当前浏览器页面内容源码"""
        ...

    async def navigate(self, url: str) -> ToolResult:
        """传递对应的url使用浏览器导航到该页面"""
        ...

    async def restart(self, url: str) -> ToolResult:
        """重启浏览器并导航到指定url"""
        ...

    async def click(
            self,
            index: Optional[int] = None,
            coordinate_x: Optional[float] = None,
            coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        """传递对应元素的索引或坐标，点击该元素"""
        ...

    async def input(
            self,
            text: str,
            press_enter: bool,
            index: Optional[int] = None,
            coordinate_x: Optional[float] = None,
            coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        """传递文本+回车标识/xy坐标，输入到指定元素"""
        ...

    async def move_mouse(self, coordinate_x: float,
                         coordinate_y: float) -> ToolResult:
        """传递xy坐标，移动鼠标到指定位置"""
        ...

    async def press_key(self, key: str) -> ToolResult:
        """传递按键，模拟按键操作"""
        ...

    async def select_option(self, index: int, option: int) -> ToolResult:
        """传递选择框索引和选项索引，选择指定选项"""
        ...

    async def scroll_up(self, to_top: Optional[bool] = None) -> ToolResult:
        """向上滚动浏览器，如果没有传递to_top=True则向上滚动一页，否则直接滚动到顶部"""
        ...

    async def scroll_down(self,
                          to_bottom: Optional[bool] = None) -> ToolResult:
        """向下滚动浏览器，如果没有传递to_bottom=True则向下滚动一页，否则直接滚动到底部"""
        ...

    async def screenshot(self, full_page: Optional[bool] = None) -> bytes:
        """截取当前浏览器页面截图，如果传递full_page=True则截取完整页面，否则截取当前可见区域"""
        ...

    async def console_exec(self, javascript: str) -> ToolResult:
        """传递javascript代码，在浏览器控制台执行该代码"""
        ...

    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """传递最大输出行数，获取控制台输出结果，如果不传递则表示获取所有输出结果"""
        ...
