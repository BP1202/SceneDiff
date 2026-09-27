"""Task 29 — Screenshot & Visual Artifact Collector.

Captures visual evidence (PNG screenshots) at key points in the user
journey.  Screenshots are stored as base64-encoded strings inside the
runtime artifact.

Design rules
------------
- Screenshots are EVIDENCE only — comparison logic uses DOM traces.
- Full-page and viewport captures are both supported.
- Images are capped at _MAX_IMAGE_BYTES before base64-encoding.
- No PII extraction from images.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)

_MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB cap per screenshot

ScreenshotType = Literal["full_page", "viewport", "element"]


@dataclass(frozen=True)
class ScreenshotArtifact:
    """A single captured screenshot."""

    route: str
    screenshot_type: ScreenshotType
    format: str  # "png"
    width: int
    height: int
    data_base64: str  # base64-encoded PNG bytes
    truncated: bool  # True if image was capped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def capture_screenshot(
    page: Page,
    route: str,
    screenshot_type: ScreenshotType = "full_page",
) -> ScreenshotArtifact:
    """Capture a screenshot of the current page.

    Args:
        page:            Active Playwright page.
        route:           Human-readable label for this checkpoint.
        screenshot_type: "full_page" | "viewport" | "element".

    Returns:
        Immutable ``ScreenshotArtifact`` with base64 PNG data.
    """
    full_page = screenshot_type == "full_page"

    raw_bytes: bytes = await page.screenshot(
        full_page=full_page,
        type="png",
    )

    truncated = False
    if len(raw_bytes) > _MAX_IMAGE_BYTES:
        raw_bytes = raw_bytes[:_MAX_IMAGE_BYTES]
        truncated = True
        logger.warning(
            "runtime.screenshots: image truncated to %d bytes route=%s",
            _MAX_IMAGE_BYTES,
            route,
        )

    data_b64 = base64.b64encode(raw_bytes).decode("ascii")

    viewport = page.viewport_size or {"width": 1280, "height": 720}

    artifact = ScreenshotArtifact(
        route=route,
        screenshot_type=screenshot_type,
        format="png",
        width=viewport.get("width", 1280),
        height=viewport.get("height", 720),
        data_base64=data_b64,
        truncated=truncated,
    )
    logger.info(
        "runtime.screenshots: captured route=%s type=%s size=%d bytes",
        route,
        screenshot_type,
        len(raw_bytes),
    )
    return artifact
