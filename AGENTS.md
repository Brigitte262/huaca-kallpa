# TEMPLE RUN 3D - ARCADE LOGIC
# Coding Standards & Architectural Rules

## PROJECT PHILOSOPHY

This is a **3D endless runner** built with **arcade logic**, not physics simulation.
- 3D visuals (Ursina engine)
- 2D state logic (discrete lanes, deterministic collision)
- Low-poly aesthetic (simple geometry, flat colors, clean design)

The code should be **procedural, explicit, and testable**. No magic. No surprises.

---

## CORE ARCHITECTURAL PRINCIPLES

### 1. ARCADE LOGIC OVER PHYSICS
- Player position is **discrete**: lane index is 0, 1, or 2 (never floating values like 0.5)
- Collision is **math-based**: `if player_lane == obstacle_lane and distance < threshold`
- No velocity vectors, no gravity variables, no raycasts
- Animations are **tweens/sequences**, not physics simulation

### 2. STATE MACHINE CLARITY
Player has exactly 3 vertical states:
- `'grounded'` - normal running
- `'jumping'` - tween animation in progress
- `'sliding'` - crouched state with timer

State transitions are **explicit and documented**:
```python
# GOOD
if player_state == 'grounded' and input_jump:
    player_state = 'jumping'
    jump_progress = 0.0

# BAD (implicit state change)
if jump_pressed:
    y += 5
```

### 3. DATA OVER CLASSES
Use **dictionaries for game entities** when it makes sense:
```python
# GOOD - Simple data structure
obstacle = {
    'lane': 1,
    'z_position': 50.0,
    'type': 'low',
    'entity': Entity(...)  # Ursina visual
}

# ACCEPTABLE - When Ursina Entity is needed
class Obstacle(Entity):
    def __init__(self, lane, z_pos, obs_type):
        super().__init__(...)
        self.lane = lane
        self.z_position = z_pos
        self.obs_type = obs_type
```

**Rule**: If it's mostly data + simple updates, use dict. If it needs complex methods or is an Ursina Entity, use class.

### 4. SEPARATION OF CONCERNS
- **main.py**: Game loop, input handling, state transitions
- **config.py**: ALL constants (no magic numbers in code)
- **entities/**: Visual components (Ursina Entities)
- **systems/**: Pure logic (spawning, collision, scoring)

---

## PYTHON STYLE GUIDE

### Naming Conventions
```python
# Variables & Functions: snake_case
player_lane = 1
current_speed = 20.0

def calculate_score(distance):
    pass

# Constants: SCREAMING_SNAKE_CASE
LANE_POSITIONS = [-2.0, 0.0, 2.0]
JUMP_DURATION = 0.5

# Classes: PascalCase (only when necessary)
class Player(Entity):
    pass
```

### Code Structure
```python
# GOOD - Clear, explicit, testable
def check_collision(player_lane, player_z, obstacles):
    """Check if player collides with any obstacle."""
    for obs in obstacles:
        if obs['lane'] == player_lane:
            distance = abs(obs['z_position'] - player_z)
            if distance < 1.0:
                return True
    return False

# BAD - Implicit, hard to test
def update():
    if hit:
        game_over = True
```

### Documentation Requirements
Every function needs:
1. **Docstring** explaining what it does
2. **Parameters** documented if not obvious
3. **Return value** documented

```python
def spawn_obstacle(lane, z_position, obs_type):
    """
    Create a new obstacle at specified position.
    
    Args:
        lane (int): Lane index (0=left, 1=center, 2=right)
        z_position (float): Z coordinate in world space
        obs_type (str): 'low', 'high', or 'moving'
    
    Returns:
        dict: Obstacle data structure with entity reference
    """
    pass
```

---

## URSINA-SPECIFIC RULES

### Entity Creation
```python
# GOOD - All parameters explicit
player = Entity(
    model='cube',
    color=color.cyan,
    scale=(0.8, 0.8, 0.8),
    position=(0, 0.5, 0),
    collider='box'
)

# BAD - Relying on defaults
player = Entity(model='cube')
```

### Update Loop Pattern
```python
def update():
    """Called every frame by Ursina."""
    if game_state != 'playing':
        return  # Early exit if not playing
    
    dt = time.dt  # Delta time
    
    # 1. Update game state
    distance += current_speed * dt
    
    # 2. Update entities
    update_player(dt)
    update_obstacles(dt)
    
    # 3. Check collisions
    if check_collision():
        trigger_game_over()
    
    # 4. Update UI
    score_text.text = f"Score: {int(score)}"
```

### Input Handling
```python
def input(key):
    """Ursina input callback."""
    if game_state == 'menu':
        if key == 'enter':
            start_game()
    
    elif game_state == 'playing':
        if key == 'a' or key == 'left arrow':
            move_player_left()
        elif key == 'd' or key == 'right arrow':
            move_player_right()
        elif key == 'space':
            player_jump()
        elif key == 's' or key == 'down arrow':
            player_slide()
    
    elif game_state == 'game_over':
        if key == 'r':
            restart_game()
    
    if key == 'escape':
        quit()
```

---

## CRITICAL IMPLEMENTATION RULES

### 1. LANE SYSTEM
```python
# Player lane is ALWAYS an integer
player_lane = 1  # 0=left, 1=center, 2=right

# Visual position can lerp smoothly
player_visual_x = lerp(player_visual_x, LANE_POSITIONS[player_lane], dt * LANE_SPEED)

# But collision checks use the INTEGER lane
if obstacle['lane'] == player_lane:
    # Collision possible
```

### 2. JUMP ANIMATION (NOT PHYSICS)
```python
# GOOD - Deterministic tween
def update_jump(dt):
    if player_state == 'jumping':
        jump_progress += dt / JUMP_DURATION  # 0.0 to 1.0
        
        # Parabolic curve: starts high, peaks, then falls
        height = 4 * jump_progress * (1 - jump_progress)
        player_y = 0.5 + height * JUMP_HEIGHT
        
        if jump_progress >= 1.0:
            player_state = 'grounded'
            player_y = 0.5
            jump_progress = 0.0

# BAD - Physics simulation
velocity_y += gravity * dt
player_y += velocity_y * dt
```

### 3. WORLD SCROLLING (NOT PLAYER MOVEMENT)
```python
# GOOD - World moves toward player
def update_obstacles(dt):
    for obs in obstacles:
        obs['z_position'] -= current_speed * dt
        obs['entity'].z = obs['z_position']

# BAD - Player moves forward (causes float precision errors at large distances)
player_z += speed * dt
```

### 4. COLLISION DETECTION
```python
# GOOD - Simple math
def check_collision(player_lane, player_state, player_z, obstacles):
    for obs in obstacles:
        # Same lane?
        if obs['lane'] != player_lane:
            continue
        
        # Close enough?
        distance = obs['z_position'] - player_z
        if distance < -1.0 or distance > 1.0:
            continue
        
        # Check if player can avoid it
        if obs['type'] == 'low' and player_state == 'jumping':
            continue  # Jumped over it
        if obs['type'] == 'high' and player_state == 'sliding':
            continue  # Slid under it
        
        return True  # Collision!
    
    return False

# BAD - Using Ursina's collision system (unreliable for moving objects)
if player.intersects().hit:
    game_over()
```

---

## TESTING REQUIREMENTS

### After Each Micro-Phase
1. **Run the game**: `python main.py`
2. **Visual test**: Does it look right?
3. **Functional test**: Does the mechanic work?
4. **Edge cases**: What breaks it?
5. **Console check**: Any errors or warnings?

### Acceptance Criteria Checklist
Every instruction file has an **ACCEPTANCE CRITERIA** section. You MUST verify ALL items before proceeding:

```
✓ Game runs without errors
✓ Player moves smoothly between lanes
✓ Jump animation completes in 0.5 seconds
✓ Obstacles spawn at correct positions
✓ Collision detection works for all obstacle types
✓ UI displays correct values
✓ No visual glitches or stuttering
```

### Lint & Code Quality
Run these checks:
```bash
# Check for syntax errors
python -m py_compile main.py

# Check for common issues (if pylint installed)
pylint main.py --disable=C0111,C0103
```

**Required Standards:**
- No syntax errors
- No undefined variables
- No unused imports
- Consistent indentation (4 spaces)
- No lines over 100 characters (except comments)

---

## DEBUGGING PROTOCOL

### When Something Breaks
1. **Read the error message** - Python errors are usually clear
2. **Check the traceback** - Find the exact line
3. **Isolate the problem** - Comment out code until it works
4. **Add print statements** - See what values variables have
5. **Test incrementally** - Don't add 50 lines without testing

### Common Mistakes to Avoid
```python
# MISTAKE 1: Forgetting to check game state
def update():
    player_x += speed  # BUG: Updates even in menu!

# FIX:
def update():
    if game_state != 'playing':
        return
    player_x += speed

# MISTAKE 2: Modifying list while iterating
for obs in obstacles:
    if obs['z_position'] < -10:
        obstacles.remove(obs)  # BUG: Skips elements

# FIX:
obstacles = [obs for obs in obstacles if obs['z_position'] >= -10]

# MISTAKE 3: Global state confusion
def reset_game():
    score = 0  # BUG: Creates local variable instead of modifying global

# FIX:
def reset_game():
    global score
    score = 0
```

---

## VISUAL POLISH GUIDELINES

### Color Palette (Low-Poly Aesthetic)
```python
# Use Ursina's color module
from ursina import color

# Primary Colors
COLOR_BACKGROUND = color.rgb(20, 20, 35)      # Dark blue-purple
COLOR_TRACK = color.rgb(40, 40, 60)           # Slightly lighter
COLOR_GRID = color.rgba(0, 255, 255, 50)      # Cyan with transparency

# Player
COLOR_PLAYER = color.cyan                     # Bright cyan

# Obstacles
COLOR_OBS_LOW = color.yellow                  # Jump over these
COLOR_OBS_HIGH = color.red                    # Slide under these
COLOR_OBS_MOVING = color.orange               # Move around these

# Collectibles
COLOR_ORB = color.gold                        # Points
COLOR_SHIELD = color.azure                    # Invincibility
```

### "Juice" Effects (Makes it feel polished)
```python
# Screen shake on collision
def trigger_shake(duration=0.3, intensity=0.8):
    global shake_timer, shake_intensity
    shake_timer = duration
    shake_intensity = intensity

# Particle trail when moving
def spawn_trail_particle(position):
    particle = Entity(
        model='cube',
        scale=0.3,
        color=color.cyan,
        position=position
    )
    # Fade out and destroy after 0.2 seconds
    particle.animate_color(color.clear, duration=0.2)
    destroy(particle, delay=0.2)

# Camera tilt when changing lanes
camera.rotation_z = player_lane * -5  # Slight tilt
```

---

## PERFORMANCE TARGETS

- **FPS**: Locked 60 (Ursina default)
- **Memory**: No leaks (destroy old obstacles/collectibles)
- **Load Time**: < 2 seconds to main menu
- **Responsiveness**: Input latency < 50ms

### Performance Checklist
```python
# GOOD - Cleanup old entities
if obstacle['z_position'] < -10:
    destroy(obstacle['entity'])
    obstacles.remove(obstacle)

# BAD - Memory leak
if obstacle['z_position'] < -10:
    obstacles.remove(obstacle)  # Entity still exists in Ursina!

# GOOD - Efficient collision check
for obs in obstacles:
    if obs['z_position'] < player_z - 5:
        break  # No need to check further back

# BAD - Checking every obstacle
for obs in all_obstacles_ever_spawned:
    check_collision(obs)
```

---

## FILE STRUCTURE REQUIREMENTS

```
temple_run_arcade/
├── main.py              # Entry point, game loop, input
├── config.py            # ALL constants
├── systems/
│   ├── __init__.py
│   ├── spawner.py       # Obstacle/collectible spawning logic
│   ├── collision.py     # Collision detection logic
│   └── scoring.py       # Score calculation
├── entities/
│   ├── __init__.py
│   ├── player.py        # Player entity (Ursina class)
│   ├── track.py         # Track entity (scrolling floor)
│   ├── obstacle.py      # Obstacle entity
│   └── collectible.py   # Collectible entity
└── utils/
    ├── __init__.py
    └── effects.py       # Visual effects (shake, particles)
```

---

## FINAL QUALITY GATES

Before marking a phase as COMPLETE, verify:

**Functional:**
- [ ] Code runs without errors
- [ ] All features work as specified
- [ ] No obvious bugs or glitches

**Technical:**
- [ ] No syntax errors
- [ ] No undefined variables
- [ ] Consistent naming conventions
- [ ] All functions have docstrings
- [ ] No code over 100 chars per line

**Visual:**
- [ ] Game runs at 60 FPS
- [ ] Colors match palette
- [ ] Animations are smooth
- [ ] UI is readable

**Architectural:**
- [ ] Follows arcade logic principles
- [ ] State management is explicit
- [ ] Collision is math-based, not physics
- [ ] Constants in config.py, not hardcoded

---

## REMEMBER

This game is **deterministic by design**. Every collision, every animation, every spawn is **predictable and testable**. If something feels "floaty" or "random," you've probably introduced physics where there should be logic.

**When in doubt:**
1. Is this state machine-based? (Good)
2. Is this math-based? (Good)
3. Is this physics-based? (Bad)

Build it clean. Build it solid. Build it arcade-style.

🎮 Let's make something great.
