"""ファイル書き込みツール"""

import os

from lightcode.tools.base import Tool


class WriteFileTool(Tool):
    """ファイルに内容を書き込むツール"""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "指定したファイルに内容を書き込む（既存ファイルは上書き）"

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "書き込むファイルのパス",
            },
            "content": {
                "type": "string",
                "description": "書き込む内容",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        content = kwargs.get("content")

        if not path:
            return "Error: path is required"
        if content is None:
            return "Error: content is required"

        try:
            # 親ディレクトリが存在しない場合は作成
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully wrote {len(content)} bytes to {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory: {path}"
