"""Render actual Ursina UI states with synthetic camera input, without pose dependencies."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ursina import Ursina, window, application, color
from PIL import Image
import config
from systems.ui import CharacterSelectScreen, HUD
from systems.pose_hud import PoseHUD

app = Ursina(development_mode=False, size=config.WINDOW_SIZE, borderless=False)
application.asset_folder = Path(__file__).resolve().parents[1]
from ursina import texture_importer
texture_importer.folders[1] = application.asset_folder
window.size = config.WINDOW_SIZE
window.color = config.UI_INK
window.exit_button.enabled = False
window.fps_counter.enabled = False
from entities.track import Track
from entities.player import Player
from systems.camera import CameraController
track = Track()
player = Player()
controller = CameraController(player)
hud = HUD()
selected = []
menu = CharacterSelectScreen(selected.append)
pose = PoseHUD()


class Snapshot:
    """Synthetic UI snapshot; never supplies commands to gameplay."""
    snap_camera_error = False
    snap_calibrating = True
    snap_lane = None
    preview_active = False
    snap_preview_size = (640, 480)
    snap_preview_rgb = Image.new('RGB', (640, 480), (48, 80, 92)).tobytes()

    def refresh(self):
        """Keep the test snapshot stable; return None."""
        return None


snapshot = Snapshot()
out = Path('artifacts/ui')
out.mkdir(parents=True, exist_ok=True)


def capture(name):
    """Render frames and save the complete game framebuffer; return None."""
    pose.update(snapshot)
    for _ in range(8):
        app.step()
    app.graphicsEngine.renderFrame()
    app.win.saveScreenshot(str(out / f'{name}.png'))


capture('01_menu_guardiana')
menu.input('d')
assert menu._selected == 'male'
assert menu._cards[1]['badge'].enabled
assert not menu._cards[0]['badge'].enabled
capture('02_menu_guardian')
snapshot.preview_active = True
capture('03_calibration_preview')
snapshot.preview_active = False
capture('04_camera_hidden')
menu.input('enter')
assert selected == ['male']
assert not menu.root.enabled
pose.set_gameplay_mode()
capture('05_calibration_gameplay')
snapshot.snap_calibrating = False
snapshot.snap_lane = 1
snapshot.preview_active = True
capture('06_pose_ready')
snapshot.snap_camera_error = True
capture('07_camera_error')
menu = CharacterSelectScreen(selected.append)
window.size = (1024, 768)
capture('08_menu_4_3')
window.size = (1440, 600)
capture('09_menu_ultrawide')
pose.destroy()
print('UI checks passed')
application.quit()
