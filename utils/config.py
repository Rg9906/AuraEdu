from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class VisionConfig:
    """Vision system configuration."""
    camera_index: int = 0
    preprocess_width: int = 960
    yolo_model_path: str = "models/yolov8n.pt"
    detection_confidence: float = 0.5
    target_fps: int = 30


@dataclass(frozen=True)
class SensorConfig:
    """Sensor simulation configuration."""
    ultrasonic_max_range: float = 400.0  # cm
    ultrasonic_min_range: float = 2.0   # cm
    noise_level: float = 0.1
    update_frequency: float = 10.0  # Hz
    approach_speed: float = 50.0  # cm/s when simulating approaching objects


@dataclass(frozen=True)
class DecisionConfig:
    """Decision engine configuration."""
    observation_window: float = 2.0  # seconds to wait for user reaction
    critical_distance: float = 50.0  # cm - trigger intervention if closer
    reaction_distance_threshold: float = 10.0  # cm change to consider as reaction
    neglected_side: str = "LEFT"
    intervention_cooldown: float = 1.0  # seconds between interventions


@dataclass(frozen=True)
class FeedbackConfig:
    """Haptic feedback configuration."""
    vibration_duration: float = 0.5  # seconds
    max_intensity: float = 1.0
    intensity_mapping: Dict[str, float] = None
    
    def __post_init__(self):
        if self.intensity_mapping is None:
            object.__setattr__(self, 'intensity_mapping', {
                "LOW": 0.3,
                "MEDIUM": 0.6,
                "HIGH": 1.0
            })


@dataclass(frozen=True)
class HardwareConfig:
    """Hardware interface configuration."""
    esp32_port: str = "COM3"
    esp32_baudrate: int = 115200
    motor_count: int = 8
    motor_positions: Dict[str, int] = None
    
    def __post_init__(self):
        if self.motor_positions is None:
            object.__setattr__(self, 'motor_positions', {
                "LEFT": [0, 1],
                "RIGHT": [6, 7],
                "FRONT": [3, 4],
                "BACK": [2, 5]
            })


@dataclass(frozen=True)
class SystemConfig:
    """System monitoring configuration."""
    battery_capacity: float = 5000.0  # mAh
    battery_drain_rate: float = 100.0  # mAh/hour
    low_battery_threshold: float = 20.0  # percentage
    data_retention_days: int = 30
    log_level: str = "INFO"


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""
    vision: VisionConfig = VisionConfig()
    sensors: SensorConfig = SensorConfig()
    decision: DecisionConfig = DecisionConfig()
    feedback: FeedbackConfig = FeedbackConfig()
    hardware: HardwareConfig = HardwareConfig()
    system: SystemConfig = SystemConfig()
    
    # Legacy compatibility
    @property
    def camera_index(self) -> int:
        return self.vision.camera_index
    
    @property
    def neglected_side(self) -> str:
        return self.decision.neglected_side
    
    @property
    def preprocess_width(self) -> int:
        return self.vision.preprocess_width
    
    @property
    def esp32_port(self) -> str:
        return self.hardware.esp32_port
    
    @property
    def esp32_baudrate(self) -> int:
        return self.hardware.esp32_baudrate

    def as_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for API responses."""
        return {
            "vision": self.vision.__dict__,
            "sensors": self.sensors.__dict__,
            "decision": self.decision.__dict__,
            "feedback": self.feedback.__dict__,
            "hardware": self.hardware.__dict__,
            "system": self.system.__dict__
        }
