"""
FastAPI main application for Aura-Edu system.
Provides REST API endpoints for UI integration and real-time monitoring.
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    VibrationRequest, ConfigUpdateRequest, LiveDataResponse, 
    MetricsResponse, SystemStatusResponse, HistoricalDataResponse,
    ConfigurationResponse, ErrorResponse, SuccessResponse
)
from core.types import Direction, VibrationPattern
from utils.config import AppConfig
from data.storage import DataStorage
from data.metrics import MetricsEngine
from dashboard.logger import EventLogger


# Global system components (in production, these would be properly injected)
app_config = AppConfig()
data_storage = DataStorage()
metrics_engine = MetricsEngine(data_storage)
event_logger = EventLogger(data_storage)

# System state
system_state = {
    "state": "ACTIVE",
    "battery_level": 85.0,
    "uptime_start": time.time(),
    "last_intervention": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Aura-Edu API starting up...")
    
    yield
    
    # Shutdown
    print("🛑 Aura-Edu API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Aura-Edu API",
    description="AI-powered neuroadaptive wearable system for hemispatial neglect rehabilitation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def get_current_time() -> float:
    """Get current timestamp."""
    return time.time()


def get_uptime() -> float:
    """Get system uptime in seconds."""
    return get_current_time() - system_state["uptime_start"]


def update_battery_level():
    """Simulate battery drain."""
    drain_rate = 0.01  # 0.01% per second
    system_state["battery_level"] = max(0, system_state["battery_level"] - drain_rate)


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Aura-Edu API",
        "version": "1.0.0",
        "description": "AI-powered neuroadaptive wearable system",
        "status": "ACTIVE"
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint."""
    update_battery_level()
    
    return {
        "status": "healthy",
        "timestamp": get_current_time(),
        "uptime": get_uptime(),
        "battery_level": system_state["battery_level"]
    }


@app.get("/live-data", response_model=LiveDataResponse)
async def get_live_data():
    """
    Get current live system data.
    Returns real-time detections, metrics, and system status.
    """
    try:
        current_time = get_current_time()
        
        # Get current metrics
        metrics = metrics_engine.get_real_time_metrics()
        
        # Get recent events for live data
        recent_events = event_logger.get_recent_events(count=5)
        
        # Extract current stimuli and decisions
        current_stimuli = []
        recent_decisions = []
        
        for event in recent_events:
            if event.stimulus:
                current_stimuli.append({
                    "bbox": list(event.stimulus.bbox),
                    "direction": event.stimulus.direction.value,
                    "area": event.stimulus.area,
                    "danger": event.stimulus.danger.value,
                    "confidence": event.stimulus.confidence,
                    "class_id": event.stimulus.class_id,
                    "class_name": event.stimulus.class_name,
                    "estimated_distance": event.stimulus.estimated_distance
                })
            
            recent_decisions.append({
                "action": event.decision.action,
                "intensity": event.decision.intensity,
                "response_type": event.decision.response_type.value,
                "pattern": event.decision.pattern.value
            })
        
        # Get system status
        system_status = await get_system_status()
        
        return LiveDataResponse(
            timestamp=current_time,
            current_stimuli=current_stimuli,
            active_observations=metrics.get("reaction_monitor", {}).get("active_observations", []),
            recent_decisions=recent_decisions,
            system_metrics=MetricsResponse(**metrics),
            system_status=SystemStatusResponse(**system_status)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live data: {str(e)}")


@app.get("/events", response_model=List[Dict[str, Any]])
async def get_events(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    event_type: Optional[str] = Query(default=None, description="Filter by event type")
):
    """
    Get system events with pagination and filtering.
    """
    try:
        if event_type:
            # Get filtered events from logger
            filtered_events = event_logger.get_events_by_type(event_type, count=limit)
            return [event.as_dict() for event in filtered_events]
        else:
            # Get events from storage
            events = data_storage.get_events(limit=limit, offset=offset)
            return events
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    period: str = Query(default="realtime", description="Time period: realtime, hourly, daily")
):
    """
    Get system metrics for specified time period.
    """
    try:
        if period == "realtime":
            metrics = metrics_engine.get_real_time_metrics()
        elif period in ["hourly", "daily"]:
            days = 1 if period == "hourly" else 7
            historical = metrics_engine.get_historical_metrics(days=days)
            # Convert historical to realtime format for response
            metrics = {
                "timestamp": get_current_time(),
                "session": historical.get("summary", {}),
                "awareness_score": historical.get("summary", {}),
                "left_vs_right_analysis": historical.get("summary", {}),
                "system_health": {"health_score": 100.0}
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid period parameter")
        
        return MetricsResponse(**metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.get("/metrics/historical", response_model=HistoricalDataResponse)
async def get_historical_metrics(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get historical metrics and trends.
    """
    try:
        historical_data = metrics_engine.get_historical_metrics(days=days)
        return HistoricalDataResponse(**historical_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical metrics: {str(e)}")


@app.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get current system status including battery, state, and health.
    """
    try:
        update_battery_level()
        
        # Get system health from metrics
        metrics = metrics_engine.get_real_time_metrics()
        system_health = metrics.get("system_health", {})
        
        return SystemStatusResponse(
            state=system_state["state"],
            uptime_seconds=get_uptime(),
            battery_level=system_state["battery_level"],
            active_observations=len(metrics.get("reaction_monitor", {}).get("active_observations", [])),
            last_intervention=system_state["last_intervention"],
            system_health=system_health
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@app.get("/config", response_model=ConfigurationResponse)
async def get_configuration():
    """
    Get current system configuration.
    """
    try:
        config_dict = app_config.as_dict()
        return ConfigurationResponse(**config_dict)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@app.post("/config", response_model=SuccessResponse)
async def update_configuration(request: ConfigUpdateRequest):
    """
    Update system configuration.
    """
    try:
        # In a real implementation, this would update the actual configuration
        # For now, just return success
        
        return SuccessResponse(
            success=True,
            message=f"Configuration updated for section: {request.section}",
            timestamp=get_current_time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@app.post("/vibration/trigger", response_model=SuccessResponse)
async def trigger_vibration(request: VibrationRequest):
    """
    Manually trigger vibration for testing or calibration.
    """
    try:
        # Convert API request to internal format
        direction = Direction(request.direction.value)
        pattern = VibrationPattern(request.pattern)
        
        # In a real implementation, this would trigger the actual vibration
        print(f"🔧 Manual vibration trigger: {direction.value} intensity={request.intensity}")
        
        return SuccessResponse(
            success=True,
            message=f"Vibration triggered for {direction.value}",
            timestamp=get_current_time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger vibration: {str(e)}")


@app.post("/vibration/stop", response_model=SuccessResponse)
async def stop_all_vibrations():
    """
    Stop all active vibrations.
    """
    try:
        # In a real implementation, this would stop all vibrations
        print("🔧 Stopping all vibrations")
        
        return SuccessResponse(
            success=True,
            message="All vibrations stopped",
            timestamp=get_current_time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop vibrations: {str(e)}")


@app.post("/export", response_model=SuccessResponse)
async def export_data(
    background_tasks: BackgroundTasks,
    format: str = Query(default="json", regex="^(json|csv)$"),
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Export system data in specified format.
    """
    try:
        # Generate export filename
        timestamp = int(get_current_time())
        filename = f"aura_edu_export_{timestamp}.{format}"
        output_path = f"exports/{filename}"
        
        # Schedule export in background
        def perform_export():
            event_logger.export_logs(output_path, format)
        
        background_tasks.add_task(perform_export)
        
        return SuccessResponse(
            success=True,
            message=f"Export started. File will be saved as {filename}",
            timestamp=get_current_time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start export: {str(e)}")


@app.get("/performance/report", response_model=Dict[str, Any])
async def get_performance_report():
    """
    Get comprehensive performance report with insights and recommendations.
    """
    try:
        report = metrics_engine.get_performance_report()
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate performance report: {str(e)}")


@app.get("/analytics/left-right", response_model=Dict[str, Any])
async def get_left_right_analysis():
    """
    Get detailed left vs right performance analysis.
    Critical for hemispatial neglect assessment.
    """
    try:
        analysis = metrics_engine.reaction_monitor.get_left_vs_right_analysis()
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get left-right analysis: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail,
            timestamp=get_current_time()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message=str(exc),
            timestamp=get_current_time()
        ).dict()
    )


# WebSocket support for real-time updates (optional enhancement)
@app.websocket("/ws/live")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time live data updates."""
    await websocket.accept()
    
    try:
        while True:
            # Send live data every second
            live_data = await get_live_data()
            await websocket.send_json(live_data.dict())
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Aura-Edu API server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔌 WebSocket Endpoint: ws://localhost:8000/ws/live")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
