"""Webページ取得ツール"""

import re

import requests
from bs4 import BeautifulSoup

from lightcode.tools.base import Tool


class WebFetchTool(Tool):
    """URLからWebページの内容を取得するツール"""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "URLを指定してWebページの内容を取得する。ドキュメントやコード例の詳細確認に使用。"

    @property
    def parameters(self) -> dict:
        return {
            "url": {
                "type": "string",
                "description": "取得するWebページのURL",
                "required": True,
            },
            "max_length": {
                "type": "integer",
                "description": "取得するテキストの最大文字数（デフォルト: 10000）",
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

        # HTMLの場合はパースしてテキスト抽出
        if "text/html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")

            # 不要な要素を削除
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # タイトル取得
            title = soup.title.string if soup.title else "No title"

            # メインコンテンツを取得
            main_content = soup.find("article") or soup.find("main") or soup.body
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # 複数の空行を1つにまとめる
            text = re.sub(r"\n{3,}", "\n\n", text)

            output = f"# {title}\n\nURL: {url}\n\n{text}"

        # プレーンテキストやJSONの場合はそのまま
        elif "text/" in content_type or "application/json" in content_type:
            output = f"URL: {url}\n\n{response.text}"

        else:
            return f"Error: Unsupported content type: {content_type}"

        # 長さ制限
        if len(output) > max_length:
            output = output[:max_length] + f"\n\n... (truncated at {max_length} characters)"

        return output
