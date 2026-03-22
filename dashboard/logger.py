"""
Enhanced event logger for Aura-Edu system.
Provides comprehensive logging with storage integration and real-time monitoring.
"""

import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.types import SystemEvent, Stimulus, Decision, ReactionResult, SensorReading
from data.storage import DataStorage


class EventLogger:
    """
    Enhanced event logger with persistent storage and real-time monitoring.
    Logs all system events for analytics and debugging.
    """
    
    def __init__(self, storage: DataStorage = None, log_file: str = "logs/aura_edu.log"):
        self.storage = storage or DataStorage()
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory event buffer for real-time access
        self.event_buffer: List[SystemEvent] = []
        self.max_buffer_size = 1000
        
        # Statistics
        self.total_events = 0
        self.start_time = time.time()
        
        # Initialize log file
        self._write_log_header()
    
    def _write_log_header(self):
        """Write log file header."""
        header = f"""
# Aura-Edu System Log
# Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(self.start_time))}
# Format: JSON objects, one per line
# ========================================
"""
        with open(self.log_file, 'a') as f:
            f.write(header)
    
    def log_event(self, event: SystemEvent):
        """
        Log a complete system event.
        
        Args:
            event: SystemEvent to log
        """
        # Add to buffer
        self.event_buffer.append(event)
        if len(self.event_buffer) > self.max_buffer_size:
            self.event_buffer.pop(0)  # Remove oldest
        
        # Store in persistent storage
        event_id = self.storage.store_event(event)
        
        # Write to log file
        self._write_to_file(event)
        
        # Update statistics
        self.total_events += 1
        
        return event_id
    
    def log_stimulus_decision(self, stimulus: Optional[Stimulus], decision: Decision, 
                           reaction_result: Optional[ReactionResult] = None,
                           sensor_reading: Optional[SensorReading] = None):
        """
        Log stimulus, decision, and reaction in one call.
        
        Args:
            stimulus: Detected stimulus
            decision: System decision
            reaction_result: User reaction result
            sensor_reading: Sensor reading data
        """
        event = SystemEvent(
            timestamp=time.time(),
            stimulus=stimulus,
            reaction_result=reaction_result,
            decision=decision,
            sensor_reading=sensor_reading
        )
        
        return self.log_event(event)
    
    def log_legacy_format(self, log_data: Dict[str, Any]):
        """
        Log data in legacy format for backward compatibility.
        
        Args:
            log_data: Dictionary with log data
        """
        # Convert legacy format to new SystemEvent
        stimulus = None
        decision = None
        reaction_result = None
        sensor_reading = None
        
        # Extract decision
        if 'action' in log_data or 'intensity' in log_data:
            decision = Decision(
                action=log_data.get('action', 'NONE'),
                intensity=float(log_data.get('intensity', 0.0)),
                response_type=log_data.get('response_type', 'SELF_RECOGNIZED'),
                pattern=log_data.get('pattern', 'SINGLE_PULSE')
            )
        
        # Extract stimulus information
        stimulus_data = {k: v for k, v in log_data.items() 
                       if k in ['stimulus_side', 'stimulus_area', 'danger_level', 'confidence']}
        if stimulus_data:
            # Create minimal stimulus for logging
            from core.types import Direction, Danger
            stimulus = Stimulus(
                bbox=(0, 0, 0, 0),  # Placeholder
                direction=Direction(log_data.get('stimulus_side', 'CENTER')),
                area=log_data.get('stimulus_area', 0.0),
                danger=Danger(log_data.get('danger_level', 'LOW')),
                confidence=log_data.get('confidence', 0.0),
                class_id=0
            )
        
        event = SystemEvent(
            timestamp=time.time(),
            stimulus=stimulus,
            reaction_result=reaction_result,
            decision=decision,
            sensor_reading=sensor_reading
        )
        
        return self.log_event(event)
    
    def _write_to_file(self, event: SystemEvent):
        """Write event to log file."""
        log_entry = {
            "timestamp": event.timestamp,
            "event_id": self.total_events,
            "data": event.as_dict()
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_recent_events(self, count: int = 50) -> List[SystemEvent]:
        """
        Get recent events from buffer.
        
        Args:
            count: Number of recent events to return
            
        Returns:
            List of recent SystemEvent objects.
        """
        return self.event_buffer[-count:] if count > 0 else list(self.event_buffer)
    
    def get_events_by_type(self, event_type: str, count: int = 50) -> List[SystemEvent]:
        """
        Get events filtered by type.
        
        Args:
            event_type: Type of events to filter
            count: Maximum number of events to return
            
        Returns:
            Filtered list of SystemEvent objects.
        """
        filtered_events = []
        
        for event in reversed(self.event_buffer):  # Start from most recent
            if event_type == "intervention" and event.decision.action != "NONE":
                filtered_events.append(event)
            elif event_type == "success" and event.decision.response_type.value == "SELF_RECOGNIZED":
                filtered_events.append(event)
            elif event_type == "assisted" and event.decision.response_type.value == "ASSISTED_RESPONSE":
                filtered_events.append(event)
            
            if len(filtered_events) >= count:
                break
        
        return filtered_events
    
    def get_logger_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calculate events per minute
        events_per_minute = (self.total_events / uptime) * 60 if uptime > 0 else 0
        
        # Count event types in buffer
        intervention_count = sum(1 for e in self.event_buffer if e.decision.action != "NONE")
        success_count = sum(1 for e in self.event_buffer if e.decision.response_type.value == "SELF_RECOGNIZED")
        assisted_count = sum(1 for e in self.event_buffer if e.decision.response_type.value == "ASSISTED_RESPONSE")
        
        return {
            "total_events": self.total_events,
            "uptime_seconds": uptime,
            "events_per_minute": round(events_per_minute, 2),
            "buffer_size": len(self.event_buffer),
            "max_buffer_size": self.max_buffer_size,
            "event_types": {
                "interventions": intervention_count,
                "successes": success_count,
                "assisted_responses": assisted_count
            },
            "log_file": str(self.log_file),
            "storage_connected": self.storage is not None
        }
    
    def export_logs(self, output_path: str, format: str = "json"):
        """
        Export logs to file.
        
        Args:
            output_path: Path to output file
            format: Export format ('json', 'csv')
        """
        # Get events from storage
        events = self.storage.get_events(limit=10000) if self.storage else []
        
        # Convert to SystemEvent objects for consistency
        system_events = []
        for event_data in events:
            # Reconstruct SystemEvent from stored data
            stimulus = None
            if event_data.get('stimulus_data'):
                from core.types import Direction, Danger
                stim_data = event_data['stimulus_data']
                stimulus = Stimulus(
                    bbox=tuple(stim_data.get('bbox', [0, 0, 0, 0])),
                    direction=Direction(stim_data.get('direction', 'CENTER')),
                    area=stim_data.get('area', 0.0),
                    danger=Danger(stim_data.get('danger', 'LOW')),
                    confidence=stim_data.get('confidence', 0.0),
                    class_id=stim_data.get('class_id', 0)
                )
            
            decision = None
            if event_data.get('decision_data'):
                dec_data = event_data['decision_data']
                decision = Decision(
                    action=dec_data.get('action', 'NONE'),
                    intensity=dec_data.get('intensity', 0.0),
                    response_type=dec_data.get('response_type', 'SELF_RECOGNIZED'),
                    pattern=dec_data.get('pattern', 'SINGLE_PULSE')
                )
            
            reaction_result = None
            if event_data.get('reaction_result_data'):
                react_data = event_data['reaction_result_data']
                reaction_result = ReactionResult(
                    user_responded=react_data.get('user_responded', False),
                    reaction_time=react_data.get('reaction_time'),
                    initial_distance=react_data.get('initial_distance', 0.0),
                    final_distance=react_data.get('final_distance', 0.0),
                    direction=Direction(react_data.get('direction', 'CENTER')),
                    stimulus_id=react_data.get('stimulus_id', '')
                )
            
            sensor_reading = None
            if event_data.get('sensor_reading_data'):
                sensor_data = event_data['sensor_reading_data']
                sensor_reading = SensorReading(
                    direction=Direction(sensor_data.get('direction', 'CENTER')),
                    distance=sensor_data.get('distance', 0.0),
                    timestamp=sensor_data.get('timestamp', 0.0),
                    confidence=sensor_data.get('confidence', 1.0)
                )
            
            system_event = SystemEvent(
                timestamp=event_data['timestamp'],
                stimulus=stimulus,
                reaction_result=reaction_result,
                decision=decision,
                sensor_reading=sensor_reading
            )
            system_events.append(system_event)
        
        # Export using storage system
        if self.storage:
            self.storage.export_data(output_path, format)
        else:
            # Fallback export
            self._fallback_export(system_events, output_path, format)
    
    def _fallback_export(self, events: List[SystemEvent], output_path: str, format: str):
        """Fallback export method when storage is not available."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            export_data = {
                "events": [event.as_dict() for event in events],
                "export_timestamp": time.time(),
                "total_events": len(events)
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            
            if not events:
                return
            
            # Flatten events for CSV
            flattened = []
            for event in events:
                flat_event = {
                    'timestamp': event.timestamp,
                    'action': event.decision.action if event.decision else 'NONE',
                    'intensity': event.decision.intensity if event.decision else 0.0,
                    'response_type': event.decision.response_type.value if event.decision else 'NONE'
                }
                
                if event.stimulus:
                    flat_event.update({
                        'stimulus_direction': event.stimulus.direction.value,
                        'stimulus_danger': event.stimulus.danger.value,
                        'stimulus_confidence': event.stimulus.confidence
                    })
                
                if event.reaction_result:
                    flat_event.update({
                        'user_responded': event.reaction_result.user_responded,
                        'reaction_time': event.reaction_result.reaction_time,
                        'initial_distance': event.reaction_result.initial_distance,
                        'final_distance': event.reaction_result.final_distance
                    })
                
                flattened.append(flat_event)
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                writer.writeheader()
                writer.writerows(flattened)
    
    def clear_buffer(self):
        """Clear the in-memory event buffer."""
        self.event_buffer.clear()
    
    def rotate_log(self):
        """Rotate log file to prevent excessive growth."""
        if self.log_file.exists():
            # Create backup filename with timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_path = self.log_file.with_suffix(f'.{timestamp}.log')
            
            # Move current log to backup
            self.log_file.rename(backup_path)
            
            # Start new log
            self._write_log_header()
            
            return backup_path
        
        return None
