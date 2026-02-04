"""PowerPoint slide addition tool."""

import os
import json
from pptx import Presentation

from lightcode.tools.base import Tool
from lightcode.tools.pptx._common import get_layout, set_slide_background, add_shape


class PptxAddSlideTool(Tool):
    """Tool for adding slides to existing PowerPoint presentations."""

    @property
    def name(self) -> str:
        return "pptx_add_slide"

    @property
    def description(self) -> str:
        return """Add a new slide to an existing PowerPoint (.pptx) file. USE THIS TOOL instead of writing Python code to add slides.

Slide size: 10 x 7.5 inches (widescreen)

Define the slide using shapes array:
{
  "shapes": [
    {"type": "textbox", "left": 0.5, "top": 0.3, "width": 9, "height": 1,
     "text": "Title", "font_size": 40, "font_color": "#1F4E79", "bold": true},
    {"type": "textbox", "left": 0.5, "top": 1.8, "width": 9, "height": 5,
     "text": "• Point 1\\n• Point 2", "font_size": 24}
  ]
}

Shape types: textbox, rectangle, rounded_rectangle, oval, arrow_right, arrow_left, etc.

Shape properties: type, left, top, width, height, text, rich_text, font_size, font_color, bold, italic, underline, font_name, alignment, fill_color, line_color, line_width

Rich text: [{"text": "Normal "}, {"text": "BOLD", "bold": true}, {"text": "Link", "hyperlink": "https://example.com"}]
font_theme_color values: TEXT_1, TEXT_2, ACCENT_1-6, BACKGROUND_1-2, DARK_1-2, LIGHT_1-2
hyperlink: URL string for clickable links

The slide is added at the specified position or at the end if position is not specified."""

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the PowerPoint file (.pptx)",
                "required": True,
            },
            "shapes": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of shape objects to add to the slide",
                "required": True,
            },
            "background_color": {
                "type": "string",
                "description": "Slide background color as hex (e.g., '#FFFFFF')",
            },
            "position": {
                "type": "integer",
                "description": "Position to insert the slide (1-based, starts from 1 NOT 0). If omitted, adds at the end.",
            },
            "notes": {
                "type": "string",
                "description": "Speaker notes for the slide",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        shapes = kwargs.get("shapes", [])
        background_color = kwargs.get("background_color")
        position = kwargs.get("position")
        notes = kwargs.get("notes")

        if not path:
            return "Error: path is required"
        if not shapes:
            return "Error: shapes is required"

        if not os.path.exists(path):
            return f"Error: File not found: {path}"

        try:
            prs = Presentation(path)

            # Parse shapes if string
            if isinstance(shapes, str):
                try:
                    shapes = json.loads(shapes)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in shapes: {e}"

            # Get blank layout
            blank_layout = get_layout(prs, "blank")

            # Add slide
            slide = prs.slides.add_slide(blank_layout)

            # Set background
            if background_color:
                set_slide_background(slide, background_color)

            # Add shapes
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

            # Set speaker notes
            if notes:
                notes_slide = slide.notes_slide
                notes_tf = notes_slide.notes_text_frame
                notes_tf.text = notes

            # Move slide to specified position if needed
            new_slide_idx = len(prs.slides) - 1
            if position is not None:
                target_idx = max(0, min(position - 1, len(prs.slides) - 1))
                if target_idx != new_slide_idx:
                    # Move the slide by manipulating the XML
                    slides = prs.slides._sldIdLst
                    slide_id = slides[-1]
                    slides.remove(slide_id)
                    slides.insert(target_idx, slide_id)
                    new_slide_idx = target_idx

            prs.save(path)

            slide_position = new_slide_idx + 1
            return f"Successfully added slide at position {slide_position}. Total slides: {len(prs.slides)}"

        except Exception as e:
            return f"Error adding slide: {e}"
