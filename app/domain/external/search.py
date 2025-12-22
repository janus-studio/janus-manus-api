from typing import Protocol, Optional

from app.domain.models.search import SearchResults
from app.domain.models.tool_result import ToolResult


class SearchEngine(Protocol):
    async def invoke(self, query: str, date_range: Optional[str] = None) -> \
            ToolResult[SearchResults]:
        pass
