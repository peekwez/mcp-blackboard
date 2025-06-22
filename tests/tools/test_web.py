# type: ignore
from unittest.mock import MagicMock, patch

import pytest  # noqa F401

from nexus.tools.web import (
    SearchResult,
    SearchResults,
    WebSearchArguments,
    run_web_search,
)


@patch("nexus.tools.web.get_settings")
@patch("nexus.tools.web.TavilyClient")
def test_run_web_search(mock_tavily_client, mock_get_settings, settings):
    """Test running a web search."""
    # Setup
    mock_get_settings.return_value = settings
    mock_client_instance = MagicMock()
    mock_tavily_client.return_value = mock_client_instance

    # Mock the search results
    mock_client_instance.search.return_value = {
        "results": [
            {
                "title": "Test Result 1",
                "content": "This is test content 1",
                "url": "https://example.com/1",
                "raw_content": "Raw content 1",
            },
            {
                "title": "Test Result 2",
                "content": "This is test content 2",
                "url": "https://example.com/2",
                "raw_content": "Raw content 2",
            },
        ]
    }

    # Execute
    result = run_web_search("test query", 2)

    # Assert
    mock_get_settings.assert_called_once()
    mock_tavily_client.assert_called_once_with(api_key=settings.web.tavily_api_key)
    mock_client_instance.search.assert_called_once_with(
        "test query",
        topic="general",
        include_raw_content=True,
        max_results=2,
        timeout=3000,
    )

    # Check that the result is properly formatted
    results = SearchResults.model_validate_json(result)
    assert len(results.results) == 2
    assert results.results[0].title == "Test Result 1"
    assert results.results[0].content == "This is test content 1"
    assert results.results[0].url == "https://example.com/1"
    assert results.results[0].raw_content == "Raw content 1"
    assert results.results[1].title == "Test Result 2"


def test_web_search_arguments_model():
    """Test WebSearchArguments model."""
    # Test with default values
    args = WebSearchArguments(query="test query")
    assert args.query == "test query"
    assert args.num_results == 10

    # Test with custom values
    args = WebSearchArguments(query="test query", num_results=5)
    assert args.query == "test query"
    assert args.num_results == 5


def test_search_result_model():
    """Test SearchResult model."""
    # Test with required values
    result = SearchResult(
        title="Test Result",
        content="This is test content",
        url="https://example.com",
    )
    assert result.title == "Test Result"
    assert result.content == "This is test content"
    assert result.url == "https://example.com"
    assert result.raw_content is None

    # Test with all values
    result = SearchResult(
        title="Test Result",
        content="This is test content",
        url="https://example.com",
        raw_content="Raw content",
    )
    assert result.title == "Test Result"
    assert result.content == "This is test content"
    assert result.url == "https://example.com"
    assert result.raw_content == "Raw content"


def test_search_results_model():
    """Test SearchResults model."""
    # Test with empty results
    results = SearchResults()
    assert len(results.results) == 0

    # Test with some results
    results = SearchResults(
        results=[
            SearchResult(
                title="Test Result 1",
                content="This is test content 1",
                url="https://example.com/1",
            ),
            SearchResult(
                title="Test Result 2",
                content="This is test content 2",
                url="https://example.com/2",
                raw_content="Raw content 2",
            ),
        ]
    )
    assert len(results.results) == 2
    assert results.results[0].title == "Test Result 1"
    assert results.results[1].raw_content == "Raw content 2"
