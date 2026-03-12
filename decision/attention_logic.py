from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

Side = Literal["LEFT", "CENTER", "RIGHT"]
ResponseType = Literal["SELF_RECOGNIZED", "ASSISTED_RESPONSE", "MISSED_STIMULUS"]


@dataclass(frozen=True)
class Decision:
    action: Literal["NONE", "VIBRATE_LEFT", "VIBRATE_RIGHT"]
    intensity: float  # 0..1
    response_type: ResponseType

    def as_dict(self) -> Dict:
        return {
            "action": self.action,
            "intensity": float(self.intensity),
            "response_type": self.response_type,
        }


def danger_to_intensity(danger: str) -> float:
    return {"LOW": 0.25, "MEDIUM": 0.6, "HIGH": 1.0}.get(danger, 0.4)


def decide_feedback(
    stimulus: Optional[Dict],
    *,
    neglected_side: Side = "LEFT",
) -> Decision:
    """
    Prototype decision engine:
    - No stimulus => no action
    - LEFT stimulus => vibrate left; RIGHT stimulus => vibrate right
    - CENTER => no directional vibration (can be extended)
    """
    if not stimulus:
        return Decision(action="NONE", intensity=0.0, response_type="SELF_RECOGNIZED")

    side = stimulus.get("side", "CENTER")
    danger = stimulus.get("danger", "LOW")
    intensity = danger_to_intensity(danger)

    if side == "LEFT":
        return Decision(action="VIBRATE_LEFT", intensity=intensity, response_type="ASSISTED_RESPONSE")
    if side == "RIGHT":
        return Decision(action="VIBRATE_RIGHT", intensity=intensity, response_type="ASSISTED_RESPONSE")
    return Decision(action="NONE", intensity=0.0, response_type="SELF_RECOGNIZED")
