# PHASES 4-6: QUICK REFERENCE

## PHASE 4.1: COLLECTIBLES & SCORING

**Create entities/collectible.py:**
- Orb type (gold spheres, +100 points)
- Shield type (azure spheres, 5s invincibility)
- Spawn in lanes at height 0.8
- Auto-collect on proximity

**Scoring Logic:**
- Distance score: +10 per unit traveled
- Survival score: +10 per second
- Orb collect: +100 per orb
- Display running score total

**Acceptance:**
- [ ] Gold orbs spawn randomly
- [ ] Collecting orb gives +100 points
- [ ] Shield gives invincibility (collision ignored)
- [ ] Score increases over time

---

## PHASE 4.2: HUD DISPLAY

**Create UI elements:**
- Score display (top-left): "Score: 12450"
- Distance display (top-right): "Distance: 245m"
- Shield status (center): "SHIELD ACTIVE" when active
- FPS counter (debug mode only)

**Update every frame with current values**

**Acceptance:**
- [ ] Score updates in real-time
- [ ] Distance matches track progress
- [ ] Shield indicator shows/hides correctly
- [ ] Text is readable and positioned well

---

## PHASE 5.1: PROGRESSIVE DIFFICULTY

**Difficulty Ramping:**
```python
# Every 500 units:
current_speed = min(initial_speed + (distance/500) * 2.0, max_speed)
spawn_interval *= 0.95
```

**Acceptance:**
- [ ] Speed increases gradually
- [ ] Obstacles spawn faster over time
- [ ] Caps at maximum speed
- [ ] Player feels increasing challenge

---

## PHASE 5.2: VISUAL EFFECTS ("JUICE")

**Screen Shake:**
- On collision: 0.5s shake, intensity 1.0
- On shield hit: 0.3s shake, intensity 0.5

**Particle Trails:**
- Cyan particles when switching lanes
- Gold particles when collecting orbs

**Camera Tilt:**
- Subtle rotation when changing lanes

**Acceptance:**
- [ ] Screen shakes on collision
- [ ] Particles add visual feedback
- [ ] Effects don't impact performance
- [ ] Game feels polished and juicy

---

## PHASE 6.1: MENU SYSTEM

**Create UI states:**
```python
game_state = 'menu'  # menu, playing, paused, game_over

MENU:
- Title: "TEMPLE RUN 3D"
- Subtitle: "ARCADE EDITION"
- "Press ENTER to Start"
- "Press ESC to Quit"

PLAYING:
- Hide menu
- Show HUD
- Active gameplay

PAUSED:
- Dim screen
- "PAUSED"
- "Press P to Resume"
```

**Acceptance:**
- [ ] Game starts in menu
- [ ] ENTER transitions to playing
- [ ] ESC quits from menu
- [ ] P pauses/resumes during play

---

## PHASE 6.2: GAME OVER & RESTART

**Game Over Screen:**
```
GAME OVER

Final Score: 12450
Distance: 245m
Orbs Collected: 24

Press R to Restart
Press ESC to Main Menu
```

**Reset Logic:**
```python
def reset_game():
    global score, distance, current_speed
    score = 0
    distance = 0
    current_speed = initial_speed
    spawner.reset()
    player.reset()
    game_state = 'playing'
```

**Acceptance:**
- [ ] Game over screen shows final stats
- [ ] R restarts game
- [ ] ESC returns to menu
- [ ] All state properly resets
- [ ] Can play multiple sessions

---

## FINAL TESTING CHECKLIST

**Functionality:**
- [ ] Can move between all 3 lanes
- [ ] Can jump and slide
- [ ] Obstacles spawn continuously
- [ ] Collision detection works correctly
- [ ] Collectibles grant rewards
- [ ] Score/distance track accurately
- [ ] Difficulty increases over time
- [ ] Game over triggers correctly
- [ ] Can restart and replay

**Technical:**
- [ ] No errors in console
- [ ] 60 FPS maintained
- [ ] No memory leaks
- [ ] Clean code (follows .cursorrules)
- [ ] All constants in config.py

**Polish:**
- [ ] Visual effects work
- [ ] UI is readable
- [ ] Controls are responsive
- [ ] Game feels smooth and polished

