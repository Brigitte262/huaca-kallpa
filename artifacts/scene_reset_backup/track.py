"""
Track Entity – Huaca Kallpa (pista + escenario Moche)

Mantiene la lógica de scroll de pista original.
Añade:
  - Fondo parallax con los 4 fondos del recorrido
  - Transiciones suaves entre fondos (crossfade)
  - Camino visible proporcionado exclusivamente por los fondos Moche
  - Antorchas laterales en zonas ceremoniales (con scroll correcto)
"""

from ursina import *
from math import tan, radians
import config

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
_FADE_DURATION = 3.0

# Velocidad de parallax del fondo (fracción de la velocidad de pista)
_PARALLAX_FACTOR = 0.18

# Intervalo (en metros) entre apariciones de antorchas
_TORCH_INTERVAL = 200.0   # más espaciadas para no saturar

# Distancia máxima a la que existen antorchas antes de destruirse
_TORCH_DESPAWN_Z = -15.0


class Track(Entity):
    """
    Pista con escenario progresivo y parallax.

    NOTA: la distancia acumulada la gestiona ScoreManager; Track la recibe
    mediante set_distance() para calcular transiciones de fondo.
    No incrementa _total_distance internamente (evita doble conteo).
    """

    def __init__(self):
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

        # ── Cielo / fondos ────────────────────────────────────────────────────
        # Fondo actual (visible)
        self._bg_current = Entity(
            model='quad',
            parent=camera,
            texture=_BG_SEQUENCE[0],
            scale=(1, 1),
            position=(0, 0, config.WORLD_BACKGROUND_DEPTH),
            color=color.white,
        )

        # Fondo siguiente (para crossfade)
        self._bg_next = Entity(
            model='quad',
            parent=camera,
            texture=_BG_SEQUENCE[0],
            scale=(1, 1),
            position=(0, 0, config.WORLD_BACKGROUND_DEPTH - 0.01),
            color=color.rgba32(255, 255, 255, 0),
        )

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
        self._bg_next.scale = size

    # ── Actualización ─────────────────────────────────────────────────────────
    def update(self, speed=None):
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

        # Parallax del fondo
        self._parallax_offset += current_speed * _PARALLAX_FACTOR * dt * 0.001
        self._bg_current.texture_offset = (0, self._parallax_offset % 1.0)
        self._bg_next.texture_offset    = (0, self._parallax_offset % 1.0)

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
            if not t.enabled:
                continue
            t.z -= current_speed * dt
            if t.z < _TORCH_DESPAWN_Z:
                destroy(t)
            else:
                surviving.append(t)
        self._torches = surviving

    def _update_background(self):
        # Comprobar si hay que iniciar fade al siguiente fondo
        if not self._fading and self._bg_index < len(_BG_THRESHOLDS) - 1:
            next_idx = self._bg_index + 1
            if self._total_distance >= _BG_THRESHOLDS[next_idx]:
                # Cargar el siguiente fondo en la capa superior
                try:
                    self._bg_next.texture = load_texture(_BG_SEQUENCE[next_idx])
                except Exception:
                    pass
                self._bg_next.color = color.rgba32(255, 255, 255, 0)
                self._fading   = True
                self._fade_t   = 0.0
                self._next_idx = next_idx
                print(f"[TRACK] Transición fondo {next_idx}: {_BG_SEQUENCE[next_idx]}")

        if self._fading:
            self._fade_t += time.dt / _FADE_DURATION
            alpha = min(1.0, self._fade_t)
            self._bg_next.color = color.rgba32(255, 255, 255, int(alpha * 255))
            if alpha >= 1.0:
                # Swap: next pasa a ser current
                self._bg_current.texture = self._bg_next.texture
                self._bg_current.color   = color.white
                self._bg_next.color      = color.rgba32(255, 255, 255, 0)
                self._bg_index           = self._next_idx
                self._fading             = False

    def _spawn_torches(self):
        """Genera par de antorchas laterales decorativas que se mueven con la pista."""
        z_spawn = config.OBSTACLE_SPAWN_DISTANCE * 0.80
        for side in (-1, 1):
            try:
                t = Entity(
                    model='quad',
                    texture='assets/environment/antorcha_lateral.png',
                    scale=(0.9, 1.8),
                    position=(side * (config.TRACK_WIDTH / 2 + 0.7), 1.2, z_spawn),
                    billboard=False,
                )
                self._torches.append(t)
            except Exception:
                pass

    # ── API para escena final ─────────────────────────────────────────────────
    def force_final_bg(self):
        """Fuerza el fondo de meta ceremonial."""
        try:
            self._bg_current.texture = load_texture(_BG_SEQUENCE[-1])
            self._bg_current.color   = color.white
            self._bg_next.color      = color.rgba32(255, 255, 255, 0)
            self._fading             = False
            self._bg_index           = len(_BG_SEQUENCE) - 1
        except Exception:
            pass

    def set_distance(self, dist: float):
        """
        Recibe la distancia acumulada de ScoreManager.
        Track no la calcula internamente para evitar doble conteo.
        """
        self._total_distance = dist
