"""
Base sensor interface for Aura-Edu system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.types import Direction, SensorReading


class BaseSensor(ABC):
    """Abstract base class for all sensors in the Aura-Edu system."""
    
    def __init__(self, direction: Direction, sensor_id: str):
        self.direction = direction
        self.sensor_id = sensor_id
        self.is_active = False
        self.last_reading: Optional[SensorReading] = None
    
    @abstractmethod
    def read(self) -> Optional[SensorReading]:
        """
        Read sensor data.
        
        Returns:
            SensorReading object with current sensor data, or None if reading failed.
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start the sensor.
        
        Returns:
            True if sensor started successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the sensor.
        
        Returns:
            True if sensor stopped successfully, False otherwise.
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current sensor status.
        
        Returns:
            Dictionary containing sensor status information.
        """
        return {
            "sensor_id": self.sensor_id,
            "direction": self.direction.value,
            "is_active": self.is_active,
            "last_reading": self.last_reading.as_dict() if self.last_reading else None
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(direction={self.direction.value}, id={self.sensor_id})"
