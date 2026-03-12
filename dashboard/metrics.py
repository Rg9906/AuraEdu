from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict


def compute_basic_metrics(log_path: Path = Path("dashboard") / "events.jsonl") -> Dict:
    if not log_path.exists():
        return {"total_events": 0, "response_type_counts": {}}

    counts = Counter()
    total = 0
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            counts[obj.get("response_type", "UNKNOWN")] += 1

    return {"total_events": total, "response_type_counts": dict(counts)}
