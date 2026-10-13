# PHASE 3.2: SPAWNER SYSTEM

## WHY
Automated obstacle spawning creates the endless runner gameplay loop. The spawner manages:
- Random obstacle generation
- Spawn timing (difficulty-based)
- Lane distribution (avoidance patterns)
- Prevents impossible situations

## WHAT
- Spawner system that creates obstacles at regular intervals
- Random type selection (low, high, moving)
- Random lane selection (with fairness logic)
- Spawn timer management
- List tracking for all active obstacles

## HOW

Create `systems/spawner.py`:

```python
"""
Spawner System - Procedural Obstacle Generation
"""

import random
from entities.obstacle import Obstacle
import config

class ObstacleSpawner:
    """
    Manages procedural obstacle spawning.
    Creates varied patterns while avoiding impossible situations.
    """
    
    def __init__(self):
        self.spawn_timer = config.SPAWN_INTERVAL_MAX
        self.obstacles = []  # Track all active obstacles
        self.last_lane = 1  # Avoid spawning same lane twice
        
        print("[SPAWNER] Initialized")
    
    def update(self, current_speed):
        """
        Update spawner each frame.
        
        Args:
            current_speed (float): Current track scroll speed
        """
        self.spawn_timer -= time.dt
        
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            
            # Calculate next spawn interval (scales with speed)
            base_interval = random.uniform(
                config.SPAWN_INTERVAL_MIN,
                config.SPAWN_INTERVAL_MAX
            )
            speed_factor = config.TRACK_SCROLL_SPEED / current_speed
            self.spawn_timer = base_interval * speed_factor
    
    def spawn_obstacle(self):
        """
        Create a new obstacle at spawn distance.
        """
        # Choose random type
        obs_type = random.choice(['low', 'high', 'moving'])
        
        # Choose lane (avoid same lane as last time)
        valid_lanes = [0, 1, 2]
        if self.last_lane in valid_lanes:
            valid_lanes.remove(self.last_lane)
        lane = random.choice(valid_lanes)
        self.last_lane = lane
        
        # Create obstacle
        obs = Obstacle(lane, config.OBSTACLE_SPAWN_DISTANCE, obs_type)
        self.obstacles.append(obs)
        
        return obs
    
    def cleanup_obstacles(self):
        """
        Remove obstacles that have been destroyed.
        """
        self.obstacles = [obs for obs in self.obstacles if obs.enabled]
    
    def reset(self):
        """
        Clear all obstacles and reset spawner.
        """
        for obs in self.obstacles:
            destroy(obs)
        self.obstacles.clear()
        self.spawn_timer = config.SPAWN_INTERVAL_MAX
        print("[SPAWNER] Reset")
```

Update `main.py` to use spawner:

```python
from systems.spawner import ObstacleSpawner

# In init_entities():
spawner = ObstacleSpawner()

# In update():
spawner.update(config.TRACK_SCROLL_SPEED)
spawner.cleanup_obstacles()
```

## ACCEPTANCE CRITERIA
- [ ] Obstacles spawn automatically every 0.8-1.5 seconds
- [ ] Random types (low, high, moving)
- [ ] Random lanes (avoids consecutive same lane)
- [ ] Obstacles scroll smoothly toward player
- [ ] Old obstacles are cleaned up
- [ ] No memory leaks

**STATUS:** [ ] PHASE 3.2 COMPLETE
