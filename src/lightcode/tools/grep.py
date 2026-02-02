"""コード内検索ツール"""

import os
import re

from lightcode.tools.base import Tool


class GrepTool(Tool):
    """ファイル内容を正規表現で検索するツール"""

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "ディレクトリ内のファイルを正規表現で検索し、マッチした行を返す。"

    @property
    def parameters(self) -> dict:
        return {
            "pattern": {
                "type": "string",
                "description": "検索する正規表現パターン",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "検索対象のディレクトリパス（デフォルト: カレントディレクトリ）",
            },
            "include": {
                "type": "string",
                "description": "対象ファイルのglobパターン（例: *.py）",
            },
            "max_results": {
                "type": "integer",
                "description": "最大結果数（デフォルト: 50）",
            },
        }

    def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        path = kwargs.get("path", ".")
        include = kwargs.get("include")
        max_results = kwargs.get("max_results", 50)

        if not pattern:
            return "Error: pattern is required"

        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        results = []
        files_searched = 0

        try:
            for root, _, files in os.walk(path):
                # 隠しディレクトリをスキップ
                if "/." in root or root.startswith("."):
                    continue

                for filename in files:
                    # includeパターンがある場合はフィルタ
                    if include:
                        import fnmatch
                        if not fnmatch.fnmatch(filename, include):
                            continue

                    filepath = os.path.join(root, filename)
                    files_searched += 1

                    try:
                        with open(filepath, encoding="utf-8") as f:
                            for line_num, line in enumerate(f, 1):
                                if regex.search(line):
                                    results.append(f"{filepath}:{line_num}: {line.rstrip()}")
                                    if len(results) >= max_results:
                                        break
                    except (UnicodeDecodeError, PermissionError, IsADirectoryError):
                        continue

                    if len(results) >= max_results:
                        break

                if len(results) >= max_results:
                    break

        except FileNotFoundError:
            return f"Error: Path not found: {path}"

        if not results:
            return f"No matches found (searched {files_searched} files)"

        output = "\n".join(results)
        if len(results) >= max_results:
            output += f"\n... (truncated at {max_results} results)"

        return output
