"""
Enhanced feedback controller for Aura-Edu 8-motor vibration system.
Supports directional haptic feedback with multiple patterns and intensities.
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from core.types import Decision, Direction, VibrationPattern


@dataclass
class MotorCommand:
    """Command for individual vibration motor."""
    motor_id: int
    intensity: float  # 0.0 to 1.0
    duration: float   # seconds
    pattern: VibrationPattern


class VibrationController:
    """
    Controls 8-motor vibration belt for directional haptic feedback.
    Supports multiple vibration patterns and hardware-ready interface.
    """
    
    def __init__(self, config=None):
        self.config = config
        self.is_active = False
        
        # Motor configuration (8 motors around the body)
        self.motor_count = 8 if not config else config.hardware.motor_count
        self.motor_positions = {
            "LEFT": [0, 1],
            "RIGHT": [6, 7],
            "FRONT": [3, 4],
            "BACK": [2, 5]
        } if not config else config.hardware.motor_positions
        
        # Vibration settings
        self.vibration_duration = 0.5 if not config else config.feedback.vibration_duration
        self.max_intensity = 1.0 if not config else config.feedback.max_intensity
        self.intensity_mapping = {
            "LOW": 0.3,
            "MEDIUM": 0.6,
            "HIGH": 1.0
        } if not config else config.feedback.intensity_mapping
        
        # State tracking
        self.active_motors: Dict[int, threading.Timer] = {}
        self.last_feedback_time = 0.0
        self.feedback_history: List[Dict[str, Any]] = []
        
        # Hardware interface (simulation for now)
        self.hardware_interface = None
        self.simulation_mode = True
    
    def start(self) -> bool:
        """Start the vibration controller."""
        try:
            self.is_active = True
            if self.simulation_mode:
                print("🔧 Vibration controller started in simulation mode")
            return True
        except Exception as e:
            print(f"❌ Failed to start vibration controller: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the vibration controller and all active motors."""
        try:
            # Stop all active motors
            for motor_id, timer in self.active_motors.items():
                if timer.is_alive():
                    timer.cancel()
                self._stop_motor(motor_id)
            
            self.active_motors.clear()
            self.is_active = False
            
            if self.simulation_mode:
                print("🔧 Vibration controller stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop vibration controller: {e}")
            return False
    
    def apply_decision(self, decision: Decision) -> bool:
        """
        Apply a decision by triggering appropriate vibration feedback.
        
        Args:
            decision: Decision object with action and parameters
            
        Returns:
            True if feedback applied successfully, False otherwise.
        """
        if not self.is_active or decision.action == "NONE":
            return False
        
        try:
            motor_commands = self._decision_to_motor_commands(decision)
            
            # Execute motor commands
            for command in motor_commands:
                self._execute_motor_command(command)
            
            # Log feedback
            self._log_feedback(decision, motor_commands)
            
            self.last_feedback_time = time.time()
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply feedback: {e}")
            return False
    
    def _decision_to_motor_commands(self, decision: Decision) -> List[MotorCommand]:
        """Convert decision to motor commands."""
        commands = []
        
        if decision.action == "NONE":
            return commands
        
        # Get motor IDs for the action direction
        direction = self._action_to_direction(decision.action)
        motor_ids = self.motor_positions.get(direction, [])
        
        # Create commands for each motor in the direction
        for motor_id in motor_ids:
            command = MotorCommand(
                motor_id=motor_id,
                intensity=decision.intensity,
                duration=self.vibration_duration,
                pattern=decision.pattern
            )
            commands.append(command)
        
        return commands
    
    def _action_to_direction(self, action: str) -> str:
        """Convert action string to direction key."""
        action_to_direction = {
            "VIBRATE_LEFT": "LEFT",
            "VIBRATE_RIGHT": "RIGHT", 
            "VIBRATE_FRONT": "FRONT",
            "VIBRATE_BACK": "BACK"
        }
        return action_to_direction.get(action, "NONE")
    
    def _execute_motor_command(self, command: MotorCommand):
        """Execute a single motor command."""
        if command.pattern == VibrationPattern.SINGLE_PULSE:
            self._single_pulse(command)
        elif command.pattern == VibrationPattern.DOUBLE_PULSE:
            self._double_pulse(command)
        elif command.pattern == VibrationPattern.CONTINUOUS:
            self._continuous_vibration(command)
        elif command.pattern == VibrationPattern.ESCALATING:
            self._escalating_vibration(command)
    
    def _single_pulse(self, command: MotorCommand):
        """Execute single pulse vibration."""
        self._start_motor(command.motor_id, command.intensity)
        
        # Schedule motor stop
        timer = threading.Timer(
            command.duration,
            self._stop_motor,
            args=[command.motor_id]
        )
        timer.start()
        self.active_motors[command.motor_id] = timer
    
    def _double_pulse(self, command: MotorCommand):
        """Execute double pulse vibration."""
        pulse_duration = command.duration / 3
        pause_duration = command.duration / 3
        
        def pulse_sequence():
            # First pulse
            self._start_motor(command.motor_id, command.intensity)
            threading.Timer(pulse_duration, self._stop_motor, args=[command.motor_id]).start()
            
            # Second pulse
            threading.Timer(pulse_duration + pause_duration, 
                          self._start_motor, 
                          args=[command.motor_id, command.intensity]).start()
            threading.Timer(command.duration, 
                          self._stop_motor, 
                          args=[command.motor_id]).start()
        
        pulse_sequence()
    
    def _continuous_vibration(self, command: MotorCommand):
        """Execute continuous vibration for specified duration."""
        self._start_motor(command.motor_id, command.intensity)
        
        # Schedule motor stop
        timer = threading.Timer(
            command.duration,
            self._stop_motor,
            args=[command.motor_id]
        )
        timer.start()
        self.active_motors[command.motor_id] = timer
    
    def _escalating_vibration(self, command: MotorCommand):
        """Execute escalating vibration pattern."""
        steps = 5
        step_duration = command.duration / steps
        
        def escalate_step(step: int):
            if step >= steps:
                self._stop_motor(command.motor_id)
                return
            
            # Calculate escalating intensity
            intensity = command.intensity * ((step + 1) / steps)
            self._start_motor(command.motor_id, intensity)
            
            # Schedule next step
            threading.Timer(
                step_duration,
                escalate_step,
                args=[step + 1]
            ).start()
        
        escalate_step(0)
    
    def _start_motor(self, motor_id: int, intensity: float):
        """Start a motor with specified intensity."""
        if self.simulation_mode:
            direction_name = self._get_motor_direction_name(motor_id)
            print(f"⚡ START Motor {motor_id} ({direction_name}) - Intensity: {intensity:.2f}")
        else:
            # Real hardware interface would go here
            if self.hardware_interface:
                self.hardware_interface.start_motor(motor_id, intensity)
    
    def _stop_motor(self, motor_id: int):
        """Stop a motor."""
        if self.simulation_mode:
            direction_name = self._get_motor_direction_name(motor_id)
            print(f"⚡ STOP Motor {motor_id} ({direction_name})")
        else:
            # Real hardware interface would go here
            if self.hardware_interface:
                self.hardware_interface.stop_motor(motor_id)
        
        # Remove from active motors if present
        if motor_id in self.active_motors:
            del self.active_motors[motor_id]
    
    def _get_motor_direction_name(self, motor_id: int) -> str:
        """Get direction name for motor ID."""
        for direction, motor_ids in self.motor_positions.items():
            if motor_id in motor_ids:
                return direction
        return "UNKNOWN"
    
    def _log_feedback(self, decision: Decision, commands: List[MotorCommand]):
        """Log feedback event for analytics."""
        log_entry = {
            "timestamp": time.time(),
            "decision": decision.as_dict(),
            "motor_commands": [
                {
                    "motor_id": cmd.motor_id,
                    "intensity": cmd.intensity,
                    "duration": cmd.duration,
                    "pattern": cmd.pattern.value
                }
                for cmd in commands
            ],
            "directions_activated": list(set(
                self._get_motor_direction_name(cmd.motor_id) for cmd in commands
            ))
        }
        
        self.feedback_history.append(log_entry)
        
        # Keep history size manageable
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-500:]
    
    def trigger_direction(self, direction: Direction, intensity: float = 0.5, 
                         pattern: VibrationPattern = VibrationPattern.SINGLE_PULSE):
        """
        Trigger vibration for specific direction.
        
        Args:
            direction: Direction to vibrate
            intensity: Vibration intensity (0.0 to 1.0)
            pattern: Vibration pattern to use
        """
        action = f"VIBRATE_{direction.value}"
        decision = Decision(
            action=action,
            intensity=min(1.0, max(0.0, intensity)),
            response_type="ASSISTED_RESPONSE",
            pattern=pattern
        )
        self.apply_decision(decision)
    
    def stop_all_motors(self):
        """Immediately stop all active motors."""
        for motor_id in list(self.active_motors.keys()):
            if motor_id in self.active_motors:
                timer = self.active_motors[motor_id]
                if timer.is_alive():
                    timer.cancel()
            self._stop_motor(motor_id)
    
    def get_controller_status(self) -> Dict[str, Any]:
        """Get comprehensive controller status."""
        return {
            "is_active": self.is_active,
            "motor_count": self.motor_count,
            "active_motors": list(self.active_motors.keys()),
            "motor_positions": self.motor_positions,
            "simulation_mode": self.simulation_mode,
            "last_feedback_time": self.last_feedback_time,
            "total_feedback_events": len(self.feedback_history),
            "recent_feedback": self.feedback_history[-5:] if self.feedback_history else []
        }
    
    def get_motor_layout(self) -> Dict[str, Any]:
        """Get motor layout information for UI display."""
        layout = {
            "motor_count": self.motor_count,
            "positions": {}
        }
        
        for direction, motor_ids in self.motor_positions.items():
            layout["positions"][direction] = {
                "motor_ids": motor_ids,
                "description": f"{direction} side vibration motors"
            }
        
        return layout


class FeedbackController:
    """
    Main feedback controller interface for the Aura-Edu system.
    Wraps VibrationController with high-level interface and legacy compatibility.
    """
    
    def __init__(self, config=None):
        self.vibration_controller = VibrationController(config)
        self.config = config
    
    def start(self) -> bool:
        """Start the feedback controller."""
        return self.vibration_controller.start()
    
    def stop(self) -> bool:
        """Stop the feedback controller."""
        return self.vibration_controller.stop()
    
    def apply(self, decision_dict: Dict[str, Any]) -> bool:
        """
        Apply feedback decision (legacy interface compatibility).
        
        Args:
            decision_dict: Decision dictionary from legacy system
            
        Returns:
            True if feedback applied successfully.
        """
        # Convert legacy dict to Decision object
        decision = Decision(
            action=decision_dict.get("action", "NONE"),
            intensity=float(decision_dict.get("intensity", 0.0)),
            response_type=decision_dict.get("response_type", "SELF_RECOGNIZED"),
            pattern=decision_dict.get("pattern", "SINGLE_PULSE")
        )
        
        return self.vibration_controller.apply_decision(decision)
    
    def get_status(self) -> Dict[str, Any]:
        """Get feedback controller status."""
        return {
            "vibration_controller": self.vibration_controller.get_controller_status(),
            "motor_layout": self.vibration_controller.get_motor_layout()
        }
