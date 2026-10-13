"""Replay the production game loop using pose states at its input seam, not MediaPipe."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import random
import numpy as np
from ursina import application, texture_importer, time, destroy
import main
import config
from entities.obstacle import Obstacle

OUTPUT = Path('artifacts/flow')
OUTPUT.mkdir(parents=True, exist_ok=True)
app = main.init_game()
application.asset_folder = Path(__file__).resolve().parents[1]
texture_importer.folders[1] = application.asset_folder
application.calculate_dt = False
DT = 0.1
time.dt = DT
time.dt_unscaled = DT
random.seed(17)
import systems.score as score_module
score_module.HIGH_SCORE_FILE = str(OUTPUT / 'test_high_score.json')


class PoseReplay:
    """Controlled outputs of a pose controller; does not run or replace classifiers."""

    def __init__(self):
        """Start without posture or hardware; return None."""
        self.state = 'NO_POSE'
        self.frame = None
        self.running = True

    def is_running(self):
        """Return simulated worker health."""
        return self.running

    def start(self):
        """Mark the replacement worker active; return None."""
        self.running = True

    def stop(self):
        """Mark the old worker stopped; return None."""
        self.running = False

    def get_state(self):
        """Return the scripted classifier output."""
        return self.state

    def get_frame(self):
        """Return a synthetic BGR frame or None."""
        return self.frame


def update():
    """Run the unchanged production callback through Ursina's engine; return None."""
    main.update()


def advance(frames=1):
    """Advance fixed frames through the actual Ursina loop; return None."""
    for _ in range(frames):
        app.step()


def capture(name):
    """Save a real framebuffer for visual checks; return None."""
    app.graphicsEngine.renderFrame()
    app.win.saveScreenshot(str(OUTPUT / f'{name}.png'))


main.init_entities()
main.init_character_select()
main.pose_thread = PoseReplay()
main.pose_adapter = main._PoseAdapter(main.pose_thread)
advance(2)
capture('01_menu_unchanged')
main.input('d')
main.input('enter')
assert main.game_state == 'calibration'
assert not main.player.enabled
assert main.player.texture in main.player._animation_frames['run']
assert main.camera_controller.player is main.player
advance(10)
assert main.game_state == 'calibration'
assert main.score_manager.distance == 0
assert not main.spawner.obstacles
assert main.track.scroll_offset == 0
capture('02_no_camera_blocks_start')
main.pose_thread.state = 'CENTER'
advance(2)
assert main.game_state == 'calibration'
assert not main.player.enabled

main.pose_thread.frame = np.full((480, 640, 3), (92, 80, 48), dtype=np.uint8)
main.pose_thread.state = 'CALIBRATING'
advance(10)
assert main.game_state == 'calibration'
assert main.score_manager.distance == 0
assert main.pose_hud._cam.scale_y == config.UI_CALIBRATION_CAMERA_HEIGHT
capture('03_large_calibration_camera')
main.input('c')
advance()
assert not main.pose_hud._cam_root.enabled
main.input('c')
advance()
assert main.pose_hud._cam_root.enabled

main.pose_thread.state = 'CENTER'
advance()
assert main.game_state == 'countdown'
assert main.countdown_text.text == '3'
capture('04_countdown_3')
main.pose_thread.state = 'NO_POSE'
advance()
assert main.game_state == 'calibration'
assert not main.player.enabled
main.pose_thread.state = 'CENTER'
seen = set()
for _ in range(35):
    advance()
    if main.game_state == 'countdown':
        number = main.countdown_text.text
        if number not in seen:
            capture(f'05_countdown_{number}')
        seen.add(number)
    if main.game_state == 'playing':
        break
assert seen == {'3', '2', '1'}
assert main.game_state == 'playing'
assert main.player.enabled
assert main.player.ignore
assert main.player.texture in main.player._animation_frames['run']
advance()
assert abs(main.pose_hud._cam.scale_y - config.UI_WEBCAM_HEIGHT) < 0.00001
capture('06_running_player_visible')
advance(45)
assert main.game_state == 'playing'
assert main.score_manager.distance > 50
assert main.track.scroll_offset > 0
assert main.spawner.obstacles
assert all(o.ignore for o in main.spawner.obstacles)
assert any(o.z_position < config.OBSTACLE_SPAWN_DISTANCE for o in main.spawner.obstacles)
capture('07_obstacles_and_scroll')
# Isolate gesture checks from random approaching obstacles; collision tested below.
main.spawner.reset()

main.pose_thread.state = 'LEFT'
advance()
assert main.player.lane == 0
capture('08_left')
main.pose_thread.state = 'RIGHT'
advance()
assert main.player.lane == 2
capture('09_right')
main.pose_thread.state = 'JUMP'
advance(2)
assert main.player.vertical_state == 'jumping'
assert main.player.y > config.PLAYER_START_Y
assert main.player.texture in main.player._animation_frames['jump']
capture('10_jump')
main.pose_thread.state = 'CENTER'
advance(5)
assert main.player.vertical_state == 'grounded'
main.pose_thread.state = 'CROUCH'
advance()
assert main.player.vertical_state == 'sliding'
assert main.player.texture in main.player._animation_frames['crouch']
capture('11_crouch')
main.pose_thread.state = 'CENTER'
advance(9)
assert main.player.vertical_state == 'grounded'
assert main.player.texture in main.player._animation_frames['run']

main.input('escape')
distance = main.score_manager.distance
positions = [o.z_position for o in main.spawner.obstacles]
advance(4)
assert main.score_manager.distance == distance
assert [o.z_position for o in main.spawner.obstacles] == positions
main.input('escape')
main.spawner.reset()
speed, _ = main.difficulty_manager.update(main.score_manager.distance)
obstacle = Obstacle(main.player.lane, config.TRACK_SCROLL_SPEED * DT + 0.75, 'low')
main.spawner.obstacles.append(obstacle)
advance()
assert main.game_state == 'game_over'
assert main.hud.game_over_text.enabled
capture('12_collision_game_over')
distance = main.score_manager.distance
advance(4)
assert main.score_manager.distance == distance

main.input('r')
assert main.game_state == 'calibration'
assert not main.player.enabled
main.pose_thread.state = 'CALIBRATING'
advance(2)
assert main.game_state == 'calibration'
assert not main.hud.game_over_text.enabled
main.game_state = 'character_select'
main.init_character_select()
main.input('a')
main.input('enter')
assert main.game_state == 'calibration'
assert main.player.texture in main.player._animation_frames['run']
main.pose_thread.state = 'CENTER'
advance(35)
assert main.game_state == 'playing'
assert main.player.enabled
capture('13_female_running')
# Simulate a stopped capture worker: no stale frame or automatic gameplay resume.
distance = main.score_manager.distance
positions = [o.z_position for o in main.spawner.obstacles]
previous = main.pose_thread
previous.frame = None
previous.state = 'NO_POSE'
previous.running = False
factory = main.PoseThread
main.PoseThread = PoseReplay
advance()
main.PoseThread = factory
assert main.pose_thread is not previous
assert main.game_state == 'calibration'
assert not main.player.enabled
assert main.score_manager.distance == distance
assert [o.z_position for o in main.spawner.obstacles] == positions
main.pose_thread.frame = np.full((480, 640, 3), (92, 80, 48), dtype=np.uint8)
main.pose_thread.state = 'CALIBRATING'
advance(5)
assert main.game_state == 'calibration'
assert main.score_manager.distance == distance
main.pose_thread.state = 'CENTER'
advance(35)
assert main.game_state == 'playing'
assert main.player.enabled
assert main.score_manager.distance >= distance
capture('15_camera_reconnection')
print('PASS: camera worker replacement, frozen run, recalibration and countdown')
main.pose_hud.destroy()
print('PASS: selection -> calibration -> 3/2/1 -> run -> obstacles -> '
      'LEFT/RIGHT -> JUMP -> CROUCH -> collision/Game Over; synthetic pose outputs')
application.quit()


