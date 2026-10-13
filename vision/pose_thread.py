"""
pose_thread.py – Hilo de captura OpenCV + MediaPipe para Huaca Kallpa.

Diseño intencional:
  · Un hilo daemon lee la webcam y MediaPipe.
  · Publica un string de estado en una variable atómica (lock).
  · Abre una ventana cv2 de DEBUG con frame + landmarks + estado.
  · El hilo de Ursina solo llama a PoseThread.get_state().

Estados posibles:
  'CENTER'  – torso centrado   → carril 1
  'LEFT'    – torso a la izq.  → carril 0
  'RIGHT'   – torso a la der.  → carril 2
  'JUMP'    – salto detectado
  'CROUCH'  – agacharse detectado
  'NO_POSE' – MediaPipe no ve el cuerpo
  'CALIBRATING' – fase inicial de calibración

Uso:
    from vision.pose_thread import PoseThread
    pt = PoseThread()
    pt.start()             # inicia el hilo y la ventana de debug
    state = pt.get_state() # llama cada frame desde Ursina
    pt.stop()              # al cerrar el juego
"""

from __future__ import annotations

import threading
import time
from math import isfinite
from collections import deque
from statistics import median

# ── Constantes de clasificación ───────────────────────────────────────────────

# Lateral
DEAD_ZONE   = 0.12   # fracción del ancho; zona central
HYSTERESIS  = 0.03   # banda extra para evitar flicker

# Vertical (fracción de altura de torso)
JUMP_THRESH   = 0.08   # hombros/cadera suben más de esto → JUMP
CROUCH_THRESH = 0.10   # hombros/cadera bajan más de esto → CROUCH
RELEASE_RATIO = 0.50   # umbral de "vuelta a neutro"
COOLDOWN_S    = 0.80   # segundos entre gestos iguales
CONFIRM_S     = 0.06   # segundos que debe mantenerse el gesto para confirmarlo
NEUTRAL_S     = 0.12   # segundos en neutro antes de armar de nuevo

# Calibración
CALIB_SECONDS = 2.5    # duración de la calibración inicial
CALIB_MIN_FRAMES = 10  # mínimo de frames para aceptar baseline
WINDOW_FRAMES = 5      # ventana de suavizado
WINDOW_S      = 0.22
MIN_CONF      = 0.50   # confianza mínima de MediaPipe

# Estabilizador lateral
STABLE_S = 0.18        # segundos que debe mantenerse la posición lateral

# ── Clase principal ───────────────────────────────────────────────────────────

class PoseThread:
    """
    Hilo daemon que:
      1. Busca una cámara disponible con backends DirectShow/MSMF y espera frames iniciales.
         Esto activa físicamente el hardware de la cámara (LED) en Windows.
      2. Ejecuta MediaPipe Pose cada frame.
      3. Clasifica estado lateral + gesto vertical.
      4. Opcionalmente muestra ventana de debug con OpenCV (show_debug=True).
      5. Publica estado en self._state (string, protegido por Lock).
      6. Publica el frame BGR más reciente en self._frame (accesible via get_frame()).

    Parámetros
    ----------
    show_debug : bool
        Si True, abre la ventana "Huaca Kallpa – Pose Debug" con cv2.imshow.
        Por defecto False para no abrir ventanas externas al juego.
    """

    DEBUG_WINDOW = "Huaca Kallpa - Pose Debug"

    def __init__(self, show_debug: bool = False):
        from vision.body_action_bridge import BodyActionBridge
        self._body_actions = BodyActionBridge()
        self._state: str = "CALIBRATING"
        self._lock = threading.Lock()
        self._frame_lock = threading.Lock()
        self._frame = None          # frame BGR más reciente (para get_frame())
        self._show_debug = show_debug
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="pose-thread",
            daemon=True,
        )
        # Lateral
        self._lat_position: str = "CENTER"   # LEFT / CENTER / RIGHT
        # Vertical classifier state
        self._vert_baseline: tuple[float, float] | None = None
        self._vert_samples: list[tuple[float, float]] = []
        self._calib_since: float | None = None
        self._calib_progress: float = 0.0
        self._vert_window: deque = deque(maxlen=WINDOW_FRAMES)
        self._vert_gesture: str = "RUN"   # RUN / JUMP / CROUCH
        self._vert_candidate: str = "RUN"
        self._vert_since: float = 0.0
        self._vert_last_activation: float = float('-inf')
        self._vert_armed: bool = True
        self._vert_neutral_since: float | None = None

    # ── API pública ────────────────────────────────────────────────────────

    def start(self) -> None:
        """Arranca el hilo daemon (no bloquea)."""
        self._thread.start()

    def is_running(self) -> bool:
        """Return whether the acquisition worker is still alive."""
        return self._thread.is_alive()

    def get_state(self) -> str:
        """Thread-safe. Devuelve el estado actual como string."""
        with self._lock:
            return self._state

    def get_frame(self):
        """
        Thread-safe. Devuelve el frame BGR más reciente (numpy array) o None.
        Usado por main.py para actualizar el panel webcam dentro de Ursina.
        """
        with self._frame_lock:
            return self._frame

    def stop(self) -> None:
        """Señala parada y espera hasta 0.5 s."""
        self._stop_event.set()
        self._thread.join(timeout=0.5)
        try:
            import cv2
            cv2.destroyWindow(self.DEBUG_WINDOW)
        except Exception:
            pass

    # ── Hilo principal ────────────────────────────────────────────────────

    def _open_camera(self, cv2_mod):
        """Return the first working integrated/external camera, with startup warmup."""
        from vision.camera_source import open_available_camera
        capture, index, backend = open_available_camera(cv2_mod, self._stop_event)
        if capture is not None:
            print(f'[POSE] CAMERA INITIALIZED indice={index}, backend={backend}')
        return capture, index, backend

    def _run(self) -> None:
        try:
            import cv2
            from vision.pose_detector import PoseDetector
        except ImportError as exc:
            print(f"[POSE] No se pudo importar cv2/MediaPipe: {exc}")
            self._set_state("NO_POSE")
            return

        # ── Abrir cámara con backend explícito ────────────────────────────
        import config
        cam = None
        while cam is None and not self._stop_event.is_set():
            cam, cam_index, bname = self._open_camera(cv2)
            if cam is None:
                self._set_state("NO_POSE")
                print('[POSE] Camara no disponible; reintentando automaticamente.')
                if self._stop_event.wait(config.CAMERA_RETRY_DELAY):
                    return
        if cam is None:
            return

        # ── Bucle de captura ──────────────────────────────────────────────
        try:
            with PoseDetector() as detector:
                failed_reads = 0
                while not self._stop_event.is_set():
                    ok, frame = cam.read()
                    if not ok or frame is None or frame.size == 0:
                        failed_reads += 1
                        if failed_reads >= config.CAMERA_FAILED_READ_LIMIT:
                            print('[POSE] Camera signal lost; releasing device.')
                            break
                        if self._stop_event.wait(config.CAMERA_FAILED_READ_DELAY):
                            break
                        continue
                    failed_reads = 0

                    frame = cv2.flip(frame, 1)   # espejo
                    now   = time.monotonic()

                    # Detectar landmarks
                    landmarks = detector.detect(frame)
                    center    = detector.torso_center(landmarks)

                    # Clasificar
                    state = self._classify(landmarks, center, now)
                    state = self._body_actions.classify(
                        landmarks, state, now, self._vert_baseline)
                    self._set_state(state)

                    # Guardar frame para get_frame() (siempre, antes de anotar debug)
                    with self._frame_lock:
                        self._frame = frame.copy()

                    # Ventana de debug (solo si show_debug=True)
                    if self._show_debug:
                        self._draw_debug(frame, detector, landmarks, center, state)
                        cv2.imshow(self.DEBUG_WINDOW, frame)
                        if cv2.waitKey(1) & 0xFF == 27:   # Esc cierra solo la ventana
                            break
                    else:
                        # Sin ventana de debug: solo procesar eventos OpenCV mínimos
                        # para evitar bloqueos en algunos drivers de Windows
                        cv2.waitKey(1)

        except Exception as exc:
            print(f"[POSE] Error en bucle de captura: {exc}")
            self._set_state("NO_POSE")
        finally:
            with self._frame_lock:
                self._frame = None
            self._set_state("NO_POSE")
            cam.release()
            try:
                cv2.destroyWindow(self.DEBUG_WINDOW)
            except Exception:
                pass

    # ── Clasificación lateral ─────────────────────────────────────────────

    def _classify_lateral(self, center_x: float | None) -> str:
        if center_x is None or not isfinite(center_x):
            return "CENTER"   # pose perdida → mantener centro
        left_bound  = 0.5 - DEAD_ZONE
        right_bound = 0.5 + DEAD_ZONE

        prev = self._lat_position
        if center_x < left_bound:
            self._lat_position = "LEFT"
        elif center_x > right_bound:
            self._lat_position = "RIGHT"
        elif prev == "LEFT"  and center_x < left_bound  + HYSTERESIS:
            pass   # histéresis
        elif prev == "RIGHT" and center_x > right_bound - HYSTERESIS:
            pass
        else:
            self._lat_position = "CENTER"
        return self._lat_position

    # ── Clasificación vertical (JUMP / CROUCH) ────────────────────────────

    def _classify_vertical(self, landmarks, now: float) -> str:
        """Devuelve RUN / JUMP / CROUCH / CALIBRATING."""
        # Verificar landmarks 11,12 (hombros) y 23,24 (caderas)
        if len(landmarks) < 25 or any(
            not isfinite(landmarks[i].y)
            or not (0 <= landmarks[i].y <= 1)
            or (getattr(landmarks[i], 'visibility', 0) or 0) < MIN_CONF
            for i in (11, 12, 23, 24)
        ):
            self._vert_window.clear()
            self._vert_gesture = "RUN"
            self._vert_baseline = None
            self._vert_samples.clear()
            self._calib_since = None
            self._calib_progress = 0.0
            return "CALIBRATING"

        shoulder = (landmarks[11].y + landmarks[12].y) / 2
        hip      = (landmarks[23].y + landmarks[24].y) / 2

        # Calibración
        if self._vert_baseline is None:
            if self._calib_since is None:
                self._calib_since = now
            self._vert_samples.append((shoulder, hip))
            recent = self._vert_samples[-15:]
            # Reiniciar si hay mucho movimiento
            if len(recent) >= 5 and any(
                max(p[i] for p in recent) - min(p[i] for p in recent) > 0.04
                for i in (0, 1)
            ):
                self._vert_samples = [(shoulder, hip)]
                self._calib_since = now
            self._calib_progress = min(1.0, (now - self._calib_since) / CALIB_SECONDS)
            if self._calib_progress < 1.0 or len(self._vert_samples) < CALIB_MIN_FRAMES:
                return "CALIBRATING"
            self._vert_baseline = (
                sum(p[0] for p in self._vert_samples) / len(self._vert_samples),
                sum(p[1] for p in self._vert_samples) / len(self._vert_samples),
            )
            self._vert_samples.clear()
            print(f"[POSE] Calibración completada  baseline=({self._vert_baseline[0]:.3f}, {self._vert_baseline[1]:.3f})")

        # Ventana temporal
        self._vert_window.append((now, shoulder, hip))
        while self._vert_window and now - self._vert_window[0][0] > WINDOW_S:
            self._vert_window.popleft()
        if len(self._vert_window) < 3:
            return self._vert_gesture if self._vert_gesture != "RUN" else "RUN"

        s_med = median(p[1] for p in self._vert_window)
        h_med = median(p[2] for p in self._vert_window)
        base_s, base_h = self._vert_baseline
        scale = max(0.1, base_h - base_s)
        ds = (base_s - s_med) / scale   # >0 → subida (JUMP)
        dh = (base_h - h_med) / scale

        # Estado neutro
        neutral = max(abs(ds), abs(dh)) < min(JUMP_THRESH, CROUCH_THRESH) * RELEASE_RATIO
        if neutral:
            if self._vert_neutral_since is None:
                self._vert_neutral_since = now
            if now - self._vert_neutral_since >= NEUTRAL_S:
                self._vert_armed = True
        else:
            self._vert_neutral_since = None

        # Umbrales con histéresis
        j_lim = JUMP_THRESH   * (RELEASE_RATIO if self._vert_gesture == "JUMP"   else 1)
        c_lim = CROUCH_THRESH * (RELEASE_RATIO if self._vert_gesture == "CROUCH" else 1)

        if   ds > j_lim and dh > j_lim:
            candidate = "JUMP"
        elif ds < -c_lim and dh < -c_lim:
            candidate = "CROUCH"
        else:
            candidate = "RUN"

        if candidate != self._vert_candidate:
            self._vert_candidate = candidate
            self._vert_since = now

        if now - self._vert_since >= CONFIRM_S:
            if candidate == "RUN":
                self._vert_gesture = "RUN"
            elif candidate != self._vert_gesture:
                if self._vert_armed and now - self._vert_last_activation >= COOLDOWN_S:
                    self._vert_gesture = candidate
                    self._vert_last_activation = now
                    self._vert_armed = False

        return self._vert_gesture   # RUN / JUMP / CROUCH

    # ── Clasificador combinado ────────────────────────────────────────────

    def _classify(self, landmarks, center, now: float) -> str:
        """Devuelve el estado final del frame."""
        if not landmarks:
            return "NO_POSE"

        vert  = self._classify_vertical(landmarks, now)
        if vert == "CALIBRATING":
            return "CALIBRATING"
        if vert in ("JUMP", "CROUCH"):
            return vert

        # Solo lateral si el gesto vertical es RUN
        lateral = self._classify_lateral(center[0] if center else None)
        return lateral   # LEFT / CENTER / RIGHT

    # ── Dibujado en ventana de debug ──────────────────────────────────────

    def _draw_debug(self, frame, detector, landmarks, center, state: str):
        import cv2
        h, w = frame.shape[:2]

        # Franjas de zona
        dz = DEAD_ZONE
        x1 = int(w * (0.5 - dz))
        x2 = int(w * (0.5 + dz))
        tint = frame.copy()
        zone_colors = [
            ((40, 60, 200), 0, x1),
            ((40, 160, 60), x1, x2),
            ((200, 60, 40), x2, w),
        ]
        for col, xa, xb in zone_colors:
            cv2.rectangle(tint, (xa, 0), (xb - 1, h - 1), col, -1)
        cv2.addWeighted(tint, 0.18, frame, 0.82, 0, dst=frame)

        # Líneas divisorias
        for x in (x1, x2):
            cv2.line(frame, (x, 0), (x, h - 1), (240, 240, 240), 2)

        # Etiquetas de zona
        for txt, cx in (("IZQ", x1 // 2), ("CEN", (x1 + x2) // 2), ("DER", (x2 + w) // 2)):
            cv2.putText(frame, txt, (cx - 20, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 2, cv2.LINE_AA)

        # Esqueleto
        detector.draw_landmarks(frame, landmarks)

        # Centro del torso
        if center is not None:
            pt = (int(center[0] * w), int(center[1] * h))
            cv2.circle(frame, pt, max(10, w // 40), (0, 0, 0), 4)
            cv2.drawMarker(frame, pt, (0, 255, 255), cv2.MARKER_CROSS,
                           max(20, w // 25), 4)

        # Estado grande en pantalla
        state_colors = {
            "LEFT":        (40,  80, 220),
            "RIGHT":       (220, 60,  40),
            "CENTER":      (40, 200,  80),
            "JUMP":        (40, 210, 240),
            "CROUCH":      (200, 50, 200),
            "NO_POSE":     (80,  80,  80),
            "CALIBRATING": (200,200,  50),
        }
        col = state_colors.get(state, (200, 200, 200))

        # Barra de calibración
        if state == "CALIBRATING":
            bar_w = int(w * self._calib_progress)
            cv2.rectangle(frame, (0, h - 20), (bar_w, h), (50, 200, 230), -1)
            pct = int(self._calib_progress * 100)
            cv2.putText(frame, f"Calibrando {pct}%  — párate erguido y quieto",
                        (10, h - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 10, 10), 2, cv2.LINE_AA)

        # Estado principal (fondo negro + texto)
        label = state
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 1.2, 2)
        tx = (w - text_size[0]) // 2
        ty = h - 45
        cv2.rectangle(frame, (tx - 8, ty - text_size[1] - 8),
                      (tx + text_size[0] + 8, ty + 8), (0, 0, 0), -1)
        cv2.putText(frame, label, (tx, ty),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, col, 2, cv2.LINE_AA)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _set_state(self, new_state: str) -> None:
        with self._lock:
            old = self._state
            self._state = new_state
        if new_state != old:
            print(f"[POSE] Estado: {old} → {new_state}")
