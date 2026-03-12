from __future__ import annotations

from typing import Dict, Tuple


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def bbox_center_x(bbox: Tuple[float, float, float, float]) -> float:
    x1, _, x2, _ = bbox
    return (x1 + x2) / 2.0


def safe_frame_width(frame) -> int:
    try:
        return int(frame.shape[1])
    except Exception:
        return 0
