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
