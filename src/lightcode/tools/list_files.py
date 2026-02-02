"""ファイル一覧取得ツール"""

import os

from lightcode.tools.base import Tool


class ListFilesTool(Tool):
    """ディレクトリ内のファイル一覧を取得するツール"""

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "指定したディレクトリ内のファイルとフォルダの一覧を取得する"

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "一覧を取得するディレクトリのパス（デフォルトはカレントディレクトリ）",
            }
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path", ".")

        try:
            entries = os.listdir(path)
            result = []
            for entry in sorted(entries):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    result.append(f"[DIR]  {entry}")
                else:
                    result.append(f"[FILE] {entry}")
            return "\n".join(result) if result else "(empty directory)"
        except FileNotFoundError:
            return f"Error: Directory not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
