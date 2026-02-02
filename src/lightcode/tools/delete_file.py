"""ファイル削除ツール"""

import os

from lightcode.tools.base import Tool


class DeleteFileTool(Tool):
    """ファイルを削除するツール"""

    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return "指定したファイルを削除する。"

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "削除するファイルのパス",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")

        if not path:
            return "Error: path is required"

        try:
            os.remove(path)
            return f"Deleted: {path}"
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory (use rmdir): {path}"
