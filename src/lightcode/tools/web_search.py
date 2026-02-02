"""Tavily Web Search tool."""

import os

from tavily import TavilyClient

from lightcode.tools.base import Tool


class WebSearchTool(Tool):
    """Tool for web search using Tavily API."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("TAVILY_API_KEY")

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for up-to-date information on programming, tech, and general topics."

    @property
    def parameters(self) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "Search query",
                "required": True,
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 5)",
            },
            "search_depth": {
                "type": "string",
                "description": "Search depth: 'basic' or 'advanced' (default: basic)",
            },
            "include_answer": {
                "type": "boolean",
                "description": "Include AI-generated summary (default: True)",
            },
        }

    def execute(self, **kwargs) -> str:
        query = kwargs.get("query")
        max_results = kwargs.get("max_results", 5)
        search_depth = kwargs.get("search_depth", "basic")
        include_answer = kwargs.get("include_answer", True)

        if not query:
            return "Error: query is required"

        if not self._api_key:
            return "Error: TAVILY_API_KEY environment variable is not set"

        try:
            client = TavilyClient(api_key=self._api_key)
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer,
            )
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

        # Format results
        output_lines = []

        # AI-generated answer
        if include_answer and response.get("answer"):
            output_lines.append("## Summary")
            output_lines.append(response["answer"])
            output_lines.append("")

        # Search results
        results = response.get("results", [])
        if results:
            output_lines.append("## Search Results")
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("url", "")
                content = result.get("content", "")
                output_lines.append(f"### {i}. {title}")
                output_lines.append(f"URL: {url}")
                if content:
                    # Truncate content to reasonable length
                    truncated = content[:500] + "..." if len(content) > 500 else content
                    output_lines.append(truncated)
                output_lines.append("")
        else:
            output_lines.append("No results found.")

        return "\n".join(output_lines)
