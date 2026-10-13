"""
Collectible Entity - Arcade Logic Rewards

Collectibles are simple spheres that:
1. Stay in their assigned lane
2. Move toward the player (decreasing Z)
3. Get collected on proximity
"""

from ursina import *
import config

class Collectible(Entity):
    """
    Collectible entity with type-based behavior.
    
    Types:
    - 'orb': Points (gold)
    - 'shield': Invincibility (azure)
    """
    
    def __init__(self, lane, z_position, item_type):
        """
        Create a collectible.
        
        Args:
            lane (int): Lane index (0, 1, or 2)
            z_position (float): Starting Z coordinate
            item_type (str): 'orb' or 'shield'
        """
        # Set properties based on type
        if item_type == 'orb':
            color = config.COLOR_ORB
            texture = config.TEXTURE_ORB
        elif item_type == 'shield':
            color = config.COLOR_SHIELD
            texture = config.TEXTURE_ORB # Reuse orb texture for now
        else:
            raise ValueError(f"Invalid collectible type: {item_type}")
        
        # Calculate X position from lane
        x_pos = config.LANE_POSITIONS[lane]
        
        # Initialize entity
        super().__init__(
            model='sphere',
            color=color,
            texture=texture,
            scale=config.COLLECTIBLE_SIZE,
            position=(x_pos, config.COLLECTIBLE_HEIGHT, z_position),
            collider='box'
        )
        
        # Store state
        self.lane = lane
        self.z_position = z_position
        self.item_type = item_type
        
        print(f"[COLLECTIBLE] Created {item_type} at lane {lane}, z={z_position}")
    
    def update(self):
        """
        Update collectible position.
        Scrolls toward player.
        """
        # Scroll toward player
        self.z_position -= config.TRACK_SCROLL_SPEED * time.dt
        self.z = self.z_position
        
        # Auto-cleanup if behind player
        if self.z_position < config.OBSTACLE_DESPAWN_DISTANCE:
            self.cleanup()
    
    def cleanup(self):
        """
        Remove this item from the game.
        """
        destroy(self)
