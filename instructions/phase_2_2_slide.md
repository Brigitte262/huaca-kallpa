# PHASE 2.2: SLIDE MECHANIC

## WHY

The slide mechanic completes the vertical movement system. It gives players a way to:
1. **Avoid high obstacles** (duck under them)
2. **Add variety** to gameplay (not just jumping)
3. **Create skill expression** (knowing when to jump vs slide)

**Arcade Logic Approach:**
- Slide is a **timed state**, not a physics crouch
- Player height scales down instantly
- After fixed duration, stands back up automatically
- Cannot slide while jumping (state machine prevents it)

---

## WHAT (Deliverables)

By the end of this phase, you will have:
1. Slide mechanic triggered by S or Down Arrow
2. Player height scales down to 40% when sliding
3. Automatic standup after 0.8 seconds
4. Visual feedback (player cube shrinks/grows)
5. Cannot slide while in air

---

## HOW (Architecture)

### State Machine Extension

Vertical states now include:
- `'grounded'`: Normal running (can jump or slide)
- `'jumping'`: Mid-air (cannot slide)
- `'sliding'`: Crouched (timer-based, auto-standup)

### Slide Mechanics

**On slide trigger:**
1. Check state is 'grounded' (can't slide in air)
2. Set state to 'sliding'
3. Scale player height to 40% (scale_y = 0.4)
4. Lower Y position to match new height
5. Start timer countdown

**During slide:**
1. Timer decreases each frame
2. Player remains low
3. Collision height is reduced (for avoiding high obstacles)

**On timer complete:**
1. Set state back to 'grounded'
2. Restore normal height (scale_y = 0.8)
3. Restore normal Y position

### Visual Effect

```
Normal:  ████  (height = 0.8, y = 0.5)
         ████
         
Sliding: ██    (height = 0.32, y = 0.25)
```

---

## UX (User Experience)

**What the User Sees:**
- Press S or Down Arrow: Player instantly crouches
- Player cube flattens to about 40% height
- After ~0.8 seconds, player stands back up automatically
- Cannot slide while jumping

**What the User Feels:**
- Responsive (instant crouch)
- Controlled (fixed duration, not hold-to-crouch)
- Strategic (need to time slides carefully)

**Future context:** This will let players slide under high red barriers while jumping over low yellow barriers.

---

## TASK (Step-by-Step Instructions)

### Step 1: Update Player Class for Slide

Modify `entities/player.py`:

```python
"""
Player Entity - Arcade Lane System
"""

from ursina import *
import config

class Player(Entity):
    """
    Player entity with arcade-style movement:
    - Lane switching (left/right)
    - Jump animation (spacebar)
    - Slide mechanic (s/down arrow)
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
        
        # Lane State
        self.lane = config.PLAYER_START_LANE
        self.target_x = config.LANE_POSITIONS[self.lane]
        
        # Vertical State Machine
        self.vertical_state = 'grounded'  # grounded, jumping, sliding
        
        # Jump state
        self.jump_progress = 0.0
        
        # Slide state
        self.slide_timer = 0.0
        
        # Store original scale for restore
        self.normal_scale_y = config.PLAYER_SIZE[1]
        self.slide_scale_y = config.PLAYER_SIZE[1] * config.SLIDE_HEIGHT_SCALE
        
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
            return
        
        self.vertical_state = 'jumping'
        self.jump_progress = 0.0
        
        print("[PLAYER] Jump started")
    
    def slide(self):
        """
        Initiate slide (crouch).
        Only works if player is grounded.
        """
        if self.vertical_state != 'grounded':
            return  # Cannot slide while jumping
        
        self.vertical_state = 'sliding'
        self.slide_timer = config.SLIDE_DURATION
        
        # Shrink height
        self.scale_y = self.slide_scale_y
        
        # Lower Y position to match new height
        # Player's Y is at their center, so we need to adjust
        self.y = self.slide_scale_y / 2.0
        
        print("[PLAYER] Slide started")
    
    def stand_up(self):
        """
        Return to normal standing state from slide.
        """
        self.vertical_state = 'grounded'
        self.scale_y = self.normal_scale_y
        self.y = config.PLAYER_START_Y
        
        print("[PLAYER] Stood up")
    
    def update(self):
        """
        Called every frame by Ursina.
        Updates all movement.
        """
        # 1. Lane Movement (Horizontal)
        self.x = lerp(self.x, self.target_x, time.dt * config.LANE_SWITCH_SPEED)
        
        # 2. Vertical Movement (State-based)
        if self.vertical_state == 'jumping':
            self.update_jump()
        elif self.vertical_state == 'sliding':
            self.update_slide()
    
    def update_jump(self):
        """
        Update jump animation using parabolic curve.
        """
        self.jump_progress += time.dt / config.JUMP_DURATION
        
        if self.jump_progress >= 1.0:
            # Land
            self.vertical_state = 'grounded'
            self.jump_progress = 0.0
            self.y = config.PLAYER_START_Y
            
            print("[PLAYER] Landed")
            return
        
        # Parabolic curve
        t = self.jump_progress
        curve_value = 4 * t * (1 - t)
        height = curve_value * config.JUMP_HEIGHT
        
        self.y = config.PLAYER_START_Y + height
    
    def update_slide(self):
        """
        Update slide state.
        Countdown timer, then stand back up.
        """
        self.slide_timer -= time.dt
        
        if self.slide_timer <= 0.0:
            # Slide complete, stand up
            self.stand_up()
```

---

### Step 2: Update Input Handling

Modify `main.py` input function:

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
        
        # Slide
        elif key == 's' or key == 'down arrow':
            player.slide()
```

---

### Step 3: Update Debug Display (Optional)

If you have DEBUG_MODE enabled, the existing debug text should now show "SLIDING" state:

```python
def update():
    """
    Called every frame by Ursina.
    """
    if game_state != 'playing':
        return
    
    camera_controller.update()
    
    if config.DEBUG_MODE and debug_text:
        state = player.vertical_state.upper()
        
        if player.vertical_state == 'jumping':
            progress = int(player.jump_progress * 100)
            state = f"JUMPING ({progress}%)"
        elif player.vertical_state == 'sliding':
            remaining = player.slide_timer
            state = f"SLIDING ({remaining:.1f}s)"
        
        debug_text.text = f"Lane: {player.lane} | State: {state}"
```

---

### Step 4: Test Slide Mechanic

Run the game:
```bash
python main.py
```

**Test these scenarios:**

1. **Basic Slide:**
   - Press S or Down Arrow
   - Player instantly flattens
   - Height reduces to ~40% of normal
   - Player automatically stands up after 0.8 seconds
   - Height returns to normal

2. **Slide Duration:**
   - Time the slide with a stopwatch
   - Should last exactly 0.8 seconds (or config value)
   - Standup should be instant (not gradual)

3. **Cannot Slide While Jumping:**
   - Press Spacebar to jump
   - Press S mid-jump
   - Nothing should happen (stays in jump state)
   - Console should NOT show "Slide started"

4. **Cannot Jump While Sliding:**
   - Press S to slide
   - Press Spacebar during slide
   - Nothing should happen (stays in slide state)
   - After slide ends, jump should work again

5. **Slide While Moving:**
   - Hold A to switch lanes
   - Press S mid-transition
   - Both should work simultaneously
   - Lane switch continues during slide

6. **Rapid Slide-Jump-Slide:**
   - Slide → wait for standup → Jump → land → Slide
   - All transitions should be smooth
   - State machine should handle all transitions

---

### Step 5: Visual Verification

**The slide should look:**
- Instant flatten (no gradual shrink)
- Cube maintains width (only height changes)
- Position adjusts so bottom stays on ground
- Instant standup (no gradual grow)

**Check these details:**
- Player's bottom edge should always be at y=0
- Sliding: Player center is at y=0.16 (half of 0.32 height)
- Normal: Player center is at y=0.5 (half of 0.8 height + 0.1 margin)

---

### Step 6: Adjust Feel (Optional)

If slide doesn't feel right:

**Too short/long:**
```python
# In config.py
SLIDE_DURATION = 1.0  # Default: 0.8 (increase for longer slide)
```

**Not flat enough:**
```python
# In config.py
SLIDE_HEIGHT_SCALE = 0.3  # Default: 0.4 (lower = flatter)
```

**Recommended values:**
- Duration: 0.7-1.0 seconds
- Height scale: 0.3-0.5 (40% is good balance)

---

## ACCEPTANCE CRITERIA

Before proceeding to Phase 3.1, verify ALL of these:

### Functional
- [ ] Pressing S or Down Arrow makes player slide
- [ ] Player height scales to 40% (or configured value)
- [ ] Slide lasts 0.8 seconds (or configured value)
- [ ] Player automatically stands up after timer
- [ ] Cannot slide while jumping
- [ ] Cannot jump while sliding
- [ ] Can slide while switching lanes

### Technical
- [ ] Player has `slide_timer` attribute
- [ ] `vertical_state` becomes 'sliding' during slide
- [ ] `scale_y` changes correctly
- [ ] `y` position adjusts for height change
- [ ] Timer decrements each frame using `time.dt`
- [ ] `stand_up()` method restores normal state
- [ ] Console logs slide events (if DEBUG_MODE)

### Code Quality
- [ ] `slide()` method has docstring
- [ ] `stand_up()` method has docstring
- [ ] `update_slide()` method has docstring
- [ ] No hardcoded values (uses config.py)
- [ ] Follows .cursorrules standards

### Visual
- [ ] Slide is instant (no gradual shrink)
- [ ] Standup is instant (no gradual grow)
- [ ] Player's bottom edge stays on ground
- [ ] Height change is clearly visible
- [ ] No visual glitches during slide

### State Machine
- [ ] Can transition: grounded → sliding → grounded
- [ ] Cannot transition: jumping → sliding
- [ ] Cannot transition: sliding → jumping
- [ ] All transitions are clean (no stuck states)
- [ ] Debug text shows correct state (if enabled)

---

## TROUBLESHOOTING

### Problem: Slide doesn't start
**Solution:**
1. Check `input()` calls `player.slide()`
2. Verify player is 'grounded' (not jumping)
3. Check console for errors

### Problem: Player floats when sliding
**Solution:**
1. Check Y position calculation: `self.y = self.slide_scale_y / 2.0`
2. Verify scale_y is being set correctly
3. Print y value during slide to debug

### Problem: Doesn't stand up automatically
**Solution:**
1. Verify `update_slide()` is called each frame
2. Check timer decrements with `time.dt`
3. Check `stand_up()` is called when timer <= 0

### Problem: Can slide while jumping
**Solution:**
1. Check `if self.vertical_state != 'grounded': return` in `slide()`
2. Make sure state isn't being changed elsewhere

### Problem: Height looks wrong
**Solution:**
1. Verify `SLIDE_HEIGHT_SCALE` in config (should be 0.4)
2. Check normal_scale_y and slide_scale_y are calculated correctly
3. Print scale_y during slide to debug

---

## NEXT PHASE

Once all acceptance criteria pass, proceed to **Phase 3.1: Obstacle Entities**.

In Phase 3.1, we'll add:
- Three obstacle types (low, high, moving)
- Color-coded obstacles
- Obstacle positioning in lanes
- Foundation for collision detection

---

**STATUS:** [ ] PHASE 2.2 COMPLETE

(Check this box once all acceptance criteria are verified)
