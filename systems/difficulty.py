"""
Difficulty System - Progressive Challenge
"""

import config

class DifficultyManager:
    """
    Manages game difficulty scaling based on distance traveled.
    """
    
    def __init__(self):
        self.current_speed = config.INITIAL_SPEED
        self.difficulty_multiplier = 1.0
        
        print("[DIFFICULTY] Initialized")
    
    def update(self, distance):
        """
        Update difficulty parameters based on distance.
        
        Args:
            distance (float): Total distance traveled
        """
        # Calculate speed based on distance
        # Formula: initial + (distance / scale) * 2
        # Example: 20 + (500 / 500) * 2 = 22 (+10% every 500m)
        
        speed_increase = (distance / config.DIFFICULTY_SCALE_DISTANCE) * 2.0
        target_speed = config.INITIAL_SPEED + speed_increase
        
        # Cap at max speed
        self.current_speed = min(target_speed, config.MAX_SPEED)
        
        # Calculate multiplier (1.0 to 2.5)
        self.difficulty_multiplier = self.current_speed / config.INITIAL_SPEED

        return self.current_speed, self.difficulty_multiplier

        
    def get_spawn_interval_multiplier(self):
        """
        Get multiplier for spawn intervals.
        Faster speed = smaller interval (more frequent spawns).
        """
        # Inverse of difficulty multiplier, but maybe not linear
        # If speed doubles (2.0), interval should halve (0.5) to keep same density?
        # Actually, if speed doubles, we cover ground 2x faster.
        # If we keep same time interval, distance between obstacles doubles.
        # To keep same distance density, we must halve the time interval.
        # So yes, 1 / multiplier.
        
        return 1.0 / self.difficulty_multiplier

    def reset(self):
        """
        Reset difficulty to initial state.
        """
        self.current_speed = config.INITIAL_SPEED
        self.difficulty_multiplier = 1.0
        config.TRACK_SCROLL_SPEED = config.INITIAL_SPEED
        print("[DIFFICULTY] Reset")
