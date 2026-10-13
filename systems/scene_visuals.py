"""Cached scene textures and a one-surface crossfade shader."""
from functools import lru_cache
from pathlib import Path
from ursina import Shader, load_texture
from ursina.shaders.unlit_shader import unlit_shader
import config


@lru_cache(maxsize=config.SCENE_TEXTURE_CACHE_SIZE)
def scene_texture(path):
    """Return the same loaded texture across rounds; raise for a missing asset."""
    absolute = Path(__file__).resolve().parents[1] / path
    texture = load_texture(absolute.name, path=absolute.parent)
    if texture is None:
        raise FileNotFoundError(f'Missing scene texture: {absolute}')
    return texture


background_shader = Shader(
    name='moche_single_background', language=Shader.GLSL, vertex=unlit_shader.vertex,
    fragment='''#version 140
uniform sampler2D p3d_Texture0;
uniform sampler2D next_texture;
uniform float blend_amount;
uniform vec4 p3d_ColorScale;
in vec2 texcoords;
in vec4 vertex_color;
out vec4 fragColor;
void main() {
    fragColor = mix(texture(p3d_Texture0, texcoords), texture(next_texture, texcoords),
                    clamp(blend_amount, 0.0, 1.0)) * p3d_ColorScale * vertex_color;
}
''',
    default_input={'texture_scale': (1, 1), 'texture_offset': (0, 0), 'blend_amount': 0.0},
)
