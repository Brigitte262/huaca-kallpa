"""Run the real main.py with a bounded camera startup check; recognition is untouched."""
from pathlib import Path
import sys
import ursina
from ursina import application, texture_importer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORIGINAL_URSINA = ursina.Ursina


def verification_app(**kwargs):
    """Return the real app with two scheduled verification callbacks."""
    app = ORIGINAL_URSINA(**kwargs)
    application.asset_folder = ROOT
    texture_importer.folders[1] = ROOT

    def confirm(task):
        """Confirm the default character through the production input callback."""
        sys.modules['__main__'].input('enter')
        return task.done

    def finish(task):
        """Capture the real camera startup state, stop its thread and exit."""
        module = sys.modules['__main__']
        print('REAL CAMERA CHECK:', module.game_state,
              module.pose_thread.get_state(),
              'frame_available=', module.pose_thread.get_frame() is not None,
              flush=True)
        app.win.saveScreenshot(str(ROOT / 'artifacts/flow/14_real_camera_startup.png'))
        module._shutdown()
        application.quit()
        return task.done

    app.taskMgr.doMethodLater(1, confirm, 'verify-character-confirm')
    app.taskMgr.doMethodLater(15, finish, 'verify-camera-result')
    return app


ursina.Ursina = verification_app
source = ROOT / 'main.py'
__file__ = str(source)
exec(compile(source.read_text(encoding='utf-8'), str(source), 'exec'), globals())

