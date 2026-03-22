"""
Main Aura-Edu System Integration.
Brings together all components into a unified closed-loop neuroadaptive system.
"""

import time
import asyncio
import threading
from typing import Dict, Any, Optional

from utils.config import AppConfig
from sensors.camera_sensor import CameraSensor
from sensors.ultrasonic_sim import UltrasonicArray
from decision.engine import DecisionEngine
from decision.reaction_monitor import ReactionMonitor
from decision.feedback_controller import FeedbackController
from data.storage import DataStorage
from data.metrics import MetricsEngine
from dashboard.logger import EventLogger
from system.battery import BatteryManager
from system.monitor import SystemMonitor
from core.types import SystemEvent, Stimulus, Decision, SensorReading


class AuraEduSystem:
    """
    Main Aura-Edu system integration.
    Coordinates all components for closed-loop neuroadaptive operation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = AppConfig()
        
        # Initialize core components
        self.data_storage = DataStorage()
        self.metrics_engine = MetricsEngine(self.data_storage)
        self.event_logger = EventLogger(self.data_storage)
        self.battery_manager = BatteryManager(self.config)
        self.system_monitor = SystemMonitor(self.battery_manager)
        
        # Initialize sensors
        self.camera_sensor = CameraSensor(
            camera_index=self.config.vision.camera_index,
            config=self.config
        )
        self.ultrasonic_array = UltrasonicArray(self.config)
        
        # Initialize decision and feedback systems
        self.decision_engine = DecisionEngine(self.config)
        self.reaction_monitor = ReactionMonitor()
        self.feedback_controller = FeedbackController(self.config)
        
        # System state
        self.is_running = False
        self.main_loop_thread: Optional[threading.Thread] = None
        
        # Performance tracking
        self.loop_count = 0
        self.last_loop_time = 0.0
        self.target_fps = self.config.vision.target_fps
        
        print("🧠 Aura-Edu System initialized")
    
    def start(self):
        """Start the Aura-Edu system."""
        if self.is_running:
            print("⚠️ System is already running")
            return
        
        print("🚀 Starting Aura-Edu System...")
        
        try:
            # Start monitoring systems
            self.system_monitor.start_monitoring()
            
            # Start sensors
            if not self.camera_sensor.start():
                raise RuntimeError("Failed to start camera sensor")
            
            if not self.ultrasonic_array.start():
                raise RuntimeError("Failed to start ultrasonic array")
            
            # Start feedback controller
            if not self.feedback_controller.start():
                raise RuntimeError("Failed to start feedback controller")
            
            # Start main loop
            self.is_running = True
            self.main_loop_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_loop_thread.start()
            
            print("✅ Aura-Edu System started successfully")
            print("📊 API available at: http://localhost:8000")
            print("🔌 Press Ctrl+C to stop")
            
        except Exception as e:
            print(f"❌ Failed to start system: {e}")
            self.stop()
    
    def stop(self):
        """Stop the Aura-Edu system."""
        if not self.is_running:
            return
        
        print("🛑 Stopping Aura-Edu System...")
        
        self.is_running = False
        
        # Stop main loop
        if self.main_loop_thread:
            self.main_loop_thread.join(timeout=5.0)
        
        # Stop components
        self.feedback_controller.stop()
        self.ultrasonic_array.stop()
        self.camera_sensor.release()
        self.system_monitor.stop_monitoring()
        
        # End session and generate report
        session_data = self.metrics_engine.end_session()
        print(f"📊 Session ended: {session_data['total_events']} events in {session_data['total_duration']:.1f}s")
        
        print("✅ Aura-Edu System stopped")
    
    def _main_loop(self):
        """Main processing loop."""
        print("🔄 Main loop started")
        
        while self.is_running:
            loop_start_time = time.time()
            
            try:
                # Process one cycle
                self._process_cycle()
                
                # Maintain target FPS
                loop_duration = time.time() - loop_start_time
                target_duration = 1.0 / self.target_fps
                
                if loop_duration < target_duration:
                    time.sleep(target_duration - loop_duration)
                
                # Update performance metrics
                self.loop_count += 1
                self.last_loop_time = loop_start_time
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(1.0)  # Brief pause on error
    
    def _process_cycle(self):
        """Process one complete cycle of the closed-loop system."""
        # 1. Get sensor data
        frame = self.camera_sensor.capture_frame()
        if frame is None:
            return
        
        # 2. Detect objects
        detections = self.camera_sensor.detect_objects(frame)
        
        # 3. Map to stimuli
        frame_width = frame.shape[1]
        stimuli = self.camera_sensor.map_to_stimuli(detections, frame_width)
        
        # 4. Get ultrasonic readings
        sensor_readings = self.ultrasonic_array.read_all()
        
        # 5. Process each stimulus through decision engine
        for stimulus in stimuli:
            # Get corresponding sensor reading
            sensor_reading = sensor_readings.get(stimulus.direction)
            
            # Process through decision engine
            decision = self.decision_engine.process_stimulus(stimulus, sensor_reading)
            
            # Apply feedback if needed
            if decision.action != "NONE":
                self.feedback_controller.apply(decision.as_dict())
            
            # Create and log event
            event = SystemEvent(
                timestamp=time.time(),
                stimulus=stimulus,
                reaction_result=None,  # Will be updated by reaction monitor
                decision=decision,
                sensor_reading=sensor_reading
            )
            
            self.event_logger.log_event(event)
            self.metrics_engine.process_event(event)
        
        # 6. Update ongoing observations with new sensor data
        completed_decisions = self.decision_engine.update_observations(sensor_readings)
        
        # 7. Process completed observations
        for decision in completed_decisions:
            # Apply feedback if needed
            if decision.action != "NONE":
                self.feedback_controller.apply(decision.as_dict())
            
            # Log completion
            self._log_observation_completion(decision, sensor_readings)
        
        # 8. Simulate random object approaches for demonstration
        if self.loop_count % 100 == 0:  # Every 100 cycles
            self._simulate_random_approach()
    
    def _log_observation_completion(self, decision: Decision, sensor_readings: Dict):
        """Log completion of an observation period."""
        # Get reaction result from decision engine
        active_observations = self.decision_engine.get_active_observations()
        
        if active_observations:
            # Find the most recent completed observation
            recent_obs = active_observations[-1] if active_observations else None
            
            if recent_obs:
                # Create reaction result (simplified)
                reaction_result = None
                if decision.response_type.value == "SELF_RECOGNIZED":
                    from core.types import ReactionResult, Direction
                    reaction_result = ReactionResult(
                        user_responded=True,
                        reaction_time=1.5,  # Simulated
                        initial_distance=100.0,
                        final_distance=120.0,
                        direction=Direction(recent_obs["direction"]),
                        stimulus_id=recent_obs["stimulus_id"]
                    )
                elif decision.response_type.value == "ASSISTED_RESPONSE":
                    from core.types import ReactionResult, Direction
                    reaction_result = ReactionResult(
                        user_responded=False,
                        reaction_time=None,
                        initial_distance=100.0,
                        final_distance=50.0,
                        direction=Direction(recent_obs["direction"]),
                        stimulus_id=recent_obs["stimulus_id"]
                    )
                
                # Log completion event
                event = SystemEvent(
                    timestamp=time.time(),
                    stimulus=None,  # Already logged at start
                    reaction_result=reaction_result,
                    decision=decision,
                    sensor_reading=sensor_readings.get(Direction(recent_obs["direction"]))
                )
                
                self.event_logger.log_event(event)
                self.metrics_engine.process_event(event)
    
    def _simulate_random_approach(self):
        """Simulate random object approach for demonstration."""
        import random
        from core.types import Direction
        
        # Random direction
        direction = random.choice(list(Direction))
        
        # Simulate approaching object
        self.ultrasonic_array.simulate_approaching_object(
            direction=direction,
            initial_distance=200.0,
            target_distance=30.0
        )
        
        print(f"🎯 Simulated approaching object from {direction.value}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "is_running": self.is_running,
            "uptime": time.time() - (self.system_monitor.start_time if self.system_monitor else time.time()),
            "loop_count": self.loop_count,
            "current_fps": self._calculate_current_fps(),
            "target_fps": self.target_fps,
            "components": {
                "camera": self.camera_sensor.get_status(),
                "ultrasonic": self.ultrasonic_array.get_all_status(),
                "decision_engine": self.decision_engine.get_engine_status(),
                "feedback_controller": self.feedback_controller.get_status(),
                "system_monitor": self.system_monitor.get_system_status(),
                "battery": self.battery_manager.get_battery_info()
            },
            "metrics": self.metrics_engine.get_real_time_metrics(),
            "recent_events": [event.as_dict() for event in self.event_logger.get_recent_events(count=5)]
        }
    
    def _calculate_current_fps(self) -> float:
        """Calculate current FPS."""
        if self.last_loop_time == 0:
            return 0.0
        
        current_time = time.time()
        time_diff = current_time - self.last_loop_time
        
        if time_diff > 0:
            return 1.0 / time_diff
        return 0.0
    
    def manual_vibration_test(self, direction: str, intensity: float = 0.5):
        """Manually trigger vibration for testing."""
        from core.types import Direction, VibrationPattern
        
        try:
            dir_enum = Direction(direction.upper())
            self.feedback_controller.vibration_controller.trigger_direction(
                dir_enum, intensity, VibrationPattern.SINGLE_PULSE
            )
            print(f"🔧 Manual vibration: {direction} at {intensity:.2f}")
        except ValueError:
            print(f"❌ Invalid direction: {direction}")
    
    def export_session_data(self, format: str = "json"):
        """Export current session data."""
        timestamp = int(time.time())
        filename = f"aura_edu_session_{timestamp}.{format}"
        
        try:
            self.event_logger.export_logs(f"exports/{filename}", format)
            print(f"📁 Session data exported to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def print_system_info(self):
        """Print detailed system information."""
        status = self.get_system_status()
        
        print("\n" + "="*60)
        print("🧠 AURA-EDU SYSTEM STATUS")
        print("="*60)
        print(f"🟢 System Running: {status['is_running']}")
        print(f"⏱️  Uptime: {status['uptime']:.1f}s")
        print(f"🔄 Loops: {status['loop_count']}")
        print(f"📊 FPS: {status['current_fps']:.1f}/{status['target_fps']}")
        
        print("\n📊 METRICS")
        print("-" * 30)
        metrics = status['metrics']
        if 'awareness_score' in metrics:
            awareness = metrics['awareness_score']
            print(f"🎯 Awareness Score: {awareness.get('awareness_score', 0):.1f}")
            print(f"📈 Grade: {awareness.get('grade', 'N/A')}")
        
        if 'left_vs_right_analysis' in metrics:
            analysis = metrics['left_vs_right_analysis']
            if 'analysis' in analysis:
                print(f"⚖️  Neglect Severity: {analysis['analysis'].get('neglect_severity', 'N/A')}")
        
        print("\n🔋 BATTERY")
        print("-" * 30)
        battery = status['components']['battery']
        print(f"📊 Level: {battery['level']:.1f}%")
        print(f"⚡ Runtime: {battery['estimated_runtime_minutes']:.0f}min")
        print(f"🌡️  Temp: {battery['temperature']:.1f}°C")
        
        print("\n🔧 COMPONENTS")
        print("-" * 30)
        components = status['components']
        print(f"📷 Camera: {'✅' if components['camera']['camera_open'] else '❌'}")
        print(f"📡 Sensors: {'✅' if components['ultrasonic']['array_active'] else '❌'}")
        print(f"🧠 Decision Engine: {'✅' if len(components['decision_engine']['active_observations']) >= 0 else '❌'}")
        print(f"⚡ Feedback: {'✅' if components['feedback_controller']['vibration_controller']['is_active'] else '❌'}")
        
        print("="*60)


def main():
    """Main entry point for Aura-Edu system."""
    print("🧠 Aura-Edu AI-Powered Neuroadaptive System")
    print("🎯 Target: Hemispatial Neglect Rehabilitation")
    print("=" * 60)
    
    # Create and start system
    system = AuraEduSystem()
    
    try:
        system.start()
        
        # Keep main thread alive
        while system.is_running:
            time.sleep(1.0)
            
            # Print status every 30 seconds
            if system.loop_count % (system.target_fps * 30) == 0:
                system.print_system_info()
    
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
    finally:
        system.stop()


if __name__ == "__main__":
    main()
