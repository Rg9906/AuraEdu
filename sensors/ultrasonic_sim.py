"""
Ultrasonic sensor simulation for Aura-Edu system.
Simulates 4-directional distance sensors with realistic behavior.
"""

import time
import random
import math
from typing import Optional, Dict, Any
from core.types import Direction, SensorReading
from sensors.base_sensor import BaseSensor


class UltrasonicSimulator(BaseSensor):
    """
    Simulates ultrasonic distance sensors with realistic behavior.
    Supports object approach simulation and user reaction monitoring.
    """
    
    def __init__(self, direction: Direction, sensor_id: str, config=None):
        super().__init__(direction, sensor_id)
        
        # Default configuration
        self.max_range = 400.0 if not config else config.sensors.ultrasonic_max_range
        self.min_range = 2.0 if not config else config.sensors.ultrasonic_min_range
        self.noise_level = 0.1 if not config else config.sensors.noise_level
        self.approach_speed = 50.0 if not config else config.sensors.approach_speed
        
        # Simulation state
        self.current_distance = 200.0  # Start with mid-range distance
        self.target_distance = 200.0
        self.is_approaching = False
        self.approach_start_time = None
        self.simulation_start_time = time.time()
        
    def start(self) -> bool:
        """Start the ultrasonic sensor simulation."""
        self.is_active = True
        self.simulation_start_time = time.time()
        return True
    
    def stop(self) -> bool:
        """Stop the ultrasonic sensor simulation."""
        self.is_active = False
        return True
    
    def read(self) -> Optional[SensorReading]:
        """
        Read simulated distance with realistic noise and behavior.
        
        Returns:
            SensorReading with distance data or None if sensor inactive.
        """
        if not self.is_active:
            return None
        
        # Update distance based on simulation state
        self._update_distance()
        
        # Add realistic noise
        noise = random.gauss(0, self.noise_level * self.current_distance)
        noisy_distance = max(self.min_range, min(self.max_range, self.current_distance + noise))
        
        # Create sensor reading
        reading = SensorReading(
            direction=self.direction,
            distance=noisy_distance,
            timestamp=time.time(),
            confidence=1.0 - abs(noise) / self.current_distance if self.current_distance > 0 else 0.5
        )
        
        self.last_reading = reading
        return reading
    
    def _update_distance(self):
        """Update distance based on simulation state."""
        current_time = time.time()
        
        if self.is_approaching and self.approach_start_time:
            # Object approaching - decrease distance
            elapsed = current_time - self.approach_start_time
            distance_change = self.approach_speed * elapsed
            self.current_distance = max(self.min_range, self.target_distance - distance_change)
        else:
            # Gradual drift towards target
            diff = self.target_distance - self.current_distance
            self.current_distance += diff * 0.1  # Smooth convergence
    
    def simulate_approaching_object(self, initial_distance: float = 200.0, target_distance: float = 30.0):
        """
        Simulate an object approaching this sensor.
        
        Args:
            initial_distance: Starting distance in cm
            target_distance: Target distance in cm
        """
        self.current_distance = initial_distance
        self.target_distance = target_distance
        self.is_approaching = True
        self.approach_start_time = time.time()
    
    def simulate_user_reaction(self, retreat_distance: float = 100.0):
        """
        Simulate user reacting and moving away from object.
        
        Args:
            retreat_distance: New distance after reaction in cm
        """
        self.is_approaching = False
        self.target_distance = retreat_distance
        self.approach_start_time = None
    
    def simulate_random_movement(self):
        """Simulate random environmental movement."""
        if not self.is_approaching:
            # Random walk for ambient movement
            change = random.gauss(0, 5.0)
            self.target_distance = max(self.min_range, min(self.max_range, self.target_distance + change))
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """
        Get detailed simulation status.
        
        Returns:
            Dictionary with simulation state information.
        """
        return {
            **self.get_status(),
            "current_distance": self.current_distance,
            "target_distance": self.target_distance,
            "is_approaching": self.is_approaching,
            "approach_start_time": self.approach_start_time,
            "simulation_duration": time.time() - self.simulation_start_time if self.simulation_start_time else 0
        }


class UltrasonicArray:
    """
    Manages an array of 4 ultrasonic sensors (LEFT, RIGHT, FRONT, BACK).
    """
    
    def __init__(self, config=None):
        self.config = config
        self.sensors: Dict[Direction, UltrasonicSimulator] = {}
        self.is_active = False
        
        # Create sensors for all directions
        for direction in [Direction.LEFT, Direction.RIGHT, Direction.FRONT, Direction.BACK]:
            sensor_id = f"ultrasonic_{direction.value.lower()}"
            self.sensors[direction] = UltrasonicSimulator(direction, sensor_id, config)
    
    def start(self) -> bool:
        """Start all ultrasonic sensors."""
        success = True
        for sensor in self.sensors.values():
            if not sensor.start():
                success = False
        self.is_active = success
        return success
    
    def stop(self) -> bool:
        """Stop all ultrasonic sensors."""
        success = True
        for sensor in self.sensors.values():
            if not sensor.stop():
                success = False
        self.is_active = False
        return success
    
    def read_all(self) -> Dict[Direction, SensorReading]:
        """
        Read from all sensors.
        
        Returns:
            Dictionary mapping directions to sensor readings.
        """
        readings = {}
        for direction, sensor in self.sensors.items():
            reading = sensor.read()
            if reading:
                readings[direction] = reading
        return readings
    
    def get_sensor(self, direction: Direction) -> Optional[UltrasonicSimulator]:
        """Get sensor for specific direction."""
        return self.sensors.get(direction)
    
    def simulate_approaching_object(self, direction: Direction, **kwargs):
        """Simulate approaching object from specific direction."""
        sensor = self.get_sensor(direction)
        if sensor:
            sensor.simulate_approaching_object(**kwargs)
    
    def simulate_user_reaction(self, direction: Direction, **kwargs):
        """Simulate user reaction to object from specific direction."""
        sensor = self.get_sensor(direction)
        if sensor:
            sensor.simulate_user_reaction(**kwargs)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all sensors."""
        return {
            "array_active": self.is_active,
            "sensors": {direction.value: sensor.get_simulation_status() 
                       for direction, sensor in self.sensors.items()}
        }
