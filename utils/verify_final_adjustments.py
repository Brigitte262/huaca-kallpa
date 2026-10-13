"""Verify spacing and real landmark-to-action dispatch without a webcam or MP changes."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from types import SimpleNamespace
import random
import numpy as np
from ursina import application, texture_importer, time, destroy
import main
import config
from vision.pose_thread import PoseThread
from entities.obstacle import Obstacle
import systems.score as score_module

OUT = Path('artifacts/final_adjustments')
OUT.mkdir(parents=True, exist_ok=True)
score_module.HIGH_SCORE_FILE = str(OUT / 'test_score.json')
app = main.init_game()
application.asset_folder = Path(__file__).resolve().parents[1]
texture_importer.folders[1] = application.asset_folder
application.calculate_dt = False
time.dt = 1 / 60
time.dt_unscaled = time.dt
main.init_entities()
source = PoseThread()
clock = 0.0
crouch_frames_seen = []


class Input:
    """Publish actual classifier/bridge results at the production game's input seam."""
    state = 'CALIBRATING'
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def get_state(self):
        """Return the classified input state."""
        return self.state

    def get_frame(self):
        """Return a synthetic BGR preview."""
        return self.frame

    def is_running(self):
        """Return True for the controlled input source."""
        return True


main.pose_thread = Input()
main.pose_adapter = main._PoseAdapter(main.pose_thread)


def update():
    """Run production gameplay through Ursina's callback; return None."""
    main.update()


def points(arms=False, bent=False, lane_x=0.5):
    """Return plausible MP-format landmarks for neutral, raised arms or a forward bend."""
    items = [SimpleNamespace(x=0.5, y=0.5, z=0, visibility=1, presence=1)
             for _ in range(33)]
    for i in config.BODY_ACTION_HEAD_INDICES:
        items[i].y = 0.45 if bent else 0.2
    for i in (11, 12):
        items[i].x = lane_x
        items[i].y = 0.445 if bent else 0.4
    for i in (23, 24):
        items[i].y = 0.727 if bent else 0.7
    for i in (15, 16):
        items[i].y = 0.08 if arms else 0.65
    return items


def feed(landmarks, frames):
    """Pass landmarks through the original classifier, bridge, and Player dispatch."""
    global clock
    for _ in range(frames):
        clock += time.dt
        center = ((landmarks[11].x + landmarks[12].x) / 2, landmarks[11].y)
        fallback = source._classify(landmarks, center, clock)
        main.pose_thread.state = source._body_actions.classify(
            landmarks, fallback, clock, source._vert_baseline)
        app.step()
        if main.player._current_anim == 'crouch':
            index = main.player._frame_index
            if index not in crouch_frames_seen:
                crouch_frames_seen.append(index)
                capture(f'crouch_{index + 1:02d}')


def capture(name):
    """Save an actual game framebuffer; return None."""
    app.graphicsEngine.renderFrame()
    app.win.saveScreenshot(str(OUT / f'{name}.png'))


main.init_character_select()
main.input('enter')
feed(points(), 350)
assert source._vert_baseline is not None
assert main.game_state == 'playing'
main.spawner.spawn_timer = 1000  # Isolate gesture mechanics before spacing simulation.
feed(points(arms=True), 10)
assert main.pose_thread.state == 'JUMP'
assert main.player.vertical_state == 'jumping'
capture('01_arms_up_jump')
feed(points(), 60)
assert main.player.vertical_state == 'grounded'
baseline_before_bend = source._vert_baseline
source._body_actions.debug_crouch = True  # Diagnostics only during this controlled trial.
feed(points(bent=True), 10)
assert main.pose_thread.state == 'CROUCH'
assert main.player.vertical_state == 'sliding'
feed(points(bent=True), 70)
assert main.player.vertical_state == 'sliding'
assert main.player._current_anim == 'crouch'
assert main.player._frame_index == 2
assert crouch_frames_seen == [0, 1, 2]
assert source._vert_baseline == baseline_before_bend
capture('02_bent_torso_crouch')
# A high portal at the real collision boundary must be avoided while crouch is held.
portal = Obstacle(main.player.lane,
                  config.OBSTACLE_COLLISION_THRESHOLD + config.TRACK_SCROLL_SPEED * time.dt,
                  'high')
main.spawner.obstacles.append(portal)
feed(points(bent=True), 10)
assert main.game_state == 'playing'
assert main.player.vertical_state == 'sliding'
capture('03_portal_passed_crouching')
feed(points(), 12)
assert main.pose_thread.state == 'CROUCH'  # Neutral jitter cannot end the hold early.
feed(points(), 48)
assert main.player.vertical_state == 'grounded'
assert main.player._current_anim == 'run'
source._body_actions.debug_crouch = False
main.spawner.reset()

# Verify the original lateral classifier remains connected too.
main.spawner.spawn_timer = 1000
feed(points(lane_x=0.3), 15)
assert main.player.lane == 0
feed(points(lane_x=0.7), 15)
assert main.player.lane == 2
feed(points(), 15)
assert main.player.lane == 1

# Portals still collide when standing or jumping; only SLIDE avoids them.
portal = Obstacle(1, 0.75, 'high')
portal.ignore = True
for state, expected in (('grounded', True), ('jumping', True), ('sliding', False)):
    main.player.vertical_state = state
    assert main.collision_detector.check_collision(main.player, [portal])[0] == expected
main.player.reset()
destroy(portal)

# An action requested while the player is busy must remain available after landing.
main.spawner.spawn_timer = 1000
main._last_pose_state = 'CENTER'
main.pose_thread.state = 'JUMP'
app.step()
assert main.player.vertical_state == 'jumping'
main.pose_thread.state = 'CROUCH'
for _ in range(35):
    app.step()
assert main.player.vertical_state == 'sliding'
main.pose_thread.state = 'CENTER'
for _ in range(60):
    app.step()
assert main.player.vertical_state == 'grounded'

# Simulate many spawn decisions at high difficulty without collision intervention.
main.spawner.reset()
random.seed(42)
main.difficulty_manager.difficulty_multiplier = config.MAX_SPEED / config.INITIAL_SPEED
last_spawn = None
seen = set()
spawn_history = []
spawn_times = []
for frame in range(7200):
    elapsed = frame * time.dt
    main.spawner.update(config.MAX_SPEED)
    current = [item for item in main.spawner.obstacles if isinstance(item, Obstacle)]
    for item in current:
        if id(item) not in seen:
            seen.add(id(item))
            spawn_history.append(item)
            if last_spawn is not None:
                assert elapsed - last_spawn >= config.OBSTACLE_MIN_REACTION_SECONDS - time.dt
            last_spawn = elapsed
            spawn_times.append((elapsed, item.obs_type, item.z_position))
            if item.obs_type == 'high':
                assert item.z_position == config.PORTICO_SPAWN_DISTANCE
        for other in current:
            if item is not other:
                assert abs(item.z_position - other.z_position) >= (
                    config.OBSTACLE_MIN_SPAWN_GAP - config.TRACK_SCROLL_SPEED * time.dt)
    main.spawner.update_entities()
assert len(spawn_times) >= 20
assert any(kind == 'high' for _, kind, _ in spawn_times)
(OUT / 'spawn_times.txt').write_text('\n'.join(map(str, spawn_times)), encoding='utf-8')
print('PASS: calibrated landmarks -> arms JUMP -> bent torso held CROUCH -> portal safely passed')
print('PASS: LEFT/RIGHT, high requires SLIDE, minimum time/distance and isolated hazard windows')
print('Spawns checked:', len(spawn_times))
main.spawner.reset()
main.pose_hud.destroy()
application.quit()
