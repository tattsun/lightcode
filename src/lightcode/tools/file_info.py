"""ファイル情報取得ツール"""

import os
from datetime import datetime

from lightcode.tools.base import Tool


class FileInfoTool(Tool):
    """ファイルの情報を取得するツール"""

    @property
    def name(self) -> str:
        return "file_info"

    @property
    def description(self) -> str:
        return "ファイルのサイズ、更新日時、パーミッションなどの情報を取得する。"

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "情報を取得するファイルのパス",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")

        if not path:
            return "Error: path is required"

        try:
            stat = os.stat(path)

            # ファイルタイプ
            if os.path.isfile(path):
                file_type = "file"
            elif os.path.isdir(path):
                file_type = "directory"
            elif os.path.islink(path):
                file_type = "symlink"
            else:
                file_type = "other"

            # サイズのフォーマット
            size = stat.st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            # 日時のフォーマット
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            ctime = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")

            # パーミッション
            mode = oct(stat.st_mode)[-3:]

            info = f"""Path: {path}
Type: {file_type}
Size: {size_str} ({size} bytes)
Modified: {mtime}
Created: {ctime}
Permissions: {mode}"""

            return info

        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
