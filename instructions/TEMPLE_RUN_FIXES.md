# TEMPLE RUN 3D - BUG FIXES & IMPROVEMENTS
# Phase-Based Implementation Guide
# Total Phases: 12 (Critical: 5, Important: 4, Enhancement: 3)

---

## PHASE 1: Fix Duplicate ScoreManager Definition
**Priority:** CRITICAL
**File:** `systems/score.py`
**Estimated Time:** 2 minutes

### Current Issue
Lines 1-16 contain an incomplete first definition of ScoreManager that gets shadowed by the complete definition starting at line 17.

### Instructions
1. Open `systems/score.py`
2. Delete lines 1-16 (everything before the second docstring)
3. The file should now start with:
```python
"""
Score System - Track Progress and Rewards
"""

import time
import config

class ScoreManager:
```

### Verification
```bash
# Check for duplicate class definitions
grep -n "class ScoreManager" systems/score.py
# Should only show ONE line number
```

### Acceptance Criteria
- ✅ Only ONE `class ScoreManager` definition exists
- ✅ File starts with docstring
- ✅ Shield timer logic is present in `update()` method
- ✅ `orbs_collected` attribute exists in `__init__`

---

## PHASE 2: Fix Duplicate Camera Docstring
**Priority:** CRITICAL
**File:** `systems/camera.py`
**Estimated Time:** 1 minute

### Current Issue
Lines 1-7 contain a duplicate docstring.

### Instructions
1. Open `systems/camera.py`
2. Delete lines 1-7 (first docstring block)
3. File should start with:
```python
"""
Camera System - Smooth Follow

The camera follows the player's lane position smoothly.
Y and Z are fixed, only X position follows.
"""

from ursina import *
import config
```

### Verification
```bash
# Count docstrings at top of file
head -20 systems/camera.py | grep -c '"""'
# Should return 2 (opening and closing of ONE docstring)
```

### Acceptance Criteria
- ✅ Only ONE docstring at top of file
- ✅ Imports immediately follow docstring
- ✅ No duplicate text

---

## PHASE 3: Add z_position Attribute to Player
**Priority:** CRITICAL
**File:** `entities/player.py`
**Estimated Time:** 3 minutes

### Current Issue
CollisionDetector expects `player.z_position` but Player only has inherited `.z` from Entity.

### Instructions
1. Open `entities/player.py`
2. In `__init__` method, after line 35 (`self.slide_scale_y = ...`), add:
```python
        
        # Z position (for collision detection)
        self.z_position = config.PLAYER_START_Z
```

3. In `reset()` method, after line 145 (`self.scale_y = self.normal_scale_y`), add:
```python
        self.z_position = config.PLAYER_START_Z
```

### Verification
```bash
# Run game and check for collision system working
python main.py
# Move into obstacles - should trigger game over correctly
```

### Acceptance Criteria
- ✅ `self.z_position` is initialized in `__init__`
- ✅ `self.z_position` is reset in `reset()` method
- ✅ Collision detection works without falling back to default 0
- ✅ No runtime errors when colliding with obstacles

---

## PHASE 4: Auto-Generate Textures on First Run
**Priority:** CRITICAL
**File:** `main.py`
**Estimated Time:** 5 minutes

### Current Issue
Game crashes if textures don't exist. Need to auto-generate on first run.

### Instructions
1. Open `main.py`
2. Add import at top (after existing imports):
```python
import os
```

3. Replace the `if __name__ == '__main__':` block at the bottom with:
```python
# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == '__main__':
    # Generate textures if they don't exist
    required_textures = [
        'assets/track_texture.png',
        'assets/wall_texture.png',
        'assets/wood_texture.png',
        'assets/metal_texture.png',
        'assets/orb_texture.png'
    ]
    
    missing_textures = [tex for tex in required_textures if not os.path.exists(tex)]
    
    if missing_textures:
        print("[SETUP] Generating missing textures...")
        from utils.texture_gen import (
            ensure_assets_dir,
            generate_track_texture,
            generate_wall_texture,
            generate_wood_texture,
            generate_metal_texture,
            generate_orb_texture
        )
        
        ensure_assets_dir()
        
        if not os.path.exists('assets/track_texture.png'):
            generate_track_texture()
        if not os.path.exists('assets/wall_texture.png'):
            generate_wall_texture()
        if not os.path.exists('assets/wood_texture.png'):
            generate_wood_texture()
        if not os.path.exists('assets/metal_texture.png'):
            generate_metal_texture()
        if not os.path.exists('assets/orb_texture.png'):
            generate_orb_texture()
        
        print("[SETUP] Texture generation complete!")
    
    app = init_game()
    init_entities()
    
    print("[READY] Game ready - Use A/D or Arrow Keys to switch lanes")
    print("[READY] Track is scrolling - Player movement creates camera follow")
    print("[READY] Press ESC to exit")
    
    app.run()
```

### Verification
```bash
# Delete assets folder and test
rm -rf assets/
python main.py
# Should auto-generate textures and run without crash

# Verify textures exist
ls -la assets/
# Should show all 5 texture files
```

### Acceptance Criteria
- ✅ Game runs on first launch without manual texture generation
- ✅ Console shows "[SETUP] Generating missing textures..." if needed
- ✅ All 5 textures are created automatically
- ✅ Second run doesn't regenerate (checks existence first)
- ✅ No import errors

---

## PHASE 5: Wire Up Difficulty Manager in Spawner
**Priority:** IMPORTANT
**File:** `systems/spawner.py`
**Estimated Time:** 5 minutes

### Current Issue
`DifficultyManager.get_spawn_interval_multiplier()` exists but is never used. Spawner manually calculates speed factor.

### Instructions
1. Open `systems/spawner.py`
2. Modify `__init__` to accept difficulty_manager:
```python
    def __init__(self, difficulty_manager=None):
        self.spawn_timer = config.SPAWN_INTERVAL_MAX
        self.obstacles = []  # Track all active obstacles (and collectibles)
        self.last_lane = 1  # Avoid spawning same lane twice
        self.difficulty_manager = difficulty_manager
        
        print("[SPAWNER] Initialized")
```

3. Replace the spawn timer calculation in `update()` method (lines 36-41) with:
```python
            # Calculate next spawn interval (scales with difficulty)
            base_interval = random.uniform(
                config.SPAWN_INTERVAL_MIN,
                config.SPAWN_INTERVAL_MAX
            )
            
            # Use difficulty manager if available
            if self.difficulty_manager:
                multiplier = self.difficulty_manager.get_spawn_interval_multiplier()
            else:
                # Fallback: calculate manually
                multiplier = config.TRACK_SCROLL_SPEED / current_speed
            
            self.spawn_timer = base_interval * multiplier
```

4. Open `main.py` and modify spawner initialization (line 73):
```python
    # Create spawner
    global spawner, difficulty_manager
    difficulty_manager = DifficultyManager()
    spawner = ObstacleSpawner(difficulty_manager)
```

5. Move `difficulty_manager = DifficultyManager()` line BEFORE spawner creation

### Verification
```bash
# Run game and watch spawn rate increase as speed increases
python main.py
# Obstacles should spawn more frequently as game speeds up
```

### Acceptance Criteria
- ✅ Spawner accepts `difficulty_manager` in constructor
- ✅ Spawn interval uses `get_spawn_interval_multiplier()` when available
- ✅ Fallback calculation exists if no difficulty_manager provided
- ✅ Game difficulty scales correctly
- ✅ No runtime errors

---

## PHASE 6: Update README - Remove False Claims
**Priority:** IMPORTANT
**File:** `README.md`
**Estimated Time:** 10 minutes

### Current Issue
README claims "ECS architecture" and "Zero-Allocation Pooling" which aren't implemented.

### Instructions
1. Open `README.md`
2. Replace line 9:
```markdown
**Temple Run Arcade 3D** is a specialized engine implementation of the classic endless runner genre, re-engineered for **deterministic arcade compliance**. Unlike traditional physics-based runners, this engine utilizes a discrete state machine and lane-based coordinate system to ensure pixel-perfect collision detection and zero-latency input response.
```

3. Replace lines 18-21 with:
```markdown
*   **Deterministic State Machine** — Uses discrete integer-based lane logic (0, 1, 2) rather than floating-point physics to guarantee predictable outcomes.
*   **Efficient Entity Management** — Clean separation of visual and logical layers with automatic entity cleanup to prevent memory leaks.
*   **Procedural Track Generation** — Infinite world generation using dynamic difficulty scaling and pattern-based spawning.
*   **Modular System Architecture** — Decoupled game systems (collision, scoring, spawning) that communicate through well-defined interfaces.
```

4. Remove line 23 (Hot-Reloadable Config is actually true, keep it)

5. Replace "Architecture" badge on line 6:
```markdown
![Architecture](https://img.shields.io/badge/Architecture-Modular-red?style=for-the-badge)
```

### Verification
```bash
# Check for misleading terms
grep -i "ECS\|pooling" README.md
# Should return no results
```

### Acceptance Criteria
- ✅ No mention of "ECS" or "Entity-Component-System"
- ✅ No mention of "Zero-Allocation Pooling"
- ✅ Claims match actual implementation
- ✅ Technical accuracy maintained
- ✅ Still sounds professional

---

## PHASE 7: Add High Score Persistence
**Priority:** IMPORTANT
**File:** `systems/score.py`
**Estimated Time:** 8 minutes

### Current Issue
High score resets every time game closes.

### Instructions
1. Open `systems/score.py`
2. Add import at top:
```python
import os
import json
```

3. Add constant after imports:
```python
HIGH_SCORE_FILE = 'high_score.json'
```

4. Add method to ScoreManager class (after `__init__`):
```python
    def load_high_score(self):
        """Load high score from file."""
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, 'r') as f:
                    data = json.load(f)
                    self.high_score = data.get('high_score', 0)
                    print(f"[SCORE] Loaded high score: {self.high_score}")
            except Exception as e:
                print(f"[SCORE] Could not load high score: {e}")
                self.high_score = 0
        else:
            self.high_score = 0
    
    def save_high_score(self):
        """Save high score to file."""
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
                print(f"[SCORE] Saved high score: {self.high_score}")
        except Exception as e:
            print(f"[SCORE] Could not save high score: {e}")
```

5. Modify `__init__` to call load:
```python
    def __init__(self):
        self.score = 0.0
        self.distance = 0.0
        self.high_score = 0.0
        self.orbs_collected = 0
        self.shield_active = False
        self.shield_timer = 0.0
        
        # Load high score from file
        self.load_high_score()
        
        print("[SCORE] Initialized")
```

6. Modify `reset()` to save if new high score:
```python
    def reset(self):
        """
        Reset score for new game.
        """
        if self.score > self.high_score:
            self.high_score = int(self.score)
            self.save_high_score()  # Save to file
        
        self.score = 0.0
        self.distance = 0.0
        self.orbs_collected = 0
        
        # Shield state
        self.shield_active = False
        self.shield_timer = 0.0
        print("[SCORE] Reset")
```

7. Update `.gitignore` to exclude high score file:
```
high_score.json
```

### Verification
```bash
# Run game, score some points, die, restart
python main.py
# Check if high_score.json exists
cat high_score.json
# Should show {"high_score": YOUR_SCORE}

# Restart game - high score should persist
```

### Acceptance Criteria
- ✅ High score saves to `high_score.json` on game over
- ✅ High score loads on game start
- ✅ File is created automatically if missing
- ✅ Graceful error handling if file is corrupted
- ✅ `.gitignore` excludes high score file

---

## PHASE 8: Display High Score in HUD
**Priority:** IMPORTANT
**File:** `systems/ui.py`
**Estimated Time:** 5 minutes

### Current Issue
High score is tracked but never displayed.

### Instructions
1. Open `systems/ui.py`
2. In `__init__`, add new text element after `self.distance_text`:
```python
        
        # High Score (Top Right, below distance)
        self.high_score_text = Text(
            text='Best: 0',
            position=(0.65, 0.40),
            scale=config.UI_FONT_SIZE * 0.8,  # Slightly smaller
            color=config.COLOR_MENU_TITLE,  # Gold color
            enabled=False
        )
```

3. Modify `update()` method signature:
```python
    def update(self, score, distance, shield_active, shield_timer, game_state, orbs_collected=0, high_score=0):
```

4. In `update()`, add to the "Hide everything" section:
```python
        self.high_score_text.enabled = False
```

5. In `update()`, in the `elif game_state == 'playing':` block, add:
```python
            
            # Show high score if it exists
            if high_score > 0:
                self.high_score_text.enabled = True
                self.high_score_text.text = f'Best: {int(high_score)}'
```

6. Open `main.py` and update all `hud.update()` calls to include high_score:
```python
# Search for: hud.update(
# Add high_score parameter to all calls:
hud.update(
    score_manager.score,
    score_manager.distance,
    score_manager.shield_active,
    score_manager.shield_timer,
    game_state,
    score_manager.orbs_collected,
    score_manager.high_score  # ADD THIS
)
```

### Verification
```bash
# Run game, check if "Best: X" appears in top right
python main.py
# Should see high score displayed if one exists
```

### Acceptance Criteria
- ✅ High score displays in gold text below distance
- ✅ Only shows if high_score > 0
- ✅ Updates correctly when new high score is achieved
- ✅ Smaller font than main score (less prominent)

---

## PHASE 9: Add First-Time Setup Instructions to README
**Priority:** ENHANCEMENT
**File:** `README.md`
**Estimated Time:** 3 minutes

### Instructions
1. Open `README.md`
2. Replace the "Running the Engine" section (lines 133-136) with:
```markdown
### Running the Engine
```bash
python main.py
```

**First-Time Setup:**
The game will automatically generate all required texture assets on first run. You should see:
```
[SETUP] Generating missing textures...
[SETUP] Texture generation complete!
```

This only happens once. Subsequent runs will skip this step.

**Manual Texture Generation (Optional):**
If you want to regenerate textures or inspect the generation process:
```bash
python utils/texture_gen.py
```
```

### Verification
```bash
# Check README renders correctly
cat README.md | grep -A 10 "Running the Engine"
```

### Acceptance Criteria
- ✅ Clear first-run instructions
- ✅ Explains auto-generation behavior
- ✅ Provides manual generation alternative
- ✅ User knows what to expect on first launch

---

## PHASE 10: Fix requirements.txt with Pillow
**Priority:** ENHANCEMENT
**File:** `requirements.txt`
**Estimated Time:** 1 minute

### Current Issue
`utils/texture_gen.py` requires Pillow but it's not in requirements.txt.

### Instructions
1. Open `requirements.txt`
2. Replace contents with:
```
ursina
pillow
```

### Verification
```bash
# Test clean install
pip install -r requirements.txt
python utils/texture_gen.py
# Should work without errors
```

### Acceptance Criteria
- ✅ `pillow` is listed in requirements.txt
- ✅ Fresh install can generate textures
- ✅ No missing dependency errors

---

## PHASE 11: Add Gameplay GIF Placeholder to README
**Priority:** ENHANCEMENT
**File:** `README.md`
**Estimated Time:** 2 minutes

### Instructions
1. Open `README.md`
2. After line 13 (after the badges), add:
```markdown

---

## 🎮 Gameplay Preview

![Gameplay Demo](docs/gameplay.gif)

*Use A/D or Arrow Keys to switch lanes • Space to jump • S to slide*

---
```

3. Create docs folder:
```bash
mkdir -p docs
```

4. Add placeholder to `.gitignore`:
```
# Docs
docs/gameplay.gif
```

5. Create `docs/README.md`:
```markdown
# Documentation Assets

## gameplay.gif
Record gameplay using:
- OBS Studio (screen capture)
- Convert to GIF using: `ffmpeg -i gameplay.mp4 -vf "fps=15,scale=800:-1" gameplay.gif`
- Keep under 5MB for GitHub

## Future Assets
- Architecture diagrams
- Performance benchmarks
- Tutorial images
```

### Verification
```bash
# Check structure
ls -la docs/
# Should show README.md
```

### Acceptance Criteria
- ✅ README has gameplay section
- ✅ GIF placeholder is documented
- ✅ Instructions for creating GIF exist
- ✅ Folder structure is clean

---

## PHASE 12: Add .editorconfig for Consistency
**Priority:** ENHANCEMENT
**File:** `.editorconfig` (new file)
**Estimated Time:** 2 minutes

### Purpose
Ensure consistent formatting across editors (matches your coding style).

### Instructions
1. Create `.editorconfig` in project root:
```ini
# EditorConfig is awesome: https://EditorConfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.md]
trim_trailing_whitespace = false
max_line_length = off

[*.{yml,yaml,json}]
indent_style = space
indent_size = 2
```

### Verification
```bash
# Check if editors respect settings
# (Most modern editors auto-detect .editorconfig)
cat .editorconfig
```

### Acceptance Criteria
- ✅ `.editorconfig` exists
- ✅ Python files use 4 spaces
- ✅ 100 character line limit is enforced
- ✅ Consistent line endings (LF)

---

## IMPLEMENTATION ORDER

### Session 1 (Critical Bugs - 15 minutes)
1. ✅ Phase 1: Fix Duplicate ScoreManager
2. ✅ Phase 2: Fix Duplicate Camera Docstring
3. ✅ Phase 3: Add z_position to Player
4. ✅ Phase 4: Auto-Generate Textures
5. ✅ Phase 10: Fix requirements.txt

### Session 2 (Important Features - 30 minutes)
6. ✅ Phase 5: Wire Up Difficulty Manager
7. ✅ Phase 6: Update README Claims
8. ✅ Phase 7: High Score Persistence
9. ✅ Phase 8: Display High Score

### Session 3 (Polish - 10 minutes)
10. ✅ Phase 9: README Setup Instructions
11. ✅ Phase 11: Gameplay GIF Placeholder
12. ✅ Phase 12: EditorConfig

---

## TESTING PROTOCOL

After **each session**, run full test suite:

```bash
# 1. Syntax check
python -m py_compile main.py

# 2. Run game
python main.py

# 3. Test gameplay
# - Move between all 3 lanes (A/D)
# - Jump over low obstacles (Space)
# - Slide under high obstacles (S)
# - Collect orbs and shields
# - Verify collision detection
# - Check game over and restart
# - Verify high score saves/loads

# 4. Check for errors
# - No console errors
# - Smooth 60 FPS
# - No visual glitches
```

---

## COMPLETION CHECKLIST

### Critical (Must Complete)
- [ ] No duplicate code in any files
- [ ] Player has z_position attribute
- [ ] Textures auto-generate on first run
- [ ] Pillow in requirements.txt
- [ ] Game runs without crashes

### Important (Should Complete)
- [ ] Difficulty manager is properly wired
- [ ] README claims match implementation
- [ ] High score persists between sessions
- [ ] High score displays in HUD

### Enhancement (Nice to Have)
- [ ] README has setup instructions
- [ ] Gameplay GIF placeholder exists
- [ ] EditorConfig for consistency

---

## NOTES

- Each phase is **atomic** - can be completed and tested independently
- Phases 1-5 are **blocking** - must be done before showing anyone
- Phases 6-8 make it **portfolio-grade**
- Phases 9-12 add **professional polish**
- Total estimated time: **55 minutes** for all phases

This is **not** a refactor - these are surgical fixes that preserve your architecture.
