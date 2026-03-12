from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Esp32Config:
    port: str = "COM3"
    baudrate: int = 115200
    timeout_s: float = 0.2


class Esp32Comm:
    """
    Minimal serial comm wrapper.

    Protocol suggestion (simple for prototype):
      VIBRATE LEFT 0.60\n
      VIBRATE RIGHT 1.00\n
      STOP\n
    """

    def __init__(self, config: Esp32Config):
        self.config = config
        self._ser = None

    def connect(self) -> None:
        try:
            import serial  # type: ignore
        except Exception as e:
            raise RuntimeError("pyserial not installed. Add it to requirements.txt.") from e

        self._ser = serial.Serial(
            port=self.config.port,
            baudrate=self.config.baudrate,
            timeout=self.config.timeout_s,
        )

    def is_connected(self) -> bool:
        return self._ser is not None

    def send_line(self, line: str) -> None:
        if not self._ser:
            return
        data = (line.rstrip("\n") + "\n").encode("utf-8", errors="ignore")
        self._ser.write(data)

    def close(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            finally:
                self._ser = None
