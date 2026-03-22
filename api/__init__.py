"""
REST API layer for Aura-Edu system.
Provides endpoints for UI integration and real-time monitoring.
"""

from .main import app
from .models import *

__all__ = ["app"]
