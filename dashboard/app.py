from __future__ import annotations

from dashboard.metrics import compute_basic_metrics


def run():
    # Minimal CLI dashboard (Streamlit can replace this later)
    metrics = compute_basic_metrics()
    print("AuraEdu Dashboard (basic)")
    print(metrics)


if __name__ == "__main__":
    run()
