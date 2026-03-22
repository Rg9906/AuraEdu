"""
System monitoring for Aura-Edu system.
Provides comprehensive system health monitoring and status tracking.
"""

import time
import threading
import psutil
import platform
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from core.types import SystemState
from .battery import BatteryManager


class AlertLevel(Enum):
    """System alert levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SystemAlert:
    """System alert information."""
    timestamp: float
    level: AlertLevel
    component: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False


@dataclass
class SystemMetrics:
    """Current system metrics."""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_status: bool
    temperature: float
    uptime: float
    active_threads: int


class SystemMonitor:
    """
    Comprehensive system monitoring for Aura-Edu.
    Tracks hardware performance, battery status, and system health.
    """
    
    def __init__(self, battery_manager: BatteryManager = None):
        self.battery_manager = battery_manager or BatteryManager()
        
        # System state
        self.current_state = SystemState.ACTIVE
        self.start_time = time.time()
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Metrics tracking
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Alert management
        self.alerts: List[SystemAlert] = []
        self.alert_callbacks: Dict[AlertLevel, List[Callable]] = {
            level: [] for level in AlertLevel
        }
        
        # Performance thresholds
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "temperature_warning": 70.0,
            "temperature_critical": 85.0
        }
        
        # Component status
        self.component_status = {
            "camera": True,
            "sensors": True,
            "decision_engine": True,
            "feedback_controller": True,
            "data_storage": True,
            "api_server": True
        }
        
        # Health score calculation
        self.health_weights = {
            "cpu": 0.2,
            "memory": 0.2,
            "disk": 0.15,
            "battery": 0.25,
            "components": 0.2
        }
    
    def start_monitoring(self):
        """Start system monitoring thread."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start battery monitoring
        self.battery_manager.start_monitoring()
        
        print("🖥️ System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring thread."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        # Stop battery monitoring
        self.battery_manager.stop_monitoring()
        
        print("🖥️ System monitoring stopped")
    
    def _monitor_loop(self):
        """Main system monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect current metrics
                metrics = self._collect_metrics()
                
                # Store metrics
                self._store_metrics(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Update system state
                self._update_system_state(metrics)
                
                # Sleep for monitoring interval
                time.sleep(5.0)  # Update every 5 seconds
                
            except Exception as e:
                self._create_alert(
                    AlertLevel.ERROR,
                    "system_monitor",
                    f"Monitoring error: {str(e)}",
                    {"error": str(e)}
                )
                time.sleep(10.0)  # Wait longer on error
    
    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network status (simple check)
            network_status = self._check_network_status()
            
            # Temperature (use battery temperature)
            temperature = self.battery_manager.temperature
            
            # Uptime
            uptime = time.time() - self.start_time
            
            # Thread count
            active_threads = threading.active_count()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_status=network_status,
                temperature=temperature,
                uptime=uptime,
                active_threads=active_threads
            )
            
        except Exception as e:
            print(f"❌ Error collecting metrics: {e}")
            return SystemMetrics(0, 0, 0, False, 25.0, 0, 0)
    
    def _check_network_status(self) -> bool:
        """Check network connectivity."""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False
    
    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in history."""
        metrics_dict = {
            "timestamp": time.time(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_usage_percent": metrics.disk_usage_percent,
            "network_status": metrics.network_status,
            "temperature": metrics.temperature,
            "uptime": metrics.uptime,
            "active_threads": metrics.active_threads,
            "system_state": self.current_state.value
        }
        
        self.metrics_history.append(metrics_dict)
        
        # Maintain history size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
    
    def _check_alerts(self, metrics: SystemMetrics):
        """Check for alert conditions."""
        # CPU alerts
        if metrics.cpu_percent >= self.thresholds["cpu_critical"]:
            self._create_alert(
                AlertLevel.CRITICAL,
                "cpu",
                f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                {"cpu_percent": metrics.cpu_percent}
            )
        elif metrics.cpu_percent >= self.thresholds["cpu_warning"]:
            self._create_alert(
                AlertLevel.WARNING,
                "cpu",
                f"High CPU usage: {metrics.cpu_percent:.1f}%",
                {"cpu_percent": metrics.cpu_percent}
            )
        
        # Memory alerts
        if metrics.memory_percent >= self.thresholds["memory_critical"]:
            self._create_alert(
                AlertLevel.CRITICAL,
                "memory",
                f"Critical memory usage: {metrics.memory_percent:.1f}%",
                {"memory_percent": metrics.memory_percent}
            )
        elif metrics.memory_percent >= self.thresholds["memory_warning"]:
            self._create_alert(
                AlertLevel.WARNING,
                "memory",
                f"High memory usage: {metrics.memory_percent:.1f}%",
                {"memory_percent": metrics.memory_percent}
            )
        
        # Disk alerts
        if metrics.disk_usage_percent >= self.thresholds["disk_critical"]:
            self._create_alert(
                AlertLevel.CRITICAL,
                "disk",
                f"Critical disk usage: {metrics.disk_usage_percent:.1f}%",
                {"disk_usage_percent": metrics.disk_usage_percent}
            )
        elif metrics.disk_usage_percent >= self.thresholds["disk_warning"]:
            self._create_alert(
                AlertLevel.WARNING,
                "disk",
                f"High disk usage: {metrics.disk_usage_percent:.1f}%",
                {"disk_usage_percent": metrics.disk_usage_percent}
            )
        
        # Temperature alerts
        if metrics.temperature >= self.thresholds["temperature_critical"]:
            self._create_alert(
                AlertLevel.CRITICAL,
                "temperature",
                f"Critical temperature: {metrics.temperature:.1f}°C",
                {"temperature": metrics.temperature}
            )
        elif metrics.temperature >= self.thresholds["temperature_warning"]:
            self._create_alert(
                AlertLevel.WARNING,
                "temperature",
                f"High temperature: {metrics.temperature:.1f}°C",
                {"temperature": metrics.temperature}
            )
        
        # Network alerts
        if not metrics.network_status:
            self._create_alert(
                AlertLevel.WARNING,
                "network",
                "Network connectivity lost",
                {"network_status": False}
            )
    
    def _create_alert(self, level: AlertLevel, component: str, message: str, details: Dict[str, Any]):
        """Create and process a system alert."""
        alert = SystemAlert(
            timestamp=time.time(),
            level=level,
            component=component,
            message=message,
            details=details
        )
        
        self.alerts.append(alert)
        
        # Maintain alert history size
        if len(self.alerts) > 500:
            self.alerts = self.alerts[-250:]
        
        # Trigger callbacks
        for callback in self.alert_callbacks[level]:
            try:
                callback(alert)
            except Exception as e:
                print(f"❌ Alert callback error: {e}")
        
        # Log alert
        print(f"🚨 {level.value} ALERT [{component}]: {message}")
    
    def _update_system_state(self, metrics: SystemMetrics):
        """Update system state based on metrics."""
        battery_status = self.battery_manager.get_status()
        
        # Determine state based on conditions
        if battery_status.current_level <= 10.0:
            self.current_state = SystemState.ALERT
        elif (metrics.cpu_percent >= 95.0 or 
              metrics.memory_percent >= 95.0 or 
              metrics.temperature >= 85.0):
            self.current_state = SystemState.ALERT
        elif not metrics.network_status:
            self.current_state = SystemState.MAINTENANCE
        else:
            self.current_state = SystemState.ACTIVE
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        current_metrics = self._collect_metrics()
        battery_status = self.battery_manager.get_status()
        
        # Calculate health score
        health_score = self._calculate_health_score(current_metrics, battery_status)
        
        return {
            "state": self.current_state.value,
            "uptime_seconds": current_metrics.uptime,
            "health_score": health_score,
            "metrics": {
                "cpu_percent": current_metrics.cpu_percent,
                "memory_percent": current_metrics.memory_percent,
                "disk_usage_percent": current_metrics.disk_usage_percent,
                "temperature": current_metrics.temperature,
                "active_threads": current_metrics.active_threads,
                "network_status": current_metrics.network_status
            },
            "battery": self.battery_manager.get_battery_info(),
            "components": self.component_status.copy(),
            "recent_alerts": [
                {
                    "timestamp": alert.timestamp,
                    "level": alert.level.value,
                    "component": alert.component,
                    "message": alert.message,
                    "details": alert.details
                }
                for alert in self.alerts[-10:]  # Last 10 alerts
            ]
        }
    
    def _calculate_health_score(self, metrics: SystemMetrics, battery_status) -> float:
        """Calculate overall system health score."""
        scores = {}
        
        # CPU score (inverse of usage)
        scores["cpu"] = max(0, 100 - metrics.cpu_percent)
        
        # Memory score (inverse of usage)
        scores["memory"] = max(0, 100 - metrics.memory_percent)
        
        # Disk score (inverse of usage)
        scores["disk"] = max(0, 100 - metrics.disk_usage_percent)
        
        # Battery score
        scores["battery"] = battery_status.current_level
        
        # Components score (percentage of operational components)
        operational = sum(1 for status in self.component_status.values() if status)
        total = len(self.component_status)
        scores["components"] = (operational / total) * 100 if total > 0 else 0
        
        # Calculate weighted average
        health_score = sum(
            scores[component] * weight 
            for component, weight in self.health_weights.items()
        )
        
        return round(health_score, 2)
    
    def get_performance_trends(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance trends over specified time period."""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self.metrics_history 
            if m["timestamp"] >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No data available for specified period"}
        
        # Calculate averages and trends
        cpu_values = [m["cpu_percent"] for m in recent_metrics]
        memory_values = [m["memory_percent"] for m in recent_metrics]
        
        return {
            "period_minutes": minutes,
            "data_points": len(recent_metrics),
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "trend": self._calculate_trend(cpu_values)
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "trend": self._calculate_trend(memory_values)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values list."""
        if len(values) < 2:
            return "STABLE"
        
        # Compare first half with second half
        mid = len(values) // 2
        first_avg = sum(values[:mid]) / mid if mid > 0 else 0
        second_avg = sum(values[mid:]) / (len(values) - mid) if len(values) > mid else 0
        
        diff = second_avg - first_avg
        
        if diff > 5:
            return "INCREASING"
        elif diff < -5:
            return "DECREASING"
        else:
            return "STABLE"
    
    def set_component_status(self, component: str, status: bool):
        """Set component status."""
        if component in self.component_status:
            self.component_status[component] = status
            status_text = "OPERATIONAL" if status else "FAILED"
            print(f"🔧 Component {component}: {status_text}")
            
            if not status:
                self._create_alert(
                    AlertLevel.ERROR,
                    component,
                    f"Component failure: {component}",
                    {"component": component, "status": status}
                )
    
    def add_alert_callback(self, level: AlertLevel, callback: Callable[[SystemAlert], None]):
        """Add callback for specific alert level."""
        self.alert_callbacks[level].append(callback)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "start_time": self.start_time,
            "monitoring_active": self.is_monitoring,
            "total_alerts": len(self.alerts),
            "metrics_history_size": len(self.metrics_history)
        }
    
    def force_alert(self, level: AlertLevel, component: str, message: str):
        """Force create an alert for testing."""
        self._create_alert(level, component, message, {"forced": True})
