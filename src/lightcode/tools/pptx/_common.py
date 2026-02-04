"""Common utilities for PowerPoint tools."""

from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.presentation import Presentation
from pptx.slide import Slide
from pptx.shapes.base import BaseShape

# Layout name to index mapping (standard PowerPoint layouts)
LAYOUT_MAP = {
    "title": 0,           # Title slide
    "title_content": 1,   # Title and Content
    "section": 2,         # Section Header
    "two_content": 3,     # Two Content
    "comparison": 4,      # Comparison
    "title_only": 5,      # Title Only
    "blank": 6,           # Blank
}

# Shape type mapping
SHAPE_MAP = {
    "textbox": None,  # Uses dedicated method
    "rectangle": MSO_SHAPE.RECTANGLE,
    "rounded_rectangle": MSO_SHAPE.ROUNDED_RECTANGLE,
    "oval": MSO_SHAPE.OVAL,
    "arrow_right": MSO_SHAPE.RIGHT_ARROW,
    "arrow_left": MSO_SHAPE.LEFT_ARROW,
    "arrow_up": MSO_SHAPE.UP_ARROW,
    "arrow_down": MSO_SHAPE.DOWN_ARROW,
    "diamond": MSO_SHAPE.DIAMOND,
    "pentagon": MSO_SHAPE.PENTAGON,
    "hexagon": MSO_SHAPE.HEXAGON,
    "star": MSO_SHAPE.STAR_5_POINT,
    "callout": MSO_SHAPE.ROUNDED_RECTANGULAR_CALLOUT,
}

# Text alignment mapping
ALIGN_MAP = {
    "left": PP_ALIGN.LEFT,
    "center": PP_ALIGN.CENTER,
    "right": PP_ALIGN.RIGHT,
    "justify": PP_ALIGN.JUSTIFY,
}

# Theme color mapping (string name -> MSO_THEME_COLOR)
THEME_COLOR_MAP = {
    "TEXT_1": MSO_THEME_COLOR.TEXT_1,
    "TEXT_2": MSO_THEME_COLOR.TEXT_2,
    "BACKGROUND_1": MSO_THEME_COLOR.BACKGROUND_1,
    "BACKGROUND_2": MSO_THEME_COLOR.BACKGROUND_2,
    "ACCENT_1": MSO_THEME_COLOR.ACCENT_1,
    "ACCENT_2": MSO_THEME_COLOR.ACCENT_2,
    "ACCENT_3": MSO_THEME_COLOR.ACCENT_3,
    "ACCENT_4": MSO_THEME_COLOR.ACCENT_4,
    "ACCENT_5": MSO_THEME_COLOR.ACCENT_5,
    "ACCENT_6": MSO_THEME_COLOR.ACCENT_6,
    "DARK_1": MSO_THEME_COLOR.DARK_1,
    "DARK_2": MSO_THEME_COLOR.DARK_2,
    "LIGHT_1": MSO_THEME_COLOR.LIGHT_1,
    "LIGHT_2": MSO_THEME_COLOR.LIGHT_2,
    "HYPERLINK": MSO_THEME_COLOR.HYPERLINK,
    "FOLLOWED_HYPERLINK": MSO_THEME_COLOR.FOLLOWED_HYPERLINK,
}

# Predefined color themes
COLOR_THEMES = {
    "default": {
        "background": "#FFFFFF",
        "title": "#1F4E79",
        "body": "#333333",
        "accent": "#2E75B6",
    },
    "dark": {
        "background": "#1E1E1E",
        "title": "#FFFFFF",
        "body": "#E0E0E0",
        "accent": "#4FC3F7",
    },
    "blue": {
        "background": "#E3F2FD",
        "title": "#0D47A1",
        "body": "#1565C0",
        "accent": "#42A5F5",
    },
    "green": {
        "background": "#E8F5E9",
        "title": "#1B5E20",
        "body": "#2E7D32",
        "accent": "#66BB6A",
    },
    "corporate": {
        "background": "#F5F5F5",
        "title": "#212121",
        "body": "#424242",
        "accent": "#FF5722",
    },
    "modern": {
        "background": "#FAFAFA",
        "title": "#263238",
        "body": "#455A64",
        "accent": "#00BCD4",
    },
}

# Default styling
DEFAULT_STYLE = {
    "title_font_size": 36,
    "body_font_size": 18,
    "title_bold": True,
    "body_bold": False,
}


def emu_to_inches(emu: int) -> float:
    """Convert EMU (English Metric Units) to inches."""
    if emu is None:
        return 0.0
    return emu / 914400


def inches_to_emu(inches: float) -> int:
    """Convert inches to EMU."""
    return int(inches * 914400)


def hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert hex color string to RGBColor.

    Args:
        hex_color: Color in format '#RRGGBB' or 'RRGGBB'

    Returns:
        RGBColor object
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return RGBColor(r, g, b)


def set_slide_background(slide: Slide, color: str = None):
    """Set slide background color.

    Args:
        slide: Slide object
        color: Background color as hex string
    """
    if not color:
        return

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = hex_to_rgb(color)


def apply_paragraph_style(paragraph, font_size: int = None, font_color: str = None,
                          bold: bool = None, alignment: str = None, font_name: str = None):
    """Apply styling to a paragraph.

    Args:
        paragraph: Paragraph object
        font_size: Font size in points
        font_color: Font color as hex string
        bold: Whether text should be bold
        alignment: Text alignment ('left', 'center', 'right', 'justify')
        font_name: Font family name
    """
    if font_size:
        paragraph.font.size = Pt(font_size)
    if font_color:
        paragraph.font.color.rgb = hex_to_rgb(font_color)
    if bold is not None:
        paragraph.font.bold = bold
    if font_name:
        paragraph.font.name = font_name
    if alignment and alignment in ALIGN_MAP:
        paragraph.alignment = ALIGN_MAP[alignment]


def get_layout(prs: Presentation, layout_name: str):
    """Get slide layout by name.

    Args:
        prs: Presentation object
        layout_name: Layout name (e.g., 'title', 'title_content', 'blank')

    Returns:
        SlideLayout object
    """
    layout_idx = LAYOUT_MAP.get(layout_name, 1)  # Default to title_content

    # Ensure index is within available layouts
    layouts = prs.slide_layouts
    if layout_idx >= len(layouts):
        layout_idx = min(1, len(layouts) - 1)  # Fallback to first or second layout

    return layouts[layout_idx]


def populate_placeholder(slide: Slide, placeholder_idx: int, content,
                         font_size: int = None, font_color: str = None,
                         bold: bool = None, alignment: str = None,
                         font_name: str = None) -> bool:
    """Populate a placeholder with content and optional styling.

    Args:
        slide: Slide object
        placeholder_idx: Placeholder index (0=title, 1=body, etc.)
        content: String or list of strings
        font_size: Font size in points
        font_color: Font color as hex string
        bold: Whether text should be bold
        alignment: Text alignment ('left', 'center', 'right', 'justify')
        font_name: Font family name

    Returns:
        True if placeholder was found and populated
    """
    for shape in slide.shapes:
        if shape.is_placeholder and shape.placeholder_format.idx == placeholder_idx:
            if hasattr(shape, 'text_frame'):
                tf = shape.text_frame
                if isinstance(content, list):
                    # First paragraph
                    if content:
                        tf.paragraphs[0].text = content[0]
                        apply_paragraph_style(
                            tf.paragraphs[0], font_size, font_color, bold, alignment, font_name
                        )
                    # Additional paragraphs
                    for item in content[1:]:
                        p = tf.add_paragraph()
                        p.text = item
                        apply_paragraph_style(
                            p, font_size, font_color, bold, alignment, font_name
                        )
                else:
                    tf.paragraphs[0].text = str(content)
                    apply_paragraph_style(
                        tf.paragraphs[0], font_size, font_color, bold, alignment, font_name
                    )
                return True
    return False


def extract_shape_info(shape: BaseShape, include_rich_text: bool = False) -> dict:
    """Extract information from a shape.

    Args:
        shape: Shape object
        include_rich_text: Whether to include rich text (run-level) information

    Returns:
        Dictionary with shape information
    """
    info = {
        "shape_id": shape.shape_id,
        "name": shape.name,
        "type": shape.shape_type.name if hasattr(shape.shape_type, 'name') else str(shape.shape_type),
        "left": round(emu_to_inches(shape.left), 2) if shape.left else 0,
        "top": round(emu_to_inches(shape.top), 2) if shape.top else 0,
        "width": round(emu_to_inches(shape.width), 2) if shape.width else 0,
        "height": round(emu_to_inches(shape.height), 2) if shape.height else 0,
    }

    # Extract text if available
    if hasattr(shape, 'text_frame'):
        info["text"] = shape.text_frame.text

        # Extract rich text information if requested
        if include_rich_text:
            rich_text = []
            tf = shape.text_frame
            for para in tf.paragraphs:
                for run in para.runs:
                    run_info = {"text": run.text}
                    # Only include non-default styles
                    if run.font.bold:
                        run_info["bold"] = True
                    if run.font.italic:
                        run_info["italic"] = True
                    if run.font.underline:
                        run_info["underline"] = True
                    if run.font.size:
                        run_info["font_size_pt"] = run.font.size.pt
                    if run.font.name:
                        run_info["font_name"] = run.font.name
                    # Font color info
                    if run.font.color and run.font.color.type is not None:
                        try:
                            tc = run.font.color.theme_color
                            if tc is not None and tc != MSO_THEME_COLOR.NOT_THEME_COLOR:
                                # Extract just the name (e.g., "TEXT_1" from "TEXT_1 (13)")
                                tc_str = str(tc).replace("MSO_THEME_COLOR.", "")
                                if " (" in tc_str:
                                    tc_str = tc_str.split(" (")[0]
                                run_info["font_theme_color"] = tc_str
                        except (AttributeError, TypeError):
                            pass
                        try:
                            if run.font.color.rgb is not None:
                                run_info["font_color"] = str(run.font.color.rgb)
                        except (AttributeError, TypeError):
                            pass
                    # Hyperlink
                    if run.hyperlink and run.hyperlink.address:
                        run_info["hyperlink"] = run.hyperlink.address
                    rich_text.append(run_info)
            if rich_text:
                info["rich_text"] = rich_text
    elif hasattr(shape, 'text'):
        info["text"] = shape.text

    # Check if it's a placeholder
    if shape.is_placeholder:
        info["is_placeholder"] = True
        info["placeholder_idx"] = shape.placeholder_format.idx

    return info


def add_textbox(slide: Slide, left: float, top: float, width: float, height: float,
                text: str = None, font_size: int = None, font_color: str = None,
                bold: bool = None, alignment: str = None, font_name: str = None,
                background_color: str = None, rich_text: list = None,
                italic: bool = None, underline: bool = None) -> BaseShape:
    """Add a textbox to a slide.

    Args:
        slide: Slide object
        left, top, width, height: Position and size in inches
        text: Text content (simple text, mutually exclusive with rich_text)
        font_size: Font size in points (optional, default style)
        font_color: Font color as hex string (optional, default style)
        bold: Whether text should be bold (optional, default style)
        alignment: Text alignment (optional)
        font_name: Font family name (optional, default style)
        background_color: Background color as hex string (optional)
        rich_text: List of text segments with individual styles (optional)
        italic: Whether text should be italic (optional, default style)
        underline: Whether text should be underlined (optional, default style)

    Returns:
        Created shape
    """
    textbox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = textbox.text_frame
    tf.word_wrap = True

    # Set background color
    if background_color:
        textbox.fill.solid()
        textbox.fill.fore_color.rgb = hex_to_rgb(background_color)

    p = tf.paragraphs[0]

    if rich_text:
        # Rich text: multiple runs with individual styles
        for i, segment in enumerate(rich_text):
            seg_text = segment.get("text", "")
            if i == 0:
                p.text = seg_text
                if p.runs:
                    _apply_run_style(p.runs[0], segment, font_size, font_color, bold, italic, underline, font_name)
            else:
                run = p.add_run()
                run.text = seg_text
                _apply_run_style(run, segment, font_size, font_color, bold, italic, underline, font_name)
        if alignment and alignment in ALIGN_MAP:
            p.alignment = ALIGN_MAP[alignment]
    else:
        # Simple text
        p.text = text or ""
        apply_paragraph_style(p, font_size, font_color, bold, alignment, font_name)
        # Apply italic and underline
        if p.runs:
            if italic is not None:
                p.runs[0].font.italic = italic
            if underline is not None:
                p.runs[0].font.underline = underline

    return textbox


def _apply_run_style(run, segment: dict, default_font_size: int = None,
                     default_font_color: str = None, default_bold: bool = None,
                     default_italic: bool = None, default_underline: bool = None,
                     default_font_name: str = None):
    """Apply style to a run, with segment overrides over defaults."""
    # Font size
    size = segment.get("font_size", default_font_size)
    if size:
        run.font.size = Pt(size)
    # Font name
    name = segment.get("font_name", default_font_name)
    if name:
        run.font.name = name
    # Bold
    bold = segment.get("bold", default_bold)
    if bold is not None:
        run.font.bold = bold
    # Italic
    italic = segment.get("italic", default_italic)
    if italic is not None:
        run.font.italic = italic
    # Underline
    underline = segment.get("underline", default_underline)
    if underline is not None:
        run.font.underline = underline
    # Font color (RGB or theme color)
    theme_color = segment.get("font_theme_color")
    if theme_color:
        # Theme color takes priority
        theme_enum = THEME_COLOR_MAP.get(theme_color.upper())
        if theme_enum:
            run.font.color.theme_color = theme_enum
    else:
        color = segment.get("font_color", default_font_color)
        if color:
            run.font.color.rgb = hex_to_rgb(color)
    # Hyperlink
    hyperlink = segment.get("hyperlink")
    if hyperlink:
        run.hyperlink.address = hyperlink


def add_shape(slide: Slide, shape_type: str, left: float, top: float,
              width: float, height: float, text: str = None,
              fill_color: str = None, font_size: int = None,
              font_color: str = None, bold: bool = None,
              alignment: str = None, line_color: str = None,
              line_width: float = None, rich_text: list = None,
              italic: bool = None, underline: bool = None,
              font_name: str = None) -> BaseShape:
    """Add a shape to a slide.

    Args:
        slide: Slide object
        shape_type: Shape type name (e.g., 'rectangle', 'oval')
        left, top, width, height: Position and size in inches
        text: Text content (optional, mutually exclusive with rich_text)
        fill_color: Fill color as hex string (optional)
        font_size: Font size in points (optional)
        font_color: Font color as hex string (optional)
        bold: Whether text should be bold (optional)
        alignment: Text alignment (optional)
        line_color: Border/line color as hex string (optional)
        line_width: Border/line width in points (optional)
        rich_text: List of text segments with individual styles (optional)
        italic: Whether text should be italic (optional)
        underline: Whether text should be underlined (optional)
        font_name: Font family name (optional)

    Returns:
        Created shape
    """
    if shape_type == "textbox":
        return add_textbox(slide, left, top, width, height, text=text, font_size=font_size,
                          font_color=font_color, bold=bold, alignment=alignment,
                          background_color=fill_color, rich_text=rich_text,
                          italic=italic, underline=underline, font_name=font_name)

    mso_shape = SHAPE_MAP.get(shape_type, MSO_SHAPE.RECTANGLE)

    shape = slide.shapes.add_shape(
        mso_shape,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )

    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = hex_to_rgb(fill_color)

    if line_color:
        shape.line.color.rgb = hex_to_rgb(line_color)
    if line_width:
        shape.line.width = Pt(line_width)

    if text or rich_text:
        tf = shape.text_frame
        tf.word_wrap = True
        # Center text vertically
        tf.anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]

        if rich_text:
            # Rich text: multiple runs with individual styles
            for i, segment in enumerate(rich_text):
                seg_text = segment.get("text", "")
                if i == 0:
                    p.text = seg_text
                    if p.runs:
                        _apply_run_style(p.runs[0], segment, font_size, font_color, bold, italic, underline, font_name)
                else:
                    run = p.add_run()
                    run.text = seg_text
                    _apply_run_style(run, segment, font_size, font_color, bold, italic, underline, font_name)
            if alignment and alignment in ALIGN_MAP:
                p.alignment = ALIGN_MAP[alignment]
            elif alignment is None:
                p.alignment = ALIGN_MAP.get("center")
        else:
            p.text = text
            apply_paragraph_style(p, font_size, font_color, bold, alignment or "center", font_name)
            # Apply italic and underline
            if p.runs:
                if italic is not None:
                    p.runs[0].font.italic = italic
                if underline is not None:
                    p.runs[0].font.underline = underline

    return shape


def format_shape_info(shape: BaseShape, indent: int = 0, include_rich_text: bool = False) -> list[str]:
    """Format a single shape's information.

    Args:
        shape: Shape object
        indent: Indentation level for nested shapes
        include_rich_text: Whether to include rich text (run-level) information

    Returns:
        List of formatted strings
    """
    lines = []
    prefix = "  " * indent + "- "
    text_prefix = "  " * indent + "  "

    info = extract_shape_info(shape, include_rich_text=include_rich_text)

    shape_desc = f"{prefix}Shape ID {info['shape_id']}: {info['type']}"
    if info.get('is_placeholder'):
        shape_desc += f" (Placeholder {info['placeholder_idx']})"
    shape_desc += f" at ({info['left']}, {info['top']}), size ({info['width']}, {info['height']})"

    lines.append(shape_desc)

    if 'text' in info and info['text'].strip():
        # Indent and truncate long text
        text = info['text'].replace('\n', '\\n')
        if len(text) > 200:
            text = text[:200] + "..."
        lines.append(f"{text_prefix}Text: \"{text}\"")

        # Show rich text info if available and has styled runs
        if include_rich_text and 'rich_text' in info:
            # Check if there are any style variations across runs
            has_styled_runs = any(
                r.get('bold') or r.get('italic') or r.get('underline') or
                r.get('font_theme_color') or r.get('font_color') or r.get('hyperlink')
                for r in info['rich_text']
            )
            # Check if font sizes vary
            font_sizes = [r.get('font_size_pt') for r in info['rich_text'] if r.get('font_size_pt')]
            has_size_variation = len(set(font_sizes)) > 1 if font_sizes else False

            if has_styled_runs or has_size_variation:
                runs_desc = []
                for r in info['rich_text']:
                    run_text = r['text'][:30] + "..." if len(r['text']) > 30 else r['text']
                    styles = []
                    if r.get('bold'):
                        styles.append('B')
                    if r.get('italic'):
                        styles.append('I')
                    if r.get('underline'):
                        styles.append('U')
                    if r.get('font_size_pt') and has_size_variation:
                        styles.append(f"{r['font_size_pt']}pt")
                    if r.get('font_theme_color'):
                        styles.append(r['font_theme_color'])
                    elif r.get('font_color'):
                        styles.append(f"#{r['font_color']}")
                    if r.get('hyperlink'):
                        # Truncate long URLs
                        url = r['hyperlink']
                        if len(url) > 30:
                            url = url[:27] + "..."
                        styles.append(f"link:{url}")
                    style_str = f"[{','.join(styles)}]" if styles else ""
                    runs_desc.append(f'"{run_text}"{style_str}')
                lines.append(f"{text_prefix}Runs: {' | '.join(runs_desc)}")

    # Recursively process group shapes
    if info['type'] == 'GROUP' and hasattr(shape, 'shapes'):
        for child_shape in shape.shapes:
            lines.extend(format_shape_info(child_shape, indent + 1, include_rich_text=include_rich_text))

    return lines


def format_slide_info(slide: Slide, slide_number: int, include_notes: bool = False,
                      include_rich_text: bool = False) -> str:
    """Format slide information as readable text.

    Args:
        slide: Slide object
        slide_number: 1-based slide number
        include_notes: Whether to include speaker notes
        include_rich_text: Whether to include rich text (run-level) information

    Returns:
        Formatted string with slide information
    """
    lines = [f"[Slide {slide_number}]"]

    for shape in slide.shapes:
        lines.extend(format_shape_info(shape, include_rich_text=include_rich_text))

    if include_notes and slide.has_notes_slide:
        notes_text = slide.notes_slide.notes_text_frame.text
        if notes_text.strip():
            lines.append(f"Notes: {notes_text}")

    return "\n".join(lines)
