"""
Collision System - Math-Based Detection

Uses discrete lane matching and distance thresholds.
No physics collision - pure logic.
"""

import config
from entities.obstacle import Obstacle
from entities.collectible import Collectible

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
            # Skip if not an obstacle (e.g. collectible)
            if not isinstance(obs, Obstacle):
                continue
                
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
    
    def check_collectibles(self, player, entities):
        """
        Check if player collects any items.
        
        Args:
            player: Player entity
            entities: List of entities (obstacles + collectibles)
            
        Returns:
            Collectible or None
        """
        player_z = player.z_position if hasattr(player, 'z_position') else 0
        
        for entity in entities:
            # Skip if not a collectible
            if not isinstance(entity, Collectible):
                continue
            
            # Check lane match
            if entity.lane != player.lane:
                continue
            
            # Check distance (close enough to collect)
            distance = abs(entity.z_position - player_z)
            if distance < config.PLAYER_COLLISION_RADIUS: # generous hit box
                return entity
        
        return None

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
