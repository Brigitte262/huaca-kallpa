"""
Spawner System - Procedural Obstacle Generation
"""

import random
from ursina import *
from entities.obstacle import Obstacle
from entities.collectible import Collectible
import config

class ObstacleSpawner:
    """
    Manages procedural obstacle spawning.
    Creates varied patterns while avoiding impossible situations.
    """
    
    def __init__(self, difficulty_manager=None):
        self.spawn_timer = config.SPAWN_INTERVAL_MAX
        self.obstacles = []  # Track all active obstacles (and collectibles)
        self.last_lane = 1  # Avoid spawning same lane twice
        self.difficulty_manager = difficulty_manager
        
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
            
            # Chance to spawn collectible
            if random.random() < config.COLLECTIBLE_SPAWN_CHANCE:  # 30% chance
                self.spawn_collectible()
            
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
    
    def spawn_collectible(self):
        """
        Create a new collectible.
        """
        # Choose random type (mostly orbs, rare shields)
        item_type = 'orb'
        if random.random() < 0.1:  # 10% chance for shield
            item_type = 'shield'
        
        # Choose lane (try to put it in a different lane than the obstacle if possible)
        # For simplicity, just random lane for now, or maybe the same lane as obstacle if it's jumpable?
        # Let's pick a random lane that ISN'T the last obstacle lane to encourage movement
        valid_lanes = [0, 1, 2]
        if self.last_lane in valid_lanes:
            valid_lanes.remove(self.last_lane)
        lane = random.choice(valid_lanes)
        
        # Spawn slightly behind the obstacle so it doesn't overlap perfectly?
        # Or just same distance.
        # Let's spawn it at same distance but different lane.
        
        item = Collectible(lane, config.OBSTACLE_SPAWN_DISTANCE, item_type)
        self.obstacles.append(item)
        
        return item
    
    def cleanup_obstacles(self):
        """
        Remove obstacles that have been destroyed.
        """
        # Keep only obstacles that still exist (enabled is Ursina property)
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
