from __future__ import annotations

from typing import Literal

Side = Literal["LEFT", "CENTER", "RIGHT"]


def head_direction_from_imu(imu: dict) -> Side:
    """
    Prototype placeholder: map yaw/pitch/roll to coarse head direction.
    """
    yaw = float(imu.get("yaw", 0.0))
    if yaw < -15:
        return "LEFT"
    if yaw > 15:
        return "RIGHT"
    return "CENTER"
