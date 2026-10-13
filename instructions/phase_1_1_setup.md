# PHASE 1.1: PROJECT SETUP & CONFIGURATION

## WHY

Before we can build anything, we need a stable foundation. This phase establishes:
- Python environment with Ursina installed
- Project directory structure
- Configuration file with ALL constants (zero magic numbers in code)
- Empty game window to verify Ursina works

**Critical Insight:** We're setting up for *arcade logic*, not physics simulation. The config values reflect this: discrete lane positions, animation durations, not gravity/velocity.

---

## WHAT (Deliverables)

By the end of this phase, you will have:
1. Working Ursina installation
2. Clean project structure (`temple_run_arcade/` directory)
3. `config.py` with all game constants
4. `main.py` that opens an empty window
5. Verification that Ursina works on your system

---

## HOW (Architecture)

### Directory Structure
```
temple_run_arcade/
├── main.py              # Entry point, game loop
├── config.py            # ALL constants
├── .cursorrules         # Coding standards (copy from instructions)
├── systems/
│   └── __init__.py
├── entities/
│   └── __init__.py
└── utils/
    └── __init__.py
```

### Architectural Decisions

**config.py Design:**
- **Lane System**: Discrete X positions (-2.0, 0.0, 2.0 for left/mid/right)
- **Animation Timing**: Duration-based, not velocity-based (jump is 0.5s, not jump force)
- **World Space**: Z-axis is "forward" direction (toward player = decreasing Z)
- **Colors**: RGB tuples using Ursina's color module

**main.py Design:**
- Minimal for now: just initialize Ursina and open window
- Game state will be added in Phase 6
- Input handling will be added as features are built

---

## UX (User Experience)

**What the User Sees:**
- Running `python main.py` opens a window
- Window is 1280x720, titled "Temple Run 3D - Arcade"
- Background is dark blue-purple (low-poly aesthetic)
- Window is responsive (can be closed with X button or ESC key)
- No errors in console

**What the User Feels:**
- "The game is launching correctly"
- "The environment is stable"
- Confidence to proceed

---

## TASK (Step-by-Step Instructions)

### Step 1: Install Ursina

Open terminal and run:
```bash
pip install ursina
```

**Verify installation:**
```bash
python -c "from ursina import *; print('Ursina installed successfully')"
```

**Expected output:** "Ursina installed successfully"

**If it fails:**
- Make sure Python 3.8+ is installed: `python --version`
- Try `pip3 install ursina` if you have multiple Python versions
- On some systems: `python3 -m pip install ursina`

---

### Step 2: Create Project Directory

Create folder structure:
```bash
mkdir temple_run_arcade
cd temple_run_arcade

mkdir systems
mkdir entities
mkdir utils

touch systems/__init__.py
touch entities/__init__.py
touch utils/__init__.py
```

**On Windows:**
```cmd
mkdir temple_run_arcade
cd temple_run_arcade
mkdir systems entities utils
type nul > systems\__init__.py
type nul > entities\__init__.py
type nul > utils\__init__.py
```

---

### Step 3: Create config.py

Create `config.py` with the following content:

```python
"""
Temple Run 3D - Arcade Logic Edition
Configuration & Constants

All magic numbers live here. NEVER hardcode values in game logic.
"""

from ursina import color

# ==========================================
# WINDOW SETTINGS
# ==========================================
WINDOW_TITLE = "Temple Run 3D - Arcade"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TARGET_FPS = 60

# ==========================================
# COLORS (Low-Poly Aesthetic)
# ==========================================
# Background & Environment
COLOR_BACKGROUND = color.rgb(20, 20, 35)      # Dark blue-purple void
COLOR_TRACK = color.rgb(40, 40, 60)           # Track surface
COLOR_GRID_LINES = color.rgba(0, 255, 255, 50)  # Cyan grid (transparent)

# Player
COLOR_PLAYER = color.cyan                     # Bright cyan cube

# Obstacles
COLOR_OBS_LOW = color.yellow                  # Jump over these
COLOR_OBS_HIGH = color.red                    # Slide under these
COLOR_OBS_MOVING = color.orange               # Avoid these

# Collectibles
COLOR_ORB = color.gold                        # Score points
COLOR_SHIELD = color.azure                    # Temporary invincibility

# UI
COLOR_UI_TEXT = color.white
COLOR_UI_SCORE = color.cyan
COLOR_UI_WARNING = color.red

# ==========================================
# LANE SYSTEM (Arcade Logic)
# ==========================================
LANE_COUNT = 3
LANE_POSITIONS = [-2.0, 0.0, 2.0]            # X positions for left, mid, right
LANE_SWITCH_SPEED = 12.0                      # Units per second for smooth lerp
LANE_SWITCH_DURATION = 0.15                   # Seconds for lane change animation

# Starting lane (0=left, 1=center, 2=right)
PLAYER_START_LANE = 1

# ==========================================
# PLAYER SETTINGS
# ==========================================
PLAYER_SIZE = (0.8, 0.8, 0.8)                # Cube dimensions
PLAYER_START_Y = 0.5                          # Ground level height
PLAYER_START_Z = 0.0                          # Always at origin (world moves toward player)

# Jump Animation (NOT physics-based)
JUMP_DURATION = 0.5                           # Total jump time in seconds
JUMP_HEIGHT = 2.5                             # Peak height above ground

# Slide Mechanic
SLIDE_DURATION = 0.8                          # How long crouch lasts
SLIDE_HEIGHT_SCALE = 0.4                      # Player height when sliding (0.4 = 40% of normal)

# ==========================================
# CAMERA SETTINGS
# ==========================================
CAMERA_POSITION = (0, 4.0, -10.0)            # (X, Y, Z) relative to player
CAMERA_ROTATION_X = 20                        # Look down angle in degrees
CAMERA_FOLLOW_SPEED = 0.1                     # Smooth camera follow (lower = smoother)

# ==========================================
# TRACK SETTINGS
# ==========================================
TRACK_WIDTH = 10.0                            # Total width of playable area
TRACK_LENGTH = 100.0                          # How far ahead track extends
TRACK_SCROLL_SPEED = 20.0                     # Initial forward speed (units/sec)
TRACK_SCROLL_SPEED_MAX = 40.0                 # Max speed as difficulty increases

GRID_SPACING = 2.0                            # Distance between grid lines
GRID_ANIMATION_SPEED = 0.5                    # How fast grid scrolls

# ==========================================
# OBSTACLE SETTINGS
# ==========================================
OBSTACLE_SPAWN_DISTANCE = 60.0                # Z position where obstacles spawn
OBSTACLE_DESPAWN_DISTANCE = -10.0             # Z position where we destroy them
OBSTACLE_COLLISION_THRESHOLD = 1.0            # Distance for collision detection

# Obstacle Dimensions
OBS_LOW_SIZE = (1.0, 0.6, 1.0)               # Short barrier (jump over)
OBS_LOW_HEIGHT = 0.3                          # Y position

OBS_HIGH_SIZE = (1.0, 2.5, 1.0)              # Tall barrier (slide under)
OBS_HIGH_HEIGHT = 1.25                        # Y position

OBS_MOVING_SIZE = (1.0, 1.2, 1.0)            # Medium barrier (moves between lanes)
OBS_MOVING_HEIGHT = 0.6                       # Y position
OBS_MOVING_SPEED = 2.0                        # Lateral movement speed

# Spawn Timing
SPAWN_INTERVAL_MIN = 0.8                      # Minimum time between spawns (seconds)
SPAWN_INTERVAL_MAX = 1.5                      # Maximum time between spawns
SPAWN_INTERVAL_DECREASE = 0.95                # Multiplier per difficulty increase

# ==========================================
# COLLECTIBLE SETTINGS
# ==========================================
COLLECTIBLE_SIZE = 0.5                        # Sphere radius
COLLECTIBLE_HEIGHT = 0.8                      # Y position (floating above ground)
COLLECTIBLE_SPAWN_CHANCE = 0.6                # 60% chance to spawn with obstacle

# Collectible Types
ORB_POINTS = 100                              # Points per orb
SHIELD_DURATION = 5.0                         # Invincibility time in seconds
SHIELD_SPAWN_CHANCE = 0.15                    # 15% of collectibles are shields

# ==========================================
# SCORING & PROGRESSION
# ==========================================
SCORE_PER_DISTANCE = 10                       # Points per unit traveled
SCORE_SURVIVAL_RATE = 10.0                    # Points per second survived

# Difficulty Ramping
DIFFICULTY_DISTANCE_THRESHOLD = 500.0         # Distance before speed increase
DIFFICULTY_SPEED_INCREMENT = 2.0              # Speed increase per threshold
DIFFICULTY_SPAWN_RATE_MULTIPLIER = 0.95       # Spawn faster over time

# ==========================================
# VISUAL EFFECTS
# ==========================================
SCREEN_SHAKE_DURATION = 0.3                   # Shake time on collision
SCREEN_SHAKE_INTENSITY = 0.8                  # Shake magnitude

PARTICLE_LIFETIME = 0.2                       # How long particles exist
PARTICLE_SPAWN_RATE = 0.05                    # Seconds between particle spawns

# ==========================================
# DEBUG SETTINGS
# ==========================================
DEBUG_MODE = False                            # Show debug info
DEBUG_SHOW_COLLISION_BOXES = False            # Show collision boundaries
DEBUG_SHOW_LANE_MARKERS = False               # Show lane positions
```

**Important:** Notice everything is explicitly defined. No magic numbers allowed in game code.

---

### Step 4: Create main.py

Create `main.py` with minimal initialization:

```python
"""
Temple Run 3D - Arcade Logic Edition
Main Entry Point

This is a 3D endless runner using ARCADE LOGIC:
- Discrete lane system (no free X movement)
- Animation-based mechanics (no physics simulation)
- Math-based collision (deterministic and testable)
"""

from ursina import *
import config

# ==========================================
# INITIALIZATION
# ==========================================
def init_game():
    """Initialize Ursina and configure window."""
    app = Ursina()
    
    # Window setup
    window.title = config.WINDOW_TITLE
    window.size = (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    window.color = config.COLOR_BACKGROUND
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    window.fps_counter.enabled = config.DEBUG_MODE
    
    print(f"[INIT] {config.WINDOW_TITLE}")
    print(f"[INIT] Window: {config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
    print(f"[INIT] Ursina initialized successfully")
    
    return app

# ==========================================
# GAME LOOP
# ==========================================
def update():
    """
    Called every frame by Ursina.
    Game logic will be added in future phases.
    """
    pass

def input(key):
    """
    Handle keyboard input.
    Controls will be added in future phases.
    """
    if key == 'escape':
        print("[INPUT] ESC pressed - Exiting game")
        quit()

# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == '__main__':
    app = init_game()
    
    print("[READY] Game window opened")
    print("[READY] Press ESC to exit")
    
    app.run()
```

---

### Step 5: Copy .cursorrules

Copy the `.cursorrules` file (provided in instructions) to the project root:

```bash
cp /path/to/.cursorrules ./
```

This file contains all coding standards and architectural rules. Read it before writing any code.

---

### Step 6: Test the Setup

Run the game:
```bash
python main.py
```

**You should see:**
- Window opens (1280x720)
- Title: "Temple Run 3D - Arcade"
- Background: Dark blue-purple color
- Console prints initialization messages
- Pressing ESC closes the window

**Console output should look like:**
```
[INIT] Temple Run 3D - Arcade
[INIT] Window: 1280x720
[INIT] Ursina initialized successfully
[READY] Game window opened
[READY] Press ESC to exit
```

---

## ACCEPTANCE CRITERIA

Before proceeding to Phase 1.2, verify ALL of these:

### Functional
- [ ] Running `python main.py` opens a window without errors
- [ ] Window is 1280x720 pixels
- [ ] Window title is "Temple Run 3D - Arcade"
- [ ] Background color is dark blue-purple
- [ ] Pressing ESC closes the window cleanly
- [ ] Console shows initialization messages

### Technical
- [ ] Ursina is installed and imports successfully
- [ ] `config.py` exists with all constants defined
- [ ] `main.py` exists and runs without errors
- [ ] Directory structure matches specification
- [ ] `.cursorrules` file is in project root
- [ ] No syntax errors in any file

### Code Quality
- [ ] All imports are at top of file
- [ ] Constants use SCREAMING_SNAKE_CASE
- [ ] Functions have docstrings
- [ ] Code follows .cursorrules standards
- [ ] No hardcoded values (all in config.py)

### Visual
- [ ] Window opens in reasonable time (< 2 seconds)
- [ ] Window can be moved and resized
- [ ] Close button (X) works
- [ ] No visual glitches or flickering

---

## TROUBLESHOOTING

### Problem: "ModuleNotFoundError: No module named 'ursina'"
**Solution:** Ursina not installed. Run `pip install ursina`

### Problem: Window doesn't open
**Solution:** 
1. Check Python version: `python --version` (needs 3.8+)
2. Check for other errors in console
3. Try running with `python3 main.py` instead

### Problem: Window opens then crashes
**Solution:**
1. Check console for error message
2. Verify config.py has no syntax errors: `python -m py_compile config.py`
3. Verify imports are correct

### Problem: Colors look wrong
**Solution:** Make sure you imported `from ursina import color` in config.py

---

## NEXT PHASE

Once all acceptance criteria pass, proceed to **Phase 1.2: Player Lane System**.

In Phase 1.2, we'll add:
- Player cube entity
- Lane switching (left/right input)
- Smooth visual lerping between lanes
- Fixed camera following player

---

**STATUS:** [ ] PHASE 1.1 COMPLETE

(Check this box once all acceptance criteria are verified)
