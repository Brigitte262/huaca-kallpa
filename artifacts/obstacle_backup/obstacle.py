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


class Obstacle(Entity):
    """
    Obstáculo visual con sprites Moche.
    Mantiene la interfaz pública de la versión anterior.
    """

    def __init__(self, lane: int, z_position: float, obs_type: str):
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

        # Estado interno
        self.lane        = lane
        self.z_position  = z_position
        self.obs_type    = obs_type
        self._base_w     = w
        self._base_h     = h
        self._base_y     = y_pos

        # Moving obstacle
        self.move_direction = 1 if lane == 0 else -1

        print(f"[OBSTACLE] {obs_type} ({tex_path.split('/')[-1]}) – carril {lane}, z={z_position}")

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self):
        # Avanzar hacia el jugador
        self.z_position -= config.TRACK_SCROLL_SPEED * time.dt
        self.z           = self.z_position

        # Escalado por perspectiva: crece al acercarse (z negativo = cerca)
        t = 1.0 - max(0.0, self.z_position / _SPAWN_Z)  # 0 lejos → 1 muy cerca
        scale_f = max(0.05, 0.05 + 0.95 * t)
        self.scale_x = self._base_w * scale_f
        self.scale_y = self._base_h * scale_f

        # Mantener Y proporcional
        self.y = self._base_y * scale_f + 0.05

        # Comportamiento de obstáculo móvil
        if self.obs_type == 'moving':
            self._update_moving()

        # Eliminar si pasó al jugador
        if self.z_position < config.OBSTACLE_DESPAWN_DISTANCE:
            self.cleanup()

    def _update_moving(self):
        self.x += self.move_direction * config.OBS_MOVING_SPEED * time.dt
        if self.x <= config.LANE_POSITIONS[0]:
            self.x = config.LANE_POSITIONS[0]
            self.move_direction = 1
            self.lane = 0
        elif self.x >= config.LANE_POSITIONS[2]:
            self.x = config.LANE_POSITIONS[2]
            self.move_direction = -1
            self.lane = 2
        else:
            distances = [abs(self.x - pos) for pos in config.LANE_POSITIONS]
            self.lane = distances.index(min(distances))

    def cleanup(self):
        destroy(self)
