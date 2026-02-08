from typing import Protocol, Optional, BinaryIO

from app.domain.external.brower import Browser
from app.domain.models.tool_result import ToolResult


class Sandbox(Protocol):
    async def exec_command(self, session_id: str, exec_dir: str, command: str) -> ToolResult:
        ...

    async def view_shell(self, session_id: str, console: bool = False) -> ToolResult:
        ...

    async def wait_for_process(self, session_id: str, seconds: Optional[int] = None) -> ToolResult:
        ...

    async def write_to_process(self, session_id: str, input_text: str,
                               press_enter: bool = True) -> ToolResult:
        ...

    async def kill_process(self, session_id: str) -> ToolResult:
        ...

    async def write_file(
            self,
            filepath: str,
            content: str,
            append: bool = False,
            leading_newline: bool = False,
            trailing_newline: bool = False,
            sudo: bool = False,
    ) -> ToolResult:
        ...

    async def read_file(
            self,
            filepath: str,
            start_line: Optional[int] = None,
            end_line: Optional[int] = None,
            sudo: bool = False,
            max_length: int = 10000
    ) -> ToolResult:
        ...

    async def check_file_exists(self, filepath: str) -> ToolResult:
        ...

    async def delete_file(self, filepath: str) -> ToolResult:
        ...

    async def file_list(self, dir_path: str) -> ToolResult:
        ...

    async def file_replace(self, filepath: str, old_str: str, new_str: str,
                           sudo: bool = False) -> ToolResult:
        ...

    async def replace_in_file(
            self,
            filepath: str,
            old_str: str,
            new_str: str,
            sudo: bool = False,
    ) -> ToolResult:
        ...

    async def search_in_file(
            self,
            filepath: str,
            regex: str,
            sudo: bool = False,
    ) -> ToolResult:
        ...

    async def find_files(self, dir_path: str, glob_pattern: str) -> ToolResult:
        ...

    async def upload_file(
            self,
            file_data: BinaryIO,
            filepath: str,
            filename: str = None,
    ) -> ToolResult:
        ...

    async def download_file(self, filepath: str) -> BinaryIO:
        ...

    async def ensure_sandbox(self) -> None:
        ...

    async def destroy(self) -> bool:
        ...

    async def get_browser(self) -> Browser:
        ...

    @property
    def id(self) -> str:
        ...

    @property
    def cdp_url(self) -> str:
        ...

    @property
    def vnc_url(self) -> str:
        ...

    @classmethod
    async def create(cls) -> 'Sandbox':
        ...

    @classmethod
    async def get(cls, id: str) -> 'Sandbox':
        ...
