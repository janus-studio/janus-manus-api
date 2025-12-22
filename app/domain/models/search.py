from typing import List, Optional

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    url: str
    title: str
    snippet: str


class SearchResults(BaseModel):
    query: str
    date_range: Optional[str] = None
    total_results: int = 0
    results: List[SearchResultItem] = Field(default_factory=list)
