"""PowerPoint creation tool."""

import os
import json
from pptx import Presentation

from lightcode.tools.base import Tool
from lightcode.tools.pptx._common import get_layout, set_slide_background, add_shape, populate_placeholder


class PptxCreateTool(Tool):
    """Tool for creating new PowerPoint presentations."""

    @property
    def name(self) -> str:
        return "pptx_create"

    @property
    def description(self) -> str:
        return """Create a new PowerPoint (.pptx) file with full shape control. USE THIS TOOL instead of writing Python code to create PowerPoint files.

Slide size: 10 x 7.5 inches (template default)

Each slide is defined by shapes array for complete layout control:
{
  "layout": "title_content",
  "background_color": "#FFFFFF",
  "shapes": [
    {"type": "textbox", "left": 0.5, "top": 0.3, "width": 9, "height": 1,
     "text": "Title", "font_size": 40, "font_color": "#1F4E79", "bold": true, "alignment": "center"},
    {"type": "textbox", "left": 0.5, "top": 1.8, "width": 9, "height": 5,
     "text": "• Point 1\\n• Point 2", "font_size": 24, "font_color": "#333333"},
    {"type": "rounded_rectangle", "left": 6, "top": 4, "width": 3.5, "height": 2,
     "text": "Highlight", "fill_color": "#E3F2FD", "font_size": 18}
  ],
  "notes": "Speaker notes here"
}

Shape types: textbox, rectangle, rounded_rectangle, oval, arrow_right, arrow_left, arrow_up, arrow_down, diamond, pentagon, hexagon, star, callout

Layout:
- layout: Layout name or index (optional). Examples: "title", "title_content", "blank", "Title Slide", 0

Placeholders:
- placeholders: Array of {idx, text or rich_text, font_size, font_color, bold, italic, underline, alignment, font_name}
- idx is the placeholder index in the selected layout (0=title, 1=body, etc.)

Shape properties:
- type: Shape type (required)
- left, top: Position in inches (required)
- width, height: Size in inches (required)
- text: Text content (simple text)
- rich_text: Array of styled segments [{text, bold, italic, underline, font_size, font_name, font_color, font_theme_color, hyperlink}, ...]
- font_theme_color values: TEXT_1, TEXT_2, ACCENT_1-6, BACKGROUND_1-2, DARK_1-2, LIGHT_1-2
- hyperlink: URL string (e.g., "https://example.com")
- font_size: Font size in points (default for all text)
- font_color: Text color as hex (e.g., "#333333")
- bold, italic, underline: true/false
- font_name: Font family name
- alignment: "left", "center", "right"
- fill_color: Background/fill color as hex
- line_color: Border color as hex
- line_width: Border width in points

Rich text example:
{"type": "textbox", ..., "rich_text": [{"text": "Normal "}, {"text": "BOLD", "bold": true}]}"""

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path for the new PowerPoint file (.pptx)",
                "required": True,
            },
            "slides": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of slide objects. Each slide has: shapes (array), layout (optional), placeholders (optional), background_color (optional), notes (optional)",
                "required": True,
            },
            "template": {
                "type": "string",
                "description": "Path to template file (.pptx or .potx) to use as base",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        slides = kwargs.get("slides", [])
        template = kwargs.get("template")

        if not path:
            return "Error: path is required"

        if not slides:
            return "Error: slides is required"

        if not path.endswith(".pptx"):
            path += ".pptx"

        try:
            # Create presentation from template or new
            if template:
                if not os.path.exists(template):
                    return f"Error: Template file not found: {template}"
                prs = Presentation(template)
            else:
                prs = Presentation()

            # Parse slides if provided as string (JSON)
            if isinstance(slides, str):
                try:
                    slides = json.loads(slides)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in slides parameter: {e}"

            # Add slides
            for slide_data in slides:
                if isinstance(slide_data, str):
                    try:
                        slide_data = json.loads(slide_data)
                    except json.JSONDecodeError:
                        continue

                # Create slide with layout
                layout_name = slide_data.get("layout", "blank")
                slide = prs.slides.add_slide(get_layout(prs, layout_name))

                # Set background color
                bg_color = slide_data.get("background_color")
                if bg_color:
                    set_slide_background(slide, bg_color)

                # Add shapes
                shapes = slide_data.get("shapes", [])
                for shape_data in shapes:
                    if isinstance(shape_data, str):
                        try:
                            shape_data = json.loads(shape_data)
                        except json.JSONDecodeError:
                            continue

                    shape_type = shape_data.get("type", "textbox")
                    left = float(shape_data.get("left", 0))
                    top = float(shape_data.get("top", 0))
                    width = float(shape_data.get("width", 2))
                    height = float(shape_data.get("height", 1))

                    add_shape(
                        slide,
                        shape_type=shape_type,
                        left=left,
                        top=top,
                        width=width,
                        height=height,
                        text=shape_data.get("text"),
                        fill_color=shape_data.get("fill_color"),
                        font_size=shape_data.get("font_size"),
                        font_color=shape_data.get("font_color"),
                        bold=shape_data.get("bold"),
                        alignment=shape_data.get("alignment"),
                        line_color=shape_data.get("line_color"),
                        line_width=shape_data.get("line_width"),
                        rich_text=shape_data.get("rich_text"),
                        italic=shape_data.get("italic"),
                        underline=shape_data.get("underline"),
                        font_name=shape_data.get("font_name"),
                    )

                # Populate placeholders (optional)
                placeholders = slide_data.get("placeholders", [])
                for ph in placeholders:
                    if isinstance(ph, str):
                        try:
                            ph = json.loads(ph)
                        except json.JSONDecodeError:
                            continue
                    idx = ph.get("idx")
                    if idx is None:
                        continue
                    rich_text = ph.get("rich_text")
                    text = ph.get("text", "")
                    populate_placeholder(
                        slide,
                        placeholder_idx=int(idx),
                        content=text,
                        font_size=ph.get("font_size"),
                        font_color=ph.get("font_color"),
                        bold=ph.get("bold"),
                        alignment=ph.get("alignment"),
                        font_name=ph.get("font_name"),
                        rich_text=rich_text,
                        italic=ph.get("italic"),
                        underline=ph.get("underline"),
                    )

                # Set speaker notes
                if "notes" in slide_data:
                    notes_slide = slide.notes_slide
                    notes_tf = notes_slide.notes_text_frame
                    notes_tf.text = slide_data["notes"]

            # Create parent directory if needed
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent)

            # Save presentation
            prs.save(path)

            slide_count = len(prs.slides)
            return f"Successfully created PowerPoint with {slide_count} slide(s): {path}"

        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            return f"Error creating PowerPoint: {e}"
