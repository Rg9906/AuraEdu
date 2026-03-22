"""
Data storage module for Aura-Edu system.
Handles persistent storage of events, metrics, and configuration.
"""

import json
import sqlite3
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from contextlib import contextmanager

from core.types import SystemEvent


class DataStorage:
    """
    Persistent data storage for Aura-Edu system.
    Uses SQLite for structured data with JSON export capabilities.
    """
    
    def __init__(self, db_path: str = "data/aura_edu.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # System events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    stimulus_data TEXT,
                    reaction_result_data TEXT,
                    decision_data TEXT NOT NULL,
                    sensor_reading_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    total_stimuli INTEGER DEFAULT 0,
                    successful_reactions INTEGER DEFAULT 0,
                    missed_reactions INTEGER DEFAULT 0,
                    assisted_reactions INTEGER DEFAULT 0,
                    avg_reaction_time REAL DEFAULT 0.0,
                    left_success_rate REAL DEFAULT 0.0,
                    right_success_rate REAL DEFAULT 0.0,
                    awareness_score REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT NOT NULL UNIQUE,
                    config_value TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Session summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start REAL NOT NULL,
                    session_end REAL,
                    total_events INTEGER DEFAULT 0,
                    total_duration REAL DEFAULT 0.0,
                    avg_awareness_score REAL DEFAULT 0.0,
                    left_vs_right_improvement REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def store_event(self, event: SystemEvent) -> int:
        """
        Store a system event in the database.
        
        Args:
            event: SystemEvent object to store
            
        Returns:
            ID of the stored event.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_events 
                (timestamp, stimulus_data, reaction_result_data, decision_data, sensor_reading_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.timestamp,
                json.dumps(event.stimulus.as_dict()) if event.stimulus else None,
                json.dumps(event.reaction_result.as_dict()) if event.reaction_result else None,
                json.dumps(event.decision.as_dict()),
                json.dumps(event.sensor_reading.as_dict()) if event.sensor_reading else None
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            return event_id
    
    def get_events(self, limit: int = 100, offset: int = 0, 
                  start_time: Optional[float] = None, 
                  end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Retrieve system events from database.
        
        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            start_time: Filter events after this timestamp
            end_time: Filter events before this timestamp
            
        Returns:
            List of event dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM system_events WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event_data = dict(row)
                # Parse JSON fields
                if event_data['stimulus_data']:
                    event_data['stimulus_data'] = json.loads(event_data['stimulus_data'])
                if event_data['reaction_result_data']:
                    event_data['reaction_result_data'] = json.loads(event_data['reaction_result_data'])
                if event_data['decision_data']:
                    event_data['decision_data'] = json.loads(event_data['decision_data'])
                if event_data['sensor_reading_data']:
                    event_data['sensor_reading_data'] = json.loads(event_data['sensor_reading_data'])
                
                events.append(event_data)
            
            return events
    
    def store_daily_metrics(self, date: str, metrics: Dict[str, Any]):
        """
        Store daily metrics summary.
        
        Args:
            date: Date string in YYYY-MM-DD format
            metrics: Dictionary of metrics for the day
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO daily_metrics 
                (date, total_stimuli, successful_reactions, missed_reactions, 
                 assisted_reactions, avg_reaction_time, left_success_rate, 
                 right_success_rate, awareness_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                date,
                metrics.get('total_stimuli', 0),
                metrics.get('successful_reactions', 0),
                metrics.get('missed_reactions', 0),
                metrics.get('assisted_reactions', 0),
                metrics.get('avg_reaction_time', 0.0),
                metrics.get('left_success_rate', 0.0),
                metrics.get('right_success_rate', 0.0),
                metrics.get('awareness_score', 0.0)
            ))
            
            conn.commit()
    
    def get_daily_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieve daily metrics for specified number of days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of daily metrics dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM daily_metrics 
                ORDER BY date DESC 
                LIMIT ?
            """, (days,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def store_session_summary(self, session_data: Dict[str, Any]):
        """
        Store session summary.
        
        Args:
            session_data: Dictionary with session information
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO session_summaries 
                (session_start, session_end, total_events, total_duration,
                 avg_awareness_score, left_vs_right_improvement)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_data.get('session_start'),
                session_data.get('session_end'),
                session_data.get('total_events', 0),
                session_data.get('total_duration', 0.0),
                session_data.get('avg_awareness_score', 0.0),
                session_data.get('left_vs_right_improvement', 0.0)
            ))
            
            conn.commit()
    
    def get_session_summaries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent session summaries.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summary dictionaries.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM session_summaries 
                ORDER BY session_start DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def export_data(self, output_path: str, format: str = "json"):
        """
        Export all data to file.
        
        Args:
            output_path: Path to output file
            format: Export format ('json' or 'csv')
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            self._export_json(output_file)
        elif format.lower() == "csv":
            self._export_csv(output_file)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, output_file: Path):
        """Export data as JSON."""
        export_data = {
            "events": self.get_events(limit=10000),  # Get all events
            "daily_metrics": self.get_daily_metrics(days=365),
            "session_summaries": self.get_session_summaries(limit=100),
            "export_timestamp": time.time()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_csv(self, output_file: Path):
        """Export data as CSV (events only)."""
        import csv
        
        events = self.get_events(limit=10000)
        
        if not events:
            return
        
        # Flatten event data for CSV
        flattened_events = []
        for event in events:
            flat_event = {
                'id': event['id'],
                'timestamp': event['timestamp'],
                'created_at': event['created_at']
            }
            
            # Add stimulus data
            if event['stimulus_data']:
                for key, value in event['stimulus_data'].items():
                    flat_event[f'stimulus_{key}'] = value
            
            # Add reaction result data
            if event['reaction_result_data']:
                for key, value in event['reaction_result_data'].items():
                    flat_event[f'reaction_{key}'] = value
            
            # Add decision data
            if event['decision_data']:
                for key, value in event['decision_data'].items():
                    flat_event[f'decision_{key}'] = value
            
            # Add sensor reading data
            if event['sensor_reading_data']:
                for key, value in event['sensor_reading_data'].items():
                    flat_event[f'sensor_{key}'] = value
            
            flattened_events.append(flat_event)
        
        # Write to CSV
        if flattened_events:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_events[0].keys())
                writer.writeheader()
                writer.writerows(flattened_events)
    
    def cleanup_old_data(self, retention_days: int = 30):
        """
        Clean up old data beyond retention period.
        
        Args:
            retention_days: Number of days to retain data
        """
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete old events
            cursor.execute("DELETE FROM system_events WHERE timestamp < ?", (cutoff_time,))
            events_deleted = cursor.rowcount
            
            # Delete old daily metrics (keep last year)
            cutoff_date = time.strftime("%Y-%m-%d", time.gmtime(cutoff_time))
            cursor.execute("DELETE FROM daily_metrics WHERE date < ?", (cutoff_date,))
            metrics_deleted = cursor.rowcount
            
            conn.commit()
            
            return {
                "events_deleted": events_deleted,
                "metrics_deleted": metrics_deleted
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count events
            cursor.execute("SELECT COUNT(*) as count FROM system_events")
            event_count = cursor.fetchone()['count']
            
            # Count daily metrics
            cursor.execute("SELECT COUNT(*) as count FROM daily_metrics")
            metrics_count = cursor.fetchone()['count']
            
            # Count sessions
            cursor.execute("SELECT COUNT(*) as count FROM session_summaries")
            session_count = cursor.fetchone()['count']
            
            # Get database file size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "event_count": event_count,
                "daily_metrics_count": metrics_count,
                "session_count": session_count,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "database_path": str(self.db_path)
            }
