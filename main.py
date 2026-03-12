from __future__ import annotations

import time

from dashboard.logger import EventLogger
from decision.attention_logic import decide_feedback
from decision.feedback_controller import FeedbackController
from spatial.object_mapper import map_detections, pick_priority_stimulus
from utils.config import AppConfig
from vision.camera import Camera
from vision.detector import Detector
from vision.preprocess import preprocess_frame


def main():
    cfg = AppConfig()

    camera = Camera(camera_index=cfg.camera_index)
    detector = Detector()
    feedback = FeedbackController()
    logger = EventLogger()

    print("AuraEdu running.")
    print("Controls: Q to quit, P to pause/resume.")

    paused = False

    try:
        import cv2  # type: ignore
    except Exception:
        cv2 = None

    while True:
        if cv2 is not None:
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                paused = not paused
                print("Paused." if paused else "Resumed.")

        if paused:
            time.sleep(0.05)
            continue

        frame = camera.get_frame()
        frame = preprocess_frame(frame, target_width=cfg.preprocess_width)

        detections = detector.detect(frame)
        frame_width = int(frame.shape[1])

        stimuli = map_detections(detections, frame_width=frame_width)
        chosen = pick_priority_stimulus(stimuli, neglected_side=cfg.neglected_side)  # type: ignore[arg-type]

        decision = decide_feedback(chosen, neglected_side=cfg.neglected_side)  # type: ignore[arg-type]
        feedback.apply(decision.as_dict())

        if chosen:
            logger.log(
                {
                    "stimulus_side": chosen["side"],
                    "stimulus_area": chosen["area"],
                    "danger_level": chosen["danger"],
                    "response_type": decision.response_type,
                    "action": decision.action,
                    "intensity": decision.intensity,
                }
            )

        if cv2 is not None:
            # Simple viz: draw only chosen stimulus box
            if chosen:
                x1, y1, x2, y2 = map(int, chosen["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f'{chosen["side"]} {chosen["danger"]}',
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
            cv2.imshow("AuraEdu Vision", frame)

    camera.release()
    if cv2 is not None:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()