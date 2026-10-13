"""Verify three rounds with one reusable background and stable entity counts."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from time import perf_counter
import numpy as np
from ursina import application, texture_importer, time, scene
import main
import config
from entities.obstacle import Obstacle
from systems.scene_visuals import scene_texture
import systems.score as score_module

OUT = Path('artifacts/scene_reset')
OUT.mkdir(parents=True, exist_ok=True)
score_module.HIGH_SCORE_FILE = str(OUT / 'test_score.json')
app = main.init_game()
application.asset_folder = Path(__file__).resolve().parents[1]
texture_importer.folders[1] = application.asset_folder
application.calculate_dt = False
time.dt = 1 / 60
time.dt_unscaled = time.dt
main.init_entities()
track = main.track
background = track._bg_current
textures = track._background_textures
hud_root = main.hud.root
pose_root = main.pose_hud.root


class Pose:
    """Stable already-calibrated controller outputs for scene lifecycle checks."""
    def get_state(self):
        """Return neutral posture."""
        return 'CENTER'

    def get_frame(self):
        """Return no image; startup is activated explicitly in this lifecycle test."""
        return None

    def is_running(self):
        """Return True so this fixture does not restart the camera."""
        return True


main.pose_thread = Pose()
main.init_character_select()
main.input('enter')
main.pose_thread.get_frame = lambda: np.zeros((480, 640, 3), dtype=np.uint8)
main._begin_playing()


def update():
    """Run the production callback from Ursina; return None."""
    main.update()


def step(count=1):
    """Advance frames, including scheduled visual cleanup; return None."""
    for _ in range(count):
        app.step()


def counts():
    """Return total entities, camera children and background surfaces."""
    live = [item for item in scene.entities if not item.is_empty()]
    backgrounds = [item for item in live if item.name == 'moche_background']
    return len(live), len(main.camera.children), len(backgrounds)


step(10)
counts_after_reset = []
timing = []
for number in range(1, config.SCENE_TEST_ROUNDS + 1):
    # A full visual route, including interrupted transitions, torch and VFX ownership.
    for target in (300, 700, 1200):
        track.set_distance(target)
        track._update_background()
        assert track._fading
        for _ in range(185):
            track._update_background()
        assert not track._fading
        assert counts()[2] == 1
    track._spawn_torches()
    torches = list(track._torches)
    main.vfx_manager.create_particles((0, 1, 0), config.COLOR_ORB, count=4)
    # R after Game Over, R after victory, then R during a partially completed fade.
    if number == 2:
        main._trigger_victory()
        decorations = list(main._round_visuals)
        assert len(decorations) == 2
    else:
        decorations = []
        if number == 3:
            track.reset_visual_scene()
            track.set_distance(300)
            track._update_background()
            assert track._fading
            track._spawn_torches()
            torches += list(track._torches)
        main.spawner.reset()
        obstacle = Obstacle(main.player.lane, 1.5, 'moving')
        main.spawner.obstacles.append(obstacle)
        step()
        assert main.game_state == 'game_over'
    app.win.saveScreenshot(str(OUT / f'round_{number}_end.png'))
    main.input('r')
    assert main.game_state == 'calibration'
    assert main.track is track
    assert track._bg_current is background
    assert track._bg_next is None
    assert track._bg_index == track._next_idx == 0
    assert not track._fading and track._fade_t == 0
    assert track._total_distance == track.scroll_offset == track._parallax_offset == 0
    assert track._bg_current.texture is textures[0]
    assert not track._torches and not main.spawner.obstacles
    assert not main._round_visuals and not main.vfx_manager._particles
    assert all(entity.is_empty() for entity in torches + decorations)
    assert main.hud.root is hud_root and main.pose_hud.root is pose_root
    assert main._victory_triggered is False
    # Repeated R while calibrating must do nothing and never create new scene trees.
    main.input('r')
    main.init_entities()  # Guarded accidental duplicate initialization.
    assert main.track is track
    main._begin_playing()
    main.spawner.spawn_timer = 1000
    step(45)  # Flush short-lived delayed effects from the previous round.
    assert counts()[2] == 1
    counts_after_reset.append(counts())
    start = perf_counter()
    step(90)
    timing.append((perf_counter() - start) / 90)
    app.win.saveScreenshot(str(OUT / f'round_{number}_restart.png'))
    assert track._bg_current.texture.name == 'camino_del_valle.png'
    assert track._bg_current.texture_offset == (0, 0)
    for path, texture in zip(main._BG_SEQUENCE if hasattr(main, '_BG_SEQUENCE') else (
            'assets/backgrounds/camino_del_valle.png',
            'assets/backgrounds/acceso_ceremonial.png',
            'assets/backgrounds/zona_huaca_templo_final.png',
            'assets/backgrounds/escena_final_meta_ceremonial.png'), textures):
        assert scene_texture(path) is texture
    print(f'Round {number}: entities/camera children/backgrounds={counts_after_reset[-1]}, '
          f'frame_ms={timing[-1] * 1000:.2f}')
assert len(set(counts_after_reset)) == 1
(OUT / 'metrics.txt').write_text(str({'counts': counts_after_reset,
                                     'frame_ms': [v * 1000 for v in timing],
                                     'texture_cache': str(scene_texture.cache_info())}),
                                 encoding='utf-8')
print('PASS three rounds: one background, valley restart, stable entities and cached textures')
application.quit()
