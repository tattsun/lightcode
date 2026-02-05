"""PowerPoint slide addition tool."""

import os
import json
from pptx import Presentation

from lightcode.tools.base import Tool
from lightcode.tools.pptx._common import get_layout, set_slide_background, add_shape, populate_placeholder, add_table


class PptxAddSlideTool(Tool):
    """Tool for adding slides to existing PowerPoint presentations."""

    @property
    def name(self) -> str:
        return "pptx_add_slide"

    @property
    def description(self) -> str:
        return """Add a new slide to an existing PowerPoint (.pptx) file. USE THIS TOOL instead of writing Python code to add slides.

Slide size: 10 x 7.5 inches (template default)

Define the slide using shapes array:
{
  "layout": "title_content",
  "shapes": [
    {"type": "textbox", "left": 0.5, "top": 0.3, "width": 9, "height": 1,
     "text": "Title", "font_size": 40, "font_color": "#1F4E79", "bold": true},
    {"type": "textbox", "left": 0.5, "top": 1.8, "width": 9, "height": 5,
     "text": "• Point 1\\n• Point 2", "font_size": 24}
  ]
}

Shape types: textbox, rectangle, rounded_rectangle, oval, arrow_right, arrow_left, etc.

Layout:
- layout: Layout name or index (optional). Examples: "title", "title_content", "blank", "Title Slide", 0

Placeholders:
- placeholders: Array of {idx, text or rich_text, font_size, font_color, bold, italic, underline, alignment, font_name}
- idx is the placeholder index in the selected layout (0=title, 1=body, etc.)

Shape properties: type, left, top, width, height, text, rich_text, font_size, font_color, bold, italic, underline, font_name, alignment, fill_color, line_color, line_width

Rich text: [{"text": "Normal "}, {"text": "BOLD", "bold": true}, {"text": "Link", "hyperlink": "https://example.com"}]
font_theme_color values: TEXT_1, TEXT_2, ACCENT_1-6, BACKGROUND_1-2, DARK_1-2, LIGHT_1-2
hyperlink: URL string for clickable links

Tables:
[{
  "left": 1.0, "top": 2.0, "width": 8.0, "height": 3.0,
  "rows": 4, "columns": 3,
  "data": [["Header1", "Header2", "Header3"], ["A", "B", "C"]],
  "header_style": {"bold": true, "fill_color": "#1F4E79", "font_color": "#FFFFFF"},
  "column_widths": [2.0, 3.0, 3.0],
  "merge_cells": ["A1:B1"]
}]

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
            },
            "background_color": {
                "type": "string",
                "description": "Slide background color as hex (e.g., '#FFFFFF')",
            },
            "layout": {
                "type": "string",
                "description": "Slide layout name or index (e.g., 'title', 'title_content', 'blank', 'Title Slide', 0)",
            },
            "placeholders": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Placeholder values. Each: {idx, text or rich_text, font_size, font_color, bold, italic, underline, alignment, font_name}",
            },
            "position": {
                "type": "integer",
                "description": "Position to insert the slide (1-based, starts from 1 NOT 0). If omitted, adds at the end.",
            },
            "notes": {
                "type": "string",
                "description": "Speaker notes for the slide",
            },
            "tables": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Array of table objects. Each: {left, top, width, height, rows, columns, data (2D array), header_style, column_widths, merge_cells}",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        shapes = kwargs.get("shapes", [])
        background_color = kwargs.get("background_color")
        layout_name = kwargs.get("layout", "blank")
        placeholders = kwargs.get("placeholders", [])
        position = kwargs.get("position")
        notes = kwargs.get("notes")
        tables = kwargs.get("tables", [])

        if not path:
            return "Error: path is required"
        if not shapes and not placeholders and not tables:
            return "Error: shapes, placeholders, or tables is required"

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

            # Parse tables if string
            if isinstance(tables, str):
                try:
                    tables = json.loads(tables)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in tables: {e}"

            # Add slide with layout
            slide = prs.slides.add_slide(get_layout(prs, layout_name))

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

            # Add tables
            for table_data in tables:
                if isinstance(table_data, str):
                    try:
                        table_data = json.loads(table_data)
                    except json.JSONDecodeError:
                        continue

                left = float(table_data.get("left", 0))
                top = float(table_data.get("top", 0))
                width = float(table_data.get("width", 6))
                height = float(table_data.get("height", 3))
                rows = int(table_data.get("rows", 2))
                cols = int(table_data.get("columns", 2))

                add_table(
                    slide,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    rows=rows,
                    cols=cols,
                    data=table_data.get("data"),
                    header_style=table_data.get("header_style"),
                    column_widths=table_data.get("column_widths"),
                    merge_cells=table_data.get("merge_cells"),
                )

            # Populate placeholders (optional)
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
