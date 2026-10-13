# TEMPLE RUN 3D - ARCADE LOGIC EDITION
## Complete Build Package

---

## 📦 WHAT YOU HAVE

This is a **complete, production-ready instruction set** for building a 3D endless runner game using **arcade logic** (not physics simulation). An AI agent can execute these instructions end-to-end to produce a working, polished game.

**Game Features:**
- ✅ 3-lane running system (Temple Run style)
- ✅ Jump and slide mechanics
- ✅ Three obstacle types (low, high, moving)
- ✅ Collectibles (orbs and shields)
- ✅ Progressive difficulty
- ✅ Visual polish ("juice" effects)
- ✅ Full UI flow (menu → play → game over → restart)
- ✅ Low-poly aesthetic (clean, modern, portfolio-worthy)

**Tech Stack:**
- **Python 3.8+**
- **Ursina Engine** (3D rendering)
- **Arcade Logic** (deterministic, testable, bug-resistant)

---

## 📁 PACKAGE CONTENTS

```
temple_run_arcade_instructions/
│
├── .cursorrules                    # Coding standards (MUST READ FIRST)
│
├── MASTER_AI_PROMPT.md            # Give this to your AI agent
│
├── Phase Files (14 micro-phases):
│   ├── phase_1_1_setup.md         # Project setup & config
│   ├── phase_1_2_player_lanes.md  # Lane switching
│   ├── phase_1_3_track_camera.md  # Scrolling track
│   ├── phase_2_1_jump.md          # Jump animation
│   ├── phase_2_2_slide.md         # Slide mechanic
│   ├── phase_3_1_obstacles.md     # Obstacle entities
│   ├── phase_3_2_spawner.md       # Spawner system
│   ├── phase_3_3_collision.md     # Collision detection
│   └── remaining_phases.md        # Phases 4-6 (condensed)
│
└── README.md                       # This file
```

---

## 🚀 HOW TO USE THIS PACKAGE

### Option A: Full AI Agent Build (Recommended)

**Best for:** Letting AI do all the work end-to-end

1. **Copy all files to a folder** accessible to your AI agent (Cursor, Windsurf, etc.)

2. **Open your AI agent** (Cursor Composer, Claude in Cursor, etc.)

3. **Give it the master prompt:**
   ```
   Read the MASTER_AI_PROMPT.md file and execute it completely.
   
   Build the Temple Run 3D game by following all 14 phases sequentially.
   Test after each phase and only proceed when verified working.
   
   Start with Phase 1.1: Project Setup
   ```

4. **Let it run** - The agent will:
   - Read .cursorrules
   - Execute each phase in order
   - Test after each phase
   - Verify acceptance criteria
   - Report progress

5. **Review checkpoints** - After phases 1, 3, 6, review the build to ensure quality

6. **Play your game!**

---

### Option B: Guided Manual Build

**Best for:** Learning the architecture yourself

1. **Read .cursorrules first** - Understand the arcade logic philosophy

2. **Follow phases sequentially:**
   - Read each phase file completely
   - Implement the TASK steps
   - Test against acceptance criteria
   - Move to next phase only when current is working

3. **Use AI for specific phases:**
   ```
   I'm on Phase 2.1 (Jump Animation).
   Help me implement the parabolic curve jump system described in phase_2_1_jump.md
   ```

---

### Option C: Hybrid Approach

**Best for:** Oversight with automation

1. **Use AI agent for mechanical phases** (1.1, 1.2, 3.1, 3.2, 4.1, 4.2, 6.1, 6.2)
2. **Review and tune critical phases yourself** (2.1 jump feel, 3.3 collision, 5.2 visual polish)
3. **Final polish pass** - Adjust config.py values to perfect game feel

---

## 🎯 WHAT MAKES THIS DIFFERENT

### Traditional 3D Game Dev (Physics-Based)
```python
# Physics approach (UNRELIABLE with AI)
velocity_y += gravity * dt
player.y += velocity_y * dt

if player.collides_with(obstacle):
    game_over()  # Often misses collisions
```

**Problems:**
- AI can't tune gravity/velocity values
- Floating-point errors accumulate
- Collision detection is unreliable
- "Floaty" or "too heavy" feel

### Our Approach (Arcade Logic)
```python
# Arcade approach (DETERMINISTIC)
progress += dt / JUMP_DURATION  # 0 to 1
height = 4 * progress * (1 - progress) * JUMP_HEIGHT
player.y = GROUND_HEIGHT + height

if player_lane == obstacle_lane and distance < threshold:
    if can_avoid(player_state, obstacle_type):
        pass  # Jump/slide worked
    else:
        game_over()  # Collision!
```

**Benefits:**
- AI can write if/else logic perfectly
- Math is exact (no float drift)
- Collision is precise
- Jump always feels the same

---

## 🏗️ ARCHITECTURE OVERVIEW

### The "Arcade Logic" Philosophy

**Discrete Lanes:**
- Player is in lane 0, 1, or 2 (never "between" lanes logically)
- Visual position smoothly lerps, but collision uses discrete lane

**Animation-Based Mechanics:**
- Jump is a tween curve (0→1 over fixed duration)
- Slide is a timed state (fixed 0.8s duration)
- No gravity, velocity, or physics variables

**Math-Based Collision:**
- `if same_lane AND close_distance AND cannot_avoid: collision`
- No mesh intersections or raycasts
- Deterministic and testable

**World Scrolls Toward Player:**
- Player stays at Z=0
- Track, obstacles, collectibles move toward player
- Prevents floating-point errors at large distances

---

## 📊 PHASE BREAKDOWN

### Phase 1: Foundation (Core Systems)
**Duration:** ~45 minutes
- Project setup, config, Ursina initialization
- Player lane switching with smooth lerping
- Infinite scrolling track with grid lines
- Camera follow system

**Output:** Player cube on scrolling track, can switch lanes smoothly

---

### Phase 2: Vertical Movement (Jump & Slide)
**Duration:** ~30 minutes
- Jump animation using parabolic curve
- Slide mechanic with timed duration
- Vertical state machine (grounded/jumping/sliding)

**Output:** Can jump over obstacles and slide under them

---

### Phase 3: Obstacles & Collision (The Challenge)
**Duration:** ~60 minutes
- Three obstacle types (low/high/moving)
- Automated spawner system
- Math-based collision detection
- Game over trigger

**Output:** Playable game with challenge and failure state

---

### Phase 4: Scoring & HUD (Progression)
**Duration:** ~30 minutes
- Collectibles (orbs and shields)
- Scoring system (distance + survival + orbs)
- HUD display (score, distance, shield status)

**Output:** Game with clear goals and feedback

---

### Phase 5: Difficulty & Polish (Refinement)
**Duration:** ~45 minutes
- Progressive difficulty (speed ramps over time)
- Visual effects (screen shake, particles, camera tilt)
- Game feel enhancements

**Output:** Game that feels smooth and professional

---

### Phase 6: UI/UX (Complete Experience)
**Duration:** ~30 minutes
- Main menu and pause system
- Game over screen with stats
- Restart functionality

**Output:** Full game loop (menu → play → die → restart)

---

### **Total Build Time: 4-5 hours (with testing)**

---

## 🎮 EXPECTED FINAL GAME

### Visual Style
- **Low-poly aesthetic**: Clean geometric shapes
- **Neon color scheme**: Cyan player, yellow/red/orange obstacles
- **Dark background**: Deep blue-purple void
- **Grid-lined track**: Scrolling cyan grid for depth

### Gameplay Loop
1. Start in main menu
2. Press ENTER to play
3. Switch lanes (A/D) to avoid obstacles
4. Jump (SPACE) over low yellow barriers
5. Slide (S) under high red barriers
6. Collect gold orbs (+100 points)
7. Collect azure shields (5s invincibility)
8. Game gets progressively faster
9. Eventually collide with obstacle
10. See game over screen with stats
11. Press R to restart, ESC for menu

### Controls
- **A / Left Arrow:** Move left lane
- **D / Right Arrow:** Move right lane
- **Space:** Jump
- **S / Down Arrow:** Slide
- **P:** Pause/Resume
- **R:** Restart (game over only)
- **ESC:** Quit / Main menu

---

## ✅ QUALITY ASSURANCE

### Testing Checklist (Built into instructions)
Each phase has:
- Functional acceptance criteria
- Technical acceptance criteria
- Code quality standards
- Visual verification points
- Edge case tests

### Verification Gates
AI agent cannot proceed to next phase until:
- All acceptance criteria pass
- No errors in console
- Game runs smoothly
- Code follows .cursorrules standards

---

## 🐛 IF SOMETHING BREAKS

### During Build
1. Check which phase failed
2. Review that phase's acceptance criteria
3. Look at TROUBLESHOOTING section in phase file
4. Verify .cursorrules are being followed
5. Test incrementally (comment out code until it works)

### After Build
- Reference `MASTER_AI_PROMPT.md` → ERROR HANDLING PROTOCOL
- Check Final Build Verification checklist
- Review Common Mistakes to Avoid

---

## 🎯 SUCCESS METRICS

The build is successful when:
- ✅ Game launches without errors
- ✅ Can play for 5+ minutes continuously
- ✅ All mechanics work (lanes, jump, slide, collision)
- ✅ Scoring and UI display correctly
- ✅ Can restart and replay indefinitely
- ✅ Runs at stable 60 FPS
- ✅ Code is clean and follows standards

---

## 💡 CUSTOMIZATION AFTER BUILD

Once the base game works, customize via `config.py`:

**Make it faster:**
```python
TRACK_SCROLL_SPEED = 30.0  # Default: 20.0
TRACK_SCROLL_SPEED_MAX = 50.0  # Default: 40.0
```

**Make jumps higher:**
```python
JUMP_HEIGHT = 3.5  # Default: 2.5
```

**Change colors:**
```python
COLOR_PLAYER = color.magenta  # Default: cyan
COLOR_TRACK = color.rgb(10, 10, 20)  # Darker background
```

**Adjust difficulty:**
```python
SPAWN_INTERVAL_MIN = 0.5  # Default: 0.8 (faster spawning)
DIFFICULTY_SPEED_INCREMENT = 3.0  # Default: 2.0 (ramps faster)
```

---

## 🏆 PORTFOLIO PRESENTATION

This game demonstrates:

✅ **Clean Architecture** - Separation of concerns, modular design
✅ **State Management** - Proper state machines, no spaghetti logic  
✅ **Game Feel** - Animation curves, visual effects, responsive controls
✅ **Testing Discipline** - Verified at every step
✅ **Professional Code** - Documented, standardized, maintainable
✅ **Modern Aesthetic** - Low-poly style is trending in indie games

**GitHub README Template:**
> "Temple Run 3D - Arcade Edition: A deterministic endless runner built with arcade logic principles. 3-lane system, animation-based mechanics, and math-driven collision detection ensure bug-free gameplay. Built with Python and Ursina in 5 hours using systematic phase-based development."

---

## 🤝 SUPPORT

If you encounter issues:

1. **Review the phase file** - Most issues are covered in TROUBLESHOOTING sections
2. **Check .cursorrules** - Ensure you're following the architectural principles
3. **Read error messages** - Python errors are usually clear about what's wrong
4. **Test incrementally** - Isolate the problem by commenting out code
5. **Ask specific questions** - Reference the phase and acceptance criterion that's failing

---

## 📝 FINAL NOTES

This instruction set was designed with **AI agent limitations** in mind:

- ❌ Physics simulation (AI can't tune gravity/velocity)
- ✅ Arcade logic (AI excels at if/else and math)

- ❌ Complex 3D transformations (AI spatial reasoning is weak)
- ✅ Discrete lane system (AI handles integers perfectly)

- ❌ Vague "make it feel good" instructions
- ✅ Exact specifications with acceptance criteria

The result: **An AI can build this game reliably, and it will work.**

---

**NOW GO BUILD YOUR GAME! 🚀**

Start with `MASTER_AI_PROMPT.md` and let the AI agent execute the full build.

Or tackle it phase-by-phase yourself to learn the architecture.

Either way, you'll have a polished, portfolio-worthy game when you're done.
