# PHASE 3.1: OBSTACLE ENTITIES

## WHY

Obstacles are the **core challenge** of the game. We're creating three types:
1. **Low (Yellow)**: Jump over
2. **High (Red)**: Slide under
3. **Moving (Orange)**: Avoid by switching lanes

**Arcade Logic:** Obstacles don't use physics. They're just cubes at fixed positions that scroll toward the player. Collision will be pure math (distance + lane matching).

---

## WHAT (Deliverables)

By the end of this phase, you will have:
1. Obstacle entity class with three types
2. Color-coded obstacles (yellow/red/orange)
3. Obstacles positioned in specific lanes
4. Obstacles that scroll toward player
5. Auto-cleanup when off-screen

---

## HOW (Architecture)

### Obstacle Data Structure

Each obstacle tracks:
- `lane`: Which lane it's in (0, 1, or 2)
- `z_position`: World Z coordinate (starts at 60, moves toward 0)
- `obs_type`: 'low', 'high', or 'moving'
- `entity`: Ursina Entity for rendering

### Obstacle Types

**LOW (Yellow):**
- Short barrier (0.6 units high)
- Player must JUMP over
- Y position: 0.3 (ground level)

**HIGH (Red):**
- Tall barrier (2.5 units high)
- Player must SLIDE under
- Y position: 1.25 (spans from ground to 2.5 high)

**MOVING (Orange):**
- Medium height (1.2 units)
- Switches between lanes
- Player must avoid by changing lanes

---

## TASK

### Step 1: Create entities/obstacle.py

```python
"""
Obstacle Entity - Arcade Logic Hazards

Obstacles are simple cubes that:
1. Stay in their assigned lane
2. Move toward the player (decreasing Z)
3. Get destroyed when behind player
"""

from ursina import *
import config

class Obstacle(Entity):
    """
    Obstacle entity with type-based behavior.
    
    Types:
    - 'low': Jump over (yellow)
    - 'high': Slide under (red)
    - 'moving': Avoid (orange, switches lanes)
    """
    
    def __init__(self, lane, z_position, obs_type):
        """
        Create an obstacle.
        
        Args:
            lane (int): Lane index (0, 1, or 2)
            z_position (float): Starting Z coordinate
            obs_type (str): 'low', 'high', or 'moving'
        """
        # Set properties based on type
        if obs_type == 'low':
            color = config.COLOR_OBS_LOW
            scale = config.OBS_LOW_SIZE
            y_pos = config.OBS_LOW_HEIGHT
        elif obs_type == 'high':
            color = config.COLOR_OBS_HIGH
            scale = config.OBS_HIGH_SIZE
            y_pos = config.OBS_HIGH_HEIGHT
        elif obs_type == 'moving':
            color = config.COLOR_OBS_MOVING
            scale = config.OBS_MOVING_SIZE
            y_pos = config.OBS_MOVING_HEIGHT
        else:
            raise ValueError(f"Invalid obstacle type: {obs_type}")
        
        # Calculate X position from lane
        x_pos = config.LANE_POSITIONS[lane]
        
        # Initialize entity
        super().__init__(
            model='cube',
            color=color,
            scale=scale,
            position=(x_pos, y_pos, z_position),
            collider='box'
        )
        
        # Store state
        self.lane = lane
        self.z_position = z_position
        self.obs_type = obs_type
        
        # Moving obstacle specific
        self.move_direction = 1 if lane == 0 else -1  # Start moving away from edge
        
        print(f"[OBSTACLE] Created {obs_type} at lane {lane}, z={z_position}")
    
    def update(self):
        """
        Update obstacle position.
        Scrolls toward player and handles special behaviors.
        """
        # Scroll toward player
        self.z_position -= config.TRACK_SCROLL_SPEED * time.dt
        self.z = self.z_position
        
        # Moving obstacle behavior
        if self.obs_type == 'moving':
            self.update_moving_obstacle()
        
        # Auto-cleanup if behind player
        if self.z_position < config.OBSTACLE_DESPAWN_DISTANCE:
            self.cleanup()
    
    def update_moving_obstacle(self):
        """
        Special behavior for moving obstacles.
        Shifts between lanes over time.
        """
        # Move laterally
        self.x += self.move_direction * config.OBS_MOVING_SPEED * time.dt
        
        # Check lane boundaries and reverse
        if self.x <= config.LANE_POSITIONS[0]:
            self.x = config.LANE_POSITIONS[0]
            self.move_direction = 1
            self.lane = 0
        elif self.x >= config.LANE_POSITIONS[2]:
            self.x = config.LANE_POSITIONS[2]
            self.move_direction = -1
            self.lane = 2
        else:
            # Determine current lane
            distances = [abs(self.x - pos) for pos in config.LANE_POSITIONS]
            self.lane = distances.index(min(distances))
    
    def cleanup(self):
        """
        Remove this obstacle from the game.
        """
        print(f"[OBSTACLE] Destroyed {self.obs_type} at z={self.z_position:.1f}")
        destroy(self)
```

---

### Step 2: Test Obstacle Creation

Create a test file `test_obstacles.py` (temporary):

```python
"""
Temporary test file for obstacle visualization.
Run this to see obstacles without full spawning system.
"""

from ursina import *
import config
from entities.player import Player
from entities.track import Track
from entities.obstacle import Obstacle
from systems.camera import CameraController

app = Ursina()
window.title = "Obstacle Test"
window.size = (1280, 720)
window.color = config.COLOR_BACKGROUND

# Create entities
track = Track()
player = Player()
camera_controller = CameraController(player)

# Create test obstacles (one of each type in each lane)
obstacles = []

# Lane 0: Low obstacle
obs1 = Obstacle(lane=0, z_position=20, obs_type='low')
obstacles.append(obs1)

# Lane 1: High obstacle
obs2 = Obstacle(lane=1, z_position=30, obs_type='high')
obstacles.append(obs2)

# Lane 2: Moving obstacle
obs3 = Obstacle(lane=2, z_position=40, obs_type='moving')
obstacles.append(obs3)

# Another set further back
obs4 = Obstacle(lane=1, z_position=50, obs_type='low')
obstacles.append(obs4)

def update():
    camera_controller.update()

def input(key):
    if key == 'escape':
        quit()
    if key == 'a' or key == 'left arrow':
        player.switch_lane(-1)
    elif key == 'd' or key == 'right arrow':
        player.switch_lane(1)
    elif key == 'space':
        player.jump()
    elif key == 's' or key == 'down arrow':
        player.slide()

print("[TEST] Obstacle test loaded")
print("[TEST] You should see 4 obstacles ahead")
print("[TEST] Yellow (low), Red (high), Orange (moving)")

app.run()
```

Run the test:
```bash
python test_obstacles.py
```

**Verify:**
- [ ] 4 colored cubes visible ahead
- [ ] Yellow cube is short (low)
- [ ] Red cube is tall (high)
- [ ] Orange cube is medium height
- [ ] All obstacles scroll toward you
- [ ] Orange obstacle moves left/right
- [ ] Obstacles disappear when behind you
- [ ] Console shows cleanup messages

---

### Step 3: Update entities/__init__.py

```python
"""
Entities Module
"""
from entities.player import Player
from entities.track import Track
from entities.obstacle import Obstacle

__all__ = ['Player', 'Track', 'Obstacle']
```

---

## ACCEPTANCE CRITERIA

- [ ] Obstacle class exists and inherits from Entity
- [ ] Three types work: 'low', 'high', 'moving'
- [ ] Colors are correct (yellow, red, orange)
- [ ] Sizes match config values
- [ ] Obstacles scroll toward player
- [ ] Moving obstacles shift between lanes
- [ ] Obstacles auto-cleanup when z < -10
- [ ] Console logs creation and destruction
- [ ] No errors during update loop

---

## NEXT PHASE

**Phase 3.2: Spawner System** - Automated obstacle generation

---

**STATUS:** [ ] PHASE 3.1 COMPLETE
