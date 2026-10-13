"""UI-only layout helpers for a fixed 16:9 design canvas."""
from pathlib import Path
from ursina import Entity, Text, camera, window, load_texture
import config


def ui_root():
    """Return a UI tree that fits the 16:9 canvas at any window aspect."""
    root = Entity(parent=camera.ui)

    def resize():
        """Fit uniformly without changing individual component dimensions."""
        factor = min(1, window.aspect_ratio / config.UI_ASPECT)
        if abs(root.scale_x - factor) > config.UI_RESIZE_EPSILON:
            root.scale = factor
        for child in root.children:
            if getattr(child, 'fill_screen', False):
                child.scale = (window.aspect_ratio / factor, 1 / factor)

    root.update = resize
    resize()
    return root


def panel(parent, size, position, tint, z=config.UI_LAYER_PANEL):
    """Return an explicitly colored quad with centered origin and no collider."""
    return Entity(parent=parent, model='quad', scale=size, position=position,
                  origin=(0, 0), z=z, color=tint, collider=None)


def label(parent, text, position, size=1, tint=None):
    """Return centered text on the content layer; size is the font scale."""
    return Text(parent=parent, text=text, position=position, scale=size,
                origin=(0, 0), z=config.UI_LAYER_CONTENT,
                color=tint or config.UI_CREAM, font=config.UI_FONT)


def asset_texture(path):
    """Return a validated texture or None; never display an untextured white quad."""
    absolute = Path(__file__).resolve().parent.parent / path
    return load_texture(absolute.name, path=absolute.parent) if absolute.is_file() else None


