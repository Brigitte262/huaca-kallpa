# PHASE 1.3: TRACK & CAMERA

## WHY

In arcade-style endless runners, the **player stays still and the world moves toward them**. This is critical because:
1. **Prevents float precision errors** (player doesn't travel thousands of units)
2. **Simplifies collision math** (everything is relative to player at Z=0)
3. **Makes spawning predictable** (always spawn at fixed Z distance ahead)

This phase creates:
- Infinite scrolling track with grid lines
- Camera that smoothly follows player's lane position
- Visual sense of forward movement

**Key Insight:** The player's Z position never changes. The track and all obstacles scroll toward the player (decreasing Z).

---

## WHAT (Deliverables)

By the end of this phase, you will have:
1. A dark track plane extending far ahead
2. Cyan grid lines that scroll toward the player
3. Infinite scrolling effect (no visible seams)
4. Camera that follows player's X position when switching lanes
5. Clear sense of forward movement

---

## HOW (Architecture)

### Track Design

The track is a flat plane with:
- **Width**: 10 units (wide enough for 3 lanes plus margins)
- **Length**: 100 units (extends far ahead)
- **Position**: Centered at Z=50 (extends from Z=0 to Z=100)

The grid is a **scrolling texture** effect:
- Horizontal lines perpendicular to movement
- Offset updates each frame to create scrolling
- When offset wraps around, creates infinite effect

### Camera Follow

The camera has two behaviors:
1. **Fixed Y and Z**: Always at (0, 4, -10) relative to player
2. **Smooth X follow**: Lerps toward player's visual X position

This creates a nice "tilt" effect when switching lanes without being disorienting.

### World Coordinate System

```
     Z (Forward)
     ^
     |
     |  [Track extends forward]
     |
     +---------> X (Lanes)
    /
   / Y (Up)
  v

Player is at origin (0, 0.5, 0)
Track extends from Z=0 to Z=100
Obstacles will spawn at Z=60 and move toward Z=0
```

---

## UX (User Experience)

**What the User Sees:**
- Dark purple-blue track plane stretches into the distance
- Cyan grid lines scroll toward the player continuously
- Grid lines appear infinite (no pop-in or seams)
- When switching lanes, camera smoothly tilts to follow
- Strong sense of "moving forward" even though player is stationary

**What the User Feels:**
- "I'm running through a digital tunnel"
- Immersion from scrolling grid
- Camera follow feels natural and cinematic

---

## TASK (Step-by-Step Instructions)

### Step 1: Create entities/track.py

Create `entities/track.py`:

```python
"""
Track Entity - Infinite Scrolling Floor

The track is a static plane with a scrolling texture effect.
The player stays at Z=0, and the texture offset updates to create movement illusion.
"""

from ursina import *
import config

class Track(Entity):
    """
    Infinite scrolling track with grid lines.
    
    The track doesn't actually move - instead, the texture offset scrolls
    to create the illusion of forward movement.
    """
    
    def __init__(self):
        super().__init__(
            model='plane',
            texture='white_cube',  # We'll use this for grid effect
            color=config.COLOR_TRACK,
            scale=(config.TRACK_WIDTH, 1, config.TRACK_LENGTH),
            position=(0, 0, config.TRACK_LENGTH / 2),  # Centered ahead of player
            rotation_x=0,  # Flat on ground
            collider=None  # We don't need collision on the track itself
        )
        
        # Texture tiling (creates grid effect)
        # X tiling: 1 (solid across width)
        # Z tiling: Based on track length and grid spacing
        grid_lines = int(config.TRACK_LENGTH / config.GRID_SPACING)
        self.texture_scale = (1, grid_lines)
        
        # Scrolling offset
        self.scroll_offset = 0.0
        
        # Grid lines (visual enhancement)
        self.create_grid_lines()
        
        print(f"[TRACK] Created with {grid_lines} grid divisions")
    
    def create_grid_lines(self):
        """
        Create visible grid lines for visual effect.
        These are thin planes that also scroll with the texture.
        """
        # We'll create a few grid line entities
        self.grid_lines = []
        
        line_count = int(config.TRACK_LENGTH / config.GRID_SPACING)
        
        for i in range(line_count):
            z_pos = i * config.GRID_SPACING
            
            line = Entity(
                model='plane',
                scale=(config.TRACK_WIDTH, 1, 0.1),
                color=config.COLOR_GRID_LINES,
                position=(0, 0.01, z_pos),  # Slightly above track to avoid z-fighting
                rotation_x=0
            )
            self.grid_lines.append(line)
    
    def update(self):
        """
        Scroll texture and grid lines.
        """
        # Update scroll offset
        scroll_speed = config.TRACK_SCROLL_SPEED * config.GRID_ANIMATION_SPEED
        self.scroll_offset += time.dt * scroll_speed
        
        # Apply texture offset (creates scrolling effect)
        self.texture_offset = (0, self.scroll_offset)
        
        # Move grid lines (for enhanced visual effect)
        for line in self.grid_lines:
            line.z -= config.TRACK_SCROLL_SPEED * time.dt
            
            # Wrap around when off-screen
            if line.z < -config.GRID_SPACING:
                line.z += config.TRACK_LENGTH
```

---

### Step 2: Create CameraController

Add camera follow logic. Create `systems/camera.py`:

```python
"""
Camera System - Smooth Follow

The camera follows the player's lane position smoothly.
Y and Z are fixed, only X position follows.
"""

from ursina import *
import config

class CameraController:
    """
    Manages camera behavior.
    
    The camera:
    - Stays at fixed Y and Z
    - Smoothly follows player's X position
    - Can apply screen shake effects (future phase)
    """
    
    def __init__(self, player):
        """
        Initialize camera controller.
        
        Args:
            player: The player entity to follow
        """
        self.player = player
        
        # Base position (no shake)
        self.base_x = 0
        self.base_y = config.CAMERA_POSITION[1]
        self.base_z = config.CAMERA_POSITION[2]
        
        # Screen shake state (for future phase)
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        
        # Set initial position
        camera.position = config.CAMERA_POSITION
        camera.rotation_x = config.CAMERA_ROTATION_X
        
        print(f"[CAMERA] Initialized at {config.CAMERA_POSITION}")
    
    def update(self):
        """
        Update camera position each frame.
        Smoothly follow player's X position.
        """
        # Calculate target X (follow player's visual position, not lane position)
        target_x = self.player.x * 0.5  # Multiply by 0.5 for subtle follow
        
        # Smooth follow
        self.base_x = lerp(
            self.base_x,
            target_x,
            time.dt * (1.0 / config.CAMERA_FOLLOW_SPEED)
        )
        
        # Apply position (shake will be added in future phase)
        camera.position = (self.base_x, self.base_y, self.base_z)
```

---

### Step 3: Update main.py

Integrate track and camera:

```python
"""
Temple Run 3D - Arcade Logic Edition
Main Entry Point
"""

from ursina import *
import config
from entities.player import Player
from entities.track import Track
from systems.camera import CameraController

# ==========================================
# GLOBAL STATE
# ==========================================
game_state = 'playing'
player = None
track = None
camera_controller = None
debug_text = None

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
    
    return app

def init_entities():
    """Create game entities."""
    global player, track, camera_controller, debug_text
    
    # Create track first (so it's behind player visually)
    track = Track()
    
    # Create player
    player = Player()
    
    # Create camera controller
    camera_controller = CameraController(player)
    
    # Debug text (if enabled)
    if config.DEBUG_MODE:
        debug_text = Text(
            text=f"Lane: {player.lane}",
            position=(-0.85, 0.45),
            scale=2,
            color=config.COLOR_UI_TEXT
        )
    
    print("[INIT] Entities created")

# ==========================================
# GAME LOOP
# ==========================================
def update():
    """
    Called every frame by Ursina.
    """
    if game_state != 'playing':
        return
    
    # Update camera
    camera_controller.update()
    
    # Update debug text
    if config.DEBUG_MODE and debug_text:
        debug_text.text = f"Lane: {player.lane}"

def input(key):
    """
    Handle keyboard input.
    """
    if key == 'escape':
        print("[INPUT] ESC pressed - Exiting game")
        quit()
    
    # Lane switching
    if game_state == 'playing':
        if key == 'a' or key == 'left arrow':
            player.switch_lane(-1)
        elif key == 'd' or key == 'right arrow':
            player.switch_lane(1)

# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == '__main__':
    app = init_game()
    init_entities()
    
    print("[READY] Game ready - Use A/D or Arrow Keys to switch lanes")
    print("[READY] Track is scrolling - Player movement creates camera follow")
    print("[READY] Press ESC to exit")
    
    app.run()
```

---

### Step 4: Update __init__ files

Update `entities/__init__.py`:
```python
"""
Entities Module
"""
from entities.player import Player
from entities.track import Track

__all__ = ['Player', 'Track']
```

Create `systems/__init__.py`:
```python
"""
Systems Module - Game Logic
"""
from systems.camera import CameraController

__all__ = ['CameraController']
```

---

### Step 5: Test Track and Camera

Run the game:
```bash
python main.py
```

**Test these aspects:**

1. **Track Visual:**
   - Dark purple track plane visible stretching ahead
   - Cyan grid lines visible on track
   - Grid lines are evenly spaced

2. **Scrolling Effect:**
   - Grid lines move toward you continuously
   - Scrolling is smooth (no stuttering)
   - Creates strong sense of forward movement
   - Grid appears infinite (no visible wrapping/seams)

3. **Camera Follow:**
   - Switch to left lane (A): Camera smoothly shifts left
   - Switch to right lane (D): Camera smoothly shifts right
   - Camera movement is smooth and cinematic
   - Camera doesn't "snap" - it lerps smoothly

4. **Player Perspective:**
   - Player cube is clearly visible
   - Camera angle (20° down) gives good view
   - Can see track ahead clearly
   - Player appears to be "running" on the track

5. **Performance:**
   - Game runs at 60 FPS (check FPS counter if DEBUG_MODE on)
   - No lag or stuttering
   - Scrolling is perfectly smooth

---

### Step 6: Adjust Feel (Optional)

If the visuals don't feel quite right, try these config adjustments:

**Grid scrolls too fast/slow:**
```python
# In config.py
GRID_ANIMATION_SPEED = 0.7  # Default: 0.5 (higher = faster)
```

**Camera follow feels too aggressive:**
```python
# In config.py
CAMERA_FOLLOW_SPEED = 0.15  # Default: 0.1 (higher = slower/smoother)
```

**Want more dramatic camera tilt:**
```python
# In systems/camera.py, update() method
target_x = self.player.x * 0.8  # Default: 0.5 (higher = more tilt)
```

**Grid lines too bright/dim:**
```python
# In config.py
COLOR_GRID_LINES = color.rgba(0, 255, 255, 80)  # Last value is alpha (0-255)
```

---

## ACCEPTANCE CRITERIA

Before proceeding to Phase 2.1, verify ALL of these:

### Functional
- [ ] Track plane is visible stretching forward
- [ ] Grid lines are visible on track
- [ ] Grid scrolls continuously toward player
- [ ] Scrolling is smooth (no stuttering)
- [ ] Camera follows player when switching lanes
- [ ] Camera movement is smooth (lerped)
- [ ] No visual seams or pop-in in grid

### Technical
- [ ] `entities/track.py` exists and imports correctly
- [ ] `systems/camera.py` exists and imports correctly
- [ ] Track uses texture scrolling for effect
- [ ] Camera uses lerp for smooth follow
- [ ] No errors in console during gameplay
- [ ] FPS stays at 60 (check if DEBUG_MODE on)

### Code Quality
- [ ] All classes have docstrings
- [ ] All methods have docstrings
- [ ] No hardcoded values (uses config.py)
- [ ] Follows .cursorrules standards
- [ ] No lines over 100 characters

### Visual
- [ ] Track color matches config (dark purple-blue)
- [ ] Grid lines are cyan with transparency
- [ ] Camera angle (20° down) gives good view
- [ ] Player is clearly visible against track
- [ ] Strong sense of forward movement
- [ ] Camera follow feels natural and cinematic

### Performance
- [ ] Game runs at 60 FPS consistently
- [ ] No frame drops during lane switching
- [ ] Grid scrolling is perfectly smooth
- [ ] Camera lerp doesn't cause stuttering

---

## TROUBLESHOOTING

### Problem: No grid lines visible
**Solution:**
1. Check `COLOR_GRID_LINES` alpha value (should be 50-100 for transparency)
2. Verify grid lines are created in `Track.__init__()`
3. Check that grid lines have `y=0.01` (above track)

### Problem: Grid scrolling is stuttering
**Solution:**
1. Check FPS counter (should be 60)
2. Verify `time.dt` is being used in scroll calculation
3. Try reducing `GRID_ANIMATION_SPEED` in config

### Problem: Camera doesn't follow player
**Solution:**
1. Verify `camera_controller.update()` is called in main `update()`
2. Check that `player` is passed to `CameraController` correctly
3. Print `camera.position` in update to debug

### Problem: Track has visible seams/wrapping
**Solution:**
1. Check that grid lines wrap when `z < -GRID_SPACING`
2. Adjust `TRACK_LENGTH` to be multiple of `GRID_SPACING`

### Problem: Camera feels "snappy" instead of smooth
**Solution:**
1. Increase `CAMERA_FOLLOW_SPEED` in config (higher = smoother but slower)
2. Check lerp is using `time.dt` correctly

---

## NEXT PHASE

Once all acceptance criteria pass, proceed to **Phase 2.1: Jump Animation System**.

In Phase 2.1, we'll add:
- Jump mechanic (animation-based, not physics)
- Parabolic arc movement
- State machine for vertical movement
- Spacebar input for jumping

---

**STATUS:** [ ] PHASE 1.3 COMPLETE

(Check this box once all acceptance criteria are verified)
