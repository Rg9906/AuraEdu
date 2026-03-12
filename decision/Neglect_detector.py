import time


class NeglectDetector:

    def __init__(self):

        self.last_seen_time = None
        self.last_side = None
        self.threshold = 2

    def evaluate(self, object_side, head_direction):

        current_time = time.time()

        if object_side != self.last_side:
            self.last_side = object_side
            self.last_seen_time = current_time
            return "NONE"

        if object_side == "LEFT" and head_direction == "RIGHT":
            if current_time - self.last_seen_time > self.threshold:
                return "VIBRATE_LEFT"

        if object_side == "RIGHT" and head_direction == "LEFT":
            if current_time - self.last_seen_time > self.threshold:
                return "VIBRATE_RIGHT"

        return "NONE"