"""
PoseController – Captura webcam + MediaPipe en hilo daemon.
Publica PoseState inmutable; el hilo de juego llama snapshot() sin bloquear.

Cambios v3 (webcam-first):
  · preview grande (320 px) con esqueleto durante calibración
  · preview pequeño (144 px) durante partida cuando preview_active
  · state.calibrating = True mientras GestureClassifier no tenga baseline
  · camera_error = True / error_msg si la cámara no puede abrirse
"""

from dataclasses import dataclass, field
from threading import Event, Lock, Thread
import time


# ─── Estado publicado (inmutable) ────────────────────────────────────────────

@dataclass(frozen=True)
class PoseState:
    status: str = "INICIANDO"
    lane: int | None = None
    timestamp: float = 0.0
    preview_rgb: bytes | None = None
    preview_size: tuple[int, int] = (0, 0)
    gesture: str = "RUN"
    calibrated: bool = False
    calibration_progress: float = 0.0
    shoulder_delta: float | None = None
    hip_delta: float | None = None
    # nuevos campos v3
    calibrating: bool = True     # True hasta que GestureClassifier termine
    camera_error: bool = False   # True si la webcam no pudo abrirse
    error_msg: str = ""          # Descripción del error
    landmarks_visible: bool = False   # True si MediaPipe detecta hombros+caderas


# ─── Estabilizador lateral ────────────────────────────────────────────────────

class PoseStabilizer:
    def __init__(self, seconds: float = 0.18):
        self.seconds = seconds
        self.candidate = None
        self.since = 0.0

    def update(self, position, now: float) -> tuple[str, int | None]:
        """Devuelve (status_str, lane_int_or_None)."""
        if position is None:
            self.candidate = None
            return "SIN POSTURA", None
        if position != self.candidate:
            self.candidate = position
            self.since = now
        if now - self.since < self.seconds:
            return f"{position.value} (ESTABILIZANDO)", None
        lane = {"LEFT": 0, "CENTER": 1, "RIGHT": 2}[position.value]
        return position.value, lane


# ─── Controlador principal ────────────────────────────────────────────────────

class PoseController:
    """
    Hilo daemon que captura la webcam y publica PoseState.

    Uso:
        ctrl = PoseController(camera_index=0)
        ctrl.start()           # inicia el hilo
        state = ctrl.snapshot()   # sin bloquear
        ctrl.close()           # señala parada
    """

    STALE_SECONDS = 0.75       # marca estado como obsoleto si no hay frames nuevos
    PREVIEW_CAL_SIZE = 320     # resolución durante calibración (px del lado mayor)
    PREVIEW_GAME_SIZE = 144    # resolución durante partida

    def __init__(self, camera_index: int = 0,
                 dead_zone: float = 0.10, hysteresis: float = 0.03,
                 stable_seconds: float = 0.18):
        self.camera_index = camera_index
        self._dead_zone = dead_zone
        self._hysteresis = hysteresis
        self._stable_seconds = stable_seconds

        self._state = PoseState(calibrating=True)
        self._lock = Lock()
        self._stop = Event()
        self._recalibrate = Event()
        self._preview_enabled = False   # toggle mini-cam durante partida

        self._thread = Thread(
            target=self._capture,
            name="pose-camera",
            daemon=True,
        )

    # ── API pública ───────────────────────────────────────────────────────

    def start(self) -> None:
        self._thread.start()

    def snapshot(self) -> PoseState:
        """Devuelve el último estado; hilo-seguro, sin bloquear."""
        with self._lock:
            state = self._state
        # Si el estado es válido pero antiguo, márcalo como sin postura
        if (
            not state.camera_error
            and not state.calibrating
            and state.lane is not None
            and time.monotonic() - state.timestamp > self.STALE_SECONDS
        ):
            return PoseState(
                status="SIN POSTURA", lane=None,
                timestamp=state.timestamp,
                calibrated=state.calibrated,
                calibrating=False,
            )
        return state

    def enable_preview(self, value: bool) -> None:
        """Activa/desactiva mini-cam durante la partida."""
        self._preview_enabled = value

    def recalibrate(self) -> None:
        """Reinicia la calibración de gestos verticales."""
        self._recalibrate.set()
        self._publish(PoseState(status="CALIBRANDO...", calibrating=True))

    def close(self) -> None:
        """Señala al hilo que debe terminar."""
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=0.5)

    # ── Hilo de captura ───────────────────────────────────────────────────

    def _publish(self, state: PoseState) -> None:
        with self._lock:
            self._state = state

    def _capture(self) -> None:
        camera = None
        try:
            import cv2
            from vision.pose_detector import PoseDetector
            from vision.movement_classifier import MovementClassifier
            from vision.gesture_classifier import GestureClassifier

            classifier = MovementClassifier(self._dead_zone, self._hysteresis)
            stabilizer = PoseStabilizer(self._stable_seconds)
            gestures = GestureClassifier()

            with PoseDetector() as detector:
                # ── Abrir cámara ─────────────────────────────────────────
                camera = cv2.VideoCapture(self.camera_index)
                if not camera.isOpened():
                    self._publish(PoseState(
                        status="ERROR: no se pudo abrir la cámara",
                        calibrating=True,
                        camera_error=True,
                        error_msg=(
                            f"No se pudo abrir la webcam (índice {self.camera_index}).\n"
                            "Comprueba que esté conectada y que ningún otro\n"
                            "programa la esté usando. Pulsa K para reintentar."
                        ),
                    ))
                    return

                while not self._stop.is_set():
                    ok, frame = camera.read()
                    if not ok or frame is None:
                        self._publish(PoseState(
                            status="ERROR: sin señal de cámara",
                            calibrating=True,
                            camera_error=True,
                            error_msg="La cámara se desconectó. Pulsa K para reintentar.",
                        ))
                        time.sleep(0.1)
                        continue

                    frame = cv2.flip(frame, 1)   # espejo

                    # ── Recalibración ─────────────────────────────────────
                    if self._recalibrate.is_set():
                        gestures.recalibrate()
                        classifier = MovementClassifier(self._dead_zone, self._hysteresis)
                        stabilizer = PoseStabilizer(self._stable_seconds)
                        self._recalibrate.clear()

                    now = time.monotonic()

                    # ── Detección de pose ─────────────────────────────────
                    landmarks = detector.detect(frame)
                    center = detector.torso_center(landmarks)
                    landmarks_visible = center is not None

                    # ── Clasificación lateral ─────────────────────────────
                    position = classifier.classify(center[0] if center else None)
                    status_str, lane = stabilizer.update(position, now)

                    # ── Clasificación de gestos verticales ────────────────
                    gesture = gestures.classify(landmarks, now)
                    calibrated = gestures.baseline is not None
                    calibrating = not calibrated

                    # ── Preview ───────────────────────────────────────────
                    if calibrating:
                        # Durante calibración: preview grande siempre activo
                        preview, size = self._make_preview(
                            frame, detector, landmarks, center,
                            classifier, self.PREVIEW_CAL_SIZE,
                            overlay_text=self._calibration_overlay(
                                gesture, gestures.progress, landmarks_visible,
                            ),
                        )
                    elif self._preview_enabled:
                        # Durante partida si el usuario activó mini-cam
                        preview, size = self._make_preview(
                            frame, detector, landmarks, center,
                            classifier, self.PREVIEW_GAME_SIZE,
                        )
                    else:
                        preview, size = None, (0, 0)

                    self._publish(PoseState(
                        status=status_str,
                        lane=lane,
                        timestamp=now,
                        preview_rgb=preview,
                        preview_size=size,
                        gesture=gesture,
                        calibrated=calibrated,
                        calibration_progress=gestures.progress,
                        shoulder_delta=gestures.shoulder_delta,
                        hip_delta=gestures.hip_delta,
                        calibrating=calibrating,
                        camera_error=False,
                        error_msg="",
                        landmarks_visible=landmarks_visible,
                    ))

        except Exception as exc:
            msg = str(exc)
            self._publish(PoseState(
                status="NO DISPONIBLE",
                calibrating=True,
                camera_error=True,
                error_msg=f"Error inesperado:\n{msg}\n\nUsando solo teclado.",
            ))
            print(f"[POSE] Error en hilo de captura: {exc}", flush=True)
        finally:
            if camera is not None:
                try:
                    camera.release()
                except Exception:
                    pass

    # ── Helpers de preview ────────────────────────────────────────────────

    @staticmethod
    def _calibration_overlay(gesture: str, progress: float,
                              landmarks_visible: bool) -> list[tuple]:
        """Líneas de texto [(texto, color_bgr, y_ratio)] para el overlay."""
        lines = []
        if not landmarks_visible:
            lines.append(("Colócate frente a la cámara", (0, 180, 255), 0.12))
            lines.append(("Asegúrate de que se vean hombros y caderas", (0, 180, 255), 0.20))
        else:
            pct = int(progress * 100)
            lines.append((f"CALIBRANDO  {pct}%", (50, 230, 230), 0.10))
            lines.append(("Párate erguido, sin moverte", (200, 220, 180), 0.18))
        return lines

    def _make_preview(self, frame, detector, landmarks, center,
                      classifier, max_side: int,
                      overlay_text: list | None = None):
        """Anota el frame y lo reduce a max_side px; devuelve (bytes_rgb, (w, h))."""
        import cv2

        height, width = frame.shape[:2]
        dz = classifier.dead_zone
        boundaries = (
            0,
            int(width * (0.5 - dz)),
            int(width * (0.5 + dz)),
            width,
        )

        # ── Franjas de zona de carril ──────────────────────────────────────
        tint = frame.copy()
        zone_colors = ((40, 80, 180), (40, 160, 60), (180, 60, 40))  # IZQ/CEN/DER
        for idx, col in enumerate(zone_colors):
            cv2.rectangle(tint,
                          (boundaries[idx], 0),
                          (boundaries[idx + 1] - 1, height - 1),
                          col, -1)
        cv2.addWeighted(tint, 0.15, frame, 0.85, 0, dst=frame)

        # ── Esqueleto MediaPipe ────────────────────────────────────────────
        detector.draw_landmarks(frame, landmarks)

        # ── Líneas de división de carriles ────────────────────────────────
        for x in boundaries[1:-1]:
            cv2.line(frame, (x, 0), (x, height - 1), (240, 240, 240), 2)

        # ── Marcador de centro del torso ──────────────────────────────────
        if center is not None:
            pt = (int(center[0] * width), int(center[1] * height))
            cv2.circle(frame, pt, max(10, width // 40), (0, 0, 0), 4)
            cv2.drawMarker(frame, pt, (0, 255, 255), cv2.MARKER_CROSS,
                           max(20, width // 25), 4)

        # ── Overlay de texto ──────────────────────────────────────────────
        if overlay_text:
            for text, col, y_ratio in overlay_text:
                y_px = int(height * y_ratio)
                cv2.putText(frame, text, (10, y_px),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, text, (10, y_px),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 1, cv2.LINE_AA)

        # ── Reducir tamaño ────────────────────────────────────────────────
        if width >= height:
            new_w, new_h = max_side, max(1, round(height * max_side / width))
        else:
            new_w, new_h = max(1, round(width * max_side / height)), max_side

        reduced = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        rgb_bytes = cv2.cvtColor(reduced, cv2.COLOR_BGR2RGB).tobytes()
        return rgb_bytes, (new_w, new_h)
