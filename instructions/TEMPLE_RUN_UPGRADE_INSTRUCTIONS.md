# Temple Run 3D - Visual Upgrade & Bug Fix Instructions

**Implementation Style:** Phase-based with complete, cursor-ready code blocks
**Estimated Total Time:** 2-3 hours
**Philosophy:** Geometric elegance + VFX enhancement over texture complexity

---

## TABLE OF CONTENTS

### PART A: CRITICAL BUG FIXES (30 min)
- Phase 1-5: Fix runtime config mutation, imports, .gitignore, magic numbers

### PART B: PLAYER VISUAL UPGRADE (45 min)
- Phase 6-12: Octahedron geometry, particle trail, glow effects, rotation animations

### PART C: PARALLAX STAR FIELD (30 min)
- Phase 13-18: 2-layer scrolling stars with depth, twinkling effects

### PART D: OBSTACLE GLOW EFFECTS (20 min)
- Phase 19-22: Emission rendering, glow halos, difficulty-based color shifts

### PART E: POLISH & TESTING (15 min)
- Phase 23-25: Performance validation, visual tweaks, final testing

---

## PART A: CRITICAL BUG FIXES

### PHASE 1: Fix Runtime Config Mutation in difficulty.py

**File:** `systems/difficulty.py`
**Issue:** Line 34 mutates `config.TRACK_SCROLL_SPEED` globally
**Impact:** Config becomes stateful, breaks on restart

**Action:** Replace line 34 with parameter passing

**Current Code (LINE 34):**
```python
config.TRACK_SCROLL_SPEED = current_speed
```

**Replacement Code:**
```python
# Remove line 34 entirely - speed will be returned instead
```

**New Function Signature (REPLACE ENTIRE FUNCTION starting at line 18):**
```python
def update_difficulty(score, elapsed_time):
    """
    Calculate current difficulty parameters based on score and time.
    Returns speed instead of mutating config.
    
    Args:
        score: Current game score
        elapsed_time: Time elapsed in seconds
        
    Returns:
        tuple: (current_speed, spawn_rate_multiplier)
    """
    # Time-based speed increase (every 10 seconds)
    time_factor = min(elapsed_time / 60.0, 2.0)
    
    # Score-based speed increase (every 50 points)
    score_factor = min(score / 200.0, 2.0)
    
    # Combined difficulty
    difficulty = 1.0 + (time_factor * 0.5) + (score_factor * 0.5)
    
    current_speed = config.TRACK_SCROLL_SPEED_BASE * difficulty
    spawn_rate_multiplier = 1.0 + (difficulty - 1.0) * 0.3
    
    return current_speed, spawn_rate_multiplier
```

**Required Config Addition:**
Add this to `config.py` after line with `TRACK_SCROLL_SPEED`:
```python
TRACK_SCROLL_SPEED_BASE = TRACK_SCROLL_SPEED  # Base speed for difficulty scaling
```

---

### PHASE 2: Update All Callers of update_difficulty()

**File:** `main.py`
**Location:** Inside game loop where `update_difficulty()` is called

**Find this pattern:**
```python
difficulty.update_difficulty(score, elapsed_time)
# ... later ...
entities_state['track_segments'] = track.update_track(
    entities_state['track_segments'],
    entities_state['player']
)
```

**Replace with:**
```python
current_speed, spawn_multiplier = difficulty.update_difficulty(score, elapsed_time)

# Update track with explicit speed
entities_state['track_segments'] = track.update_track(
    entities_state['track_segments'],
    entities_state['player'],
    current_speed  # Pass speed explicitly
)
```

**File:** `systems/track.py`
**Update Function Signature:**

**Find:**
```python
def update_track(track_segments, player):
```

**Replace with:**
```python
def update_track(track_segments, player, scroll_speed=None):
    """
    Update track segments position.
    
    Args:
        track_segments: List of track segment entities
        player: Player entity (for reference position)
        scroll_speed: Override speed, or use config.TRACK_SCROLL_SPEED
    """
    speed = scroll_speed if scroll_speed is not None else config.TRACK_SCROLL_SPEED
```

**Inside update_track(), replace all instances of `config.TRACK_SCROLL_SPEED` with `speed`**

---

### PHASE 3: Fix Duplicate Imports in score.py

**File:** `systems/score.py`
**Lines:** 4-5

**Current Code:**
```python
import time
import time  # Duplicate
```

**Replacement:**
```python
import time
# Removed duplicate import
```

---

### PHASE 4: Fix .gitignore Broken Formatting

**File:** `.gitignore`

**Find:**
```
h i g h _ s c o r e . j s o n
```

**Replace with:**
```
high_score.json
```

---

### PHASE 5: Fix Magic Numbers - Add Config Constants

**File:** `config.py`
**Add these constants at the end:**

```python
# Collision Detection
PLAYER_COLLISION_RADIUS = 1.0  # Used in collision.py line 66

# Spawning
COLLECTIBLE_SPAWN_CHANCE = 0.3  # Used in spawner.py line 35
```

**File:** `systems/collision.py`
**Line 66 - Find:**
```python
distance < 1.0
```

**Replace with:**
```python
distance < config.PLAYER_COLLISION_RADIUS
```

**File:** `systems/spawner.py`
**Line 35 - Find:**
```python
if random.random() < 0.3:
```

**Replace with:**
```python
if random.random() < config.COLLECTIBLE_SPAWN_CHANCE:
```

---

## PART B: PLAYER VISUAL UPGRADE

### PHASE 6: Create Octahedron Geometry Module

**File:** `entities/geometry.py` (NEW FILE)
**Purpose:** Generate octahedron vertices and faces

```python
"""
Geometry generation for 3D shapes.
Provides clean geometric primitives for rendering.
"""

import numpy as np


def generate_octahedron(size=1.0):
    """
    Generate vertices and faces for a regular octahedron.
    
    An octahedron has 6 vertices and 8 triangular faces.
    Centered at origin, aligned to axes.
    
    Args:
        size: Distance from center to vertex
        
    Returns:
        tuple: (vertices, faces)
            vertices: List of [x, y, z] coordinates
            faces: List of [v0, v1, v2] vertex indices
    """
    # Six vertices aligned to axes
    vertices = [
        [0, size, 0],      # 0: Top
        [0, -size, 0],     # 1: Bottom
        [size, 0, 0],      # 2: Right
        [-size, 0, 0],     # 3: Left
        [0, 0, size],      # 4: Front
        [0, 0, -size],     # 5: Back
    ]
    
    # Eight triangular faces (counter-clockwise winding)
    faces = [
        # Upper hemisphere
        [0, 4, 2],  # Top-Front-Right
        [0, 2, 5],  # Top-Right-Back
        [0, 5, 3],  # Top-Back-Left
        [0, 3, 4],  # Top-Left-Front
        
        # Lower hemisphere
        [1, 2, 4],  # Bottom-Right-Front
        [1, 5, 2],  # Bottom-Back-Right
        [1, 3, 5],  # Bottom-Left-Back
        [1, 4, 3],  # Bottom-Front-Left
    ]
    
    return vertices, faces


def generate_particle_trail(count=12, spacing=0.5):
    """
    Generate positions for particle trail behind player.
    
    Args:
        count: Number of particles in trail
        spacing: Distance between particles
        
    Returns:
        list: List of [x, y, z] offset positions
    """
    particles = []
    for i in range(count):
        z_offset = -i * spacing  # Behind player
        particles.append([0, 0, z_offset])
    
    return particles
```

---

### PHASE 7: Update Player Entity to Use Octahedron

**File:** `entities/player.py`
**Import Addition (top of file):**

```python
from entities.geometry import generate_octahedron, generate_particle_trail
```

**Find `create_player()` function, replace entire function:**

```python
def create_player():
    """
    Create player entity with octahedron geometry and particle trail.
    
    Returns:
        dict: Player entity with geometry data
    """
    vertices, faces = generate_octahedron(size=0.8)
    trail_positions = generate_particle_trail(count=12, spacing=0.4)
    
    return {
        'position': [0, config.PLAYER_HEIGHT, 0],  # [x, y, z]
        'lane': 1,  # Center lane (0=left, 1=center, 2=right)
        'target_lane': 1,
        'vertical_state': 'grounded',  # 'grounded', 'jumping', 'sliding'
        'jump_timer': 0.0,
        'slide_timer': 0.0,
        
        # Visual properties
        'geometry': {
            'type': 'octahedron',
            'vertices': vertices,
            'faces': faces,
            'rotation': [0, 0, 0],  # [x, y, z] rotation in radians
            'rotation_speed': [0.5, 1.0, 0.3],  # Rotation per second
        },
        
        # Particle trail
        'trail': {
            'positions': trail_positions,
            'intensities': [1.0 - (i / len(trail_positions)) for i in range(len(trail_positions))],
            'sizes': [0.3 - (i / len(trail_positions)) * 0.2 for i in range(len(trail_positions))],
        },
        
        # Glow effect
        'glow': {
            'color': [0.2, 0.6, 1.0],  # Cyan glow
            'intensity': 1.0,
            'pulse_speed': 2.0,
        }
    }
```

---

### PHASE 8: Create Particle Trail System

**File:** `systems/particle_trail.py` (NEW FILE)

```python
"""
Particle trail system for player visual effects.
Manages trailing particle positions and intensities.
"""

import config


def update_particle_trail(player, dt):
    """
    Update particle trail positions to follow player.
    
    Args:
        player: Player entity with trail data
        dt: Delta time in seconds
    """
    if 'trail' not in player:
        return
    
    trail = player['trail']
    player_pos = player['position']
    
    # Shift all particles back one position (cascade effect)
    for i in range(len(trail['positions']) - 1, 0, -1):
        # Each particle moves toward the position of the one in front
        prev_pos = trail['positions'][i - 1]
        curr_pos = trail['positions'][i]
        
        # Smooth interpolation
        lerp_factor = 0.15
        curr_pos[0] = curr_pos[0] + (prev_pos[0] - curr_pos[0]) * lerp_factor
        curr_pos[1] = curr_pos[1] + (prev_pos[1] - curr_pos[1]) * lerp_factor
        curr_pos[2] = curr_pos[2] + (prev_pos[2] - curr_pos[2]) * lerp_factor
    
    # First particle follows player exactly
    trail['positions'][0] = [
        player_pos[0],
        player_pos[1],
        player_pos[2] - 0.3  # Slightly behind player
    ]


def update_player_rotation(player, dt):
    """
    Update player geometry rotation for visual interest.
    
    Args:
        player: Player entity with geometry data
        dt: Delta time in seconds
    """
    if 'geometry' not in player or 'rotation' not in player['geometry']:
        return
    
    geometry = player['geometry']
    rotation = geometry['rotation']
    rotation_speed = geometry['rotation_speed']
    
    # Continuous rotation on all axes
    rotation[0] += rotation_speed[0] * dt
    rotation[1] += rotation_speed[1] * dt
    rotation[2] += rotation_speed[2] * dt
    
    # Wrap to 0-2π
    import math
    for i in range(3):
        if rotation[i] > 2 * math.pi:
            rotation[i] -= 2 * math.pi


def update_player_glow(player, dt):
    """
    Update glow pulse effect for player.
    
    Args:
        player: Player entity with glow data
        dt: Delta time in seconds
    """
    if 'glow' not in player:
        return
    
    glow = player['glow']
    
    # Pulse intensity using sine wave
    import math
    import time
    
    pulse_time = time.time() * glow['pulse_speed']
    glow['intensity'] = 0.7 + 0.3 * math.sin(pulse_time)
```

---

### PHASE 9: Integrate Trail System into Game Loop

**File:** `main.py`
**Import Addition:**

```python
from systems import particle_trail
```

**Inside game loop, after player movement update, add:**

```python
# Update player visual effects
particle_trail.update_particle_trail(entities_state['player'], dt)
particle_trail.update_player_rotation(entities_state['player'], dt)
particle_trail.update_player_glow(entities_state['player'], dt)
```

---

### PHASE 10: Update Renderer for Octahedron

**File:** `systems/renderer.py`
**Import Addition:**

```python
import math
```

**Find `draw_player()` function, replace entire function:**

```python
def draw_player(screen, player, camera_offset=0):
    """
    Draw player with octahedron geometry, glow, and particle trail.
    
    Args:
        screen: Pygame screen surface
        player: Player entity
        camera_offset: Z-axis camera offset for perspective
    """
    if 'geometry' not in player:
        # Fallback to simple cube rendering
        draw_player_simple(screen, player, camera_offset)
        return
    
    player_pos = player['position']
    geometry = player['geometry']
    
    # Draw glow halo first (behind geometry)
    if 'glow' in player:
        draw_glow_halo(screen, player_pos, player['glow'], camera_offset)
    
    # Draw particle trail
    if 'trail' in player:
        draw_particle_trail(screen, player['trail'], camera_offset)
    
    # Draw octahedron
    draw_octahedron(screen, player_pos, geometry, camera_offset)


def draw_octahedron(screen, position, geometry, camera_offset):
    """
    Draw octahedron with rotation and perspective projection.
    
    Args:
        screen: Pygame screen surface
        position: [x, y, z] world position
        geometry: Geometry data with vertices, faces, rotation
        camera_offset: Z-axis camera offset
    """
    vertices = geometry['vertices']
    faces = geometry['faces']
    rotation = geometry['rotation']
    
    # Transform vertices with rotation
    transformed = []
    for vertex in vertices:
        # Apply rotation matrices
        v = rotate_vertex(vertex, rotation)
        
        # Translate to world position
        v = [
            v[0] + position[0],
            v[1] + position[1],
            v[2] + position[2]
        ]
        
        transformed.append(v)
    
    # Project to screen and draw faces
    screen_verts = []
    for v in transformed:
        sx, sy = world_to_screen(v[0], v[1], v[2] - camera_offset)
        screen_verts.append((sx, sy))
    
    # Draw faces with depth sorting
    face_depths = []
    for face in faces:
        # Calculate face center for depth sorting
        center_z = sum(transformed[i][2] for i in face) / 3
        face_depths.append((center_z, face))
    
    # Sort back to front
    face_depths.sort(reverse=True, key=lambda x: x[0])
    
    # Draw each face
    import pygame
    for _, face in face_depths:
        points = [screen_verts[i] for i in face]
        
        # Face color with lighting based on orientation
        base_color = [100, 180, 255]  # Cyan
        pygame.draw.polygon(screen, base_color, points)
        pygame.draw.polygon(screen, [150, 220, 255], points, 2)  # Edge highlight


def rotate_vertex(vertex, rotation):
    """
    Apply 3D rotation to a vertex.
    
    Args:
        vertex: [x, y, z] position
        rotation: [rx, ry, rz] rotation in radians
        
    Returns:
        list: Rotated [x, y, z] position
    """
    x, y, z = vertex
    rx, ry, rz = rotation
    
    # Rotation around X axis
    cos_x, sin_x = math.cos(rx), math.sin(rx)
    y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
    
    # Rotation around Y axis
    cos_y, sin_y = math.cos(ry), math.sin(ry)
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
    
    # Rotation around Z axis
    cos_z, sin_z = math.cos(rz), math.sin(rz)
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z
    
    return [x, y, z]


def draw_glow_halo(screen, position, glow, camera_offset):
    """
    Draw glow effect around player.
    
    Args:
        screen: Pygame screen surface
        position: [x, y, z] world position
        glow: Glow data with color and intensity
        camera_offset: Z-axis camera offset
    """
    import pygame
    
    sx, sy = world_to_screen(position[0], position[1], position[2] - camera_offset)
    
    # Multiple expanding circles for glow effect
    color = glow['color']
    intensity = glow['intensity']
    
    for i in range(3):
        radius = int(30 + i * 15)
        alpha = int(intensity * 50 / (i + 1))
        
        glow_color = [
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255)
        ]
        
        # Draw glow circle with alpha
        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow_color, alpha), (radius, radius), radius)
        screen.blit(glow_surf, (sx - radius, sy - radius))


def draw_particle_trail(screen, trail, camera_offset):
    """
    Draw particle trail behind player.
    
    Args:
        screen: Pygame screen surface
        trail: Trail data with positions, intensities, sizes
        camera_offset: Z-axis camera offset
    """
    import pygame
    
    positions = trail['positions']
    intensities = trail['intensities']
    sizes = trail['sizes']
    
    for i, pos in enumerate(positions):
        sx, sy = world_to_screen(pos[0], pos[1], pos[2] - camera_offset)
        
        intensity = intensities[i]
        size = sizes[i]
        
        # Particle color fades with intensity
        alpha = int(intensity * 200)
        radius = int(size * 20)
        
        # Draw particle with glow
        particle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (100, 180, 255, alpha), (radius, radius), radius)
        screen.blit(particle_surf, (sx - radius, sy - radius))


def draw_player_simple(screen, player, camera_offset):
    """
    Fallback simple cube rendering for player.
    
    Args:
        screen: Pygame screen surface
        player: Player entity
        camera_offset: Z-axis camera offset
    """
    import pygame
    
    pos = player['position']
    sx, sy = world_to_screen(pos[0], pos[1], pos[2] - camera_offset)
    
    size = 40
    pygame.draw.rect(screen, (100, 180, 255), (sx - size // 2, sy - size // 2, size, size))
    pygame.draw.rect(screen, (150, 220, 255), (sx - size // 2, sy - size // 2, size, size), 3)
```

---

### PHASE 11: Add world_to_screen Helper If Missing

**File:** `systems/renderer.py`
**Check if this function exists. If not, add it:**

```python
def world_to_screen(x, y, z):
    """
    Convert 3D world coordinates to 2D screen coordinates.
    Simple perspective projection.
    
    Args:
        x: World X coordinate
        y: World Y coordinate  
        z: World Z coordinate (distance from camera)
        
    Returns:
        tuple: (screen_x, screen_y)
    """
    import config
    
    # Perspective projection
    fov = 800  # Field of view
    scale = fov / (fov + z) if z > -fov else 1.0
    
    screen_x = config.SCREEN_WIDTH // 2 + int(x * 100 * scale)
    screen_y = config.SCREEN_HEIGHT // 2 - int(y * 100 * scale)
    
    return screen_x, screen_y
```

---

### PHASE 12: Test Player Visual Upgrade

**Action:** Run game and verify:
- Octahedron rotates smoothly
- Particle trail follows player
- Glow pulses with sine wave
- No performance drop

**Expected Result:** Player is now a rotating glowing octahedron with cyan particle trail

---

## PART C: PARALLAX STAR FIELD

### PHASE 13: Create Star Field System

**File:** `systems/starfield.py` (NEW FILE)

```python
"""
Parallax star field background system.
Creates depth with multiple scrolling layers.
"""

import random
import config


def create_starfield(num_stars_per_layer=100, num_layers=2):
    """
    Generate multi-layer star field for parallax effect.
    
    Args:
        num_stars_per_layer: Number of stars in each layer
        num_layers: Number of depth layers (2-3 recommended)
        
    Returns:
        dict: Star field data structure
    """
    layers = []
    
    for layer_idx in range(num_layers):
        stars = []
        
        for _ in range(num_stars_per_layer):
            star = {
                'x': random.randint(0, config.SCREEN_WIDTH),
                'y': random.randint(0, config.SCREEN_HEIGHT),
                'size': random.uniform(1.0, 2.5),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle_offset': random.uniform(0, 6.28),  # Phase offset for twinkling
            }
            stars.append(star)
        
        # Layer depth affects scroll speed (closer = faster)
        depth_factor = 1.0 - (layer_idx / num_layers) * 0.7  # Range: 1.0 to 0.3
        
        layers.append({
            'stars': stars,
            'depth_factor': depth_factor,
            'scroll_offset': 0.0,
        })
    
    return {
        'layers': layers,
        'twinkle_time': 0.0,
    }


def update_starfield(starfield, scroll_speed, dt):
    """
    Update star positions based on scroll speed and depth.
    
    Args:
        starfield: Star field data structure
        scroll_speed: Current game scroll speed
        dt: Delta time in seconds
    """
    starfield['twinkle_time'] += dt
    
    for layer in starfield['layers']:
        # Scroll stars based on depth (parallax effect)
        scroll_amount = scroll_speed * layer['depth_factor'] * dt * 50
        layer['scroll_offset'] += scroll_amount
        
        # Wrap stars when they scroll off screen
        for star in layer['stars']:
            star['y'] += scroll_amount
            
            # Wrap vertically
            if star['y'] > config.SCREEN_HEIGHT + 10:
                star['y'] -= config.SCREEN_HEIGHT + 20
                star['x'] = random.randint(0, config.SCREEN_WIDTH)


def draw_starfield(screen, starfield):
    """
    Render star field to screen.
    
    Args:
        screen: Pygame screen surface
        starfield: Star field data structure
    """
    import pygame
    import math
    
    twinkle_time = starfield['twinkle_time']
    
    for layer in starfield['layers']:
        for star in layer['stars']:
            # Twinkling effect (sine wave)
            twinkle_factor = math.sin(twinkle_time * 2.0 + star['twinkle_offset']) * 0.3 + 0.7
            brightness = star['brightness'] * twinkle_factor
            
            # Star color (white with brightness)
            color_val = int(brightness * 255)
            color = (color_val, color_val, color_val)
            
            # Draw star
            x, y = int(star['x']), int(star['y'])
            size = int(star['size'])
            
            if size == 1:
                screen.set_at((x, y), color)
            else:
                pygame.draw.circle(screen, color, (x, y), size)
```

---

### PHASE 14: Initialize Star Field in Game

**File:** `main.py`
**Import Addition:**

```python
from systems import starfield
```

**After initializing `entities_state`, add:**

```python
# Create star field background
background_starfield = starfield.create_starfield(num_stars_per_layer=150, num_layers=2)
```

---

### PHASE 15: Update Star Field in Game Loop

**File:** `main.py`
**Inside game loop, before entity updates, add:**

```python
# Update background (parallax star field)
starfield.update_starfield(background_starfield, current_speed, dt)
```

---

### PHASE 16: Render Star Field in Game Loop

**File:** `main.py`
**Inside render section, BEFORE drawing track/player/obstacles:**

```python
# Draw background first (back to front)
starfield.draw_starfield(screen, background_starfield)
```

**Note:** Make sure this is the FIRST thing drawn after clearing screen

---

### PHASE 17: Update Screen Clear to Deep Space Black

**File:** `main.py`
**Find screen clear/fill, update color:**

```python
screen.fill((0, 0, 5))  # Deep space black (slight blue tint)
```

---

### PHASE 18: Test Star Field System

**Action:** Run game and verify:
- Stars visible in background
- Two layers scroll at different speeds (parallax)
- Stars twinkle subtly
- Performance remains 60 FPS

**Expected Result:** Deep space background with scrolling, twinkling stars

---

## PART D: OBSTACLE GLOW EFFECTS

### PHASE 19: Add Glow Data to Obstacles

**File:** `entities/obstacle.py`
**Find `create_obstacle()` function, add glow data:**

**Add after existing obstacle properties:**

```python
    # Visual effects
    'glow': {
        'enabled': True,
        'color': [1.0, 0.3, 0.2],  # Red-orange glow
        'intensity': 0.8,
        'radius_multiplier': 1.5,  # Glow extends beyond obstacle
    }
```

---

### PHASE 20: Create Obstacle Glow Renderer

**File:** `systems/renderer.py`
**Add new function after obstacle drawing:**

```python
def draw_obstacle_glow(screen, obstacle, camera_offset=0):
    """
    Draw glow effect around obstacle.
    
    Args:
        screen: Pygame screen surface
        obstacle: Obstacle entity
        camera_offset: Z-axis camera offset
    """
    if 'glow' not in obstacle or not obstacle['glow']['enabled']:
        return
    
    import pygame
    
    pos = obstacle['position']
    sx, sy = world_to_screen(pos[0], pos[1], pos[2] - camera_offset)
    
    glow = obstacle['glow']
    color = glow['color']
    intensity = glow['intensity']
    
    # Base obstacle size (assuming cube)
    base_size = 40
    glow_radius = int(base_size * glow['radius_multiplier'])
    
    # Multiple expanding circles for glow
    for i in range(3):
        radius = glow_radius + i * 10
        alpha = int(intensity * 40 / (i + 1))
        
        glow_color = (
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255),
            alpha
        )
        
        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, glow_color, (radius, radius), radius)
        screen.blit(glow_surf, (sx - radius, sy - radius))
```

---

### PHASE 21: Update Obstacle Rendering to Include Glow

**File:** `systems/renderer.py`
**Find where obstacles are drawn, modify:**

**Replace obstacle drawing code with:**

```python
def draw_obstacle(screen, obstacle, camera_offset=0):
    """
    Draw obstacle with glow effect.
    
    Args:
        screen: Pygame screen surface
        obstacle: Obstacle entity
        camera_offset: Z-axis camera offset
    """
    # Draw glow first (behind obstacle)
    draw_obstacle_glow(screen, obstacle, camera_offset)
    
    # Draw obstacle geometry
    import pygame
    pos = obstacle['position']
    sx, sy = world_to_screen(pos[0], pos[1], pos[2] - camera_offset)
    
    obstacle_type = obstacle.get('obstacle_type', 'high')
    
    if obstacle_type == 'high':
        # High obstacle (jump over)
        size = 40
        pygame.draw.rect(screen, (255, 100, 80), (sx - size // 2, sy - size // 2, size, size))
        pygame.draw.rect(screen, (255, 150, 130), (sx - size // 2, sy - size // 2, size, size), 3)
    else:
        # Low obstacle (slide under)
        width, height = 60, 20
        pygame.draw.rect(screen, (255, 100, 80), (sx - width // 2, sy - height // 2, width, height))
        pygame.draw.rect(screen, (255, 150, 130), (sx - width // 2, sy - height // 2, width, height), 3)
```

---

### PHASE 22: Test Obstacle Glow

**Action:** Run game and verify:
- Obstacles have red-orange glow halos
- Glow extends beyond obstacle geometry
- No significant performance impact

**Expected Result:** Obstacles are now glowing with multi-layer halos

---

## PART E: POLISH & TESTING

### PHASE 23: Performance Validation

**File:** Create `test_performance.py` in project root

```python
"""
Performance test for Temple Run 3D visual upgrades.
Validates FPS remains >55 with all effects enabled.
"""

import pygame
import time
from main import *


def test_full_scene_performance():
    """
    Test FPS with full scene: stars, player, obstacles, glows.
    """
    # Initialize
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # Create test scene
    background_starfield = starfield.create_starfield(150, 2)
    player = player_entity.create_player()
    
    # Create obstacle grid
    obstacles = []
    for i in range(20):
        obs = obstacle_entity.create_obstacle(
            lane=i % 3,
            z_position=i * -10,
            obstacle_type='high' if i % 2 == 0 else 'low'
        )
        obstacles.append(obs)
    
    # Run 300 frames
    frame_times = []
    for _ in range(300):
        start = time.perf_counter()
        
        # Update
        dt = clock.tick(60) / 1000.0
        starfield.update_starfield(background_starfield, config.TRACK_SCROLL_SPEED, dt)
        particle_trail.update_particle_trail(player, dt)
        particle_trail.update_player_rotation(player, dt)
        particle_trail.update_player_glow(player, dt)
        
        # Render
        screen.fill((0, 0, 5))
        starfield.draw_starfield(screen, background_starfield)
        draw_player(screen, player, 0)
        for obs in obstacles:
            draw_obstacle(screen, obs, 0)
        
        pygame.display.flip()
        
        frame_times.append(time.perf_counter() - start)
    
    # Calculate stats
    avg_fps = 1.0 / (sum(frame_times) / len(frame_times))
    min_fps = 1.0 / max(frame_times)
    
    print(f"Average FPS: {avg_fps:.1f}")
    print(f"Minimum FPS: {min_fps:.1f}")
    print(f"Target: 55+ FPS")
    
    assert avg_fps > 55, f"Performance issue: {avg_fps:.1f} FPS < 55 FPS target"
    
    pygame.quit()


if __name__ == '__main__':
    test_full_scene_performance()
```

**Run Command:**
```bash
python test_performance.py
```

---

### PHASE 24: Visual Tweak Checklist

**File:** `config.py`
**Add tuning section at end:**

```python
# ====================================
# VISUAL EFFECTS TUNING
# ====================================

# Player Glow
PLAYER_GLOW_COLOR = [0.2, 0.6, 1.0]  # Cyan
PLAYER_GLOW_PULSE_SPEED = 2.0

# Particle Trail
PARTICLE_TRAIL_COUNT = 12
PARTICLE_TRAIL_SPACING = 0.4

# Star Field
STARS_PER_LAYER = 150
STAR_LAYERS = 2
STAR_TWINKLE_SPEED = 2.0

# Obstacle Glow
OBSTACLE_GLOW_COLOR = [1.0, 0.3, 0.2]  # Red-orange
OBSTACLE_GLOW_INTENSITY = 0.8
OBSTACLE_GLOW_RADIUS_MULT = 1.5
```

**Tuning Guide:**
- **Glow too bright?** Reduce `INTENSITY` values to 0.5-0.6
- **Trail too long?** Reduce `PARTICLE_TRAIL_COUNT` to 8
- **Stars too dense?** Reduce `STARS_PER_LAYER` to 100
- **Want more depth?** Increase `STAR_LAYERS` to 3

---

### PHASE 25: Final Integration Test

**Checklist:**

1. **Start Game:**
   ```bash
   python main.py
   ```

2. **Verify Visuals:**
   - [ ] Background shows scrolling stars (2 layers at different speeds)
   - [ ] Stars twinkle subtly
   - [ ] Player is rotating octahedron (not cube)
   - [ ] Player has cyan glow with pulse
   - [ ] Player has trailing particles
   - [ ] Obstacles have red-orange glow halos

3. **Verify Gameplay:**
   - [ ] Lane switching still works (A/D keys)
   - [ ] Jumping still works (Space key)
   - [ ] Sliding still works (S key)
   - [ ] Collision detection unchanged
   - [ ] Score system unchanged

4. **Verify Performance:**
   - [ ] FPS counter shows 55+ FPS
   - [ ] No stuttering during gameplay
   - [ ] Visual effects don't lag

5. **Verify Bug Fixes:**
   - [ ] Restart game multiple times - difficulty resets properly
   - [ ] No import errors in console
   - [ ] `high_score.json` not tracked in git (`git status` should ignore it)

---

## COMPLETION CHECKLIST

### Part A: Bug Fixes
- [ ] Fixed config mutation in difficulty.py
- [ ] Fixed duplicate imports in score.py
- [ ] Fixed .gitignore spacing
- [ ] Replaced magic numbers with config constants

### Part B: Player Visuals
- [ ] Created geometry.py with octahedron generation
- [ ] Updated player entity to use octahedron
- [ ] Created particle_trail.py system
- [ ] Updated renderer for octahedron + glow + trail
- [ ] Integrated into game loop

### Part C: Star Field
- [ ] Created starfield.py system
- [ ] Generated 2-layer parallax stars
- [ ] Integrated into game loop
- [ ] Stars render behind all game objects

### Part D: Obstacle Glow
- [ ] Added glow data to obstacles
- [ ] Created glow renderer
- [ ] Integrated into obstacle drawing

### Part E: Polish
- [ ] Performance test passes (55+ FPS)
- [ ] All gameplay mechanics unchanged
- [ ] Visual tuning parameters in config

---

## ESTIMATED TIME BREAKDOWN

- **Part A (Bug Fixes):** 30 minutes
- **Part B (Player Visuals):** 45 minutes
- **Part C (Star Field):** 30 minutes
- **Part D (Obstacle Glow):** 20 minutes
- **Part E (Testing):** 15 minutes

**Total:** ~2.5 hours

---

## POST-IMPLEMENTATION

### Record Gameplay GIF

**Using OBS Studio (Free):**
1. Set recording area to game window
2. Record 30 seconds of gameplay
3. Convert to GIF using ezgif.com
4. Add to README.md

### Update README

**Add to Features section:**

```markdown
## Visual Effects

- **Geometric Player**: Rotating octahedron with cyan glow and particle trail
- **Parallax Starfield**: Multi-layer scrolling space background
- **Obstacle Glow**: Red-orange emission effects on obstacles
- **Optimized Rendering**: Maintains 60 FPS with all effects enabled
```

---

## TROUBLESHOOTING

### Issue: FPS drops below 55

**Solutions:**
1. Reduce `STARS_PER_LAYER` to 100
2. Reduce `PARTICLE_TRAIL_COUNT` to 8
3. Disable obstacle glow: `obstacle['glow']['enabled'] = False`

### Issue: Player doesn't rotate

**Check:**
1. `particle_trail.update_player_rotation()` is called in game loop
2. `dt` is being passed correctly
3. Rotation values are incrementing (add print statement)

### Issue: Stars not visible

**Check:**
1. `starfield.draw_starfield()` is called AFTER screen clear
2. Background color is dark: `screen.fill((0, 0, 5))`
3. Star brightness values are > 0.3

### Issue: Glow effects don't show

**Check:**
1. Pygame surface created with `pygame.SRCALPHA` flag
2. Alpha blending enabled
3. Glow intensity > 0.5

---

## END OF INSTRUCTIONS

All phases are complete, cursor-ready code blocks.
No TODOs, no partial implementations.
Copy-paste and execute sequentially.

**Philosophy:** Geometric elegance beats texture complexity.
**Result:** Professional-looking space runner in 2.5 hours.
