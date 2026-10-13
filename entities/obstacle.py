"""
Obstacle Entity – Huaca Kallpa (assets Moche)

Reemplaza primitivas grises por sprites PNG.
La lógica de colisiones y tipos NO se modifica.

Mapeo de assets:
  'low'    → piedra | vasija | bloque_ceremonial  (esquivar cambiando carril)
  'high'   → portico_alto                          (agacharse)
  'moving' → muro_bajo | columna_caida             (saltar)
"""

import random
from functools import lru_cache
from pathlib import Path
from math import radians, tan
from PIL import Image
from systems.obstacle_projection import project_obstacle
from ursina import *
import config

# ── Conjuntos de texturas por tipo de obstáculo ──────────────────────────────
_TEXTURES_LOW    = [
    'assets/obstacles/piedra.png',
    'assets/obstacles/vasija.png',
    'assets/obstacles/bloque_ceremonial.png',
]
_TEXTURES_HIGH   = [
    'assets/obstacles/portico_alto.png',
]
_TEXTURES_MOVING = [
    'assets/obstacles/muro_bajo.png',
    'assets/obstacles/columna_caida.png',
]

# Escala visual de cada sprite (ancho, alto) en unidades Ursina
# Se ajusta para que el hitbox coincida razonablemente con el sprite.
_SCALE = {
    'low':    (1.8, 1.2),   # obstáculos bajos que se esquivan
    'high':   (3.0, 3.2),   # pórtico alto que ocupa casi todo el carril
    'moving': (2.0, 2.0),   # muros/columnas que hay que saltar
}

# Alturas (centro Y del sprite)
_HEIGHT = {
    'low':    0.65,
    'high':   1.7,
    'moving': 1.1,
}

# Distancia de spawn a la que comienzan los obstáculos (para el escalado por distancia)
_SPAWN_Z = config.OBSTACLE_SPAWN_DISTANCE


@lru_cache(maxsize=6)
def obstacle_texture(path):
    """Return a cached sprite trimmed to its opaque footprint, with no asset edits."""
    absolute = Path(__file__).resolve().parents[1] / path
    with Image.open(absolute) as source:
        sprite = source.convert('RGBA')
    mask = sprite.getchannel('A').point(
        lambda alpha: 255 if alpha > config.OBSTACLE_ALPHA_THRESHOLD else 0)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError(f'Empty obstacle sprite: {path}')
    return Texture(sprite.crop(bounds))


class Obstacle(Entity):
    """
    Obstáculo visual con sprites Moche.
    Mantiene la interfaz pública de la versión anterior.
    """

    def __init__(self, lane: int, z_position: float, obs_type: str):
        """Create the logical obstacle and its road-projected visual; return None."""
        # Elegir textura aleatoria del grupo correspondiente
        if obs_type == 'low':
            tex_path = random.choice(_TEXTURES_LOW)
        elif obs_type == 'high':
            tex_path = random.choice(_TEXTURES_HIGH)
        elif obs_type == 'moving':
            tex_path = random.choice(_TEXTURES_MOVING)
        else:
            raise ValueError(f"Tipo de obstáculo inválido: {obs_type}")

        w, h = _SCALE[obs_type]
        y_pos = _HEIGHT[obs_type]
        x_pos = config.LANE_POSITIONS[lane]

        # Factor de escala inicial (pequeño a distancia, crece al acercarse)
        dist_factor = max(0.05, 1.0 - (z_position / _SPAWN_Z) * 0.95)

        super().__init__(
            model='quad',
            texture=tex_path,
            scale=(w * dist_factor, h * dist_factor),
            position=(x_pos, y_pos, z_position),
            billboard=False,
            collider='box',
        )

        # Retain the logical Entity/collider; render a separate ground-anchored sprite.
        self.model.hide()
        texture = obstacle_texture(tex_path)
        near_height = config.OBSTACLE_NEAR_HEIGHTS[Path(tex_path).stem]
        self._near_size = (near_height * texture.width / texture.height, near_height)
        self._visual = Entity(
            parent=camera, model='quad', texture=texture, color=color.white,
            origin=(0, -0.5), scale=(1, 1), position=(0, 0, 1), collider=None,
        )
        self.texture_path = tex_path

        # Estado interno
        self.lane        = lane
        self.z_position  = z_position
        self.obs_type    = obs_type
        self._base_w     = w
        self._base_h     = h
        self._base_y     = y_pos

        self._update_projection()

        print(f"[OBSTACLE] {obs_type} ({tex_path.split('/')[-1]}) – carril {lane}, z={z_position}")

    def _update_projection(self):
        """Place the visual base on the road using logical lane/depth; return None."""
        x, floor_y, width, height, depth = project_obstacle(
            self.lane, self.z_position, self._near_size)
        _, vertical_fov = camera.lens.get_fov()
        film_height = 2 * depth * tan(radians(vertical_fov) / 2)
        self._visual.position = (x * film_height, floor_y * film_height, depth)
        self._visual.scale = (width * film_height, height * film_height)
        self.screen_projection = (x, floor_y, width, height, depth)

    def update(self):
        """Scroll logical depth and refresh the grounded sprite; return None."""
        if self.is_empty():
            return
        self.z_position -= config.TRACK_SCROLL_SPEED * time.dt
        self.z = self.z_position
        self.x = config.LANE_POSITIONS[self.lane]
        self._update_projection()
        if self.z_position < config.OBSTACLE_DESPAWN_DISTANCE:
            self.cleanup()

    def on_destroy(self):
        """Destroy the separately parented visual together with its owner; return None."""
        if not self._visual.is_empty():
            destroy(self._visual)

    def cleanup(self):
        """Destroy the passed obstacle and its visual; return None."""
        destroy(self)
