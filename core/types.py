"""
Core type definitions for Aura-Edu system.
"""

from enum import Enum
from typing import Literal, Dict, Any, Tuple, Optional
from dataclasses import dataclass


class Direction(Enum):
    """Spatial directions for object detection and feedback."""
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FRONT = "FRONT"
    BACK = "BACK"
    CENTER = "CENTER"


class Danger(Enum):
    """Danger levels for detected objects."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ResponseType(Enum):
    """Types of system responses."""
    SELF_RECOGNIZED = "SELF_RECOGNIZED"
    ASSISTED_RESPONSE = "ASSISTED_RESPONSE"
    MISSED_STIMULUS = "MISSED_STIMULUS"


class SystemState(Enum):
    """System operational states."""
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    ALERT = "ALERT"
    MAINTENANCE = "MAINTENANCE"


class VibrationPattern(Enum):
    """Vibration patterns for haptic feedback."""
    SINGLE_PULSE = "SINGLE_PULSE"
    DOUBLE_PULSE = "DOUBLE_PULSE"
    CONTINUOUS = "CONTINUOUS"
    ESCALATING = "ESCALATING"


@dataclass(frozen=True)
class Detection:
    """Object detection result."""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "bbox": self.bbox,
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name
        }


@dataclass(frozen=True)
class Stimulus:
    """Environmental stimulus with spatial and danger metadata."""
    bbox: Tuple[float, float, float, float]
    direction: Direction
    area: float
    danger: Danger
    confidence: float
    class_id: int
    class_name: Optional[str] = None
    estimated_distance: Optional[float] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "bbox": self.bbox,
            "direction": self.direction.value,
            "area": self.area,
            "danger": self.danger.value,
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "estimated_distance": self.estimated_distance
        }


@dataclass(frozen=True)
class Decision:
    """System decision for feedback intervention."""
    action: Literal["NONE", "VIBRATE_LEFT", "VIBRATE_RIGHT", "VIBRATE_FRONT", "VIBRATE_BACK"]
    intensity: float  # 0..1
    response_type: ResponseType
    pattern: VibrationPattern = VibrationPattern.SINGLE_PULSE

    def as_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "intensity": float(self.intensity),
            "response_type": self.response_type.value,
            "pattern": self.pattern.value
        }


@dataclass(frozen=True)
class SensorReading:
    """Sensor data from ultrasonic sensors."""
    direction: Direction
    distance: float  # in cm
    timestamp: float
    confidence: float = 1.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "distance": self.distance,
            "timestamp": self.timestamp,
            "confidence": self.confidence
        }


@dataclass(frozen=True)
class ReactionResult:
    """Result of user reaction monitoring."""
    user_responded: bool
    reaction_time: Optional[float]  # in seconds
    initial_distance: float
    final_distance: float
    direction: Direction
    stimulus_id: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "user_responded": self.user_responded,
            "reaction_time": self.reaction_time,
            "initial_distance": self.initial_distance,
            "final_distance": self.final_distance,
            "direction": self.direction.value,
            "stimulus_id": self.stimulus_id
        }


@dataclass(frozen=True)
class SystemEvent:
    """Complete event log for analytics."""
    timestamp: float
    stimulus: Optional[Stimulus]
    reaction_result: Optional[ReactionResult]
    decision: Decision
    sensor_reading: Optional[SensorReading]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "stimulus": self.stimulus.as_dict() if self.stimulus else None,
            "reaction_result": self.reaction_result.as_dict() if self.reaction_result else None,
            "decision": self.decision.as_dict(),
            "sensor_reading": self.sensor_reading.as_dict() if self.sensor_reading else None
        }
