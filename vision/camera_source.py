"""Automatic camera acquisition, separate from pose detection and classification."""
import config


def open_available_camera(cv2, stop_event):
    """Return (capture, index, backend) for the first device with a valid frame.

    Args:
        cv2: OpenCV module or a compatible test double.
        stop_event: Thread event used to cancel startup waits.
    Returns:
        tuple: Capture and device details, or (None, -1, '') when unavailable.
    """
    preferred = config.POSE_CAMERA_INDEX
    indices = [preferred] + [i for i in range(config.CAMERA_SCAN_COUNT) if i != preferred]
    backends = [(getattr(cv2, name), name) for name in config.CAMERA_BACKEND_NAMES
                if hasattr(cv2, name)]
    for index in indices:
        for backend, name in backends:
            if stop_event.is_set():
                return None, -1, ''
            capture = None
            selected = False
            try:
                capture = cv2.VideoCapture(index, backend)
                if not capture.isOpened():
                    continue
                for _ in range(config.CAMERA_WARMUP_READS):
                    if stop_event.is_set():
                        return None, -1, ''
                    ok, frame = capture.read()
                    if ok and frame is not None and frame.size > 0:
                        selected = True
                        return capture, index, name
                    if stop_event.wait(config.CAMERA_WARMUP_DELAY):
                        return None, -1, ''
            except Exception as error:
                print(f'[CAMERA] indice={index}, backend={name}: {error}')
            finally:
                if capture is not None and not selected:
                    capture.release()
    return None, -1, ''
