"""
InputController v3 – Webcam-first.
======================================================

El juego se controla PRINCIPALMENTE por pose corporal.
El teclado solo gestiona Esc / C / K durante la partida.

Flujo de estados:
  calibrating → playing

Si la cámara falla, expone camera_error=True y error_msg para que
main.py muestre el mensaje en pantalla.
"""

from __future__ import annotations
import time

# ── Importación opcional de PoseController ────────────────────────────────────
_pose_available = False
try:
    from vision.pose_controller import PoseController, PoseState  # noqa: F401
    _pose_available = True
except ImportError as _e:
    print(f"[INPUT] MediaPipe no disponible: {_e}")
    print("[INPUT] El juego NO podrá controlarse por pose.")


class InputController:
    """
    Gestiona la pose corporal como fuente principal de entrada.

    Parámetros
    ----------
    camera_index : int
        Índice de la webcam.
    enabled : bool
        False → solo teclado (fallback de emergencia).
    """

    # Cuántos segundos mantener el carril cuando se pierde la pose
    _LANE_HOLD_SECONDS = 1.5

    def __init__(self, camera_index: int = 0, enabled: bool = True):
        self.enabled: bool = enabled and _pose_available

        # ── Estado interno ────────────────────────────────────────────────
        self._last_valid_lane: int | None = None
        self._lane_lost_at: float | None = None
        self._last_gesture: str = "RUN"
        self._preview_enabled: bool = False   # toggle mini-cam

        # ── Snapshot público (leído por PoseHUD y main) ───────────────────
        self.snap_lane: int | None = None
        self.snap_gesture: str = "RUN"
        self.snap_status: str = "Sin cámara"
        self.snap_calibration_progress: float = 0.0
        self.snap_calibrated: bool = False
        self.snap_preview_rgb: bytes | None = None
        self.snap_preview_size: tuple[int, int] = (0, 0)
        self.snap_calibrating: bool = True
        self.snap_camera_error: bool = False
        self.snap_error_msg: str = ""
        self.snap_landmarks_visible: bool = False

        # ── Arrancar PoseController ───────────────────────────────────────
        if self.enabled:
            self._ctrl = PoseController(camera_index=camera_index)
            self._ctrl.start()
            print("[INPUT] PoseController iniciado – webcam activa en hilo daemon.")
        else:
            self._ctrl = None
            if not _pose_available:
                self.snap_status = "MediaPipe no instalado"
                self.snap_error_msg = (
                    "MediaPipe no está instalado.\n"
                    "Ejecuta:  pip install mediapipe opencv-python\n"
                    "y reinicia el juego."
                )
            else:
                self.snap_status = "Pose desactivada"
                self.snap_error_msg = "Pose desactivada en config.py (POSE_ENABLED=False)."
            self.snap_camera_error = True
            self.snap_calibrating = False   # no hay calibración que esperar
            print(f"[INPUT] {self.snap_status} – solo teclado.")

    # ── Propiedades de conveniencia ───────────────────────────────────────

    @property
    def is_calibrating(self) -> bool:
        """True mientras el sistema de pose aún no tiene baseline."""
        return self.snap_calibrating

    @property
    def camera_error(self) -> bool:
        return self.snap_camera_error

    @property
    def error_msg(self) -> str:
        return self.snap_error_msg

    @property
    def preview_active(self) -> bool:
        """True cuando la mini-cam está activada Y hay datos disponibles."""
        return self._preview_enabled and self.snap_preview_rgb is not None

    # ── Controles ─────────────────────────────────────────────────────────

    def toggle_preview(self) -> None:
        """Activa/desactiva la mini-ventana de webcam durante la partida."""
        self._preview_enabled = not self._preview_enabled
        if self._ctrl is not None:
            self._ctrl.enable_preview(self._preview_enabled)
        state = "activada" if self._preview_enabled else "desactivada"
        print(f"[INPUT] Mini-webcam {state}.")

    def recalibrate(self) -> None:
        """Reinicia la calibración de gestos verticales."""
        if self._ctrl is not None:
            self._ctrl.recalibrate()
            self.snap_calibrated = False
            self.snap_calibration_progress = 0.0
            self.snap_calibrating = True
            print("[INPUT] Recalibración iniciada.")

    # ── Poll (llamado cada frame durante 'playing') ───────────────────────

    def poll(self, player) -> None:
        """
        Lee el snapshot de pose y despacha comandos al jugador.
        Llamar UNA VEZ por frame en update() solo cuando game_state == 'playing'.

        Args
        ----
        player : Player
            Instancia con métodos switch_lane(delta), jump(), slide().
        """
        if not self.enabled or self._ctrl is None:
            return

        self._refresh_snapshot()

        # Si aún calibrando o hay error de cámara, no enviar comandos al jugador
        if self.snap_calibrating or self.snap_camera_error:
            return

        now = time.monotonic()

        # ── Carril lateral ─────────────────────────────────────────────────
        if self.snap_lane is not None:
            self._lane_lost_at = None
            if self.snap_lane != self._last_valid_lane:
                self._last_valid_lane = self.snap_lane
                delta = self.snap_lane - player.lane
                if delta != 0:
                    player.switch_lane(delta)
        else:
            # Pose perdida: mantener carril durante _LANE_HOLD_SECONDS
            if self._last_valid_lane is not None:
                if self._lane_lost_at is None:
                    self._lane_lost_at = now
                elif now - self._lane_lost_at > self._LANE_HOLD_SECONDS:
                    self._last_valid_lane = None
                    self._lane_lost_at = None

        # ── Gestos verticales (flanco ascendente) ──────────────────────────
        gesture = self.snap_gesture
        if gesture == "JUMP" and self._last_gesture != "JUMP":
            player.jump()
        elif gesture == "CROUCH" and self._last_gesture != "CROUCH":
            player.slide()
        self._last_gesture = gesture

    # ── Refresh snapshot (también llamado desde PoseHUD durante calibración) ─

    def refresh(self) -> None:
        """Actualiza el snapshot sin enviar comandos al jugador."""
        if self.enabled and self._ctrl is not None:
            self._refresh_snapshot()

    def _refresh_snapshot(self) -> None:
        state = self._ctrl.snapshot()
        self.snap_status              = state.status
        self.snap_lane                = state.lane
        self.snap_gesture             = state.gesture
        self.snap_calibrated          = state.calibrated
        self.snap_calibration_progress = state.calibration_progress
        self.snap_preview_rgb         = state.preview_rgb
        self.snap_preview_size        = state.preview_size
        self.snap_calibrating         = state.calibrating
        self.snap_camera_error        = state.camera_error
        self.snap_error_msg           = state.error_msg
        self.snap_landmarks_visible   = state.landmarks_visible

    def close(self) -> None:
        """Libera la cámara y el hilo de captura."""
        if self._ctrl is not None:
            self._ctrl.close()
            print("[INPUT] PoseController cerrado.")
