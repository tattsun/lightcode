"""ファイル名検索ツール"""

import fnmatch
import os

from lightcode.tools.base import Tool


class FindFilesTool(Tool):
    """ファイル名をパターンで検索するツール"""

    @property
    def name(self) -> str:
        return "find_files"

    @property
    def description(self) -> str:
        return "ファイル名をglobパターンで検索する。"

    @property
    def parameters(self) -> dict:
        return {
            "pattern": {
                "type": "string",
                "description": "検索するglobパターン（例: *.py, test_*.py）",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "検索対象のディレクトリパス（デフォルト: カレントディレクトリ）",
            },
            "max_results": {
                "type": "integer",
                "description": "最大結果数（デフォルト: 100）",
            },
        }

    def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        path = kwargs.get("path", ".")
        max_results = kwargs.get("max_results", 100)

        if not pattern:
            return "Error: pattern is required"

        results = []

        try:
            for root, dirs, files in os.walk(path):
                # 隠しディレクトリをスキップ
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        filepath = os.path.join(root, filename)
                        results.append(filepath)
                        if len(results) >= max_results:
                            break

                if len(results) >= max_results:
                    break

        except FileNotFoundError:
            return f"Error: Path not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"

        if not results:
            return f"No files found matching '{pattern}'"

        output = "\n".join(results)
        if len(results) >= max_results:
            output += f"\n... (truncated at {max_results} results)"

        return output
