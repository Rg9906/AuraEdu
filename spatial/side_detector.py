def detect_side(detection, frame_width):

    x1, y1, x2, y2 = detection["bbox"]

    center_x = (x1 + x2) / 2

    if center_x < frame_width / 3:
        return "LEFT"

    elif center_x > 2 * frame_width / 3:
        return "RIGHT"

    else:
        return "CENTER"