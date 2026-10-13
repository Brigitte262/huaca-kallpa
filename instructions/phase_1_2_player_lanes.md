# PHASE 1.2: PLAYER LANE SYSTEM

## WHY

The lane system is the **core of arcade logic**. Unlike physics-based games where the player can move anywhere, our player exists in exactly 3 discrete positions (lanes). This makes collision detection deterministic and bug-free.

**Key Insight:** The player's *logical* position (lane index 0, 1, or 2) is separate from the *visual* position (smooth X coordinate). The game logic uses the discrete lane, the visuals use smooth lerping.

This phase implements:
- Player cube entity
- Discrete lane state (0, 1, or 2)
- Smooth visual transitions between lanes
- Keyboard input for lane switching

---

## WHAT (Deliverables)

By the end of this phase, you will have:
1. A cyan player cube visible on screen
2. Lane switching with A/D or Arrow keys
3. Smooth animation between lanes
4. Player cannot move beyond lane boundaries
5. Debug text showing current lane (if DEBUG_MODE enabled)

---

## HOW (Architecture)

### State Management

**Player has TWO position values:**
```python
player_lane = 1           # LOGIC: 0, 1, or 2 (discrete)
player_visual_x = 0.0     # VISUAL: Smooth position for rendering
```

**Why separate?**
- Collision checks use `player_lane` (integer comparison)
- Rendering uses `player_visual_x` (smooth lerp)
- This prevents "half in lane" collision bugs

### Input Handling

```
User presses A/Left → player_lane -= 1 (if valid)
User presses D/Right → player_lane += 1 (if valid)
Every frame: player_visual_x lerps toward LANE_POSITIONS[player_lane]
```

### Lane Boundaries

Player lane must stay in valid range:
- Lane 0 = left lane
- Lane 1 = center lane
- Lane 2 = right lane

Attempting to move left from lane 0 = nothing happens
Attempting to move right from lane 2 = nothing happens

---

## UX (User Experience)

**What the User Sees:**
- Cyan cube appears in center of screen
- Pressing A or Left Arrow: cube smoothly slides left
- Pressing D or Right Arrow: cube smoothly slides right
- Movement feels responsive and precise
- Cannot move "off the edge" (stays in 3 lanes)

**What the User Feels:**
- Tight, responsive controls
- "I'm locked into lanes, like Subway Surfers"
- Confident they can precisely control position

**Debug Mode (if enabled):**
- Text at top showing "Lane: 1" (updates when switching)

---

## TASK (Step-by-Step Instructions)

### Step 1: Create entities/player.py

Create `entities/player.py`:

```python
"""
Player Entity - Arcade Lane System

The player is a cube that exists in one of three discrete lanes.
Visual position smoothly lerps between lanes, but game logic uses discrete lane index.
"""

from ursina import *
import config

class Player(Entity):
    """
    Player entity with arcade-style lane switching.
    
    The player has:
    - Discrete lane position (0, 1, or 2)
    - Smooth visual position (lerped X coordinate)
    - Vertical state (for future jump/slide mechanics)
    """
    
    def __init__(self):
        super().__init__(
            model='cube',
            color=config.COLOR_PLAYER,
            scale=config.PLAYER_SIZE,
            position=(
                config.LANE_POSITIONS[config.PLAYER_START_LANE],
                config.PLAYER_START_Y,
                config.PLAYER_START_Z
            ),
            collider='box'  # For future collision detection
        )
        
        # Lane State (DISCRETE)
        self.lane = config.PLAYER_START_LANE  # 0, 1, or 2
        
        # Visual State (SMOOTH)
        self.target_x = config.LANE_POSITIONS[self.lane]
        
        # Vertical State (for future phases)
        self.vertical_state = 'grounded'  # grounded, jumping, sliding
        
        print(f"[PLAYER] Initialized at lane {self.lane}")
    
    def switch_lane(self, direction):
        """
        Attempt to switch lanes.
        
        Args:
            direction (int): -1 for left, +1 for right
        """
        new_lane = self.lane + direction
        
        # Check boundaries
        if new_lane < 0 or new_lane >= config.LANE_COUNT:
            print(f"[PLAYER] Cannot move to lane {new_lane} (out of bounds)")
            return
        
        # Valid move
        self.lane = new_lane
        self.target_x = config.LANE_POSITIONS[self.lane]
        
        print(f"[PLAYER] Switched to lane {self.lane}")
    
    def update(self):
        """
        Called every frame by Ursina.
        Smoothly lerp visual position toward target lane position.
        """
        # Smooth lane transition
        self.x = lerp(self.x, self.target_x, time.dt * config.LANE_SWITCH_SPEED)
```

---

### Step 2: Update main.py

Modify `main.py` to create player and handle input:

```python
"""
Temple Run 3D - Arcade Logic Edition
Main Entry Point
"""

from ursina import *
import config
from entities.player import Player

# ==========================================
# GLOBAL STATE
# ==========================================
game_state = 'playing'  # For now, always playing (menu in Phase 6)
player = None
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
    print(f"[INIT] Ursina initialized successfully")
    
    return app

def init_entities():
    """Create game entities."""
    global player, debug_text
    
    # Create player
    player = Player()
    
    # Debug text (if enabled)
    if config.DEBUG_MODE:
        debug_text = Text(
            text=f"Lane: {player.lane}",
            position=(-0.85, 0.45),
            scale=2,
            color=config.COLOR_UI_TEXT
        )
    
    # Camera setup
    camera.position = config.CAMERA_POSITION
    camera.rotation_x = config.CAMERA_ROTATION_X
    
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
    
    # Lane switching (only in playing state)
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
    print("[READY] Press ESC to exit")
    
    app.run()
```

---

### Step 3: Update entities/__init__.py

Make the Player class easily importable:

```python
"""
Entities Module
Contains all game entity classes.
"""

from entities.player import Player

__all__ = ['Player']
```

---

### Step 4: Test Lane Switching

Run the game:
```bash
python main.py
```

**Test these actions:**

1. **Visual Check:**
   - Cyan cube appears in center of screen
   - Cube is 0.8 units in size
   - Camera is angled down looking at player

2. **Left Movement:**
   - Press A or Left Arrow
   - Cube smoothly slides to left lane
   - Pressing again does nothing (already at leftmost)

3. **Right Movement:**
   - Press D or Right Arrow (from center)
   - Cube smoothly slides to right lane
   - Pressing again does nothing (already at rightmost)

4. **Rapid Switching:**
   - Rapidly press A and D
   - Movement should feel responsive (no lag)
   - Player should always complete the transition smoothly

5. **Debug Mode (if enabled in config.py):**
   - Set `DEBUG_MODE = True` in config.py
   - Re-run game
   - Top-left text shows current lane number
   - Updates when you switch lanes

6. **Console Output:**
   ```
   [PLAYER] Initialized at lane 1
   [PLAYER] Switched to lane 0
   [PLAYER] Cannot move to lane -1 (out of bounds)
   ```

---

### Step 5: Verify Smooth Movement

**The lerping should feel:**
- Smooth (no stuttering or popping)
- Responsive (starts moving immediately when key pressed)
- Quick (completes in ~0.15 seconds)

**If movement feels slow or janky:**
- Check `LANE_SWITCH_SPEED` in config.py (default: 12.0)
- Higher value = faster transition
- Lower value = smoother but slower

**Recommended values:**
- 12.0 = Good balance (default)
- 15.0 = Very snappy (arcade feel)
- 8.0 = Smooth and floaty

---

### Step 6: Test Edge Cases

**Edge Case 1: Spam A at left edge**
```
Actions: Start at lane 1, press A twice quickly, spam A
Expected: Moves to lane 0, stays at lane 0, console shows "out of bounds"
```

**Edge Case 2: Alternating presses mid-transition**
```
Actions: Press D, then immediately press A before transition completes
Expected: Player smoothly reverses direction, no glitching
```

**Edge Case 3: Hold down key**
```
Actions: Hold D key down continuously
Expected: Player moves to lane 2, stays there (doesn't repeat)
```

---

## ACCEPTANCE CRITERIA

Before proceeding to Phase 1.3, verify ALL of these:

### Functional
- [ ] Player cube is visible on screen
- [ ] Player is cyan colored
- [ ] Pressing A/Left moves player left
- [ ] Pressing D/Right moves player right
- [ ] Player cannot move beyond left edge (lane 0)
- [ ] Player cannot move beyond right edge (lane 2)
- [ ] Lane transitions are smooth (no popping)
- [ ] Lane transitions complete in < 0.2 seconds

### Technical
- [ ] `entities/player.py` exists and imports correctly
- [ ] Player class inherits from Ursina Entity
- [ ] Player has discrete `lane` attribute (integer 0-2)
- [ ] Player has smooth `target_x` for visual lerping
- [ ] `switch_lane()` method validates boundaries
- [ ] Console logs lane switches (if DEBUG_MODE on)
- [ ] No errors in console during gameplay

### Code Quality
- [ ] Player class has docstrings
- [ ] All methods have docstrings
- [ ] No hardcoded values (uses config.py)
- [ ] Follows .cursorrules naming conventions
- [ ] No lines over 100 characters

### Visual
- [ ] Player is centered in viewport
- [ ] Camera angle shows player clearly
- [ ] Lane positions look evenly spaced
- [ ] Movement feels responsive and tight
- [ ] No visual glitches during transitions

### Edge Cases
- [ ] Spamming A at left edge doesn't crash
- [ ] Spamming D at right edge doesn't crash
- [ ] Alternating A/D rapidly works smoothly
- [ ] Holding down key doesn't cause issues

---

## TROUBLESHOOTING

### Problem: Player doesn't move
**Solution:** 
1. Check console for errors
2. Verify `input()` function is calling `player.switch_lane()`
3. Check that `game_state == 'playing'`

### Problem: Player jumps instantly (no smooth movement)
**Solution:**
1. Check `LANE_SWITCH_SPEED` in config.py (should be 12.0)
2. Make sure `player.update()` is being called (it should auto-call)
3. Verify lerp is using `time.dt`

### Problem: Player moves in wrong direction
**Solution:**
1. Check `LANE_POSITIONS` in config.py: should be `[-2.0, 0.0, 2.0]`
2. Check lane index logic in `switch_lane()`

### Problem: Console spams "out of bounds" messages
**Solution:** This is normal when at edges. Can reduce logging if annoying.

### Problem: "ImportError: cannot import name 'Player'"
**Solution:**
1. Check `entities/__init__.py` exists
2. Check `entities/player.py` exists
3. Verify class name is exactly `Player` (capital P)

---

## NEXT PHASE

Once all acceptance criteria pass, proceed to **Phase 1.3: Track & Camera**.

In Phase 1.3, we'll add:
- Infinite scrolling track (grid floor)
- Camera that follows player's lane position
- Visual feedback that world is moving

---

**STATUS:** [ ] PHASE 1.2 COMPLETE

(Check this box once all acceptance criteria are verified)
