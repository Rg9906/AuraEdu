"""
Metrics engine for Aura-Edu system.
Computes real-time and historical performance metrics.
"""

import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from core.types import Direction, SystemEvent
from decision.reaction_monitor import ReactionMonitor
from data.storage import DataStorage


class MetricsEngine:
    """
    Comprehensive metrics engine for Aura-Edu system.
    Calculates performance metrics, trends, and awareness scores.
    """
    
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or DataStorage()
        self.reaction_monitor = ReactionMonitor()
        
        # Session tracking
        self.session_start_time = time.time()
        self.session_events: List[SystemEvent] = []
        
        # Real-time metrics cache
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_timestamp = 0.0
        self._cache_ttl = 5.0  # Cache for 5 seconds
    
    def process_event(self, event: SystemEvent):
        """
        Process a system event and update metrics.
        
        Args:
            event: SystemEvent to process
        """
        self.session_events.append(event)
        self.reaction_monitor.record_event(event)
        
        # Store event if storage is available
        if self.storage:
            self.storage.store_event(event)
        
        # Invalidate cache
        self._cache_timestamp = 0.0
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Get current real-time metrics.
        
        Returns:
            Dictionary with current system metrics.
        """
        current_time = time.time()
        
        # Check cache
        if (current_time - self._cache_timestamp) < self._cache_ttl and self._metrics_cache:
            return self._metrics_cache
        
        # Calculate metrics
        monitor_status = self.reaction_monitor.get_monitor_status()
        awareness_score = self.reaction_monitor.calculate_awareness_score()
        left_right_analysis = self.reaction_monitor.get_left_vs_right_analysis()
        
        # Session metrics
        session_duration = current_time - self.session_start_time
        session_events_per_minute = (len(self.session_events) / session_duration) * 60 if session_duration > 0 else 0
        
        # Compile metrics
        metrics = {
            "timestamp": current_time,
            "session": {
                "duration_seconds": session_duration,
                "total_events": len(self.session_events),
                "events_per_minute": round(session_events_per_minute, 2),
                "start_time": self.session_start_time
            },
            "awareness_score": awareness_score,
            "left_vs_right_analysis": left_right_analysis,
            "reaction_monitor": monitor_status,
            "system_health": self._calculate_system_health()
        }
        
        # Cache results
        self._metrics_cache = metrics
        self._cache_timestamp = current_time
        
        return metrics
    
    def get_historical_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get historical metrics for specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with historical metrics and trends.
        """
        # Get daily metrics from storage
        daily_metrics = self.storage.get_daily_metrics(days=days) if self.storage else []
        
        # Calculate trends
        trend_analysis = self._analyze_trends(daily_metrics)
        
        # Get progress from reaction monitor
        progress_trend = self.reaction_monitor.get_progress_trend(days)
        
        return {
            "period_days": days,
            "daily_metrics": daily_metrics,
            "trend_analysis": trend_analysis,
            "progress_trend": progress_trend,
            "summary": self._generate_period_summary(daily_metrics)
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Detailed performance report with recommendations.
        """
        real_time_metrics = self.get_real_time_metrics()
        historical_metrics = self.get_historical_metrics(days=30)
        
        # Generate insights and recommendations
        insights = self._generate_insights(real_time_metrics, historical_metrics)
        recommendations = self._generate_recommendations(insights)
        
        return {
            "report_timestamp": time.time(),
            "real_time_metrics": real_time_metrics,
            "historical_analysis": historical_metrics,
            "insights": insights,
            "recommendations": recommendations,
            "overall_grade": self._calculate_overall_grade(real_time_metrics, historical_metrics)
        }
    
    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate system health metrics."""
        current_time = time.time()
        
        # Check if system is actively processing
        recent_events = [e for e in self.session_events if current_time - e.timestamp < 60]  # Last minute
        
        # Calculate event rate
        if len(self.session_events) > 10:
            recent_events_rate = len(recent_events) / 60.0  # Events per second
        else:
            recent_events_rate = 0.0
        
        # System health score
        health_score = 100.0
        if recent_events_rate == 0 and len(self.session_events) > 0:
            health_score -= 50  # No recent activity but has history
        elif recent_events_rate < 0.1:
            health_score -= 25  # Very low activity
        
        return {
            "health_score": max(0, health_score),
            "recent_events_count": len(recent_events),
            "events_per_second": round(recent_events_rate, 3),
            "status": "HEALTHY" if health_score >= 80 else "WARNING" if health_score >= 50 else "CRITICAL"
        }
    
    def _analyze_trends(self, daily_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in daily metrics."""
        if len(daily_metrics) < 2:
            return {"trend": "INSUFFICIENT_DATA"}
        
        # Sort by date
        daily_metrics.sort(key=lambda x: x['date'])
        
        # Calculate trends for key metrics
        awareness_scores = [m.get('awareness_score', 0) for m in daily_metrics if m.get('awareness_score')]
        left_success_rates = [m.get('left_success_rate', 0) for m in daily_metrics if m.get('left_success_rate')]
        right_success_rates = [m.get('right_success_rate', 0) for m in daily_metrics if m.get('right_success_rate')]
        
        trends = {}
        
        def calculate_trend(values):
            if len(values) < 2:
                return "INSUFFICIENT_DATA"
            
            # Simple linear trend calculation
            recent_avg = sum(values[-3:]) / min(3, len(values))
            older_avg = sum(values[:3]) / min(3, len(values))
            
            if recent_avg > older_avg + 5:
                return "IMPROVING"
            elif recent_avg < older_avg - 5:
                return "DECLINING"
            else:
                return "STABLE"
        
        trends['awareness_score'] = calculate_trend(awareness_scores)
        trends['left_performance'] = calculate_trend(left_success_rates)
        trends['right_performance'] = calculate_trend(right_success_rates)
        
        # Overall trend
        trend_values = [t for t in trends.values() if t in ["IMPROVING", "DECLINING", "STABLE"]]
        if trend_values:
            improving_count = trend_values.count("IMPROVING")
            declining_count = trend_values.count("DECLINING")
            
            if improving_count > declining_count:
                trends['overall'] = "IMPROVING"
            elif declining_count > improving_count:
                trends['overall'] = "DECLINING"
            else:
                trends['overall'] = "STABLE"
        else:
            trends['overall'] = "INSUFFICIENT_DATA"
        
        return trends
    
    def _generate_period_summary(self, daily_metrics: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for a period."""
        if not daily_metrics:
            return {"status": "NO_DATA"}
        
        # Aggregate statistics
        total_stimuli = sum(m.get('total_stimuli', 0) for m in daily_metrics)
        total_successful = sum(m.get('successful_reactions', 0) for m in daily_metrics)
        total_missed = sum(m.get('missed_reactions', 0) for m in daily_metrics)
        
        avg_awareness_score = sum(m.get('awareness_score', 0) for m in daily_metrics) / len(daily_metrics)
        avg_left_success = sum(m.get('left_success_rate', 0) for m in daily_metrics) / len(daily_metrics)
        avg_right_success = sum(m.get('right_success_rate', 0) for m in daily_metrics) / len(daily_metrics)
        
        return {
            "total_days": len(daily_metrics),
            "total_stimuli": total_stimuli,
            "total_successful_reactions": total_successful,
            "total_missed_reactions": total_missed,
            "overall_success_rate": (total_successful / total_stimuli * 100) if total_stimuli > 0 else 0,
            "average_awareness_score": round(avg_awareness_score, 2),
            "average_left_success_rate": round(avg_left_success, 2),
            "average_right_success_rate": round(avg_right_success, 2),
            "performance_gap": round(abs(avg_left_success - avg_right_success), 2)
        }
    
    def _generate_insights(self, real_time: Dict, historical: Dict) -> List[Dict[str, Any]]:
        """Generate insights from metrics data."""
        insights = []
        
        # Awareness score insight
        awareness_score = real_time.get('awareness_score', {}).get('awareness_score', 0)
        if awareness_score >= 90:
            insights.append({
                "type": "PERFORMANCE",
                "level": "EXCELLENT",
                "message": "Outstanding awareness performance! User is highly responsive to stimuli.",
                "metric": "awareness_score",
                "value": awareness_score
            })
        elif awareness_score >= 70:
            insights.append({
                "type": "PERFORMANCE",
                "level": "GOOD",
                "message": "Good awareness performance. Continue current training regimen.",
                "metric": "awareness_score",
                "value": awareness_score
            })
        elif awareness_score < 50:
            insights.append({
                "type": "PERFORMANCE",
                "level": "CONCERN",
                "message": "Low awareness performance detected. Consider adjusting difficulty or providing more guidance.",
                "metric": "awareness_score",
                "value": awareness_score
            })
        
        # Left vs Right analysis insight
        left_right = real_time.get('left_vs_right_analysis', {}).get('analysis', {})
        performance_gap = left_right.get('performance_gap', 0)
        neglect_severity = left_right.get('neglect_severity', 'MINIMAL')
        
        if neglect_severity in ['MODERATE', 'SEVERE']:
            insights.append({
                "type": "HEMISPATIAL",
                "level": "WARNING",
                "message": f"Significant left-right performance gap detected ({neglect_severity} neglect). Focus training on weaker side.",
                "metric": "neglect_severity",
                "value": neglect_severity,
                "gap": performance_gap
            })
        
        # Trend insight
        trends = historical.get('trend_analysis', {}).get('overall', 'INSUFFICIENT_DATA')
        if trends == "IMPROVING":
            insights.append({
                "type": "TREND",
                "level": "POSITIVE",
                "message": "Performance is improving over time. Current training approach is effective.",
                "metric": "trend",
                "value": trends
            })
        elif trends == "DECLINING":
            insights.append({
                "type": "TREND",
                "level": "NEGATIVE",
                "message": "Performance is declining. Consider adjusting training parameters or rest periods.",
                "metric": "trend",
                "value": trends
            })
        
        return insights
    
    def _generate_recommendations(self, insights: List[Dict]) -> List[str]:
        """Generate recommendations based on insights."""
        recommendations = []
        
        # Check for performance issues
        performance_insights = [i for i in insights if i['type'] == 'PERFORMANCE']
        if performance_insights:
            worst_performance = min(performance_insights, key=lambda x: x['value'])
            if worst_performance['level'] == 'CONCERN':
                recommendations.append("Consider reducing stimulus complexity or increasing intervention frequency")
        
        # Check for hemispatial issues
        hemispatial_insights = [i for i in insights if i['type'] == 'HEMISPATIAL']
        if hemispatial_insights:
            recommendations.append("Increase focus on neglected side with targeted exercises")
            recommendations.append("Consider longer observation windows for weaker side")
        
        # Check for trend issues
        trend_insights = [i for i in insights if i['type'] == 'TREND' and i['level'] == 'NEGATIVE']
        if trend_insights:
            recommendations.append("Review training schedule and consider rest periods")
            recommendations.append("Adjust difficulty level to match current capabilities")
        
        # Default positive recommendations
        if not recommendations:
            recommendations.append("Continue current training approach")
            recommendations.append("Monitor consistency and maintain engagement")
        
        return recommendations
    
    def _calculate_overall_grade(self, real_time: Dict, historical: Dict) -> Dict[str, Any]:
        """Calculate overall system performance grade."""
        awareness_score = real_time.get('awareness_score', {}).get('awareness_score', 0)
        left_right_analysis = real_time.get('left_vs_right_analysis', {}).get('analysis', {})
        performance_gap = left_right_analysis.get('performance_gap', 0)
        
        # Grade components
        awareness_grade = self._score_to_grade(awareness_score)
        balance_grade = self._gap_to_grade(performance_gap)
        
        # Overall grade (weighted average)
        overall_score = (awareness_score * 0.7) + ((100 - performance_gap) * 0.3)
        overall_grade = self._score_to_grade(overall_score)
        
        return {
            "overall_grade": overall_grade,
            "overall_score": round(overall_score, 2),
            "components": {
                "awareness": awareness_grade,
                "balance": balance_grade
            },
            "summary": self._grade_to_summary(overall_grade)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _gap_to_grade(self, gap: float) -> str:
        """Convert performance gap to grade."""
        if gap <= 5:
            return "A"
        elif gap <= 10:
            return "B"
        elif gap <= 20:
            return "C"
        elif gap <= 30:
            return "D"
        else:
            return "F"
    
    def _grade_to_summary(self, grade: str) -> str:
        """Convert grade to summary text."""
        summaries = {
            "A": "Excellent performance - user is highly responsive and well-balanced",
            "B": "Good performance - room for minor improvements",
            "C": "Satisfactory performance - needs focused improvement",
            "D": "Poor performance - significant intervention needed",
            "F": "Critical performance - immediate attention required"
        }
        return summaries.get(grade, "Unknown grade")
    
    def end_session(self):
        """End current session and store summary."""
        session_end_time = time.time()
        session_duration = session_end_time - self.session_start_time
        
        # Calculate session metrics
        real_time_metrics = self.get_real_time_metrics()
        awareness_score = real_time_metrics.get('awareness_score', {}).get('awareness_score', 0)
        left_right_analysis = real_time_metrics.get('left_vs_right_analysis', {}).get('analysis', {})
        performance_gap = left_right_analysis.get('performance_gap', 0)
        
        # Store session summary
        session_data = {
            'session_start': self.session_start_time,
            'session_end': session_end_time,
            'total_events': len(self.session_events),
            'total_duration': session_duration,
            'avg_awareness_score': awareness_score,
            'left_vs_right_improvement': -performance_gap  # Negative gap is improvement
        }
        
        if self.storage:
            self.storage.store_session_summary(session_data)
        
        # Reset for next session
        self.session_start_time = session_end_time
        self.session_events.clear()
        
        return session_data
