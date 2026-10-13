"""
VFX System - Visual Juice
"""

from ursina import *
import random
import config

class VFXManager:
    """
    Manages visual effects like screen shake and particles.
    """
    
    def __init__(self):
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = Vec3(0, 0, 0)
        
        print("[VFX] Initialized")
    
    def update(self):
        """
        Update effects.
        """
        # Update shake
        if self.shake_timer > 0:
            self.shake_timer -= time.dt
            
            # Random offset based on intensity
            # Decay intensity over time
            current_intensity = self.shake_intensity * (self.shake_timer / config.SHAKE_DURATION_COLLISION)
            
            self.shake_offset = Vec3(
                random.uniform(-current_intensity, current_intensity),
                random.uniform(-current_intensity, current_intensity),
                0
            )
            
            if self.shake_timer <= 0:
                self.shake_offset = Vec3(0, 0, 0)
        else:
            self.shake_offset = Vec3(0, 0, 0)
            
    def shake_camera(self, intensity, duration):
        """
        Trigger screen shake.
        """
        self.shake_intensity = intensity
        self.shake_timer = duration
        print(f"[VFX] Shake triggered: {intensity}")
        
    def create_particles(self, position, color, count=10):
        """
        Create simple particle explosion.
        """
        for _ in range(count):
            # Create a small cube that flies out
            p = Entity(
                model='cube',
                color=color,
                scale=0.2,
                position=position,
                collider=None
            )
            
            # Give it random velocity
            velocity = Vec3(
                random.uniform(-5, 5),
                random.uniform(5, 10),
                random.uniform(-5, 5)
            )
            
            # Animate it
            p.animate_position(p.position + velocity, duration=0.5, curve=curve.out_expo)
            p.animate_scale(0, duration=0.5, curve=curve.linear)
            
            # Destroy after animation
            destroy(p, delay=0.5)
