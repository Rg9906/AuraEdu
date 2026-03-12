from __future__ import annotations

from typing import Dict, Optional


class FeedbackController:
    """
    Bridges high-level decisions to hardware commands.
    """

    def __init__(self, motor_driver=None):
        # motor_driver is expected to expose: vibrate(side: str, intensity: float)
        self._motor_driver = motor_driver

    def apply(self, decision: Dict) -> None:
        action = decision.get("action", "NONE")
        intensity = float(decision.get("intensity", 0.0))

        if action == "NONE" or intensity <= 0:
            return

        if self._motor_driver is None:
            # Fallback: console print for prototype
            if action == "VIBRATE_LEFT":
                print(f"[HAPTIC] LEFT intensity={intensity:.2f}")
            elif action == "VIBRATE_RIGHT":
                print(f"[HAPTIC] RIGHT intensity={intensity:.2f}")
            return

        if action == "VIBRATE_LEFT":
            self._motor_driver.vibrate("LEFT", intensity=intensity)
        elif action == "VIBRATE_RIGHT":
            self._motor_driver.vibrate("RIGHT", intensity=intensity)
