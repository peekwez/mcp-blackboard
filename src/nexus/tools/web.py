from typing import Any

import urllib3
from pydantic import BaseModel, Field
from tavily import TavilyClient  # type: ignore
from tenacity import retry, stop_after_attempt, wait_random_exponential

from nexus.common import get_settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WebSearchArguments(BaseModel):
    query: str = Field(..., description="The search query.")
    num_results: int = Field(10, description="The number of search results to return.")


class SearchResult(BaseModel):
    title: str = Field(..., description="The title of the search result.")
    content: str = Field(
        ..., description="AI content of relevant content from the search result."
    )
    url: str = Field(..., description="The URL of the search result.")
    raw_content: str | None = Field(
        default=None, description="The raw content of the search result."
    )


class SearchResults(BaseModel):
    results: list[SearchResult] = Field(
        default=[], description="List of search results."
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    reraise=True,
)
def run_web_search(query: str, num_results: int) -> str:
    """
    Perform a web search using the provided query and number of results.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.

    Returns:
        str: A JSON string containing the search results.
    """
    settings = get_settings()
    client = TavilyClient(api_key=settings.web.tavily_api_key)
    ret: dict[str, Any] = client.search(  # type: ignore
        query,
        topic="general",
        include_raw_content=True,
        max_results=num_results,
        timeout=3000,
    )

    results: list[SearchResult] = []
    for result in ret.get("results", []):
        result = SearchResult(
            title=result.get("title"),
            content=result.get("content"),
            url=result.get("url"),
            raw_content=result.get("raw_content"),
        )
        results.append(result)

    search_results = SearchResults(results=results)
    return search_results.model_dump_json(indent=2)
