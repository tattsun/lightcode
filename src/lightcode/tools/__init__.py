"""ツールモジュール"""

from lightcode.tools.base import Tool
from lightcode.tools.copy_file import CopyFileTool
from lightcode.tools.delete_file import DeleteFileTool
from lightcode.tools.edit_file import EditFileTool
from lightcode.tools.file_info import FileInfoTool
from lightcode.tools.find_files import FindFilesTool
from lightcode.tools.grep import GrepTool
from lightcode.tools.list_files import ListFilesTool
from lightcode.tools.move_file import MoveFileTool
from lightcode.tools.read_file import ReadFileTool
from lightcode.tools.run_command import RunCommandTool
from lightcode.tools.write_file import WriteFileTool

# 利用可能なツール一覧
ALL_TOOLS: list[Tool] = [
    # Tier 1 - 必須
    RunCommandTool(),
    GrepTool(),
    FindFilesTool(),
    # ファイル操作
    ListFilesTool(),
    ReadFileTool(),
    WriteFileTool(),
    EditFileTool(),
    # Tier 2 - 便利
    DeleteFileTool(),
    MoveFileTool(),
    CopyFileTool(),
    FileInfoTool(),
]

__all__ = [
    "Tool",
    "CopyFileTool",
    "DeleteFileTool",
    "EditFileTool",
    "FileInfoTool",
    "FindFilesTool",
    "GrepTool",
    "ListFilesTool",
    "MoveFileTool",
    "ReadFileTool",
    "RunCommandTool",
    "WriteFileTool",
    "ALL_TOOLS",
]
