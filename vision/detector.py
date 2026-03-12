from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Detection:
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int

    def as_dict(self) -> Dict[str, Any]:
        return {"bbox": self.bbox, "confidence": self.confidence, "class": self.class_id}


class Detector:
    """
    Thin YOLO wrapper.

    Returns a list of dicts shaped like:
      {"bbox": (x1, y1, x2, y2), "confidence": float, "class": int}
    """

    def __init__(self, weights_path: Optional[str] = None):
        weights = (
            Path(weights_path)
            if weights_path
            else (Path(__file__).resolve().parents[1] / "models" / "yolov8n.pt")
        )

        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "ultralytics is not installed. Install requirements.txt first."
            ) from e

        if not weights.exists():
            raise FileNotFoundError(f"YOLO weights not found at: {weights}")

        self._weights_path = weights
        self._model = YOLO(str(weights))

    @property
    def weights_path(self) -> Path:
        return self._weights_path

    def detect(self, frame) -> List[Dict[str, Any]]:
        results = self._model(frame, verbose=False)
        detections: List[Dict[str, Any]] = []

        for r in results:
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                detections.append(
                    Detection(
                        bbox=(float(x1), float(y1), float(x2), float(y2)),
                        confidence=conf,
                        class_id=cls,
                    ).as_dict()
                )

        return detections