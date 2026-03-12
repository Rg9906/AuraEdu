import cv2

from vision.camera import Camera
from vision.detector import Detector
from spatial.side_detector import detect_side


camera = Camera()
detector = Detector()

running = True

print("Controls:")
print("P → Pause/Resume detection")
print("Q → Quit program")


while True:

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        print("Exiting program...")
        break

    if key == ord('p'):
        running = not running

        if running:
            print("Detection Resumed")
        else:
            print("Detection Paused")

    if not running:
        continue


    frame = camera.get_frame()

    detections = detector.detect(frame)

    frame_width = frame.shape[1]

    for d in detections:

        side = detect_side(d, frame_width)

        x1, y1, x2, y2 = map(int, d["bbox"])

        color = (0, 255, 0)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.putText(
            frame,
            side,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

        print("Object detected on:", side)

    cv2.imshow("AuraEdu Vision", frame)


camera.release()
cv2.destroyAllWindows()