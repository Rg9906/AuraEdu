"""
Camera sensor module for Aura-Edu system.
Wraps the existing camera functionality with enhanced spatial detection.
"""

import cv2
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

from core.types import Direction, Detection, Stimulus, Danger
from vision.detector import Detector
from vision.preprocess import preprocess_frame


class CameraSensor:
    """
    Enhanced camera sensor with 4-direction spatial detection.
    Integrates with existing YOLO detector and adds direction mapping.
    """
    
    def __init__(self, camera_index: int = 0, config=None):
        self.camera_index = camera_index
        self.config = config
        self.is_active = False
        self.camera = None
        self.detector = None
        self.last_frame = None
        self.last_detections = []
        self.last_stimuli = []
        
        # Direction mapping zones (normalized coordinates)
        self.zones = {
            Direction.LEFT: (0.0, 0.35),      # 0-35% of frame width
            Direction.CENTER: (0.35, 0.65),    # 35-65% of frame width
            Direction.RIGHT: (0.65, 1.0),      # 65-100% of frame width
        }
        
        # Distance estimation parameters (calibration needed for real hardware)
        self.focal_length = 800.0  # pixels
        self.known_object_width = 50.0  # cm (average person shoulder width)
    
    def start(self) -> bool:
        """Start the camera and detector."""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                return False
            
            self.detector = Detector()
            self.is_active = True
            return True
        except Exception:
            return False
    
    def stop(self) -> bool:
        """Stop the camera."""
        if self.camera:
            self.camera.release()
        self.is_active = False
        return True
    
    def capture_frame(self) -> Optional[Any]:
        """
        Capture a single frame from the camera.
        
        Returns:
            OpenCV frame or None if capture failed.
        """
        if not self.is_active or not self.camera:
            return None
        
        ret, frame = self.camera.read()
        if ret:
            self.last_frame = frame
            return frame
        return None
    
    def detect_objects(self, frame=None) -> List[Detection]:
        """
        Detect objects in the current frame.
        
        Args:
            frame: Frame to process (uses last captured frame if None)
            
        Returns:
            List of Detection objects.
        """
        if frame is None:
            frame = self.last_frame
        
        if frame is None or not self.detector:
            return []
        
        # Preprocess frame
        target_width = self.config.vision.preprocess_width if self.config else 960
        processed_frame = preprocess_frame(frame, target_width)
        
        # Detect objects
        raw_detections = self.detector.detect(processed_frame)
        
        # Convert to Detection objects
        detections = []
        for det in raw_detections:
            detection = Detection(
                bbox=tuple(det["bbox"]),
                confidence=float(det["confidence"]),
                class_id=int(det["class"]),
                class_name=self._get_class_name(int(det["class"]))
            )
            detections.append(detection)
        
        self.last_detections = detections
        return detections
    
    def map_to_stimuli(self, detections: List[Detection], frame_width: int) -> List[Stimulus]:
        """
        Convert detections to stimuli with spatial and danger information.
        
        Args:
            detections: List of object detections
            frame_width: Width of the frame for direction mapping
            
        Returns:
            List of Stimulus objects.
        """
        stimuli = []
        
        for detection in detections:
            # Determine direction
            direction = self._get_direction(detection.bbox, frame_width)
            
            # Calculate area and danger
            area = self._bbox_area(detection.bbox)
            danger = self._area_to_danger(area)
            
            # Estimate distance
            estimated_distance = self._estimate_distance(detection.bbox)
            
            stimulus = Stimulus(
                bbox=detection.bbox,
                direction=direction,
                area=area,
                danger=danger,
                confidence=detection.confidence,
                class_id=detection.class_id,
                class_name=detection.class_name,
                estimated_distance=estimated_distance
            )
            stimuli.append(stimulus)
        
        self.last_stimuli = stimuli
        return stimuli
    
    def _get_direction(self, bbox: tuple, frame_width: int) -> Direction:
        """
        Determine which direction the object is in based on bounding box.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            frame_width: Width of the frame
            
        Returns:
            Direction enum value.
        """
        x1, _, x2, _ = bbox
        center_x = (x1 + x2) / 2.0
        normalized_x = center_x / frame_width
        
        for direction, (start, end) in self.zones.items():
            if start <= normalized_x < end:
                return direction
        
        return Direction.CENTER
    
    def _bbox_area(self, bbox: tuple) -> float:
        """Calculate bounding box area."""
        x1, y1, x2, y2 = bbox
        return max(0.0, (x2 - x1)) * max(0.0, (y2 - y1))
    
    def _area_to_danger(self, area: float) -> Danger:
        """
        Convert area to danger level (distance proxy).
        
        Args:
            area: Bounding box area in pixels
            
        Returns:
            Danger level based on area size.
        """
        if area >= 90_000:
            return Danger.HIGH
        elif area >= 25_000:
            return Danger.MEDIUM
        else:
            return Danger.LOW
    
    def _estimate_distance(self, bbox: tuple) -> Optional[float]:
        """
        Estimate distance from object based on bounding box size.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Estimated distance in cm or None if estimation fails.
        """
        _, _, x2, y2 = bbox
        object_width_pixels = x2
        
        if object_width_pixels <= 0:
            return None
        
        # Simple distance estimation using similar triangles
        # distance = (known_width * focal_length) / perceived_width
        estimated_distance = (self.known_object_width * self.focal_length) / object_width_pixels
        return max(10.0, min(500.0, estimated_distance))  # Clamp to reasonable range
    
    def _get_class_name(self, class_id: int) -> Optional[str]:
        """Get class name from YOLO class ID."""
        try:
            from ultralytics import YOLO
            # Load model temporarily to get class names (cache this in production)
            model = YOLO('yolov8n.pt')
            if class_id < len(model.names):
                return model.names[class_id]
        except Exception:
            pass
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get camera sensor status."""
        return {
            "camera_index": self.camera_index,
            "is_active": self.is_active,
            "last_detection_count": len(self.last_detections),
            "last_stimuli_count": len(self.last_stimuli),
            "camera_open": self.camera.isOpened() if self.camera else False,
            "detector_loaded": self.detector is not None
        }
    
    def release(self):
        """Release camera resources."""
        if self.camera:
            self.camera.release()
        self.is_active = False
