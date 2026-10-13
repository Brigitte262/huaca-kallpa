from enum import Enum
from math import isfinite

class Position(str, Enum):
    LEFT = 'LEFT'
    CENTER = 'CENTER'
    RIGHT = 'RIGHT'

class MovementClassifier:
    """Coordenadas normalizadas en modo espejo; zona central e histéresis."""
    def __init__(self, dead_zone=0.10, hysteresis=0.03):
        if not 0 <= hysteresis < dead_zone < 0.5:
            raise ValueError('Se requiere 0 <= hysteresis < dead_zone < 0.5')
        self.dead_zone = dead_zone
        self.hysteresis = hysteresis
        self.position = Position.CENTER

    def classify(self, center_x):
        if center_x is None or not isfinite(center_x) or not 0 <= center_x <= 1:
            self.position = Position.CENTER
            return None
        left, right = 0.5 - self.dead_zone, 0.5 + self.dead_zone
        if center_x < left:
            self.position = Position.LEFT
        elif center_x > right:
            self.position = Position.RIGHT
        elif self.position == Position.LEFT and center_x < left + self.hysteresis:
            pass
        elif self.position == Position.RIGHT and center_x > right - self.hysteresis:
            pass
        else:
            self.position = Position.CENTER
        return self.position
