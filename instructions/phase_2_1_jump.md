# PHASE 2.1: JUMP ANIMATION SYSTEM

## WHY

This is where **arcade logic diverges from physics simulation**. Instead of:
```python
velocity_y += gravity * dt  # Physics approach (UNRELIABLE)
```

We use:
```python
height = 4 * progress * (1 - progress)  # Animation curve (DETERMINISTIC)
```

**Why this matters:**
- Physics: Depends on tuning gravity, jump force, air friction - AI agents fail here
- Animation: Progress goes 0→1 over fixed duration, output is predictable

This creates:
- Perfectly consistent jump arc every time
- No "floaty" or "too heavy" feel
- Deterministic collision detection
- Easy to test and debug

---

## WHAT (Deliverables)

By the end of this phase, you will have:
1. Jump mechanic triggered by Spacebar
2. Smooth parabolic arc (realistic-looking curve)
3. Fixed 0.5-second duration jump
4. Can only jump when grounded (no air control)
5. Visual feedback (player rises and falls smoothly)

---

## HOW (Architecture)

### State Machine

Player vertical state has 3 values:
- `'grounded'`: On the floor, can jump
- `'jumping'`: Mid-air, animation in progress
- `'sliding'`: Crouched (will be added in Phase 2.2)

### Jump Animation Curve

The parabolic curve formula:
```
height = 4 * t * (1 - t)

Where:
- t = 0.0 → height = 0 (start of jump)
- t = 0.5 → height = 1 (peak)
- t = 1.0 → height = 0 (landing)
```

This creates a perfect parabola. Multiply by `JUMP_HEIGHT` to get actual units.

### Update Loop Logic

```python
if vertical_state == 'jumping':
    progress += dt / JUMP_DURATION  # Progress goes from 0 to 1
    
    if progress >= 1.0:
        # Jump complete
        vertical_state = 'grounded'
        y = GROUND_HEIGHT
    else:
        # Calculate height
        height = 4 * progress * (1 - progress) * JUMP_HEIGHT
        y = GROUND_HEIGHT + height
```

---

## UX (User Experience)

**What the User Sees:**
- Press Spacebar: Player cube rises smoothly
- Reaches peak in 0.25 seconds
- Falls back down in 0.25 seconds
- Lands smoothly on track
- Cannot jump again until landed

**What the User Feels:**
- Responsive (jump starts immediately)
- Consistent (feels same every time)
- Predictable (can time jumps reliably)
- Satisfying arc (not floaty, not too heavy)

**Audio cue (future):** "Whoosh" sound on jump start

---

## TASK (Step-by-Step Instructions)

### Step 1: Update Player Class

Modify `entities/player.py` to add jump logic:

```python
"""
Player Entity - Arcade Lane System
"""

from ursina import *
import config

class Player(Entity):
    """
    Player entity with arcade-style lane switching and jump animation.
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
            collider='box'
        )
        
        # Lane State (DISCRETE)
        self.lane = config.PLAYER_START_LANE
        self.target_x = config.LANE_POSITIONS[self.lane]
        
        # Vertical State Machine
        self.vertical_state = 'grounded'  # grounded, jumping, sliding
        self.jump_progress = 0.0          # 0.0 to 1.0 during jump
        
        print(f"[PLAYER] Initialized at lane {self.lane}")
    
    def switch_lane(self, direction):
        """
        Attempt to switch lanes.
        
        Args:
            direction (int): -1 for left, +1 for right
        """
        new_lane = self.lane + direction
        
        if new_lane < 0 or new_lane >= config.LANE_COUNT:
            return
        
        self.lane = new_lane
        self.target_x = config.LANE_POSITIONS[self.lane]
        
        print(f"[PLAYER] Switched to lane {self.lane}")
    
    def jump(self):
        """
        Initiate jump animation.
        Only works if player is grounded.
        """
        if self.vertical_state != 'grounded':
            return  # Cannot jump while already jumping/sliding
        
        self.vertical_state = 'jumping'
        self.jump_progress = 0.0
        
        print("[PLAYER] Jump started")
    
    def update(self):
        """
        Called every frame by Ursina.
        Updates lane position and jump animation.
        """
        # 1. Lane Movement (Horizontal)
        self.x = lerp(self.x, self.target_x, time.dt * config.LANE_SWITCH_SPEED)
        
        # 2. Jump Animation (Vertical)
        if self.vertical_state == 'jumping':
            self.update_jump()
    
    def update_jump(self):
        """
        Update jump animation using parabolic curve.
        
        The curve formula: height = 4 * t * (1 - t)
        This creates a smooth parabolic arc from 0 -> peak -> 0
        """
        # Increment progress
        self.jump_progress += time.dt / config.JUMP_DURATION
        
        # Check if jump complete
        if self.jump_progress >= 1.0:
            # Land
            self.vertical_state = 'grounded'
            self.jump_progress = 0.0
            self.y = config.PLAYER_START_Y
            
            print("[PLAYER] Landed")
            return
        
        # Calculate height using parabolic curve
        # Formula: 4*t*(1-t) where t goes from 0 to 1
        # Result: 0 -> 1 -> 0 (smooth parabola)
        t = self.jump_progress
        curve_value = 4 * t * (1 - t)
        height = curve_value * config.JUMP_HEIGHT
        
        # Apply height
        self.y = config.PLAYER_START_Y + height
```

---

### Step 2: Update Input Handling

Modify `main.py` input function to handle jump:

```python
def input(key):
    """
    Handle keyboard input.
    """
    if key == 'escape':
        print("[INPUT] ESC pressed - Exiting game")
        quit()
    
    if game_state == 'playing':
        # Lane switching
        if key == 'a' or key == 'left arrow':
            player.switch_lane(-1)
        elif key == 'd' or key == 'right arrow':
            player.switch_lane(1)
        
        # Jump
        elif key == 'space':
            player.jump()
```

---

### Step 3: Add Debug Visualization (Optional)

If DEBUG_MODE is enabled, add vertical state display.

Update the debug text in `main.py` update function:

```python
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
        state_display = player.vertical_state.upper()
        if player.vertical_state == 'jumping':
            progress_percent = int(player.jump_progress * 100)
            state_display = f"JUMPING ({progress_percent}%)"
        
        debug_text.text = f"Lane: {player.lane} | State: {state_display}"
```

---

### Step 4: Test Jump Mechanic

Run the game:
```bash
python main.py
```

**Test these scenarios:**

1. **Basic Jump:**
   - Press Spacebar
   - Player rises smoothly
   - Reaches peak around 2.5 units high
   - Falls back down smoothly
   - Lands at original Y position (0.5)

2. **Jump Duration:**
   - Time the jump with a stopwatch
   - Should take exactly 0.5 seconds (start to landing)
   - Peak should occur at 0.25 seconds

3. **Cannot Double Jump:**
   - Press Spacebar to jump
   - Press Spacebar again while in air
   - Nothing should happen (still only one jump)
   - Console should NOT show second "Jump started" message

4. **Jump While Moving:**
   - Hold A to switch lanes
   - Press Spacebar mid-transition
   - Both should work simultaneously
   - Lane switch continues smoothly during jump

5. **Rapid Jumps:**
   - Land, immediately press Spacebar again
   - Should jump again without delay
   - Can chain jumps: Jump → Land → Jump → Land

6. **Visual Arc:**
   - Watch the player cube during jump
   - Arc should look natural (parabolic)
   - Not too "floaty" or "heavy"
   - Smooth acceleration/deceleration

---

### Step 5: Verify Jump Curve

**The curve should feel:**
- Initial rise: Fast acceleration
- At peak: Momentary hang time
- Final fall: Fast deceleration

**If it feels wrong:**

**Too floaty (slow rise/fall):**
```python
# In config.py
JUMP_DURATION = 0.4  # Reduce duration
```

**Not high enough:**
```python
# In config.py
JUMP_HEIGHT = 3.0  # Increase height
```

**Too "videogame-y" (instant):**
```python
# In config.py
JUMP_DURATION = 0.6  # Increase for more realistic feel
```

**Recommended values for arcade feel:**
- Duration: 0.4-0.5 seconds
- Height: 2.0-2.5 units

---

### Step 6: Validate Determinism

**Critical Test:** The jump should be 100% consistent.

1. Jump 10 times in a row
2. Each jump should feel identical
3. Landing should always be at same Y position
4. Duration should be same every time

If jumps feel inconsistent:
- Check that `time.dt` is being used (for frame-rate independence)
- Verify `jump_progress` resets to 0 on landing
- Ensure no external factors affect Y position

---

## ACCEPTANCE CRITERIA

Before proceeding to Phase 2.2, verify ALL of these:

### Functional
- [ ] Pressing Spacebar makes player jump
- [ ] Jump follows smooth parabolic arc
- [ ] Jump duration is 0.5 seconds (or configured value)
- [ ] Player lands at original Y position
- [ ] Cannot double jump (ignores input while in air)
- [ ] Can jump while switching lanes
- [ ] Can chain jumps (jump immediately after landing)

### Technical
- [ ] Player has `vertical_state` attribute
- [ ] `vertical_state` is 'grounded' when on floor
- [ ] `vertical_state` is 'jumping' during jump
- [ ] `jump_progress` goes from 0.0 to 1.0
- [ ] Jump uses parabolic formula: 4*t*(1-t)
- [ ] No physics variables (no velocity, gravity)
- [ ] Console logs jump events (if DEBUG_MODE)

### Code Quality
- [ ] `jump()` method has docstring
- [ ] `update_jump()` method has docstring
- [ ] Formula is commented and clear
- [ ] No hardcoded values (uses config.py)
- [ ] Follows .cursorrules standards

### Visual
- [ ] Jump arc looks natural and smooth
- [ ] No popping or stuttering during jump
- [ ] Landing is clean (no bounce or overshoot)
- [ ] Jump height feels appropriate
- [ ] Duration feels responsive (not too slow)

### Edge Cases
- [ ] Spamming Spacebar in air doesn't break state
- [ ] Jumping while at lane edge works correctly
- [ ] Jumping during camera movement is smooth
- [ ] FPS drop doesn't affect jump consistency

---

## TROUBLESHOOTING

### Problem: Jump doesn't start
**Solution:**
1. Check that `input()` function calls `player.jump()`
2. Verify player is in 'grounded' state (print `player.vertical_state`)
3. Check console for any errors

### Problem: Player floats instead of landing
**Solution:**
1. Verify `jump_progress >= 1.0` check in `update_jump()`
2. Make sure `vertical_state` resets to 'grounded'
3. Check that `self.y = PLAYER_START_Y` is executed

### Problem: Jump arc looks weird (not parabolic)
**Solution:**
1. Verify formula is exactly: `4 * t * (1 - t)`
2. Check that `t` is `self.jump_progress` (not something else)
3. Print `curve_value` during jump to debug

### Problem: Jump duration is inconsistent
**Solution:**
1. Ensure `time.dt` is used in progress increment
2. Check frame rate (should be 60 FPS)
3. Verify no other code modifies `jump_progress`

### Problem: Can jump multiple times in air
**Solution:**
1. Check `if self.vertical_state != 'grounded': return` in `jump()`
2. Make sure state isn't being reset elsewhere

---

## NEXT PHASE

Once all acceptance criteria pass, proceed to **Phase 2.2: Slide Mechanic**.

In Phase 2.2, we'll add:
- Slide (crouch) mechanic
- Timed duration (auto-standup after 0.8s)
- Reduced player height when sliding
- S or Down Arrow input

---

**STATUS:** [ ] PHASE 2.1 COMPLETE

(Check this box once all acceptance criteria are verified)
