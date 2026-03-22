"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class DirectionEnum(str, Enum):
    """Direction enum for API."""
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FRONT = "FRONT"
    BACK = "BACK"
    CENTER = "CENTER"


class DangerEnum(str, Enum):
    """Danger level enum for API."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ResponseTypeEnum(str, Enum):
    """Response type enum for API."""
    SELF_RECOGNIZED = "SELF_RECOGNIZED"
    ASSISTED_RESPONSE = "ASSISTED_RESPONSE"
    MISSED_STIMULUS = "MISSED_STIMULUS"


class SystemStateEnum(str, Enum):
    """System state enum for API."""
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    ALERT = "ALERT"
    MAINTENANCE = "MAINTENANCE"


# Request Models
class VibrationRequest(BaseModel):
    """Request model for triggering vibration."""
    direction: DirectionEnum
    intensity: float = Field(ge=0.0, le=1.0, description="Vibration intensity (0.0 to 1.0)")
    pattern: str = Field(default="SINGLE_PULSE", description="Vibration pattern")
    duration: Optional[float] = Field(default=None, ge=0.1, le=5.0, description="Duration in seconds")


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    section: str = Field(description="Configuration section to update")
    updates: Dict[str, Any] = Field(description="Configuration updates")


# Response Models
class StimulusResponse(BaseModel):
    """Response model for stimulus data."""
    bbox: List[float]
    direction: DirectionEnum
    area: float
    danger: DangerEnum
    confidence: float
    class_id: int
    class_name: Optional[str] = None
    estimated_distance: Optional[float] = None


class DecisionResponse(BaseModel):
    """Response model for decision data."""
    action: str
    intensity: float
    response_type: ResponseTypeEnum
    pattern: str


class SensorReadingResponse(BaseModel):
    """Response model for sensor reading data."""
    direction: DirectionEnum
    distance: float
    timestamp: float
    confidence: float


class EventResponse(BaseModel):
    """Response model for system event data."""
    timestamp: float
    stimulus: Optional[StimulusResponse] = None
    decision: DecisionResponse
    reaction_result: Optional[Dict[str, Any]] = None
    sensor_reading: Optional[SensorReadingResponse] = None


class MetricsResponse(BaseModel):
    """Response model for metrics data."""
    timestamp: float
    session: Dict[str, Any]
    awareness_score: Dict[str, Any]
    left_vs_right_analysis: Dict[str, Any]
    system_health: Dict[str, Any]


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    state: SystemStateEnum
    uptime_seconds: float
    battery_level: float
    active_observations: int
    last_intervention: Optional[float] = None
    system_health: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str
    message: str
    timestamp: float


class SuccessResponse(BaseModel):
    """Response model for success responses."""
    success: bool
    message: str
    timestamp: float


# Live Data Response
class LiveDataResponse(BaseModel):
    """Response model for live system data."""
    timestamp: float
    current_stimuli: List[StimulusResponse]
    active_observations: List[Dict[str, Any]]
    recent_decisions: List[DecisionResponse]
    system_metrics: MetricsResponse
    system_status: SystemStatusResponse


# Historical Data Response
class HistoricalDataResponse(BaseModel):
    """Response model for historical data."""
    period_days: int
    daily_metrics: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]
    progress_trend: Dict[str, Any]
    summary: Dict[str, Any]


# Configuration Response
class ConfigurationResponse(BaseModel):
    """Response model for configuration data."""
    vision: Dict[str, Any]
    sensors: Dict[str, Any]
    decision: Dict[str, Any]
    feedback: Dict[str, Any]
    hardware: Dict[str, Any]
    system: Dict[str, Any]


# Export Response
class ExportResponse(BaseModel):
    """Response model for data export."""
    export_id: str
    format: str
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
