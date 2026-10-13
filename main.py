"""
Huaca Kallpa – Runner Moche (v11 – PoseHUD integrado)
======================================================

Control principal: pose corporal (PoseThread).
  · La webcam se abre ANTES de Ursina.
  · Un hilo daemon captura frames y publica el estado de pose.
  · update() lee el estado y mueve al jugador.
  · PoseHUD gestiona TODA la UI de calibración/webcam — sin duplicados.

Controles:
  · ESC  = pausa / reanudar / salir
  · R    = reiniciar (solo en game_over / victory)
  · C    = mostrar/ocultar mini-cam webcam (durante partida)
  · ← / → o A / D = selección de personaje (solo en pantalla selección)
  · ENTER = confirmar selección de personaje
"""

from ursina import *
import os
import math
import sys
import time
import config

# Sistemas core (NO SE MODIFICAN)
from systems.camera import CameraController
from systems.spawner import ObstacleSpawner
from systems.collision import CollisionDetector
from systems.score import ScoreManager
from systems.difficulty import DifficultyManager
from systems.vfx import VFXManager

# Módulos visuales
from entities.track import Track
from entities.player import Player
import entities.player as player_module
from systems.ui import HUD, CharacterSelectScreen

# Control corporal (NO SE MODIFICA)
from vision.pose_thread import PoseThread

# PoseHUD — maneja TODO el overlay de webcam/calibración
from systems.pose_hud import PoseHUD
from systems.scene_visuals import scene_texture

# ══════════════════════════════════════════════════════════════════════════════
#  ADAPTADOR PoseThread → API compatible con PoseHUD (InputController-like)
#  Solo expone lo que PoseHUD necesita; no toca ninguna lógica de gameplay.
# ══════════════════════════════════════════════════════════════════════════════
class _PoseAdapter:
    """
    Envuelve PoseThread y expone la misma API de snapshot que InputController,
    para que PoseHUD funcione sin cambios.
    No toca MediaPipe, lógica de pose ni gameplay.
    """
    def __init__(self, pt: PoseThread):
        self._pt = pt
        # Estado de mini-cam (toggle con C)
        self._preview_enabled: bool = False
        # Caché del último frame BGR para construir preview_rgb
        self._last_frame = None

    # ── API que PoseHUD lee ──────────────────────────────────────────────────

    @property
    def snap_calibrating(self) -> bool:
        s = self._pt.get_state()
        return s == 'CALIBRATING'

    @property
    def snap_camera_error(self) -> bool:
        s = self._pt.get_state()
        return s in ('NO_CAMERA', 'NO_POSE') and self._pt.get_frame() is None

    @property
    def snap_error_msg(self) -> str:
        if self.snap_camera_error:
            return ("No se pudo abrir la webcam.\n"
                    "Comprueba que esté conectada y que ningún otro\n"
                    "programa la esté usando.")
        return ""

    @property
    def snap_calibration_progress(self) -> float:
        # PoseThread no expone progreso numérico; devolvemos 0.5 durante calib.
        # El HUD lo usa solo para la barra — al completarse calibrating=False.
        return 0.5 if self.snap_calibrating else 1.0

    @property
    def snap_landmarks_visible(self) -> bool:
        # Si está calibrando y hay frame disponible, asumimos landmarks visibles
        return self._pt.get_frame() is not None

    @property
    def snap_gesture(self) -> str:
        s = self._pt.get_state()
        return s if s in ('JUMP', 'CROUCH') else 'RUN'

    @property
    def snap_status(self) -> str:
        return self._pt.get_state()

    @property
    def snap_lane(self):
        s = self._pt.get_state()
        return {'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}.get(s)

    @property
    def preview_active(self) -> bool:
        """True cuando mini-cam está activa Y hay frame disponible."""
        return self._preview_enabled and (self._pt.get_frame() is not None)

    @property
    def snap_preview_rgb(self):
        """Bytes RGB del último frame, o None."""
        if not (self._preview_enabled or self.snap_calibrating):
            return None
        frame_bgr = self._pt.get_frame()
        if frame_bgr is None:
            return None
        try:
            import cv2
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            return rgb.tobytes()
        except Exception:
            return None

    @property
    def snap_preview_size(self) -> tuple:
        frame_bgr = self._pt.get_frame()
        if frame_bgr is None:
            return (0, 0)
        h, w = frame_bgr.shape[:2]
        return (w, h)

    # ── Controles ────────────────────────────────────────────────────────────

    def toggle_preview(self) -> None:
        self._preview_enabled = not self._preview_enabled

    def refresh(self) -> None:
        """Compatibilidad con API InputController — no hace nada extra aquí."""
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
game_state = 'character_select'
countdown_remaining = config.RUN_COUNTDOWN_SECONDS
countdown_text = None
_next_camera_restart = 0.0

player             = None
track              = None
camera_controller  = None
spawner            = None
collision_detector = None
score_manager      = None
hud                = None
difficulty_manager = None
vfx_manager        = None
pose_thread: 'PoseThread | None' = None
pose_adapter: '_PoseAdapter | None' = None
pose_hud: 'PoseHUD | None' = None
select_screen      = None

# Retención de carril cuando se pierde la pose
_last_lane: int = 1
_last_pose_state: str = 'CENTER'
_pose_lost_at: 'float | None' = None
LANE_HOLD_SECONDS = 1.5

# Distancia de victoria (en metros)
VICTORY_DISTANCE = 2000.0
_victory_triggered = False
_round_visuals = []


# ══════════════════════════════════════════════════════════════════════════════
#  INICIALIZACIÓN
# ══════════════════════════════════════════════════════════════════════════════
def init_game():
    """Create and return the configured Ursina application."""
    app = Ursina(development_mode=False, size=config.WINDOW_SIZE)
    window.title       = config.WINDOW_TITLE
    window.size        = config.WINDOW_SIZE
    window.color       = config.COLOR_BACKGROUND
    window.borderless  = config.WINDOW_BORDERLESS
    window.fullscreen  = config.WINDOW_FULLSCREEN
    window.size = config.WINDOW_SIZE
    window.exit_button.visible = False
    window.fps_counter.enabled = False
    if not config.WINDOW_FULLSCREEN:
        window.center_on_screen()
    return app


def init_entities():
    """Build systems with world updates owned by the playing loop; return None."""
    global player, track, camera_controller
    global difficulty_manager, spawner, collision_detector
    global score_manager, hud, vfx_manager
    global pose_hud, countdown_text

    if track is not None and not track.is_empty():
        reset_visual_scene()
        return

    track              = Track()
    player             = Player()
    player.enabled = False
    player.ignore = True
    track.ignore = True
    camera_controller  = CameraController(player)
    difficulty_manager = DifficultyManager()
    spawner            = ObstacleSpawner(difficulty_manager)
    collision_detector = CollisionDetector()
    score_manager      = ScoreManager()
    hud                = HUD()
    vfx_manager        = VFXManager()

    # PoseHUD gestiona TODA la UI de webcam/calibración
    # El panel de estado mini siempre visible — PoseHUD lo oculta cuando no hay cam
    pose_hud = PoseHUD()
    countdown_text = Text(
        parent=camera.ui, text='3', origin=(0, 0),
        position=config.UI_COUNTDOWN_POSITION, scale=config.UI_COUNTDOWN_SCALE,
        color=config.UI_GOLD, font=config.UI_FONT, z=-2, enabled=False,
    )

    Entity(parent=countdown_text, model='quad',
           scale=config.UI_COUNTDOWN_BACKING_SIZE, z=0.01, color=config.UI_INK)
    print('[INIT] Entidades creadas')


def init_character_select():
    """Open the existing character selection menu; return None."""
    global select_screen
    select_screen = CharacterSelectScreen(on_character_selected)


def on_character_selected(gender: str):
    """Prepare the selected runner and wait for real calibration; return None."""
    global game_state, select_screen, player, countdown_remaining
    reset_visual_scene()
    player_module.selected_gender = gender
    select_screen = None
    if player:
        player.enabled = False
        destroy(player)
    player = Player()
    player.enabled = False
    player.ignore = True
    camera_controller.player = player
    pose_hud.set_calibration_mode()
    if pose_adapter:
        pose_adapter._preview_enabled = True
    countdown_remaining = config.RUN_COUNTDOWN_SECONDS
    game_state = 'calibration'
    print(f'[JUEGO] Personaje elegido: {gender}; esperando calibracion')


def _pose_ready():
    """Return True only when a camera frame and a post-calibration state exist."""
    return bool(pose_thread and pose_thread.get_frame() is not None
                and pose_thread.get_state() in config.RUN_READY_STATES)


def _recover_camera():
    """Restart a stopped acquisition worker with fresh calibration; return None."""
    global pose_thread, pose_adapter, _next_camera_restart
    if pose_thread is None:
        return
    is_running = getattr(pose_thread, 'is_running', lambda: True)
    if is_running() or time.monotonic() < _next_camera_restart:
        return
    preview = pose_adapter._preview_enabled if pose_adapter else False
    pose_thread.stop()
    pose_thread = PoseThread()
    pose_adapter = _PoseAdapter(pose_thread)
    pose_adapter._preview_enabled = preview
    _next_camera_restart = time.monotonic() + config.CAMERA_RETRY_DELAY
    pose_thread.start()
    print('[CAMERA] Acquisition restarted; waiting for calibration.')


def _begin_playing():
    """Activate the runner and small preview after the countdown; return None."""
    global game_state, _last_lane, _last_pose_state, _pose_lost_at
    player.reset()
    player.enabled = True
    camera_controller.player = player
    _last_lane = player.lane
    _last_pose_state = 'CENTER'
    _pose_lost_at = None
    countdown_text.enabled = False
    pose_hud.set_gameplay_mode()
    game_state = 'playing'
    print('[JUEGO] Cuenta atras completa; carrera activa')


# ══════════════════════════════════════════════════════════════════════════════
#  GAME LOOP
# ══════════════════════════════════════════════════════════════════════════════
def update():
    """Advance startup states or exactly one playing frame; return None."""
    global game_state, countdown_remaining
    global _last_lane, _last_pose_state, _pose_lost_at, _victory_triggered

    _recover_camera()
    if game_state == 'playing' and pose_thread:
        if pose_thread.get_frame() is None or pose_thread.get_state() == 'CALIBRATING':
            game_state = 'calibration'
            player.enabled = False
            countdown_remaining = config.RUN_COUNTDOWN_SECONDS
            pose_hud.set_calibration_mode()
    if pose_hud and pose_adapter:
        pose_hud.update(pose_adapter)
    if track:
        track.fit_background()

    # ── Pantalla de selección ─────────────────────────────────────────────────
    if game_state == 'character_select':
        # Durante selección actualizar PoseHUD para mostrar calibración si aplica
        return

    if game_state in ('calibration', 'countdown'):
        hud.update(score_manager.score, score_manager.distance,
                   False, 0, game_state)
        if not _pose_ready():
            game_state = 'calibration'
            pose_hud.set_calibration_mode()
            countdown_remaining = config.RUN_COUNTDOWN_SECONDS
            countdown_text.enabled = False
            return
        if game_state == 'calibration':
            game_state = 'countdown'
            pose_hud.set_countdown_mode()
            countdown_remaining = config.RUN_COUNTDOWN_SECONDS
        countdown_text.enabled = True
        countdown_text.text = str(max(1, math.ceil(countdown_remaining)))
        countdown_remaining -= time.dt
        if countdown_remaining <= 0:
            _begin_playing()
        return

    # ── Pausa ─────────────────────────────────────────────────────────────────
    if game_state == 'paused':
        if hud and score_manager:
            hud.update(score_manager.score, score_manager.distance,
                       score_manager.shield_active, score_manager.shield_timer,
                       'paused', score_manager.orbs_collected, score_manager.high_score)
        return

    # ── Game Over ─────────────────────────────────────────────────────────────
    if game_state == 'game_over':
        if hud and score_manager:
            hud.update(score_manager.score, score_manager.distance,
                       score_manager.shield_active, score_manager.shield_timer,
                       'game_over', score_manager.orbs_collected, score_manager.high_score)
        return

    # ── Victoria ──────────────────────────────────────────────────────────────
    if game_state == 'victory':
        if hud and score_manager:
            hud.update(score_manager.score, score_manager.distance,
                       score_manager.shield_active, score_manager.shield_timer,
                       'victory', score_manager.orbs_collected, score_manager.high_score)
        if track:
            track.update(5.0)
        return

    if game_state != 'playing':
        return

    # ── Playing ───────────────────────────────────────────────────────────────

    # Pose (gameplay — NO SE MODIFICA)
    if pose_thread:
        pose_state = pose_thread.get_state()
        _dispatch_pose(pose_state)

    # PoseHUD — overlay de webcam/calibración/estado

    player.update()

    # Dificultad
    current_speed = config.INITIAL_SPEED
    if difficulty_manager and score_manager:
        current_speed, _ = difficulty_manager.update(score_manager.distance)

    # VFX
    if vfx_manager:
        vfx_manager.update()
        if camera_controller:
            camera_controller.shake_offset = vfx_manager.shake_offset

    # Sistemas
    camera_controller.update()
    track.update(current_speed)

    # Sincronizar distancia con track para transiciones de fondo
    if score_manager and track:
        track.set_distance(score_manager.distance)

    if spawner:
        spawner.update(current_speed)
        spawner.update_entities()

    if score_manager:
        score_manager.update(current_speed)

    # ── Comprobación de victoria ──────────────────────────────────────────────
    if score_manager and not _victory_triggered:
        if score_manager.distance >= VICTORY_DISTANCE:
            _trigger_victory()

    # ── Colisiones ────────────────────────────────────────────────────────────
    if collision_detector and player and spawner:
        collected_item = collision_detector.check_collectibles(player, spawner.obstacles)
        if collected_item:
            if collected_item.item_type == 'orb':
                score_manager.add_points(config.SCORE_ORB, is_orb=True)
                if vfx_manager:
                    vfx_manager.create_particles(collected_item.position, config.COLOR_ORB)
            elif collected_item.item_type == 'shield':
                score_manager.activate_shield()
                if vfx_manager:
                    vfx_manager.create_particles(collected_item.position, config.COLOR_SHIELD)
            spawner.retire(collected_item)

        collided, obstacle = collision_detector.check_collision(player, spawner.obstacles)
        if collided:
            if score_manager.shield_active:
                if vfx_manager:
                    vfx_manager.shake_camera(config.SHAKE_INTENSITY_SHIELD,
                                             config.SHAKE_DURATION_SHIELD)
                    vfx_manager.create_particles(obstacle.position, config.COLOR_SHIELD)
                spawner.retire(obstacle)
            else:
                if vfx_manager:
                    vfx_manager.shake_camera(config.SHAKE_INTENSITY_COLLISION,
                                             config.SHAKE_DURATION_COLLISION)
                game_state = 'game_over'
                print(f'[JUEGO] GAME OVER – Puntuación: {int(score_manager.score)}')

    # HUD
    if hud and score_manager:
        hud.update(score_manager.score, score_manager.distance,
                   score_manager.shield_active, score_manager.shield_timer,
                   game_state, score_manager.orbs_collected, score_manager.high_score)


def _trigger_victory():
    global game_state, _victory_triggered
    if _victory_triggered:
        return
    _victory_triggered = True
    game_state = 'victory'

    if spawner:
        spawner.reset()

    if player:
        player.set_flag()

    if track:
        track.force_final_bg()

    try:
        _round_visuals.append(Entity(
            model='quad',
            texture=scene_texture('assets/environment/pedestal_ceremonial.png'),
            scale=(3.0, 2.5),
            position=(0, 1.2, 10),
            billboard=False,
        ))
    except Exception:
        pass

    try:
        _round_visuals.append(Entity(
            model='quad',
            texture=scene_texture('assets/environment/bandera_final.png'),
            scale=(1.0, 2.0),
            position=(0, 2.0, 8),
            billboard=True,
        ))
    except Exception:
        pass

    if hud and score_manager:
        hud.show_victory(score_manager.score, score_manager.distance,
                         score_manager.orbs_collected)

    print(f'[JUEGO] VICTORIA – {int(score_manager.score)} puntos')


# ══════════════════════════════════════════════════════════════════════════════
#  DESPACHO DE POSE  (gameplay — NO SE MODIFICA)
# ══════════════════════════════════════════════════════════════════════════════
def _dispatch_pose(pose_state: str) -> None:
    global _last_lane, _last_pose_state, _pose_lost_at

    now = time.monotonic()

    if pose_state in ('NO_POSE', 'CALIBRATING', 'NO_CAMERA'):
        if _pose_lost_at is None:
            _pose_lost_at = now
        return
    else:
        _pose_lost_at = None

    if pose_state == 'JUMP':
        if player.vertical_state == 'grounded' and _last_pose_state != 'JUMP':
            player.jump()
            _last_pose_state = pose_state
        return

    if pose_state == 'CROUCH':
        if player.vertical_state == 'grounded':
            player.slide()
            _last_pose_state = pose_state
        elif player.vertical_state == 'sliding':
            # Hold the final crouch frame until the torso returns to neutral.
            player.slide_timer = max(player.slide_timer,
                                     time.dt * config.BODY_ACTION_SLIDE_HOLD_FRAMES)
            _last_pose_state = pose_state
        return

    if pose_state not in ('JUMP', 'CROUCH'):
        _last_pose_state = pose_state

    target_lane = {'LEFT': 0, 'CENTER': 1, 'RIGHT': 2}.get(pose_state, 1)
    if target_lane != _last_lane:
        delta = target_lane - player.lane
        if delta != 0:
            player.switch_lane(delta)
        _last_lane = target_lane


# ══════════════════════════════════════════════════════════════════════════════
#  TECLADO
# ══════════════════════════════════════════════════════════════════════════════
def input(key):
    """Route UI keys according to game_state; return None."""
    global game_state

    if key == 'c':
        if pose_adapter is not None:
            pose_adapter.toggle_preview()
        return

    # Pantalla de selección: delegar
    if game_state == 'character_select' and select_screen:
        select_screen.input(key)
        return

    # Pausa / reanudar / salir
    if key == 'escape':
        if game_state == 'playing':
            game_state = 'paused'
        elif game_state == 'paused':
            game_state = 'playing'
        elif game_state in ('game_over', 'victory'):
            _do_reset()
        else:
            _shutdown()
            quit()

    # Reiniciar
    if key == 'r' and game_state in ('game_over', 'victory'):
        _do_reset()


def reset_visual_scene():
    """Clear round-owned visuals and reuse existing Track/HUD trees; return None."""
    global _round_visuals
    retired, _round_visuals = _round_visuals, []
    for entity in retired:
        if not entity.is_empty():
            entity.enabled = False
            destroy(entity)
    if spawner:
        spawner.reset()
    if track:
        track.reset_visual_scene()
    if vfx_manager:
        vfx_manager.reset_visual_scene()
    if camera_controller:
        camera_controller.shake_offset = Vec3(0, 0, 0)
        camera_controller.current_tilt = camera_controller.target_tilt = 0.0
        camera.rotation_z = 0
    if countdown_text:
        countdown_text.enabled = False
    if hud and score_manager:
        hud.update(score_manager.score, score_manager.distance, False, 0, 'calibration')


def _do_reset():
    """Reset the run and return to the calibration/startup gate; return None."""
    global game_state, _last_lane, _last_pose_state, _pose_lost_at, _victory_triggered
    print('[JUEGO] Reiniciando...')
    reset_visual_scene()
    player.reset()
    score_manager.reset()
    difficulty_manager.reset()
    camera_controller.update()
    _last_lane        = 1
    _last_pose_state  = 'CENTER'
    _pose_lost_at     = None
    _victory_triggered = False
    player.enabled = False
    pose_hud.set_calibration_mode()
    game_state        = 'calibration'
    print('[JUEGO] Listo')


def _shutdown():
    if pose_thread:
        pose_thread.stop()
    if pose_hud:
        pose_hud.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    # Generar texturas si no existen
    required_textures = [
        'assets/track_texture.png',
        'assets/wall_texture.png',
        'assets/wood_texture.png',
        'assets/metal_texture.png',
        'assets/orb_texture.png',
    ]
    if any(not os.path.exists(t) for t in required_textures):
        print('[SETUP] Generando texturas base...')
        from utils.texture_gen import (
            ensure_assets_dir,
            generate_track_texture,
            generate_wall_texture,
            generate_wood_texture,
            generate_metal_texture,
            generate_orb_texture,
        )
        ensure_assets_dir()
        if not os.path.exists('assets/track_texture.png'): generate_track_texture()
        if not os.path.exists('assets/wall_texture.png'):  generate_wall_texture()
        if not os.path.exists('assets/wood_texture.png'):  generate_wood_texture()
        if not os.path.exists('assets/metal_texture.png'): generate_metal_texture()
        if not os.path.exists('assets/orb_texture.png'):   generate_orb_texture()

    # Arrancar webcam ANTES de Ursina (NO SE MODIFICA)
    print('[WEBCAM] Iniciando controlador de pose...', flush=True)
    pose_thread = PoseThread()
    pose_thread.start()

    # Adaptador para que PoseHUD pueda leer PoseThread sin cambiar PoseThread
    pose_adapter = _PoseAdapter(pose_thread)

    # Ursina
    app = init_game()
    init_entities()

    # Pantalla de selección de personaje
    init_character_select()

    print('[LISTO] Huaca Kallpa v11 – PoseHUD integrado')
    print('[LISTO] Pantalla de selección de personaje activa')
    print('[LISTO] A / D = elegir personaje  |  ENTER = iniciar')
    print('[LISTO] C = mini-cam  |  ESC = pausa/salir  |  R = reiniciar')

    app.run()

    _shutdown()
