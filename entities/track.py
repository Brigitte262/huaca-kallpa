"""
Track Entity – Huaca Kallpa (pista + escenario Moche)

Mantiene la lógica de scroll de pista original.
Añade:
  - Una superficie de fondo con los 4 fondos del recorrido
  - Transiciones suaves entre fondos (crossfade)
  - Camino visible proporcionado exclusivamente por los fondos Moche
  - Antorchas laterales en zonas ceremoniales (con scroll correcto)
"""

from ursina import *
from math import tan, radians
import config
from systems.scene_visuals import scene_texture, background_shader

# Secuencia de fondos en orden de recorrido
_BG_SEQUENCE = [
    'assets/backgrounds/camino_del_valle.png',
    'assets/backgrounds/acceso_ceremonial.png',
    'assets/backgrounds/zona_huaca_templo_final.png',
    'assets/backgrounds/escena_final_meta_ceremonial.png',
]

# Distancias (metros) a las que se inicia cada transición
_BG_THRESHOLDS = [0, 300, 700, 1200]

# Duración de la transición de crossfade en segundos
_FADE_DURATION = config.SCENE_FADE_DURATION

# Intervalo (en metros) entre apariciones de antorchas
_TORCH_INTERVAL = config.SCENE_TORCH_INTERVAL   # más espaciadas para no saturar

# Distancia máxima a la que existen antorchas antes de destruirse
_TORCH_DESPAWN_Z = config.SCENE_TORCH_DESPAWN_Z


class Track(Entity):
    """
    Pista invisible con un único escenario progresivo.

    NOTA: la distancia acumulada la gestiona ScoreManager; Track la recibe
    mediante set_distance() para calcular transiciones de fondo.
    No incrementa _total_distance internamente (evita doble conteo).
    """

    def __init__(self):
        """Create the reusable background and empty scenery collections."""
        # ── Plano de pista ────────────────────────────────────────────────────
        super().__init__(
            model=None,
            texture=None,
            texture_scale=(2, 20),
            color=config.COLOR_TRACK,
            scale=(config.TRACK_WIDTH, 1, config.TRACK_LENGTH),
            position=(0, 0, config.TRACK_LENGTH / 2),
            collider=None,
        )

        grid_lines = int(config.TRACK_LENGTH / config.GRID_SPACING)
        self.texture_scale = (1, grid_lines)
        self.scroll_offset = 0.0

        self._background_textures = tuple(scene_texture(path) for path in _BG_SEQUENCE)
        self._bg_current = Entity(
            name='moche_background', model='quad', parent=camera,
            texture=self._background_textures[0], shader=background_shader,
            scale=(1, 1), position=(0, 0, config.WORLD_BACKGROUND_DEPTH),
            color=color.white, collider=None,
        )
        self._bg_current.set_shader_input('next_texture', self._background_textures[0])
        self._bg_next = None  # No second quad exists, even during crossfades.

        # ── Estado del escenario ──────────────────────────────────────────────
        self._bg_index       = 0      # fondo actual en _BG_SEQUENCE
        self._fading         = False
        self._fade_t         = 0.0
        self._total_distance = 0.0   # actualizado SOLO por set_distance()
        self._next_idx       = 0

        # Offset de parallax acumulado
        self._parallax_offset = 0.0

        # Líneas de cuadrícula
        self.grid_lines = []
        # The Moche background supplies the visible path; lanes remain mathematical.

        # Antorchas: lista de entidades activas
        self._torches        = []
        # Acumulador de distancia para disparar nuevas antorchas
        self._dist_since_torch = 0.0

        self.fit_background()
        print("[TRACK] Escenario Moche inicializado")

    def fit_background(self):
        """Fit the backdrop behind 3D geometry without a foreground UI quad; return None."""
        horizontal, vertical = camera.lens.get_fov()
        depth = config.WORLD_BACKGROUND_DEPTH
        width = 2 * depth * tan(radians(horizontal) / 2)
        height = 2 * depth * tan(radians(vertical) / 2)
        size = (width * config.WORLD_BACKGROUND_MARGIN,
                height * config.WORLD_BACKGROUND_MARGIN)
        self._bg_current.scale = size


    # ── Actualización ─────────────────────────────────────────────────────────
    def update(self, speed=None):
        """Scroll scenery at the supplied speed and retire passed torches; return None."""
        current_speed = speed if speed is not None else config.TRACK_SCROLL_SPEED
        dt = time.dt

        # Scroll de textura
        scroll_speed = current_speed * config.GRID_ANIMATION_SPEED
        self.scroll_offset += dt * scroll_speed
        self.texture_offset = (0, self.scroll_offset)

        # Cuadrícula – scroll
        for line in self.grid_lines:
            line.z -= current_speed * dt
            if line.z < -config.GRID_SPACING:
                line.z += config.TRACK_LENGTH

        # The full image stays intact: wrapped UV offsets split the road at the edge.
        self._bg_current.texture_offset = (0, 0)

        # Transición de fondos (usa _total_distance seteado externamente)
        self._update_background()

        # ── Antorchas ─────────────────────────────────────────────────────────
        # Acumular distancia recorrida en este frame
        self._dist_since_torch += current_speed * dt

        # Spawnear par de antorchas cada _TORCH_INTERVAL metros, solo en zonas ceremoniales
        if self._dist_since_torch >= _TORCH_INTERVAL and self._bg_index >= 1:
            self._dist_since_torch = 0.0
            self._spawn_torches()

        # Mover antorchas hacia el jugador y limpiar las que pasaron
        surviving = []
        for t in self._torches:
            if t.is_empty() or not t.enabled:
                continue
            t.z -= current_speed * dt
            if t.z < _TORCH_DESPAWN_Z:
                destroy(t)
            else:
                surviving.append(t)
        self._torches = surviving

    def _update_background(self):
        """Blend cached textures on the sole background surface; return None."""
        if not self._fading and self._bg_index < len(_BG_THRESHOLDS) - 1:
            next_idx = self._bg_index + 1
            if self._total_distance >= _BG_THRESHOLDS[next_idx]:
                self._bg_current.set_shader_input('next_texture',
                                                  self._background_textures[next_idx])
                self._fading = True
                self._fade_t = 0.0
                self._next_idx = next_idx
        if self._fading:
            self._fade_t = min(1.0, self._fade_t + time.dt / _FADE_DURATION)
            self._bg_current.set_shader_input('blend_amount', self._fade_t)
            if self._fade_t >= 1.0:
                self._bg_current.texture = self._background_textures[self._next_idx]
                self._bg_current.set_shader_input('blend_amount', 0.0)
                self._bg_index = self._next_idx
                self._fading = False

    def reset_visual_scene(self):
        """Reuse the sole background and retire all previous-round scenery; return None."""
        retired = self._torches + self.grid_lines
        self._torches = []
        self.grid_lines = []
        for entity in retired:
            if not entity.is_empty():
                entity.enabled = False
                destroy(entity)
        self.scroll_offset = 0.0
        self.texture_offset = (0, 0)
        self._bg_index = self._next_idx = 0
        self._fading = False
        self._fade_t = self._total_distance = self._parallax_offset = 0.0
        self._dist_since_torch = 0.0
        self._bg_current.texture = self._background_textures[0]
        self._bg_current.texture_offset = (0, 0)
        self._bg_current.color = color.white
        self._bg_current.set_shader_input('next_texture', self._background_textures[0])
        self._bg_current.set_shader_input('blend_amount', 0.0)
        self._bg_current.enabled = True
        self.fit_background()

    def on_destroy(self):
        """Destroy independently parented scenery with its Track owner; return None."""
        for entity in [self._bg_current] + self._torches + self.grid_lines:
            if not entity.is_empty():
                destroy(entity)
        self._torches = []
        self.grid_lines = []

    def _spawn_torches(self):
        """Genera par de antorchas laterales decorativas que se mueven con la pista."""
        z_spawn = config.OBSTACLE_SPAWN_DISTANCE * 0.80
        for side in (-1, 1):
            try:
                t = Entity(
                    model='quad',
                    texture=scene_texture('assets/environment/antorcha_lateral.png'),
                    scale=(0.9, 1.8),
                    position=(side * (config.TRACK_WIDTH / 2 + 0.7), 1.2, z_spawn),
                    billboard=False,
                )
                self._torches.append(t)
            except Exception:
                pass

    # ── API para escena final ─────────────────────────────────────────────────
    def force_final_bg(self):
        """Show the cached final image without a lingering transition; return None."""
        self._bg_current.texture = self._background_textures[-1]
        self._bg_current.set_shader_input('next_texture', self._background_textures[-1])
        self._bg_current.set_shader_input('blend_amount', 0.0)
        self._fading = False
        self._fade_t = 0.0
        self._bg_index = self._next_idx = len(_BG_SEQUENCE) - 1

    def set_distance(self, dist: float):
        """
        Recibe la distancia acumulada de ScoreManager.
        Track no la calcula internamente para evitar doble conteo.
        """
        self._total_distance = dist
