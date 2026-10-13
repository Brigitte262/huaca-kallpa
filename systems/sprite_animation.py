"""Cached texture sequences with a fixed canvas and foot anchor for sprite playback."""
from functools import lru_cache
from pathlib import Path
from PIL import Image
from ursina import Texture
import config

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=2)
def character_frames(gender):
    """Return cached run/jump/crouch textures aligned on one transparent canvas.

    Args:
        gender: 'female' or 'male'.
    Returns:
        dict: Animation keys mapped to tuples of preloaded Ursina textures.
    """
    animations = {}
    for key, count in (('run', config.PLAYER_RUN_FRAME_COUNT),
                       ('jump', config.PLAYER_ACTION_FRAME_COUNT),
                       ('crouch', config.PLAYER_ACTION_FRAME_COUNT)):
        textures = []
        for index in range(1, count + 1):
            name = f'{gender}_{key}_{index:02d}.png'
            relative = config.PLAYER_FRAME_OVERRIDES.get(
                name, f'assets/characters/{gender}/{name}')
            path = ROOT / relative
            with Image.open(path) as source:
                sprite = source.convert('RGBA')
            mask = sprite.getchannel('A').point(
                lambda alpha: 255 if alpha > config.PLAYER_SPRITE_ALPHA_THRESHOLD else 0)
            bounds = mask.getbbox()
            if bounds is None:
                raise ValueError(f'Empty character frame: {path}')
            sprite = sprite.crop(bounds)
            size = config.PLAYER_SPRITE_CANVAS
            ratio = min(size * config.PLAYER_SPRITE_BODY_HEIGHT / sprite.height,
                        size * config.PLAYER_SPRITE_MAX_WIDTH / sprite.width)
            sprite = sprite.resize((round(sprite.width * ratio), round(sprite.height * ratio)),
                                   Image.Resampling.LANCZOS)
            canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            anchor = ((size - sprite.width) // 2,
                      round(size * config.PLAYER_SPRITE_BASELINE) - sprite.height)
            canvas.alpha_composite(sprite, anchor)
            texture = Texture(canvas)
            texture.frame_name = name
            textures.append(texture)
        animations[key] = tuple(textures)
    return animations
