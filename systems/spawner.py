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
        """Initialize spaced spawning with an optional difficulty manager; return None."""
        self.spawn_timer = config.SPAWN_INTERVAL_MAX
        self.obstacles = []  # Track all active obstacles (and collectibles)
        self._pending_obstacle = None
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
            if self.spawn_obstacle() is None:
                return
            
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
            
            self.spawn_timer = max(config.OBSTACLE_MIN_REACTION_SECONDS,
                                   base_interval * multiplier)
    
    def spawn_obstacle(self):
        """
        Create a hazard only when its arrival window is safely separated.

        Returns:
            Obstacle or None: Spawned hazard, or None while the pending slot is unsafe.
        """
        if self._pending_obstacle is None:
            obs_type = random.choice(['low', 'high', 'moving'])
            valid_lanes = [lane for lane in range(config.LANE_COUNT) if lane != self.last_lane]
            lane = random.choice(valid_lanes)
            self._pending_obstacle = (lane, obs_type)
        lane, obs_type = self._pending_obstacle
        distance = (config.PORTICO_SPAWN_DISTANCE if obs_type == 'high'
                    else config.OBSTACLE_SPAWN_DISTANCE)
        self.cleanup_obstacles()
        gap = max(config.OBSTACLE_MIN_SPAWN_GAP,
                  config.TRACK_SCROLL_SPEED * config.OBSTACLE_MIN_REACTION_SECONDS)
        # One hazard at a time in each reaction window, including portal arrival order.
        if any(isinstance(item, Obstacle) and abs(distance - item.z_position) < gap
               for item in self.obstacles):
            return None
        obs = Obstacle(lane, distance, obs_type)
        self.obstacles.append(obs)
        self.last_lane = lane
        self._pending_obstacle = None
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
        self.obstacles = [obs for obs in self.obstacles
                          if not obs.is_empty() and obs.enabled]
    
    def retire(self, entity):
        """Remove an entity before destroying its NodePath; return None."""
        self.obstacles = [item for item in self.obstacles if item is not entity]
        if not entity.is_empty():
            entity.enabled = False
            destroy(entity)

    def update_entities(self):
        """Prune stale nodes before updating and immediately retire passed entities."""
        self.cleanup_obstacles()
        for entity in tuple(self.obstacles):
            if entity.is_empty():
                self.retire(entity)
                continue
            entity.ignore = True
            # Retire before update can destroy its own node on the despawn boundary.
            next_z = entity.z_position - config.TRACK_SCROLL_SPEED * time.dt
            if next_z < config.OBSTACLE_DESPAWN_DISTANCE:
                self.retire(entity)
                continue
            entity.update()
            if entity.is_empty():
                self.retire(entity)
        self.cleanup_obstacles()

    def reset(self):
        """
        Clear all obstacles and reset spawner.
        """
        for obs in tuple(self.obstacles):
            self.retire(obs)
        self.spawn_timer = config.SPAWN_INTERVAL_MAX
        self._pending_obstacle = None
        print("[SPAWNER] Reset")
