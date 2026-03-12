from ultralytics import YOLO

class Detector:

    def __init__(self):
        self.model = YOLO("yolov8n.pt")

    def detect(self, frame):
        results = self.model(frame,verbose=False)

        detections = []

        for r in results:
            boxes = r.boxes

            if boxes is None:
                continue

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": conf,
                    "class": cls
                })

        return detections