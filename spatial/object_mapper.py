from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

Side = Literal["LEFT", "CENTER", "RIGHT"]
Danger = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass(frozen=True)
class Stimulus:
    bbox: Tuple[float, float, float, float]
    side: Side
    area: float
    danger: Danger
    confidence: float
    class_id: int

    def as_dict(self) -> Dict:
        return {
            "bbox": self.bbox,
            "side": self.side,
            "area": self.area,
            "danger": self.danger,
            "confidence": self.confidence,
            "class": self.class_id,
        }


def bbox_area(bbox: Tuple[float, float, float, float]) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))


def area_to_danger(area: float) -> Danger:
    # Heuristic thresholds; tune per camera FOV + mounting height.
    if area >= 90_000:
        return "HIGH"
    if area >= 25_000:
        return "MEDIUM"
    return "LOW"


def map_detections(detections: List[Dict], frame_width: int) -> List[Dict]:
    """
    Converts YOLO detections into stimuli with side + danger metadata.
    """
    from spatial.side_detector import detect_side

    stimuli: List[Dict] = []
    for d in detections:
        bbox = tuple(d["bbox"])
        area = bbox_area(bbox)  # distance proxy
        side = detect_side(d, frame_width)
        danger = area_to_danger(area)
        stimuli.append(
            Stimulus(
                bbox=bbox,
                side=side,
                area=area,
                danger=danger,
                confidence=float(d.get("confidence", 0.0)),
                class_id=int(d.get("class", -1)),
            ).as_dict()
        )
    return stimuli


def pick_priority_stimulus(stimuli: List[Dict], neglected_side: Side = "LEFT") -> Dict | None:
    """
    Prioritization rule (simple + effective for prototype):
    - prefer neglected side
    - then highest danger (proxy: area)
    - then highest confidence
    """
    if not stimuli:
        return None

    def key(s: Dict):
        neglected_bonus = 1 if s["side"] == neglected_side else 0
        danger_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get(s["danger"], 0)
        return (neglected_bonus, danger_rank, float(s.get("area", 0.0)), float(s.get("confidence", 0.0)))

    return max(stimuli, key=key)
