"""Render both complete animation/game-over runs and verify safe node retirement."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import random
import numpy as np
from ursina import application, texture_importer, time, destroy
import main
import config
import systems.score as score_module
from entities.obstacle import Obstacle

OUT = Path('artifacts/animations')
OUT.mkdir(parents=True, exist_ok=True)
score_module.HIGH_SCORE_FILE = str(OUT / 'test_score.json')
app = main.init_game()
application.asset_folder = Path(__file__).resolve().parents[1]
texture_importer.folders[1] = application.asset_folder
application.calculate_dt = False
time.dt = 1 / 60
time.dt_unscaled = time.dt
main.init_entities()


class Pose:
    """Supply classifier outputs at the input seam; no recognition code is changed."""
    state = 'CENTER'
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def get_state(self):
        """Return a reproducible gesture/state."""
        return self.state

    def get_frame(self):
        """Return test preview bytes."""
        return self.frame

    def is_running(self):
        """Return True for the stable test input source."""
        return True


def update():
    """Advance the production callback through Ursina; return None."""
    main.update()


def step(count=1):
    """Advance fixed frames; return None."""
    for _ in range(count):
        app.step()


def capture(name):
    """Save an actual framebuffer; return None."""
    app.graphicsEngine.renderFrame()
    app.win.saveScreenshot(str(OUT / f'{name}.png'))


main.pose_thread = Pose()
main.pose_adapter = main._PoseAdapter(main.pose_thread)
for gender, key in (('female', 'a'), ('male', 'd')):
    random.seed(17)
    main.spawner.reset()
    main.score_manager.reset()
    main.difficulty_manager.reset()
    main.game_state = 'character_select'
    main.init_character_select()
    main.input(key)
    main.input('enter')
    step(185)
    assert main.game_state == 'playing'
    assert main.track.model is None
    assert not main.track.grid_lines
    player = main.player
    collider = player.collider
    scale = tuple(player.scale)
    position = tuple(player.position)
    seen = set()
    for _ in range(50):
        step()
        seen.add(player._frame_index)
        assert tuple(player.scale) == scale
        assert tuple(player.position) == position
        assert player.collider is collider
        assert player.texture.size == (config.PLAYER_SPRITE_CANVAS,) * 2
    assert seen == set(range(8))
    capture(f'{gender}_run')
    main.pose_thread.state = 'JUMP'
    step()
    jump_seen = {player._frame_index}
    while player.vertical_state == 'jumping':
        step()
        if player._current_anim == 'jump':
            jump_seen.add(player._frame_index)
            if player._frame_index == 1:
                capture(f'{gender}_jump')
    assert jump_seen == {0, 1, 2}
    assert player._current_anim == 'run'
    main.pose_thread.state = 'CENTER'
    step()
    main.pose_thread.state = 'CROUCH'
    step()
    crouch_seen = {player._frame_index}
    while player.vertical_state == 'sliding':
        if player.slide_timer < 0.2:
            main.pose_thread.state = 'CENTER'
        step()
        if player._current_anim == 'crouch':
            crouch_seen.add(player._frame_index)
            if player._frame_index == 1:
                capture(f'{gender}_crouch')
    assert crouch_seen == {0, 1, 2}
    assert player._current_anim == 'run'
    assert tuple(player.scale) == scale
    assert tuple(player.position) == position
    assert player.collider is collider
    main.pose_thread.state = 'CENTER'
    # Regression: a destroyed node with enabled still True must never be updated.
    stale = Obstacle(0, 40, 'low')
    main.spawner.obstacles.append(stale)
    destroy(stale)
    assert stale.is_empty()
    passed = Obstacle(0, config.OBSTACLE_DESPAWN_DISTANCE, 'low')
    main.spawner.obstacles.append(passed)
    step()
    assert all(item is not stale and item is not passed for item in main.spawner.obstacles)
    assert passed.is_empty()
    for _ in range(1800):
        step()
        if main.game_state == 'game_over':
            break
    assert main.game_state == 'game_over'
    capture(f'{gender}_game_over')
    assert main.score_manager.distance > 0
    print(f'PASS {gender}: 8 RUN frames, 3 JUMP, 3 CROUCH, fixed collider/transforms, Game Over')
    player.set_flag()
    assert player._current_anim == 'flag'
    assert player.texture.name == f'{gender}_flag.png'
main.pose_hud.destroy()
print('PASS stale NodePaths retired before update; hidden track; both complete runs')
application.quit()
