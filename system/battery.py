"""
Battery management and simulation for Aura-Edu system.
Provides realistic battery drain simulation and monitoring.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from core.types import SystemState


class BatteryLevel(Enum):
    """Battery level categories."""
    CRITICAL = 10.0
    LOW = 20.0
    MEDIUM = 50.0
    HIGH = 80.0
    FULL = 100.0


@dataclass
class BatteryStatus:
    """Battery status information."""
    current_level: float  # Percentage (0-100)
    voltage: float  # Volts
    temperature: float  # Celsius
    is_charging: bool
    estimated_runtime: float  # Minutes remaining
    health: float  # Battery health percentage (0-100)
    cycle_count: int  # Charge cycles


class BatteryManager:
    """
    Battery management system with realistic simulation.
    Supports different power modes and drain rates.
    """
    
    def __init__(self, config=None):
        self.config = config
        
        # Battery specifications
        self.capacity = 5000.0 if not config else config.system.battery_capacity  # mAh
        self.voltage_nominal = 3.7  # Li-ion nominal voltage
        self.voltage_min = 3.0  # Minimum safe voltage
        self.voltage_max = 4.2  # Full charge voltage
        
        # Current battery state
        self.current_level = 85.0  # Start at 85%
        self.is_charging = False
        self.temperature = 25.0  # Room temperature
        self.health = 95.0  # Good health
        self.cycle_count = 150
        
        # Power consumption rates (mAh/hour)
        self.drain_rates = {
            SystemState.ACTIVE: 100.0,    # Normal operation
            SystemState.IDLE: 20.0,       # Low power idle
            SystemState.ALERT: 150.0,      # High consumption during alerts
            SystemState.MAINTENANCE: 5.0   # Very low during maintenance
        }
        
        # Simulation state
        self.start_time = time.time()
        self.last_update = time.time()
        self.total_runtime = 0.0
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Callbacks for battery events
        self.low_battery_callbacks: list[Callable] = []
        self.critical_battery_callbacks: list[Callable] = []
        self.battery_full_callbacks: list[Callable] = []
        
        # Alert thresholds
        self.low_threshold = 20.0 if not config else config.system.low_battery_threshold
        self.critical_threshold = 10.0
        self.last_alert_time = 0.0
        self.alert_cooldown = 300.0  # 5 minutes between alerts
    
    def start_monitoring(self):
        """Start battery monitoring thread."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔋 Battery monitoring started")
    
    def stop_monitoring(self):
        """Stop battery monitoring thread."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("🔋 Battery monitoring stopped")
    
    def _monitor_loop(self):
        """Main battery monitoring loop."""
        while self.is_monitoring:
            current_time = time.time()
            dt = current_time - self.last_update
            
            # Update battery level based on current state
            self._update_battery_level(dt)
            
            # Check for alerts
            self._check_battery_alerts()
            
            # Update statistics
            self.total_runtime += dt
            self.last_update = current_time
            
            # Sleep for monitoring interval
            time.sleep(1.0)  # Update every second
    
    def _update_battery_level(self, dt: float):
        """Update battery level based on time delta and current state."""
        if self.is_charging:
            # Simulate charging
            charge_rate = 1000.0  # mAh/hour charging rate
            charge_added = (charge_rate / 3600.0) * dt  # Convert to mAh
            level_increase = (charge_added / self.capacity) * 100.0
            
            self.current_level = min(100.0, self.current_level + level_increase)
            
            # Check if fully charged
            if self.current_level >= 100.0:
                self.current_level = 100.0
                self.is_charging = False
                self._trigger_battery_full()
        else:
            # Drain battery based on current state
            # Get current system state (would be passed in real system)
            current_state = self._get_current_system_state()
            drain_rate = self.drain_rates.get(current_state, 100.0)
            
            # Apply health factor
            effective_drain = drain_rate * (self.health / 100.0)
            
            # Apply temperature factor (higher temp = faster drain)
            temp_factor = 1.0 + ((self.temperature - 25.0) * 0.01)  # 1% per degree above 25°C
            effective_drain *= max(0.5, temp_factor)  # Minimum 50% drain rate
            
            # Calculate level decrease
            drain_amount = (effective_drain / 3600.0) * dt  # Convert to mAh
            level_decrease = (drain_amount / self.capacity) * 100.0
            
            self.current_level = max(0.0, self.current_level - level_decrease)
    
    def _get_current_system_state(self) -> SystemState:
        """Get current system state (simplified for simulation)."""
        # In real implementation, this would come from system monitor
        if self.current_level < self.critical_threshold:
            return SystemState.ALERT
        elif self.current_level < self.low_threshold:
            return SystemState.ALERT
        else:
            return SystemState.ACTIVE
    
    def _check_battery_alerts(self):
        """Check for battery level alerts."""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        # Critical battery alert
        if self.current_level <= self.critical_threshold:
            self._trigger_critical_battery()
            self.last_alert_time = current_time
        
        # Low battery alert
        elif self.current_level <= self.low_threshold:
            self._trigger_low_battery()
            self.last_alert_time = current_time
    
    def _trigger_low_battery(self):
        """Trigger low battery alert."""
        print(f"🔋 LOW BATTERY: {self.current_level:.1f}%")
        for callback in self.low_battery_callbacks:
            try:
                callback(self.get_status())
            except Exception as e:
                print(f"❌ Battery callback error: {e}")
    
    def _trigger_critical_battery(self):
        """Trigger critical battery alert."""
        print(f"🔋 CRITICAL BATTERY: {self.current_level:.1f}%")
        for callback in self.critical_battery_callbacks:
            try:
                callback(self.get_status())
            except Exception as e:
                print(f"❌ Battery callback error: {e}")
    
    def _trigger_battery_full(self):
        """Trigger battery full alert."""
        print("🔋 BATTERY FULL: 100%")
        for callback in self.battery_full_callbacks:
            try:
                callback(self.get_status())
            except Exception as e:
                print(f"❌ Battery callback error: {e}")
    
    def get_status(self) -> BatteryStatus:
        """Get current battery status."""
        # Calculate voltage based on level
        voltage = self.voltage_min + (self.voltage_max - self.voltage_min) * (self.current_level / 100.0)
        
        # Estimate runtime
        current_state = self._get_current_system_state()
        drain_rate = self.drain_rates.get(current_state, 100.0) * (self.health / 100.0)
        estimated_runtime = (self.current_level / 100.0) * (self.capacity / drain_rate) * 60.0  # minutes
        
        return BatteryStatus(
            current_level=self.current_level,
            voltage=voltage,
            temperature=self.temperature,
            is_charging=self.is_charging,
            estimated_runtime=estimated_runtime,
            health=self.health,
            cycle_count=self.cycle_count
        )
    
    def set_charging(self, charging: bool):
        """Set charging state."""
        if charging and not self.is_charging:
            print("🔋 Charging started")
        elif not charging and self.is_charging:
            print("🔋 Charging stopped")
        
        self.is_charging = charging
    
    def set_temperature(self, temperature: float):
        """Set battery temperature."""
        self.temperature = max(-20.0, min(60.0, temperature))  # Clamp to reasonable range
    
    def simulate_load(self, load_multiplier: float, duration: float):
        """Simulate additional load for specified duration."""
        def apply_load():
            original_rates = self.drain_rates.copy()
            
            # Apply load multiplier
            for state in self.drain_rates:
                self.drain_rates[state] *= load_multiplier
            
            print(f"🔋 Simulating load: {load_multiplier}x for {duration}s")
            time.sleep(duration)
            
            # Restore original rates
            self.drain_rates = original_rates
            print("🔋 Load simulation completed")
        
        thread = threading.Thread(target=apply_load, daemon=True)
        thread.start()
    
    def add_low_battery_callback(self, callback: Callable[[BatteryStatus], None]):
        """Add callback for low battery alerts."""
        self.low_battery_callbacks.append(callback)
    
    def add_critical_battery_callback(self, callback: Callable[[BatteryStatus], None]):
        """Add callback for critical battery alerts."""
        self.critical_battery_callbacks.append(callback)
    
    def add_battery_full_callback(self, callback: Callable[[BatteryStatus], None]):
        """Add callback for battery full alerts."""
        self.battery_full_callbacks.append(callback)
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get comprehensive battery information for API."""
        status = self.get_status()
        
        return {
            "level": status.current_level,
            "voltage": status.voltage,
            "temperature": status.temperature,
            "is_charging": status.is_charging,
            "estimated_runtime_minutes": status.estimated_runtime,
            "health": status.health,
            "cycle_count": status.cycle_count,
            "capacity_mah": self.capacity,
            "level_category": self._get_level_category(status.current_level),
            "uptime_hours": self.total_runtime / 3600.0,
            "drain_rates": {
                state.value: rate for state, rate in self.drain_rates.items()
            }
        }
    
    def _get_level_category(self, level: float) -> str:
        """Get battery level category."""
        if level >= BatteryLevel.HIGH.value:
            return "HIGH"
        elif level >= BatteryLevel.MEDIUM.value:
            return "MEDIUM"
        elif level >= BatteryLevel.LOW.value:
            return "LOW"
        else:
            return "CRITICAL"
    
    def force_level(self, level: float):
        """Force battery level for testing."""
        self.current_level = max(0.0, min(100.0, level))
        print(f"🔋 Battery level forced to: {self.current_level:.1f}%")
    
    def reset_stats(self):
        """Reset battery statistics."""
        self.start_time = time.time()
        self.total_runtime = 0.0
        print("🔋 Battery statistics reset")
