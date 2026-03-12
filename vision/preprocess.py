from __future__ import annotations

from typing import Optional


def preprocess_frame(frame, target_width: Optional[int] = None):
    """
    Minimal preprocessing hook.

    - Optionally resize for speed.
    - Keep return type compatible with OpenCV / Ultralytics.
    """
    if frame is None:
        return None

    if target_width is None:
        return frame

    try:
        import cv2  # type: ignore
    except Exception:
        return frame

    h, w = frame.shape[:2]
    if w == 0:
        return frame
    scale = target_width / float(w)
    target_height = int(h * scale)
    return cv2.resize(frame, (target_width, target_height))
