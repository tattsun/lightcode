"""PowerPoint reading tool."""

import os
from pptx import Presentation

from lightcode.tools.base import Tool
from lightcode.tools.pptx._common import format_slide_info


class PptxReadTool(Tool):
    """Tool for reading PowerPoint presentations."""

    @property
    def name(self) -> str:
        return "pptx_read"

    @property
    def description(self) -> str:
        return """Read content from a PowerPoint (.pptx) file. USE THIS TOOL instead of writing Python code to read PowerPoint files.

Returns slide information including:
- Shape ID, type, and name
- Position (left, top) and size (width, height) in inches
- Text content
- Placeholder information
- Speaker notes (optional)
- Rich text runs with styling info (optional, use include_rich_text=true)
- Paragraph structure with levels and runs (optional, use include_rich_text=true)
- Available layout names and indices (optional, use include_layouts=true)

Use pptx_modify_slide to edit shapes based on the information returned by this tool.
When using rich_text in pptx_modify_slide, first use include_rich_text=true here to see the text structure."""

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the PowerPoint file (.pptx)",
                "required": True,
            },
            "slide_number": {
                "type": "integer",
                "description": "Specific slide number to read (1-based, starts from 1 NOT 0). If omitted, reads all slides.",
            },
            "include_notes": {
                "type": "boolean",
                "description": "Include speaker notes in the output (default: false)",
            },
            "include_rich_text": {
                "type": "boolean",
                "description": "Include rich text info (bold/italic/underline per run) for styled text (default: false)",
            },
            "include_layouts": {
                "type": "boolean",
                "description": "Include available layout names and indices (default: false)",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        slide_number = kwargs.get("slide_number")
        include_notes = kwargs.get("include_notes", False)
        include_rich_text = kwargs.get("include_rich_text", False)
        include_layouts = kwargs.get("include_layouts", False)

        if not path:
            return "Error: path is required"

        if not os.path.exists(path):
            return f"Error: File not found: {path}"

        try:
            prs = Presentation(path)
            total_slides = len(prs.slides)

            if total_slides == 0:
                return f"PowerPoint file has no slides: {path}"

            # Get presentation dimensions
            width_inches = round(prs.slide_width / 914400, 2)
            height_inches = round(prs.slide_height / 914400, 2)

            output_lines = [
                f"PowerPoint: {path}",
                f"Slide dimensions: {width_inches} x {height_inches} inches",
                f"Total slides: {total_slides}",
                "",
            ]
            if include_layouts:
                output_lines.append("Layouts:")
                for i, layout in enumerate(prs.slide_layouts):
                    name = layout.name or "(no name)"
                    output_lines.append(f"- {i}: {name}")
                output_lines.append("")

            if slide_number is not None:
                # Read specific slide
                if slide_number < 1:
                    return f"Error: slide_number must be >= 1 (1-based indexing). You passed {slide_number}. Use slide_number=1 for the first slide."
                if slide_number > total_slides:
                    return f"Error: slide_number {slide_number} is out of range. File has {total_slides} slide(s). Valid range: 1-{total_slides}."

                slide = prs.slides[slide_number - 1]
                layout_name = slide.slide_layout.name or "(no name)"
                layout_index = None
                for i, layout in enumerate(prs.slide_layouts):
                    if layout == slide.slide_layout:
                        layout_index = i
                        break
                output_lines.append(
                    format_slide_info(
                        slide,
                        slide_number,
                        include_notes,
                        include_rich_text,
                        layout_name=layout_name,
                        layout_index=layout_index,
                    )
                )
            else:
                # Read all slides
                for idx, slide in enumerate(prs.slides, 1):
                    layout_name = slide.slide_layout.name or "(no name)"
                    layout_index = None
                    for i, layout in enumerate(prs.slide_layouts):
                        if layout == slide.slide_layout:
                            layout_index = i
                            break
                    output_lines.append(
                        format_slide_info(
                            slide,
                            idx,
                            include_notes,
                            include_rich_text,
                            layout_name=layout_name,
                            layout_index=layout_index,
                        )
                    )
                    output_lines.append("")  # Blank line between slides

            return "\n".join(output_lines)

        except Exception as e:
            return f"Error reading PowerPoint: {e}"
