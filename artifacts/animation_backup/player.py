"""
Player Entity – Huaca Kallpa (sprites Moche + sistema cosméticos)

Sustituye el octaedro/cubo por sprites PNG del personaje.
La lógica de carriles, salto y desliz NO se modifica.

COSMÉTICOS:
  La arquitectura está preparada. Los overlays PNG se superponen sobre el sprite
  base como un segundo quad parented al jugador.

  NOTA IMPORTANTE: los PNG de cosméticos actuales son ilustraciones de cuerpo
  completo con el personaje ya vestido, no overlays aislados.
  Para superposición correcta se necesitarían versiones con fondo transparente
  (RGBA) que muestren solo el accesorio sobre un área específica del cuerpo.
  Hasta que existan esas versiones adaptadas, apply_cosmetic() prepara la
  arquitectura y documenta el estado.

  Niveles de desbloqueo:
    0  → base (sin cosmético)
    2  → bracelets
    3  → necklace
    4  → belt_mantle
    5  → ceremonial_headpiece
    6  → ceremonial_full_set  (logro especial: completar recorrido)
"""

from ursina import *
import config

# ── Rutas de sprites por género y estado ─────────────────────────────────────
_SPRITES = {
    'female': {
        'base':   'assets/characters/female/female_base.png',
        'run':    'assets/characters/female/female_run.png',
        'jump':   'assets/characters/female/female_jump.png',
        'crouch': 'assets/characters/female/female_crouch.png',
        'flag':   'assets/characters/female/female_flag.png',
    },
    'male': {
        'base':   'assets/characters/male/male_base.png',
        'run':    'assets/characters/male/male_run.png',
        'jump':   'assets/characters/male/male_jump.png',
        'crouch': 'assets/characters/male/male_crouch.png',
        'flag':   'assets/characters/male/male_flag.png',
    },
}

# ── Rutas de cosméticos ───────────────────────────────────────────────────────
_COSMETICS = {
    2: 'assets/cosmetics/bracelets.png',
    3: 'assets/cosmetics/necklace.png',
    4: 'assets/cosmetics/belt_mantle.png',
    5: 'assets/cosmetics/ceremonial_headpiece.png',
    6: 'assets/cosmetics/ceremonial_full_set.png',
}

# Gender seleccionado (se establece en la pantalla de selección)
selected_gender: str = 'female'


class Player(Entity):
    """
    Jugador con sprites 2D en billboard (siempre mirando a la cámara).
    Lógica de carril/salto/desliz idéntica a la versión anterior.
    Incluye arquitectura de cosméticos lista para activar.
    """

    def __init__(self):
        sprites = _SPRITES.get(selected_gender, _SPRITES['female'])
        self._sprite_paths  = sprites
        self._current_anim  = 'run'

        super().__init__(
            model='quad',
            texture=sprites['run'],
            scale=(1.6, 2.2),          # ancho x alto del sprite
            position=(
                config.LANE_POSITIONS[config.PLAYER_START_LANE],
                config.PLAYER_START_Y + 0.6,
                config.PLAYER_START_Z,
            ),
            billboard=True,
            collider='box',
        )

        # ── Estado de carril (DISCRETO) ──────────────────────────────────────
        self.lane      = config.PLAYER_START_LANE
        self.target_x  = config.LANE_POSITIONS[self.lane]

        # ── Máquina de estados vertical ──────────────────────────────────────
        self.vertical_state = 'grounded'    # grounded | jumping | sliding
        self.jump_progress  = 0.0
        self.slide_timer    = 0.0

        # Escala base y desliz
        self.normal_scale_y = self.scale_y
        self.slide_scale_y  = self.scale_y * config.SLIDE_HEIGHT_SCALE

        # Alias para colisiones (mantiene compatibilidad con collision.py)
        self.z_position             = config.PLAYER_START_Z
        self.normal_scale_y_original = config.PLAYER_SIZE[1]

        # ── Arquitectura de cosméticos ────────────────────────────────────────
        # Nivel actual (0 = sin cosmético)
        self._cosmetic_level = 0
        # Entidad overlay (hijo del jugador, oculto por defecto)
        self._cosmetic_overlay = Entity(
            parent=self,
            model='quad',
            scale=(1.0, 1.0),
            position=(0, 0, -0.01),  # ligeramente delante del sprite base
            color=color.rgba(255, 255, 255, 0),   # invisible hasta activar
        )

        print(f"[PLAYER] Sprite '{selected_gender}' – carril {self.lane}")

    # ── Sprite helper ─────────────────────────────────────────────────────────
    def _set_anim(self, key: str):
        if self._current_anim == key:
            return
        self._current_anim = key
        path = self._sprite_paths.get(key, self._sprite_paths['run'])
        try:
            self.texture = load_texture(path)
        except Exception:
            pass

    # ── Cosméticos (arquitectura lista para versiones PNG adaptadas) ──────────
    def apply_cosmetic(self, level: int):
        """
        Aplica el cosmético del nivel indicado (0 = ninguno).

        ESTADO ACTUAL: los PNG de cosméticos son ilustraciones de cuerpo completo.
        Para superposición visual correcta se necesitarían archivos RGBA con el
        accesorio aislado sobre fondo transparente.
        Esta función prepara la entidad overlay y cargará el asset cuando esté listo.

        Args:
            level: 0-6 según COSMETIC_LEVELS
        """
        self._cosmetic_level = level
        path = _COSMETICS.get(level)

        if path is None or level == 0:
            # Sin cosmético: ocultar overlay
            self._cosmetic_overlay.color = color.rgba(255, 255, 255, 0)
            print(f"[PLAYER] Cosmético desactivado")
            return

        try:
            self._cosmetic_overlay.texture = load_texture(path)
            # NOTA: activar solo cuando se tengan versiones PNG RGBA adaptadas.
            # Por ahora mantenemos el overlay invisible para no romper el aspecto visual.
            # Descomentar la siguiente línea cuando los assets estén listos:
            # self._cosmetic_overlay.color = color.white
            self._cosmetic_overlay.color = color.rgba(255, 255, 255, 0)
            print(f"[PLAYER] Cosmético nivel {level} cargado (overlay en standby hasta assets RGBA)")
        except Exception as e:
            print(f"[PLAYER] Error cargando cosmético nivel {level}: {e}")

    def get_cosmetic_level(self) -> int:
        return self._cosmetic_level

    # ── Interfaz pública (sin cambios respecto a la versión anterior) ─────────
    def switch_lane(self, direction: int):
        new_lane = self.lane + direction
        if new_lane < 0 or new_lane >= config.LANE_COUNT:
            return
        self.lane     = new_lane
        self.target_x = config.LANE_POSITIONS[self.lane]
        print(f"[PLAYER] Carril {self.lane}")

    def jump(self):
        if self.vertical_state != 'grounded':
            return
        self.vertical_state = 'jumping'
        self.jump_progress  = 0.0
        self._set_anim('jump')
        print("[PLAYER] Salto")

    def slide(self):
        if self.vertical_state != 'grounded':
            return
        self.vertical_state = 'sliding'
        self.slide_timer    = config.SLIDE_DURATION
        self.scale_y        = self.slide_scale_y
        self.y              = config.PLAYER_START_Y + 0.6 * config.SLIDE_HEIGHT_SCALE
        self._set_anim('crouch')
        print("[PLAYER] Desliz")

    def stand_up(self):
        self.vertical_state = 'grounded'
        self.scale_y        = self.normal_scale_y
        self.y              = config.PLAYER_START_Y + 0.6
        self._set_anim('run')
        print("[PLAYER] De pie")

    def set_flag(self):
        """Mostrar sprite de bandera (final del recorrido)."""
        self._set_anim('flag')

    # ── Actualización por frame ───────────────────────────────────────────────
    def update(self):
        # 1. Movimiento horizontal (suavizado)
        self.x = lerp(self.x, self.target_x, time.dt * config.LANE_SWITCH_SPEED)

        # 2. Estado vertical
        if self.vertical_state == 'jumping':
            self._update_jump()
        elif self.vertical_state == 'sliding':
            self._update_slide()
        else:
            if self._current_anim not in ('run', 'flag'):
                self._set_anim('run')

    def _update_jump(self):
        self.jump_progress += time.dt / config.JUMP_DURATION
        if self.jump_progress >= 1.0:
            self.vertical_state = 'grounded'
            self.jump_progress  = 0.0
            self.y              = config.PLAYER_START_Y + 0.6
            self._set_anim('run')
            print("[PLAYER] Aterrizado")
            return
        t = self.jump_progress
        height = 4 * t * (1 - t) * config.JUMP_HEIGHT
        self.y = config.PLAYER_START_Y + 0.6 + height

    def _update_slide(self):
        self.slide_timer -= time.dt
        if self.slide_timer <= 0.0:
            self.stand_up()

    # ── Reset ─────────────────────────────────────────────────────────────────
    def reset(self):
        self.lane           = config.PLAYER_START_LANE
        self.target_x       = config.LANE_POSITIONS[self.lane]
        self.x              = self.target_x
        self.y              = config.PLAYER_START_Y + 0.6
        self.z              = config.PLAYER_START_Z
        self.vertical_state = 'grounded'
        self.jump_progress  = 0.0
        self.slide_timer    = 0.0
        self.scale_y        = self.normal_scale_y
        self.z_position     = config.PLAYER_START_Z
        self._set_anim('run')
        print("[PLAYER] Reset")
