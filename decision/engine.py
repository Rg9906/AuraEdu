"""
Core decision engine for Aura-Edu closed-loop system.
Implements wait-and-observe approach with reaction monitoring.
"""

import time
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from core.types import (
    Direction, Stimulus, Decision, ResponseType, VibrationPattern,
    SensorReading, ReactionResult, SystemEvent
)


@dataclass
class ObservationState:
    """State for monitoring user reaction to a stimulus."""
    stimulus_id: str
    stimulus: Stimulus
    start_time: float
    initial_distance: float
    initial_sensor_reading: Optional[SensorReading]
    is_monitoring: bool = True
    last_distance: float = field(default=0.0)
    distance_readings: List[float] = field(default_factory=list)
    
    def add_distance_reading(self, distance: float, timestamp: float):
        """Add a new distance reading during observation."""
        self.last_distance = distance
        self.distance_readings.append((timestamp, distance))
    
    def get_reaction_result(self) -> ReactionResult:
        """Calculate reaction result based on distance changes."""
        if not self.distance_readings:
            # No readings during observation window
            return ReactionResult(
                user_responded=False,
                reaction_time=None,
                initial_distance=self.initial_distance,
                final_distance=self.initial_distance,
                direction=self.stimulus.direction,
                stimulus_id=self.stimulus_id
            )
        
        # Analyze distance trend
        final_distance = self.last_distance
        distance_change = final_distance - self.initial_distance
        
        # User responded if distance increased significantly
        user_responded = distance_change > 10.0  # 10cm threshold
        
        reaction_time = None
        if user_responded and len(self.distance_readings) > 1:
            # Find when distance started increasing
            for i in range(1, len(self.distance_readings)):
                prev_time, prev_dist = self.distance_readings[i-1]
                curr_time, curr_dist = self.distance_readings[i]
                if curr_dist > prev_dist + 5.0:  # 5cm increase threshold
                    reaction_time = curr_time - self.start_time
                    break
        
        return ReactionResult(
            user_responded=user_responded,
            reaction_time=reaction_time,
            initial_distance=self.initial_distance,
            final_distance=final_distance,
            direction=self.stimulus.direction,
            stimulus_id=self.stimulus_id
        )


class DecisionEngine:
    """
    Core decision engine implementing the wait-and-observe approach.
    Monitors user reactions before deciding on intervention.
    """
    
    def __init__(self, config=None):
        self.config = config
        self.observations: Dict[str, ObservationState] = {}
        self.last_intervention_time = 0.0
        self.intervention_cooldown = 1.0 if not config else config.decision.intervention_cooldown
        self.observation_window = 2.0 if not config else config.decision.observation_window
        self.critical_distance = 50.0 if not config else config.decision.critical_distance
        self.neglected_side = "LEFT" if not config else config.decision.neglected_side
    
    def process_stimulus(self, stimulus: Stimulus, sensor_reading: Optional[SensorReading] = None) -> Decision:
        """
        Process a new stimulus and decide on intervention.
        
        Args:
            stimulus: Detected environmental stimulus
            sensor_reading: Corresponding sensor distance reading
            
        Returns:
            Decision object with action to take.
        """
        current_time = time.time()
        
        # Check if already monitoring this stimulus
        stimulus_id = self._get_stimulus_id(stimulus)
        if stimulus_id in self.observations:
            return self._continue_observation(stimulus_id, sensor_reading)
        
        # Start new observation
        observation = ObservationState(
            stimulus_id=stimulus_id,
            stimulus=stimulus,
            start_time=current_time,
            initial_distance=sensor_reading.distance if sensor_reading else stimulus.estimated_distance or 100.0,
            initial_sensor_reading=sensor_reading
        )
        
        self.observations[stimulus_id] = observation
        
        # Check for immediate intervention conditions
        if self._needs_immediate_intervention(stimulus, sensor_reading):
            return self._trigger_intervention(observation, immediate=True)
        
        # No immediate action - continue monitoring
        return Decision(
            action="NONE",
            intensity=0.0,
            response_type=ResponseType.SELF_RECOGNIZED,
            pattern=VibrationPattern.SINGLE_PULSE
        )
    
    def update_observations(self, sensor_readings: Dict[Direction, SensorReading]) -> List[Decision]:
        """
        Update ongoing observations with new sensor data.
        
        Args:
            sensor_readings: Current sensor readings by direction
            
        Returns:
            List of decisions from completed observations.
        """
        current_time = time.time()
        decisions = []
        
        # Update observations with new sensor data
        for stimulus_id, observation in list(self.observations.items()):
            direction = observation.stimulus.direction
            
            # Find corresponding sensor reading
            sensor_reading = sensor_readings.get(direction)
            if sensor_reading:
                observation.add_distance_reading(sensor_reading.distance, current_time)
            
            # Check if observation window is complete
            observation_duration = current_time - observation.start_time
            if observation_duration >= self.observation_window:
                decision = self._complete_observation(observation)
                decisions.append(decision)
                del self.observations[stimulus_id]
            else:
                # Check for critical distance requiring immediate intervention
                if observation.last_distance < self.critical_distance:
                    decision = self._trigger_intervention(observation, immediate=True)
                    decisions.append(decision)
                    del self.observations[stimulus_id]
        
        return decisions
    
    def _continue_observation(self, stimulus_id: str, sensor_reading: Optional[SensorReading]) -> Decision:
        """Continue monitoring an existing stimulus."""
        observation = self.observations[stimulus_id]
        
        if sensor_reading:
            observation.add_distance_reading(sensor_reading.distance, time.time())
        
        return Decision(
            action="NONE",
            intensity=0.0,
            response_type=ResponseType.SELF_RECOGNIZED,
            pattern=VibrationPattern.SINGLE_PULSE
        )
    
    def _complete_observation(self, observation: ObservationState) -> Decision:
        """Complete observation and make final decision."""
        reaction_result = observation.get_reaction_result()
        
        if reaction_result.user_responded:
            # User responded successfully
            return Decision(
                action="NONE",
                intensity=0.0,
                response_type=ResponseType.SELF_RECOGNIZED,
                pattern=VibrationPattern.SINGLE_PULSE
            )
        else:
            # User did not respond - trigger intervention
            return self._trigger_intervention(observation, immediate=False)
    
    def _needs_immediate_intervention(self, stimulus: Stimulus, sensor_reading: Optional[SensorReading]) -> bool:
        """Check if stimulus requires immediate intervention."""
        # Check critical distance
        if sensor_reading and sensor_reading.distance < self.critical_distance:
            return True
        
        # Check estimated distance from vision
        if stimulus.estimated_distance and stimulus.estimated_distance < self.critical_distance:
            return True
        
        # Check high danger level
        if stimulus.danger.value == "HIGH":
            return True
        
        return False
    
    def _trigger_intervention(self, observation: ObservationState, immediate: bool = False) -> Decision:
        """Trigger haptic intervention."""
        current_time = time.time()
        
        # Check intervention cooldown
        if current_time - self.last_intervention_time < self.intervention_cooldown and not immediate:
            return Decision(
                action="NONE",
                intensity=0.0,
                response_type=ResponseType.SELF_RECOGNIZED,
                pattern=VibrationPattern.SINGLE_PULSE
            )
        
        self.last_intervention_time = current_time
        
        # Determine action based on direction
        direction = observation.stimulus.direction
        action = self._direction_to_action(direction)
        
        # Determine intensity based on danger
        intensity = self._danger_to_intensity(observation.stimulus.danger)
        
        # Choose vibration pattern
        pattern = VibrationPattern.ESCALATING if observation.stimulus.danger.value == "HIGH" else VibrationPattern.DOUBLE_PULSE
        
        return Decision(
            action=action,
            intensity=intensity,
            response_type=ResponseType.ASSISTED_RESPONSE,
            pattern=pattern
        )
    
    def _direction_to_action(self, direction: Direction) -> str:
        """Convert direction to vibration action."""
        action_map = {
            Direction.LEFT: "VIBRATE_LEFT",
            Direction.RIGHT: "VIBRATE_RIGHT",
            Direction.FRONT: "VIBRATE_FRONT",
            Direction.BACK: "VIBRATE_BACK",
            Direction.CENTER: "NONE"
        }
        return action_map.get(direction, "NONE")
    
    def _danger_to_intensity(self, danger) -> float:
        """Convert danger level to vibration intensity."""
        intensity_map = {
            "LOW": 0.3,
            "MEDIUM": 0.6,
            "HIGH": 1.0
        }
        return intensity_map.get(danger.value, 0.5)
    
    def _get_stimulus_id(self, stimulus: Stimulus) -> str:
        """Generate unique ID for stimulus tracking."""
        # Create ID based on direction, class, and approximate location
        location_hash = hash((int(stimulus.bbox[0]), int(stimulus.bbox[1])))
        return f"{stimulus.direction.value}_{stimulus.class_id}_{abs(location_hash) % 10000}"
    
    def get_active_observations(self) -> List[Dict[str, Any]]:
        """Get information about currently active observations."""
        current_time = time.time()
        active = []
        
        for stimulus_id, observation in self.observations.items():
            duration = current_time - observation.start_time
            active.append({
                "stimulus_id": stimulus_id,
                "direction": observation.stimulus.direction.value,
                "class_name": observation.stimulus.class_name,
                "observation_duration": duration,
                "initial_distance": observation.initial_distance,
                "current_distance": observation.last_distance,
                "progress": min(1.0, duration / self.observation_window)
            })
        
        return active
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get decision engine status."""
        return {
            "active_observations": len(self.observations),
            "last_intervention_time": self.last_intervention_time,
            "time_since_last_intervention": time.time() - self.last_intervention_time,
            "neglected_side": self.neglected_side,
            "observation_window": self.observation_window,
            "critical_distance": self.critical_distance,
            "intervention_cooldown": self.intervention_cooldown
        }
