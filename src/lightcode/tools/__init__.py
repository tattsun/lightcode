"""Tools module."""

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
from lightcode.tools.read_image import ReadImageTool
from lightcode.tools.run_command import RunCommandTool
from lightcode.tools.web_fetch import WebFetchTool
from lightcode.tools.web_search import WebSearchTool
from lightcode.tools.write_file import WriteFileTool
from lightcode.tools.pptx import (
    PptxCreateTool,
    PptxReadTool,
    PptxAddSlideTool,
    PptxModifySlideTool,
    PptxExportImageTool,
)

# Available tools
ALL_TOOLS: list[Tool] = [
    # Tier 1 - Essential
    RunCommandTool(),
    GrepTool(),
    FindFilesTool(),
    # File operations
    ListFilesTool(),
    ReadFileTool(),
    WriteFileTool(),
    EditFileTool(),
    # Tier 2 - Utilities
    DeleteFileTool(),
    MoveFileTool(),
    CopyFileTool(),
    FileInfoTool(),
    # Media tools
    ReadImageTool(),
    # PowerPoint tools
    PptxCreateTool(),
    PptxReadTool(),
    PptxAddSlideTool(),
    PptxModifySlideTool(),
    PptxExportImageTool(),
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
    "ReadImageTool",
    "RunCommandTool",
    "WebFetchTool",
    "WebSearchTool",
    "WriteFileTool",
    "PptxCreateTool",
    "PptxReadTool",
    "PptxAddSlideTool",
    "PptxModifySlideTool",
    "PptxExportImageTool",
    "ALL_TOOLS",
]
