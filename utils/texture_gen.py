"""
Generador de Texturas Procedurales – Temática Moche / Huaca Kallpa
Paleta: terracota, adobe, ocre dorado, crema, azul cobalto oscuro.
"""

from PIL import Image, ImageDraw
import random
import math
import os

ASSETS_DIR = 'assets'

# ── Paleta Moche ─────────────────────────────────────────────────────────────
TERRACOTA_LIGHT = (200, 120, 70)
TERRACOTA_MID   = (175, 90,  45)
TERRACOTA_DARK  = (140, 65,  25)
ADOBE_LIGHT     = (210, 170, 120)
ADOBE_MID       = (185, 140, 90)
ADOBE_DARK      = (140, 100, 55)
ORO_BRIGHT      = (240, 195, 50)
ORO_MID         = (210, 160, 30)
ORO_DARK        = (160, 110, 10)
NEGRO_MOCHE     = (20,  15,  10)
AZUL_OSCURO     = (30,  50,  90)
CREMA           = (240, 225, 185)


def ensure_assets_dir():
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)


def generate_track_texture():
    """Camino de adobe apisonado con juntas oscuras – estilo Huaca de la Luna."""
    size = 512
    img = Image.new('RGB', (size, size), ADOBE_MID)
    draw = ImageDraw.Draw(img)

    # Bloques de adobe en patrón ladrillo
    rows, cols = 10, 4
    w = size // cols
    h = size // rows

    for r in range(rows):
        # Desplazamiento de media piedra en filas pares
        offset = (w // 2) if (r % 2 == 0) else 0
        for c in range(cols + 1):
            x = c * w - offset
            y = r * h
            noise = random.randint(-15, 15)
            shade = (
                max(0, min(255, ADOBE_LIGHT[0] + noise)),
                max(0, min(255, ADOBE_LIGHT[1] + noise)),
                max(0, min(255, ADOBE_LIGHT[2] + noise))
            )
            gap = 5
            draw.rectangle([x + gap, y + gap, x + w - gap, y + h - gap], fill=shade)

    # Juntas oscuras (terracota oscura)
    for r in range(rows + 1):
        y = r * h
        draw.line([(0, y), (size, y)], fill=TERRACOTA_DARK, width=3)
    for c in range(cols + 1):
        x = c * w
        draw.line([(x, 0), (x, size)], fill=TERRACOTA_DARK, width=3)

    img.save(os.path.join(ASSETS_DIR, 'track_texture.png'))
    print("[TEXTURE] track_texture.png (adobe Moche)")


def generate_wall_texture():
    """Muro de adobe con desgaste y grabado Moche – obstáculo alto."""
    size = 256
    img = Image.new('RGB', (size, size), TERRACOTA_MID)
    draw = ImageDraw.Draw(img)
    pixels = img.load()

    # Ruido de superficie adobe
    for x in range(size):
        for y in range(size):
            noise = random.randint(-25, 25)
            r = max(0, min(255, TERRACOTA_MID[0] + noise))
            g = max(0, min(255, TERRACOTA_MID[1] + noise))
            b = max(0, min(255, TERRACOTA_MID[2] + noise))
            # Grietas ocasionales (franjas oscuras horizontales)
            if y % 32 < 3:
                r, g, b = TERRACOTA_DARK
            pixels[x, y] = (r, g, b)

    # Patrón geométrico Moche: escalonado / grecas
    step = 32
    for i in range(0, size, step * 2):
        draw.rectangle([i, i, i + step - 2, i + step - 2], outline=ORO_DARK, width=2)
        draw.rectangle([i + step, i + step, i + step * 2 - 2, i + step * 2 - 2],
                       outline=ORO_DARK, width=2)

    img.save(os.path.join(ASSETS_DIR, 'wall_texture.png'))
    print("[TEXTURE] wall_texture.png (adobe con patrón Moche)")


def generate_wood_texture():
    """Madera de algarrobo – obstáculo bajo (tronco / vasija caída)."""
    size = 256
    img = Image.new('RGB', (size, size), TERRACOTA_DARK)
    pixels = img.load()

    for x in range(size):
        for y in range(size):
            # Veta de madera
            grain = math.sin(x * 0.15 + y * 0.03 + random.uniform(-0.1, 0.1)) * 18
            noise = random.randint(-8, 8)
            r = max(0, min(255, TERRACOTA_DARK[0] + int(grain) + noise))
            g = max(0, min(255, TERRACOTA_DARK[1] + int(grain) + noise - 5))
            b = max(0, min(255, TERRACOTA_DARK[2] + int(grain) + noise - 10))
            pixels[x, y] = (r, g, b)

    img.save(os.path.join(ASSETS_DIR, 'wood_texture.png'))
    print("[TEXTURE] wood_texture.png (algarrobo / vasija)")


def generate_metal_texture():
    """Elemento decorativo en metal (cobre oxidado) – obstáculo móvil."""
    size = 256
    img = Image.new('RGB', (size, size), (80, 110, 100))
    pixels = img.load()

    for x in range(size):
        for y in range(size):
            noise = random.randint(-20, 20)
            # Parches de cobre oxidado (verde-azulado)
            if random.random() < 0.12:
                r = max(0, min(255, 55  + noise))
                g = max(0, min(255, 130 + noise))
                b = max(0, min(255, 110 + noise))
            elif random.random() < 0.06:
                # Brillo dorado Moche
                r = max(0, min(255, ORO_MID[0] + noise))
                g = max(0, min(255, ORO_MID[1] + noise))
                b = max(0, min(255, ORO_MID[2] + noise))
            else:
                r = max(0, min(255, 80  + noise))
                g = max(0, min(255, 110 + noise))
                b = max(0, min(255, 100 + noise))
            pixels[x, y] = (r, g, b)

    img.save(os.path.join(ASSETS_DIR, 'metal_texture.png'))
    print("[TEXTURE] metal_texture.png (cobre oxidado Moche)")


def generate_orb_texture():
    """Huaco de oro – coleccionable de puntos."""
    size = 128
    img = Image.new('RGB', (size, size), NEGRO_MOCHE)
    pixels = img.load()

    center  = size // 2
    max_dist = size // 2

    for x in range(size):
        for y in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < max_dist:
                intensity = 1.0 - (dist / max_dist)
                # Gradiente oro Moche
                r = int(ORO_BRIGHT[0] * intensity)
                g = int(ORO_BRIGHT[1] * intensity)
                b = int(ORO_BRIGHT[2] * intensity)
                # Reflejo en el borde
                if dist > max_dist * 0.7:
                    r = min(255, r + 40)
                    g = min(255, g + 20)
                pixels[x, y] = (r, g, b)
            else:
                pixels[x, y] = NEGRO_MOCHE

    img.save(os.path.join(ASSETS_DIR, 'orb_texture.png'))
    print("[TEXTURE] orb_texture.png (huaco de oro)")


def generate_sky_texture():
    """Cielo nocturno sobre el Valle Moche: azul índigo con estrellas y luna."""
    size = 1024
    img = Image.new('RGB', (size, size), (10, 8, 25))
    pixels = img.load()
    draw = ImageDraw.Draw(img)

    # Gradiente vertical (horizonte más claro)
    for y in range(size):
        horizon_factor = max(0, 1 - y / (size * 0.6))
        for x in range(size):
            noise = random.randint(-3, 3)
            r = max(0, min(255, int(10  + horizon_factor * 40) + noise))
            g = max(0, min(255, int(8   + horizon_factor * 25) + noise))
            b = max(0, min(255, int(25  + horizon_factor * 55) + noise))
            pixels[x, y] = (r, g, b)

    # Estrellas
    for _ in range(800):
        sx = random.randint(0, size - 1)
        sy = random.randint(0, int(size * 0.7))
        brightness = random.randint(100, 250)
        star_color = (brightness, brightness, int(brightness * 0.9))
        if random.random() < 0.08:
            draw.point((sx, sy), fill=(255, 255, 240))
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                draw.point((sx+dx, sy+dy), fill=(brightness//2, brightness//2, brightness//3))
        else:
            draw.point((sx, sy), fill=star_color)

    # Luna (disco crema en la esquina superior)
    moon_x, moon_y, moon_r = int(size * 0.8), int(size * 0.12), 35
    draw.ellipse(
        [moon_x - moon_r, moon_y - moon_r, moon_x + moon_r, moon_y + moon_r],
        fill=CREMA
    )

    img.save(os.path.join(ASSETS_DIR, 'sky_texture.png'))
    print("[TEXTURE] sky_texture.png (cielo nocturno Valle Moche)")


if __name__ == '__main__':
    ensure_assets_dir()
    generate_track_texture()
    generate_wall_texture()
    generate_wood_texture()
    generate_metal_texture()
    generate_orb_texture()
    generate_sky_texture()
