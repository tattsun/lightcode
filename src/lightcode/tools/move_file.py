"""ファイル移動/リネームツール"""

import shutil

from lightcode.tools.base import Tool


class MoveFileTool(Tool):
    """ファイルを移動/リネームするツール"""

    @property
    def name(self) -> str:
        return "move_file"

    @property
    def description(self) -> str:
        return "ファイルを移動またはリネームする。"

    @property
    def parameters(self) -> dict:
        return {
            "source": {
                "type": "string",
                "description": "移動元のファイルパス",
                "required": True,
            },
            "destination": {
                "type": "string",
                "description": "移動先のパス",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        source = kwargs.get("source")
        destination = kwargs.get("destination")

        if not source:
            return "Error: source is required"
        if not destination:
            return "Error: destination is required"

        try:
            shutil.move(source, destination)
            return f"Moved: {source} -> {destination}"
        except FileNotFoundError:
            return f"Error: File not found: {source}"
        except PermissionError:
            return f"Error: Permission denied"
        except shutil.Error as e:
            return f"Error: {e}"
