from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from hardware.esp32_comm import Esp32Comm

Side = Literal["LEFT", "RIGHT"]


@dataclass(frozen=True)
class MotorCommand:
    side: Side
    intensity: float  # 0..1


class MotorDriver:
    """
    Sends vibration commands to an ESP32 (optional).
    If no comm is provided, it falls back to console prints.
    """

    def __init__(self, comm: Optional[Esp32Comm] = None):
        self._comm = comm

    def vibrate(self, side: Side, *, intensity: float) -> None:
        intensity = max(0.0, min(1.0, float(intensity)))

        if self._comm is None or not self._comm.is_connected():
            print(f"[MOTOR] {side} duty={intensity:.2f}")
            return

        self._comm.send_line(f"VIBRATE {side} {intensity:.2f}")

    def stop(self) -> None:
        if self._comm is None or not self._comm.is_connected():
            print("[MOTOR] STOP")
            return
        self._comm.send_line("STOP")
