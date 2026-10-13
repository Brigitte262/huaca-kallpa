

"""
Camera System - Smooth Follow

The camera follows the player's lane position smoothly.
Y and Z are fixed, only X position follows.
"""

from ursina import *
import config

class CameraController:
    """
    Manages camera behavior.
    """
    
    def __init__(self, player):
        """
        Initialize camera controller.
        
        Args:
            player: The player entity to follow
        """
        self.player = player
        
        self.offset = Vec3(config.CAMERA_POSITION)
        self.target_fov = 90
        
        # VFX
        self.shake_offset = Vec3(0, 0, 0)
        self.target_tilt = 0.0
        self.current_tilt = 0.0
        
        # Set initial position
        camera.position = self.player.position + self.offset
        camera.rotation_x = config.CAMERA_ROTATION_X
        
        print("[CAMERA] Initialized")
    
    def update(self):
        """
        Update camera position to follow player smoothly.
        """
        if not self.player:
            return
            
        # Calculate target position
        # We only follow X, keep Y and Z relative
        target_pos = self.player.position + self.offset
        
        # Smoothly interpolate to target X
        # We want strict following for gameplay, but smooth for feel
        # Actually, for arcade runners, camera usually stays centered on track X=0
        # or follows player slightly.
        # Let's follow player X with some lag.
        
        # Current implementation:
        # camera.position = lerp(camera.position, target_pos, config.CAMERA_FOLLOW_SPEED)
        
        # Better implementation for this genre:
        # Keep Z fixed relative to player (or track)
        # Keep Y fixed relative to ground (or player jump?)
        # Follow X loosely.
        
        # Let's stick to simple lerp for now but ensure Z is correct
        # The player stays at Z=0, track moves. So camera should stay at Z=-12.
        
        target_x = self.player.x * 0.5 # Follow a bit, but not fully
        target_y = config.CAMERA_POSITION[1] # Fixed height
        target_z = config.CAMERA_POSITION[2] # Fixed depth
        
        target_pos = Vec3(target_x, target_y, target_z)
        
        # Apply shake
        target_pos += self.shake_offset
        
        camera.position = lerp(camera.position, target_pos, config.CAMERA_FOLLOW_SPEED * 60 * time.dt)
        
        # Tilt logic
        # Tilt based on player lane position or movement?
        # Let's tilt based on player X
        self.target_tilt = -self.player.x * config.CAMERA_TILT_ANGLE
        self.current_tilt = lerp(self.current_tilt, self.target_tilt, config.CAMERA_TILT_SPEED * time.dt)
        
        camera.rotation_z = self.current_tilt
