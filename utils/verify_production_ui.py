"""Capture production menu and UI input with synthetic preview data only."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import main
from PIL import Image
from ursina import application, texture_importer
app = main.init_game()
application.asset_folder = Path(__file__).resolve().parents[1]
texture_importer.folders[1] = application.asset_folder
main.init_entities()
main.init_character_select()


class Preview:
    """Supply UI data without a camera, MediaPipe or gameplay commands."""
    snap_camera_error = False
    snap_calibrating = True
    snap_lane = None
    preview_active = False
    snap_preview_size = (640, 480)
    snap_preview_rgb = Image.new('RGB', (640, 480), (48, 80, 92)).tobytes()

    def refresh(self):
        """Keep the snapshot fixed; return None."""
        return None

    def toggle_preview(self):
        """Toggle only the simulated preview flag; return None."""
        self.preview_active = not self.preview_active


main.pose_adapter = Preview()


def capture(name):
    """Render production UI and capture its framebuffer; return None."""
    for _ in range(15):
        main.pose_hud.update(main.pose_adapter)
        app.step()
    app.win.saveScreenshot(f'artifacts/ui/{name}.png')


capture('10_production_menu')
main.input('d')
capture('11_production_guardian')
assert main.select_screen._selected == 'male'
main.input('c')
assert main.pose_adapter.preview_active
capture('12_production_camera')
assert main.pose_hud._cam_root.enabled
main.input('c')
capture('13_production_camera_hidden')
assert not main.pose_hud._cam_root.enabled
main.input('enter')
assert main.select_screen is None
assert main.game_state == 'calibration'
assert not main.player.enabled
capture('14_production_calibration')
print('Production UI checks passed; camera input was synthetic')
application.quit()
