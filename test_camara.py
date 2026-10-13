"""
test_camara.py – Diagnóstico completo de cámara + pose para Huaca Kallpa
========================================================================

Ejecutar desde la carpeta del proyecto:
    python test_camara.py

Qué hace:
  1. Busca cámaras disponibles en índices 0-3 con backends Windows
     (CAP_DSHOW, CAP_MSMF, CAP_ANY).
  2. Muestra cuáles funcionan con resolución y FPS.
  3. Abre la primera cámara funcional.
  4. Muestra video en espejo con MediaPipe.
  5. Detecta pose y muestra estado en pantalla:
     LEFT / CENTER / RIGHT / JUMP / CROUCH / CALIBRATING / NO_POSE.
  6. Imprime cada cambio de estado en consola.
  7. Pulsa Q o ESC para salir.

Criterio de éxito: el LED de la cámara se enciende y aparece el esqueleto.
"""

import sys
import time
from math import isfinite
from collections import deque
from statistics import median

# ── Constantes de clasificación (igual que pose_thread.py) ───────────────────
DEAD_ZONE     = 0.12
HYSTERESIS    = 0.03
JUMP_THRESH   = 0.08
CROUCH_THRESH = 0.10
RELEASE_RATIO = 0.50
COOLDOWN_S    = 0.80
CONFIRM_S     = 0.06
NEUTRAL_S     = 0.12
CALIB_SECONDS = 2.5
CALIB_MIN_FRAMES = 10
WINDOW_FRAMES = 5
WINDOW_S      = 0.22
MIN_CONF      = 0.50

# ── Backends ──────────────────────────────────────────────────────────────────
_BACKENDS = ["CAP_DSHOW", "CAP_MSMF", "CAP_ANY"]


def scan_cameras(cv2):
    """Escanea índices 0-3 con todos los backends. Devuelve lista de resultados."""
    print("=" * 64)
    print("  DIAGNÓSTICO DE CÁMARAS – Huaca Kallpa")
    print("=" * 64)

    backends = [(getattr(cv2, n, None), n) for n in _BACKENDS]
    backends = [(v, n) for v, n in backends if v is not None]

    found = []
    for idx in range(4):
        for backend_val, backend_name in backends:
            try:
                cam = cv2.VideoCapture(idx, backend_val)
            except Exception:
                print(f"  ✗  índice={idx}  backend={backend_name}  – excepción al abrir")
                continue

            if not cam.isOpened():
                print(f"  ✗  índice={idx}  backend={backend_name}  – no se pudo abrir")
                cam.release()
                continue

            ok, frame = cam.read()
            if ok and frame is not None and frame.size > 0:
                w = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cam.get(cv2.CAP_PROP_FPS) or 0
                print(f"  ✓  índice={idx}  backend={backend_name}  {w}x{h}  {fps:.0f}fps")
                found.append((idx, backend_val, backend_name, w, h))
            else:
                print(f"  ✗  índice={idx}  backend={backend_name}  – sin señal")
            cam.release()

    return found


# ── Clasificador de pose simplificado ─────────────────────────────────────────

class SimplePoseClassifier:
    def __init__(self):
        self.lat = "CENTER"
        self.vert_baseline = None
        self.vert_samples = []
        self.calib_since = None
        self.calib_progress = 0.0
        self.vert_window = deque(maxlen=WINDOW_FRAMES)
        self.vert_gesture = "RUN"
        self.vert_candidate = "RUN"
        self.vert_since = 0.0
        self.vert_last_activation = float('-inf')
        self.vert_armed = True
        self.vert_neutral_since = None

    def classify(self, landmarks, center, now: float) -> str:
        if not landmarks:
            return "NO_POSE"
        vert = self._vertical(landmarks, now)
        if vert == "CALIBRATING":
            return "CALIBRATING"
        if vert in ("JUMP", "CROUCH"):
            return vert
        return self._lateral(center[0] if center else None)

    def _lateral(self, cx):
        if cx is None or not isfinite(cx):
            return "CENTER"
        lb = 0.5 - DEAD_ZONE
        rb = 0.5 + DEAD_ZONE
        prev = self.lat
        if cx < lb:
            self.lat = "LEFT"
        elif cx > rb:
            self.lat = "RIGHT"
        elif prev == "LEFT"  and cx < lb + HYSTERESIS:
            pass
        elif prev == "RIGHT" and cx > rb - HYSTERESIS:
            pass
        else:
            self.lat = "CENTER"
        return self.lat

    def _vertical(self, landmarks, now: float) -> str:
        if len(landmarks) < 25 or any(
            not isfinite(landmarks[i].y)
            or not (0 <= landmarks[i].y <= 1)
            or (getattr(landmarks[i], 'visibility', 0) or 0) < MIN_CONF
            for i in (11, 12, 23, 24)
        ):
            self.vert_window.clear(); self.vert_gesture = "RUN"
            self.vert_baseline = None; self.vert_samples.clear()
            self.calib_since = None;  self.calib_progress = 0.0
            return "CALIBRATING"

        sh = (landmarks[11].y + landmarks[12].y) / 2
        hp = (landmarks[23].y + landmarks[24].y) / 2

        if self.vert_baseline is None:
            if self.calib_since is None:
                self.calib_since = now
            self.vert_samples.append((sh, hp))
            recent = self.vert_samples[-15:]
            if len(recent) >= 5 and any(
                max(p[i] for p in recent) - min(p[i] for p in recent) > 0.04
                for i in (0, 1)
            ):
                self.vert_samples = [(sh, hp)]; self.calib_since = now
            self.calib_progress = min(1.0, (now - self.calib_since) / CALIB_SECONDS)
            if self.calib_progress < 1.0 or len(self.vert_samples) < CALIB_MIN_FRAMES:
                return "CALIBRATING"
            self.vert_baseline = (
                sum(p[0] for p in self.vert_samples) / len(self.vert_samples),
                sum(p[1] for p in self.vert_samples) / len(self.vert_samples),
            )
            self.vert_samples.clear()
            print(f"[POSE] Calibración completada  "
                  f"baseline=({self.vert_baseline[0]:.3f}, {self.vert_baseline[1]:.3f})",
                  flush=True)

        self.vert_window.append((now, sh, hp))
        while self.vert_window and now - self.vert_window[0][0] > WINDOW_S:
            self.vert_window.popleft()
        if len(self.vert_window) < 3:
            return self.vert_gesture if self.vert_gesture != "RUN" else "RUN"

        s_m = median(p[1] for p in self.vert_window)
        h_m = median(p[2] for p in self.vert_window)
        bs, bh = self.vert_baseline
        sc = max(0.1, bh - bs)
        ds = (bs - s_m) / sc
        dh = (bh - h_m) / sc

        neutral = max(abs(ds), abs(dh)) < min(JUMP_THRESH, CROUCH_THRESH) * RELEASE_RATIO
        if neutral:
            if self.vert_neutral_since is None: self.vert_neutral_since = now
            if now - self.vert_neutral_since >= NEUTRAL_S: self.vert_armed = True
        else:
            self.vert_neutral_since = None

        jl = JUMP_THRESH   * (RELEASE_RATIO if self.vert_gesture == "JUMP"   else 1.0)
        cl = CROUCH_THRESH * (RELEASE_RATIO if self.vert_gesture == "CROUCH" else 1.0)

        if   ds > jl  and dh > jl:  cand = "JUMP"
        elif ds < -cl and dh < -cl: cand = "CROUCH"
        else:                        cand = "RUN"

        if cand != self.vert_candidate:
            self.vert_candidate = cand; self.vert_since = now

        if now - self.vert_since >= CONFIRM_S:
            if cand == "RUN":
                self.vert_gesture = "RUN"
            elif cand != self.vert_gesture:
                if self.vert_armed and now - self.vert_last_activation >= COOLDOWN_S:
                    self.vert_gesture = cand
                    self.vert_last_activation = now
                    self.vert_armed = False

        return self.vert_gesture


# ── Función principal ─────────────────────────────────────────────────────────

def main():
    try:
        import cv2
    except ImportError:
        print("ERROR: OpenCV no instalado. Ejecuta:  pip install opencv-python")
        sys.exit(1)

    try:
        import mediapipe  # noqa: F401
    except ImportError:
        print("ERROR: MediaPipe no instalado. Ejecuta:  pip install mediapipe")
        sys.exit(1)

    # ── Escanear cámaras ──────────────────────────────────────────────────
    found = scan_cameras(cv2)
    print()
    if not found:
        print("⛔  No se encontró ninguna cámara funcional.")
        print("    Verifica: Configuración → Privacidad → Cámara → activar acceso")
        sys.exit(1)

    best = found[0]
    idx, backend_val, backend_name, bw, bh = best
    print(f"✅  Usando:  índice={idx}  backend={backend_name}  {bw}x{bh}")
    print()
    print("Iniciando prueba de pose (Q o ESC para salir)...")
    print()

    # ── Abrir cámara ──────────────────────────────────────────────────────
    cap = cv2.VideoCapture(idx, backend_val)
    if not cap.isOpened():
        print("ERROR: No se pudo abrir la cámara seleccionada.")
        sys.exit(1)

    # ── Inicializar detector de pose ──────────────────────────────────────
    try:
        import sys as _sys
        _sys.path.insert(0, '.')
        from vision.pose_detector import PoseDetector
    except ImportError as e:
        print(f"ERROR: No se pudo importar PoseDetector: {e}")
        print("Asegúrate de ejecutar desde la carpeta huaca_kallpa_v2/")
        cap.release()
        sys.exit(1)

    classifier = SimplePoseClassifier()
    last_state = ""

    WINDOW = "Test Cámara – Huaca Kallpa (Q o ESC para salir)"

    with PoseDetector() as detector:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("ERROR: sin señal de cámara")
                break

            frame = cv2.flip(frame, 1)   # espejo
            now = time.monotonic()
            h, w = frame.shape[:2]

            # ── Detectar pose ─────────────────────────────────────────────
            landmarks = detector.detect(frame)
            center    = detector.torso_center(landmarks)
            state     = classifier.classify(landmarks, center, now)

            # Imprimir cada cambio
            if state != last_state:
                print(f"[POSE] {state}", flush=True)
                last_state = state

            # ── Dibujar zonas ─────────────────────────────────────────────
            x1 = int(w * (0.5 - DEAD_ZONE))
            x2 = int(w * (0.5 + DEAD_ZONE))
            tint = frame.copy()
            cv2.rectangle(tint, (0,  0), (x1 - 1, h - 1), (40,  60, 200), -1)
            cv2.rectangle(tint, (x1, 0), (x2 - 1, h - 1), (40, 160,  60), -1)
            cv2.rectangle(tint, (x2, 0), (w - 1,  h - 1), (200, 60,  40), -1)
            cv2.addWeighted(tint, 0.18, frame, 0.82, 0, dst=frame)
            cv2.line(frame, (x1, 0), (x1, h - 1), (240, 240, 240), 2)
            cv2.line(frame, (x2, 0), (x2, h - 1), (240, 240, 240), 2)
            for txt, cx in (("IZQ", x1 // 2), ("CEN", (x1 + x2) // 2), ("DER", (x2 + w) // 2)):
                cv2.putText(frame, txt, (cx - 20, 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 2, cv2.LINE_AA)

            # ── Esqueleto + centro ────────────────────────────────────────
            detector.draw_landmarks(frame, landmarks)
            if center is not None:
                pt = (int(center[0] * w), int(center[1] * h))
                cv2.circle(frame, pt, max(10, w // 40), (0, 0, 0), 4)
                cv2.drawMarker(frame, pt, (0, 255, 255), cv2.MARKER_CROSS,
                               max(20, w // 25), 4)

            # ── Barra de calibración ──────────────────────────────────────
            if state == "CALIBRATING":
                bar_w = int(w * classifier.calib_progress)
                cv2.rectangle(frame, (0, h - 24), (bar_w, h), (50, 200, 230), -1)
                pct = int(classifier.calib_progress * 100)
                cv2.putText(frame, f"Calibrando {pct}%  — párate erguido y quieto",
                            (10, h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (10, 10, 10), 2, cv2.LINE_AA)

            # ── Estado grande ─────────────────────────────────────────────
            colors = {
                "LEFT": (40, 80, 220), "RIGHT": (220, 60, 40),
                "CENTER": (40, 200, 80), "JUMP": (40, 210, 240),
                "CROUCH": (200, 50, 200), "NO_POSE": (80, 80, 80),
                "CALIBRATING": (200, 200, 50),
            }
            col = colors.get(state, (200, 200, 200))
            ts, _ = cv2.getTextSize(state, cv2.FONT_HERSHEY_DUPLEX, 1.4, 2)
            tx = (w - ts[0]) // 2
            ty = h - 50
            cv2.rectangle(frame, (tx - 8, ty - ts[1] - 8), (tx + ts[0] + 8, ty + 8),
                          (0, 0, 0), -1)
            cv2.putText(frame, state, (tx, ty),
                        cv2.FONT_HERSHEY_DUPLEX, 1.4, col, 2, cv2.LINE_AA)

            # ── Info de cámara (esquina superior izquierda) ───────────────
            info = f"idx={idx}  {backend_name}  {bw}x{bh}"
            cv2.putText(frame, info, (10, h - 34),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)

            cv2.imshow(WINDOW, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q'), 27):   # Q o ESC
                break

    cap.release()
    cv2.destroyAllWindows()
    print()
    print("Diagnóstico finalizado.")
    print(f"Cámara que funcionó:  índice={idx}  backend={backend_name}  {bw}x{bh}")


if __name__ == '__main__':
    main()
