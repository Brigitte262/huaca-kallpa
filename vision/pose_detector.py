"""Procesamiento BGR con MediaPipe Pose; independiente del videojuego."""
from math import isfinite
from pathlib import Path
import time
from urllib.request import urlopen
import cv2
import mediapipe as mp

MODEL_PATH = Path(__file__).resolve().parent / 'models' / 'pose_landmarker_lite.task'
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'

def ensure_model(path=MODEL_PATH):
    """Descarga una vez el modelo oficial; no transmite imágenes."""
    path = Path(path)
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.download')
    try:
        print('Descargando modelo MediaPipe Pose Lite...', flush=True)
        with urlopen(MODEL_URL, timeout=60) as response, temporary.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temporary.replace(path)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f'No se pudo descargar el modelo. Descarga {MODEL_URL} en {path}') from exc
    return path

class PoseDetector:
    def __init__(self, model_path=MODEL_PATH, min_confidence=0.5):
        self.min_confidence = min_confidence
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(ensure_model(model_path))),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_confidence,
            min_pose_presence_confidence=min_confidence,
            min_tracking_confidence=min_confidence,
        )
        self._pose = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        self._timestamp = -1

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp = max(self._timestamp + 1, time.monotonic_ns() // 1_000_000)
        result = self._pose.detect_for_video(image, self._timestamp)
        return result.pose_landmarks[0] if result.pose_landmarks else []

    def _visible(self, point):
        return (isfinite(point.x) and isfinite(point.y)
                and 0 <= point.x <= 1 and 0 <= point.y <= 1
                and (point.visibility or 0) >= self.min_confidence
                and (point.presence or 0) >= self.min_confidence)

    def torso_center(self, landmarks):
        """Punto medio entre hombros (11 y 12), o None si no son fiables."""
        if len(landmarks) < 13:
            return None
        left, right = landmarks[11], landmarks[12]
        if not self._visible(left) or not self._visible(right):
            return None
        return ((left.x + right.x) / 2, (left.y + right.y) / 2)

    def draw_landmarks(self, frame, landmarks):
        height, width = frame.shape[:2]
        points = {i: (int(p.x * (width - 1)), int(p.y * (height - 1)))
                  for i, p in enumerate(landmarks) if self._visible(p)}
        for connection in mp.tasks.vision.PoseLandmarksConnections.POSE_LANDMARKS:
            if connection.start in points and connection.end in points:
                cv2.line(frame, points[connection.start], points[connection.end],
                         (80, 220, 100), 2, cv2.LINE_AA)
        for point in points.values():
            cv2.circle(frame, point, 4, (30, 180, 255), -1, cv2.LINE_AA)

    def close(self):
        self._pose.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
