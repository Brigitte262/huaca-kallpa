# PHASE 3.3: COLLISION DETECTION

## WHY

This is the **heart of arcade logic**. No physics raycasts, no mesh intersections - just pure math:
```python
if player_lane == obstacle_lane and distance < threshold:
    if can_avoid(player_state, obstacle_type):
        pass  # Jumped over or slid under
    else:
        game_over()  # Collision!
```

Deterministic, testable, bug-free.

---

## WHAT

- Math-based collision system
- State-aware avoidance (jump over low, slide under high)
- Game over trigger
- No Ursina collision system (unreliable for moving objects)

---

## HOW

Create `systems/collision.py`:

```python
"""
Collision System - Math-Based Detection

Uses discrete lane matching and distance thresholds.
No physics collision - pure logic.
"""

import config

class CollisionDetector:
    """
    Detects collisions between player and obstacles.
    
    Collision rules:
    - Same lane AND close distance = potential collision
    - Jump avoids LOW obstacles
    - Slide avoids HIGH obstacles
    - Cannot avoid MOVING obstacles (must change lanes)
    """
    
    def __init__(self):
        print("[COLLISION] Initialized")
    
    def check_collision(self, player, obstacles):
        """
        Check if player collides with any obstacle.
        
        Args:
            player: Player entity with lane and vertical_state
            obstacles: List of Obstacle entities
        
        Returns:
            tuple: (collided, obstacle) or (False, None)
        """
        player_z = player.z_position if hasattr(player, 'z_position') else 0
        
        for obs in obstacles:
            # Check lane match
            if obs.lane != player.lane:
                continue  # Not in same lane
            
            # Check distance
            distance = obs.z_position - player_z
            if distance < 0 or distance > config.OBSTACLE_COLLISION_THRESHOLD:
                continue  # Too far away
            
            # Check if player can avoid
            if self.can_avoid(player.vertical_state, obs.obs_type):
                continue  # Successfully avoided
            
            # Collision detected!
            return (True, obs)
        
        return (False, None)
    
    def can_avoid(self, player_state, obstacle_type):
        """
        Determine if player's current state avoids obstacle type.
        
        Args:
            player_state (str): 'grounded', 'jumping', or 'sliding'
            obstacle_type (str): 'low', 'high', or 'moving'
        
        Returns:
            bool: True if avoided, False if collision
        """
        # Low obstacles: jump to avoid
        if obstacle_type == 'low':
            return player_state == 'jumping'
        
        # High obstacles: slide to avoid
        elif obstacle_type == 'high':
            return player_state == 'sliding'
        
        # Moving obstacles: cannot avoid (must be in different lane)
        elif obstacle_type == 'moving':
            return False
        
        return False
```

Update `main.py`:

```python
from systems.collision import CollisionDetector

# Global state
game_state = 'playing'  # playing, game_over
collision_detector = None

# In init_entities():
collision_detector = CollisionDetector()

# In update():
if game_state == 'playing':
    # Check collisions
    collided, obstacle = collision_detector.check_collision(player, spawner.obstacles)
    
    if collided:
        print(f"[GAME] Collision with {obstacle.obs_type} obstacle!")
        game_state = 'game_over'
```

---

## ACCEPTANCE CRITERIA

- [ ] Collision detected when same lane + close distance
- [ ] Jumping avoids LOW obstacles
- [ ] Sliding avoids HIGH obstacles
- [ ] Cannot avoid MOVING obstacles
- [ ] Game state changes to 'game_over' on collision
- [ ] Console logs collision events
- [ ] No false positives (collision when shouldn't)
- [ ] No false negatives (miss actual collisions)

### Test Cases

**Test 1: Jump over LOW**
- Spawn LOW obstacle in current lane
- Jump when close
- Should NOT collide

**Test 2: Slide under HIGH**
- Spawn HIGH obstacle in current lane
- Slide when close
- Should NOT collide

**Test 3: Hit LOW (no jump)**
- Spawn LOW obstacle in current lane
- Don't jump
- Should collide → game over

**Test 4: Hit HIGH (no slide)**
- Spawn HIGH obstacle in current lane
- Don't slide
- Should collide → game over

**Test 5: Avoid by lane change**
- Spawn obstacle in lane 1
- Switch to lane 0 or 2
- Should NOT collide

---

**STATUS:** [ ] PHASE 3.3 COMPLETE
