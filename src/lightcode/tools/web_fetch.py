"""Web page fetch tool."""

import re

import requests
from bs4 import BeautifulSoup

from lightcode.tools.base import Tool


class WebFetchTool(Tool):
    """Tool for fetching web page content from a URL."""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch web page content from a URL. Use for documentation or code examples."

    @property
    def parameters(self) -> dict:
        return {
            "url": {
                "type": "string",
                "description": "URL of the web page to fetch",
                "required": True,
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum text length (default: 10000)",
            },
        }

    def execute(self, **kwargs) -> str:
        url = kwargs.get("url")
        max_length = kwargs.get("max_length", 10000)

        if not url:
            return "Error: url is required"

        try:
            headers = {"User-Agent": "lightcode/1.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"Error: Failed to fetch URL: {e}"

        content_type = response.headers.get("Content-Type", "")

        # Parse HTML and extract text
        if "text/html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove unnecessary elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # Get title
            title = soup.title.string if soup.title else "No title"

            # Get main content
            main_content = soup.find("article") or soup.find("main") or soup.body
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # Collapse multiple blank lines
            text = re.sub(r"\n{3,}", "\n\n", text)

            output = f"# {title}\n\nURL: {url}\n\n{text}"

        # Plain text or JSON
        elif "text/" in content_type or "application/json" in content_type:
            output = f"URL: {url}\n\n{response.text}"

        else:
            return f"Error: Unsupported content type: {content_type}"

        # Length limit
        if len(output) > max_length:
            output = output[:max_length] + f"\n\n... (truncated at {max_length} characters)"

        return output
