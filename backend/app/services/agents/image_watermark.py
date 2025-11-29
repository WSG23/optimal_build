"""Image watermark utilities for marketing pack photos.

Applies visible watermarks to property photos for marketing materials
to indicate they are for feasibility purposes only and not for permits.
"""

from enum import Enum
from io import BytesIO
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError:
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]

import structlog

logger = structlog.get_logger()


# Phase-specific watermark text
class PropertyPhase(str, Enum):
    """Property phase determines watermark text for marketing materials."""

    ACQUISITION = "acquisition"
    SALES = "sales"


# Phase-specific watermark text mapping
PHASE_WATERMARK_TEXT = {
    PropertyPhase.ACQUISITION: "Feasibility Assessment Only – Not for Construction",
    PropertyPhase.SALES: "Sales Material – Subject to Final Approval",
}

# Default watermark text for marketing materials (backwards compatibility)
DEFAULT_WATERMARK_TEXT = "Marketing Feasibility Only – Not for Permit or Construction"


def get_watermark_text_for_phase(phase: PropertyPhase | str | None) -> str:
    """Get appropriate watermark text for a property phase.

    Args:
        phase: Property phase (acquisition or sales) or None for default

    Returns:
        Watermark text appropriate for the phase
    """
    if phase is None:
        return DEFAULT_WATERMARK_TEXT

    # Handle string input
    if isinstance(phase, str):
        phase_lower = phase.lower()
        if phase_lower == "acquisition":
            return PHASE_WATERMARK_TEXT[PropertyPhase.ACQUISITION]
        elif phase_lower == "sales":
            return PHASE_WATERMARK_TEXT[PropertyPhase.SALES]
        else:
            return DEFAULT_WATERMARK_TEXT

    # Handle enum input
    return PHASE_WATERMARK_TEXT.get(phase, DEFAULT_WATERMARK_TEXT)


# Watermark styling constants
WATERMARK_OPACITY = 128  # 0-255 (50% opacity)
WATERMARK_COLOR = (255, 255, 255)  # White
WATERMARK_SHADOW_COLOR = (0, 0, 0)  # Black shadow
WATERMARK_PADDING = 20
WATERMARK_FONT_SIZE_RATIO = 0.03  # Font size as ratio of image width


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a font for watermark text, falling back to default if needed."""
    # Try common system fonts in order of preference
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/usr/share/fonts/TTF/DejaVuSans.ttf",  # Arch Linux
        "C:\\Windows\\Fonts\\arial.ttf",  # Windows
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue

    # Fall back to PIL default font
    return ImageFont.load_default()


def apply_watermark(
    image_data: bytes,
    text: str = DEFAULT_WATERMARK_TEXT,
    position: str = "bottom-right",
    opacity: int = WATERMARK_OPACITY,
) -> bytes:
    """
    Apply a text watermark to an image.

    Args:
        image_data: Raw image bytes (JPEG, PNG, etc.)
        text: Watermark text to apply
        position: Position of watermark ("bottom-right", "bottom-left",
                  "top-right", "top-left", "center", "diagonal")
        opacity: Watermark opacity (0-255, default 128 = 50%)

    Returns:
        Watermarked image as JPEG bytes
    """
    if Image is None:
        logger.warning("PIL not available, returning original image")
        return image_data

    try:
        # Open the image
        img = Image.open(BytesIO(image_data))

        # Convert to RGBA for transparency support
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Create a transparent overlay for the watermark
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        # Calculate font size based on image dimensions
        font_size = max(16, int(img.width * WATERMARK_FONT_SIZE_RATIO))
        font = _get_font(font_size)

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        x, y = _calculate_position(
            img.size, (text_width, text_height), position, WATERMARK_PADDING
        )

        # Draw shadow (offset by 2 pixels)
        shadow_color = (*WATERMARK_SHADOW_COLOR, opacity)
        draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)

        # Draw main watermark text
        watermark_color = (*WATERMARK_COLOR, opacity)
        draw.text((x, y), text, font=font, fill=watermark_color)

        # Composite the watermark onto the original image
        watermarked = Image.alpha_composite(img, watermark_layer)

        # Convert back to RGB for JPEG output
        watermarked_rgb = watermarked.convert("RGB")

        # Save to bytes
        output = BytesIO()
        watermarked_rgb.save(output, format="JPEG", quality=90)
        output.seek(0)

        return output.getvalue()

    except Exception as e:
        logger.error(f"Failed to apply watermark: {str(e)}")
        return image_data


def apply_diagonal_watermark(
    image_data: bytes,
    text: str = DEFAULT_WATERMARK_TEXT,
    opacity: int = WATERMARK_OPACITY,
    repeat: bool = True,
) -> bytes:
    """
    Apply a diagonal watermark pattern across the entire image.

    This is more visible and harder to crop out, suitable for
    draft/preview images that should not be used officially.

    Args:
        image_data: Raw image bytes
        text: Watermark text
        opacity: Watermark opacity (0-255)
        repeat: If True, repeat the watermark across the image

    Returns:
        Watermarked image as JPEG bytes
    """
    if Image is None:
        logger.warning("PIL not available, returning original image")
        return image_data

    try:
        # Open and convert to RGBA
        img = Image.open(BytesIO(image_data))
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # Create watermark layer
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))

        # Calculate font size - larger for diagonal watermarks
        font_size = max(24, int(img.width * 0.04))
        font = _get_font(font_size)

        # Create a temporary image to get text dimensions
        temp_draw = ImageDraw.Draw(watermark_layer)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Create canvas for the text (will be rotated after)
        text_img = Image.new("RGBA", (text_width + 50, text_height + 20), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)

        # Draw text with shadow
        shadow_color = (*WATERMARK_SHADOW_COLOR, min(opacity, 100))
        text_draw.text((27, 12), text, font=font, fill=shadow_color)

        watermark_color = (*WATERMARK_COLOR, opacity)
        text_draw.text((25, 10), text, font=font, fill=watermark_color)

        # Rotate the text
        rotated_text = text_img.rotate(
            45, expand=True, resample=Image.Resampling.BICUBIC
        )

        if repeat:
            # Tile the watermark across the image
            spacing_x = rotated_text.width + 100
            spacing_y = rotated_text.height + 100

            for y in range(-spacing_y, img.height + spacing_y, spacing_y):
                for x in range(-spacing_x, img.width + spacing_x, spacing_x):
                    watermark_layer.paste(rotated_text, (x, y), rotated_text)
        else:
            # Single centered diagonal watermark
            x = (img.width - rotated_text.width) // 2
            y = (img.height - rotated_text.height) // 2
            watermark_layer.paste(rotated_text, (x, y), rotated_text)

        # Composite
        watermarked = Image.alpha_composite(img, watermark_layer)
        watermarked_rgb = watermarked.convert("RGB")

        output = BytesIO()
        watermarked_rgb.save(output, format="JPEG", quality=90)
        output.seek(0)

        return output.getvalue()

    except Exception as e:
        logger.error(f"Failed to apply diagonal watermark: {str(e)}")
        return image_data


def _calculate_position(
    image_size: Tuple[int, int],
    text_size: Tuple[int, int],
    position: str,
    padding: int,
) -> Tuple[int, int]:
    """Calculate watermark position based on position string."""
    img_width, img_height = image_size
    text_width, text_height = text_size

    positions = {
        "bottom-right": (
            img_width - text_width - padding,
            img_height - text_height - padding,
        ),
        "bottom-left": (padding, img_height - text_height - padding),
        "top-right": (img_width - text_width - padding, padding),
        "top-left": (padding, padding),
        "center": (
            (img_width - text_width) // 2,
            (img_height - text_height) // 2,
        ),
    }

    return positions.get(position, positions["bottom-right"])


def should_apply_watermark(
    is_marketing_material: bool = True,
    has_approved_signoff: bool = False,
    force_watermark: bool = False,
) -> bool:
    """
    Determine if watermark should be applied based on context.

    Args:
        is_marketing_material: True if this is for marketing/feasibility
        has_approved_signoff: True if architect has approved
        force_watermark: Always apply watermark if True

    Returns:
        True if watermark should be applied
    """
    if force_watermark:
        return True

    if is_marketing_material and not has_approved_signoff:
        return True

    return False


__all__ = [
    "apply_watermark",
    "apply_diagonal_watermark",
    "should_apply_watermark",
    "get_watermark_text_for_phase",
    "PropertyPhase",
    "PHASE_WATERMARK_TEXT",
    "DEFAULT_WATERMARK_TEXT",
]
