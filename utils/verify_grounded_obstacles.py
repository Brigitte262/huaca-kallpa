"""Verify all six obstacle assets on the rendered road with unchanged collision rules."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from unittest.mock import patch
from ursina import application, texture_importer, time, destroy
import main
import config
from entities.obstacle import Obstacle
from systems.obstacle_projection import project_obstacle

OUT = Path('artifacts/obstacles_grounded')
OUT.mkdir(parents=True, exist_ok=True)
app = main.init_game()
application.asset_folder = Path(__file__).resolve().parents[1]
texture_importer.folders[1] = application.asset_folder
application.calculate_dt = False
time.dt = 1 / 60
time.dt_unscaled = time.dt
main.init_entities()
main.pose_hud.root.enabled = False
main.player.enabled = True
main.player.ignore = True
for _ in range(120):
    main.camera_controller.update()
assets = (
    ('piedra', 'low'), ('vasija', 'low'), ('bloque_ceremonial', 'low'),
    ('muro_bajo', 'moving'), ('columna_caida', 'moving'), ('portico_alto', 'high'),
)
for asset, obs_type in assets:
    path = f'assets/obstacles/{asset}.png'
    obstacles = []
    with patch('entities.obstacle.random.choice', return_value=path):
        for lane, depth in enumerate((60, 25, 2)):
            obstacle = Obstacle(lane, depth, obs_type)
            obstacle.ignore = True
            obstacles.append(obstacle)
    for _ in range(5):
        app.step()
    app.win.saveScreenshot(str(OUT / f'{asset}.png'))
    widths = [item.screen_projection[2] for item in obstacles]
    bottoms = [item.screen_projection[1] for item in obstacles]
    assert widths[0] < widths[1] < widths[2]
    assert bottoms[0] > bottoms[1] > bottoms[2]
    for obstacle in obstacles:
        lane = obstacle.lane
        for _ in range(10):
            obstacle.update()
            assert obstacle.lane == lane
            assert obstacle.x == config.LANE_POSITIONS[lane]
            assert obstacle._visual.origin_y == -0.5
        visual = obstacle._visual
        main.spawner.obstacles.append(obstacle)
        main.spawner.retire(obstacle)
        assert obstacle.is_empty()
        assert visual.is_empty()
    print(f'PASS {asset}: grounded base, perspective growth, fixed lane, visual cleanup')

# Collision is still determined solely by logical lane/z/type/state.
for obs_type in ('low', 'high', 'moving'):
    obstacle = Obstacle(1, 0.75, obs_type)
    obstacle.ignore = True
    for state in ('grounded', 'jumping', 'sliding'):
        main.player.vertical_state = state
        hit, _ = main.collision_detector.check_collision(main.player, [obstacle])
        avoids = (obs_type == 'low' and state == 'jumping') or (
            obs_type == 'high' and state == 'sliding')
        assert hit == (not avoids)
    obstacle.z_position = -0.1
    assert not main.collision_detector.check_collision(main.player, [obstacle])[0]
    obstacle.z_position = 0
    main.player.lane = 0
    assert not main.collision_detector.check_collision(main.player, [obstacle])[0]
    main.player.lane = 1
    obstacle.z_position = config.OBSTACLE_DESPAWN_DISTANCE - 0.01
    main.spawner.obstacles.append(obstacle)
    main.spawner.update_entities()
    assert obstacle.is_empty()
    assert not main.spawner.obstacles

print('PASS all obstacle types: existing lane/depth/state collision rules and despawn')
application.quit()
