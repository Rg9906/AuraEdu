"""
Reaction monitoring module for tracking user responses to stimuli.
Provides detailed analytics on reaction patterns and improvement over time.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

from core.types import Direction, ReactionResult, Stimulus, SystemEvent


@dataclass
class ReactionMetrics:
    """Metrics for user reactions over a time period."""
    total_stimuli: int = 0
    successful_reactions: int = 0
    missed_reactions: int = 0
    assisted_reactions: int = 0
    average_reaction_time: float = 0.0
    reaction_times: List[float] = None
    
    def __post_init__(self):
        if self.reaction_times is None:
            self.reaction_times = []
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_stimuli == 0:
            return 0.0
        return (self.successful_reactions / self.total_stimuli) * 100.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate miss rate as percentage."""
        if self.total_stimuli == 0:
            return 0.0
        return (self.missed_reactions / self.total_stimuli) * 100.0
    
    def add_reaction(self, reaction_result: ReactionResult):
        """Add a new reaction result to metrics."""
        self.total_stimuli += 1
        
        if reaction_result.user_responded:
            self.successful_reactions += 1
            if reaction_result.reaction_time:
                self.reaction_times.append(reaction_result.reaction_time)
        else:
            self.missed_reactions += 1
    
    def update_average_reaction_time(self):
        """Update average reaction time from collected times."""
        if self.reaction_times:
            self.average_reaction_time = sum(self.reaction_times) / len(self.reaction_times)


class ReactionMonitor:
    """
    Monitors and analyzes user reactions to stimuli.
    Tracks improvement over time and provides detailed analytics.
    """
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.reaction_history: deque = deque(maxlen=max_history_size)
        self.events_history: deque = deque(maxlen=max_history_size)
        
        # Metrics by direction (critical for hemispatial neglect analysis)
        self.direction_metrics: Dict[Direction, ReactionMetrics] = {
            direction: ReactionMetrics() for direction in Direction
        }
        
        # Time-based metrics
        self.daily_metrics: Dict[str, Dict[Direction, ReactionMetrics]] = defaultdict(lambda: {
            direction: ReactionMetrics() for direction in Direction
        })
        
        # Performance tracking
        self.start_time = time.time()
        self.last_reaction_time = None
        self.reaction_trend = deque(maxlen=50)  # Last 50 reactions for trend analysis
    
    def record_event(self, event: SystemEvent):
        """
        Record a system event for reaction analysis.
        
        Args:
            event: Complete system event with stimulus, reaction, and decision.
        """
        self.events_history.append(event)
        
        if event.reaction_result:
            self._process_reaction_result(event.reaction_result, event.stimulus)
    
    def _process_reaction_result(self, reaction_result: ReactionResult, stimulus: Optional[Stimulus]):
        """Process a reaction result and update metrics."""
        self.reaction_history.append(reaction_result)
        self.last_reaction_time = time.time()
        
        # Update direction-specific metrics
        direction = reaction_result.direction
        self.direction_metrics[direction].add_reaction(reaction_result)
        
        # Update daily metrics
        date_key = time.strftime("%Y-%m-%d")
        self.daily_metrics[date_key][direction].add_reaction(reaction_result)
        
        # Update trend analysis
        self.reaction_trend.append({
            "timestamp": time.time(),
            "responded": reaction_result.user_responded,
            "reaction_time": reaction_result.reaction_time,
            "direction": direction.value
        })
        
        # Update averages
        self.direction_metrics[direction].update_average_reaction_time()
    
    def get_direction_metrics(self, direction: Direction) -> ReactionMetrics:
        """Get metrics for a specific direction."""
        return self.direction_metrics[direction]
    
    def get_left_vs_right_analysis(self) -> Dict[str, Any]:
        """
        Get comparative analysis between left and right side performance.
        Critical for hemispatial neglect assessment.
        """
        left_metrics = self.direction_metrics[Direction.LEFT]
        right_metrics = self.direction_metrics[Direction.RIGHT]
        
        left_success_rate = left_metrics.success_rate
        right_success_rate = right_metrics.success_rate
        
        # Calculate improvement potential
        improvement_gap = right_success_rate - left_success_rate
        
        return {
            "left_side": {
                "total_stimuli": left_metrics.total_stimuli,
                "success_rate": left_success_rate,
                "miss_rate": left_metrics.miss_rate,
                "avg_reaction_time": left_metrics.average_reaction_time,
                "total_reactions": len(left_metrics.reaction_times)
            },
            "right_side": {
                "total_stimuli": right_metrics.total_stimuli,
                "success_rate": right_success_rate,
                "miss_rate": right_metrics.miss_rate,
                "avg_reaction_time": right_metrics.average_reaction_time,
                "total_reactions": len(right_metrics.reaction_times)
            },
            "analysis": {
                "performance_gap": abs(improvement_gap),
                "dominant_side": "RIGHT" if right_success_rate > left_success_rate else "LEFT",
                "improvement_needed_left": max(0, improvement_gap),
                "neglect_severity": self._calculate_neglect_severity(left_success_rate, right_success_rate)
            }
        }
    
    def _calculate_neglect_severity(self, left_rate: float, right_rate: float) -> str:
        """Calculate hemispatial neglect severity based on performance gap."""
        gap = right_rate - left_rate
        
        if gap > 30:
            return "SEVERE"
        elif gap > 15:
            return "MODERATE"
        elif gap > 5:
            return "MILD"
        else:
            return "MINIMAL"
    
    def get_progress_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        Get progress trend over specified number of days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Progress trend data.
        """
        current_date = time.strftime("%Y-%m-%d")
        trend_data = []
        
        for i in range(days):
            date_key = self._get_date_key(i)
            daily_data = self.daily_metrics.get(date_key, {})
            
            # Calculate overall performance for this day
            total_stimuli = sum(metrics.total_stimuli for metrics in daily_data.values())
            total_successful = sum(metrics.successful_reactions for metrics in daily_data.values())
            success_rate = (total_successful / total_stimuli * 100) if total_stimuli > 0 else 0.0
            
            trend_data.append({
                "date": date_key,
                "total_stimuli": total_stimuli,
                "success_rate": success_rate,
                "left_success_rate": daily_data.get(Direction.LEFT, ReactionMetrics()).success_rate,
                "right_success_rate": daily_data.get(Direction.RIGHT, ReactionMetrics()).success_rate
            })
        
        return {
            "trend": trend_data,
            "overall_improvement": self._calculate_improvement(trend_data),
            "consistency_score": self._calculate_consistency(trend_data)
        }
    
    def _get_date_key(self, days_ago: int) -> str:
        """Get date key for specified days ago."""
        import datetime
        date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")
    
    def _calculate_improvement(self, trend_data: List[Dict]) -> float:
        """Calculate overall improvement percentage from trend data."""
        if len(trend_data) < 2:
            return 0.0
        
        # Compare oldest day with most recent day
        oldest = trend_data[-1]
        recent = trend_data[0]
        
        if oldest["success_rate"] == 0:
            return 0.0
        
        improvement = ((recent["success_rate"] - oldest["success_rate"]) / oldest["success_rate"]) * 100
        return improvement
    
    def _calculate_consistency(self, trend_data: List[Dict]) -> float:
        """Calculate consistency score based on variance in performance."""
        if len(trend_data) < 3:
            return 0.0
        
        success_rates = [day["success_rate"] for day in trend_data if day["total_stimuli"] > 0]
        if len(success_rates) < 3:
            return 0.0
        
        # Calculate coefficient of variation
        mean_rate = sum(success_rates) / len(success_rates)
        variance = sum((rate - mean_rate) ** 2 for rate in success_rates) / len(success_rates)
        std_dev = variance ** 0.5
        
        # Consistency score (inverse of coefficient of variation)
        cv = (std_dev / mean_rate) * 100 if mean_rate > 0 else 100
        consistency = max(0, 100 - cv)
        
        return consistency
    
    def calculate_awareness_score(self) -> Dict[str, Any]:
        """
        Calculate comprehensive awareness score (SENS-ED).
        Combines success rate, reaction time, and consistency.
        """
        # Overall metrics
        total_stimuli = sum(metrics.total_stimuli for metrics in self.direction_metrics.values())
        total_successful = sum(metrics.successful_reactions for metrics in self.direction_metrics.values())
        overall_success_rate = (total_successful / total_stimuli * 100) if total_stimuli > 0 else 0.0
        
        # Average reaction time across all directions
        all_reaction_times = []
        for metrics in self.direction_metrics.values():
            all_reaction_times.extend(metrics.reaction_times)
        
        avg_reaction_time = sum(all_reaction_times) / len(all_reaction_times) if all_reaction_times else 0.0
        
        # Consistency from recent trend
        trend_data = self.get_progress_trend(7)["trend"]
        consistency = self._calculate_consistency(trend_data)
        
        # Left vs Right balance (important for neglect assessment)
        left_right_analysis = self.get_left_vs_right_analysis()
        balance_score = 100 - abs(left_right_analysis["analysis"]["performance_gap"])
        
        # Calculate weighted awareness score
        success_weight = 0.4
        reaction_weight = 0.3
        consistency_weight = 0.2
        balance_weight = 0.1
        
        # Normalize reaction time (faster is better, target < 1.0 seconds)
        reaction_score = max(0, 100 - (avg_reaction_time * 20))  # 5% penalty per 0.25s
        
        awareness_score = (
            overall_success_rate * success_weight +
            reaction_score * reaction_weight +
            consistency * consistency_weight +
            balance_score * balance_weight
        )
        
        return {
            "awareness_score": min(100, max(0, awareness_score)),
            "components": {
                "success_rate": overall_success_rate,
                "reaction_score": reaction_score,
                "consistency": consistency,
                "balance_score": balance_score
            },
            "metrics": {
                "total_stimuli": total_stimuli,
                "avg_reaction_time": avg_reaction_time,
                "left_vs_right_gap": left_right_analysis["analysis"]["performance_gap"]
            },
            "grade": self._get_performance_grade(awareness_score)
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Get performance grade based on awareness score."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "GOOD"
        elif score >= 70:
            return "SATISFACTORY"
        elif score >= 60:
            return "NEEDS_IMPROVEMENT"
        else:
            return "POOR"
    
    def get_monitor_status(self) -> Dict[str, Any]:
        """Get comprehensive monitor status."""
        return {
            "total_events": len(self.events_history),
            "total_reactions": len(self.reaction_history),
            "monitoring_duration": time.time() - self.start_time,
            "last_reaction": self.last_reaction_time,
            "direction_metrics": {
                direction.value: {
                    "total_stimuli": metrics.total_stimuli,
                    "success_rate": metrics.success_rate,
                    "avg_reaction_time": metrics.average_reaction_time
                }
                for direction, metrics in self.direction_metrics.items()
            },
            "awareness_score": self.calculate_awareness_score(),
            "left_vs_right_analysis": self.get_left_vs_right_analysis()
        }
