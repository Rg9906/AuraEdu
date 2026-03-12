from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    camera_index: int = 0
    neglected_side: str = "LEFT"
    preprocess_width: int | None = 960
    esp32_port: str = "COM3"
    esp32_baudrate: int = 115200
