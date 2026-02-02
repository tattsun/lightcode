"""Tavily Web Search ツール"""

import os

from tavily import TavilyClient

from lightcode.tools.base import Tool


class WebSearchTool(Tool):
    """Tavily APIを使用してWeb検索を行うツール"""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("TAVILY_API_KEY")

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Webを検索して最新の情報を取得する。プログラミング、技術情報、一般的な質問に対応。"

    @property
    def parameters(self) -> dict:
        return {
            "query": {
                "type": "string",
                "description": "検索クエリ",
                "required": True,
            },
            "max_results": {
                "type": "integer",
                "description": "取得する検索結果の最大数（デフォルト: 5）",
            },
            "search_depth": {
                "type": "string",
                "description": "検索の深さ: 'basic' または 'advanced'（デフォルト: basic）",
            },
            "include_answer": {
                "type": "boolean",
                "description": "AIによる要約回答を含めるか（デフォルト: True）",
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

        # 結果をフォーマット
        output_lines = []

        # AI生成の回答がある場合
        if include_answer and response.get("answer"):
            output_lines.append("## Summary")
            output_lines.append(response["answer"])
            output_lines.append("")

        # 検索結果
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
                    # コンテンツを適度な長さに制限
                    truncated = content[:500] + "..." if len(content) > 500 else content
                    output_lines.append(truncated)
                output_lines.append("")
        else:
            output_lines.append("No results found.")

        return "\n".join(output_lines)
