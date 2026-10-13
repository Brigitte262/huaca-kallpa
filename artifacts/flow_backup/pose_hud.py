"""Single pose sidebar and integrated webcam; consumes snapshots without recognition changes."""
from PIL import Image
from ursina import Entity, Texture, destroy, color
import config
from systems.ui_layout import ui_root, panel, label


class PoseHUD:
    """Own all pose UI under one stable canvas; never cover the menu cards."""

    def __init__(self):
        """Create the sidebar once; return None."""
        self.root = ui_root()
        self._screen_mode = 'select'
        x = config.UI_SIDEBAR_X
        panel(self.root, (config.UI_SIDEBAR_WIDTH + 0.008,
                          config.UI_POSE_PANEL_HEIGHT + 0.008),
              (x, config.UI_POSE_PANEL_Y), config.UI_TERRACOTTA, z=-0.9)
        panel(self.root, (config.UI_SIDEBAR_WIDTH, config.UI_POSE_PANEL_HEIGHT),
              (x, config.UI_POSE_PANEL_Y), config.UI_INK)
        label(self.root, 'CONTROL CORPORAL', (x, 0.185), 0.85, config.UI_GOLD)
        self._status = label(self.root, 'Iniciando cámara...', (x, 0.12), 0.8)
        self._instruction = label(self.root, '', (x, 0.035), 0.72)
        self._progress = label(self.root, '', (x, -0.085), 0.72, config.UI_GOLD)
        self._lanes = label(self.root, 'IZQ    CEN    DER', (x, -0.085), 0.75)
        self._hint = label(self.root, 'C · Mostrar cámara', (x, -0.145), 0.7)
        self._cam_root = Entity(parent=self.root, enabled=False)
        self._cam_border = panel(self._cam_root, (0.3, 0.17),
                                 (x, config.UI_WEBCAM_Y), config.UI_GOLD, z=-0.9)
        self._cam = panel(self._cam_root, (0.29, config.UI_WEBCAM_HEIGHT),
                          (x, config.UI_WEBCAM_Y), config.UI_INK, z=-1)
        self._cam.render_queue = config.UI_CAMERA_IMAGE_ORDER
        self._cam_border.render_queue = config.UI_CAMERA_BORDER_ORDER
        self._cam.enabled = False
        label(self._cam_root, 'C · Ocultar cámara', (x, -0.427), 0.7)
        self._texture = None

    def set_select_mode(self):
        """Keep calibration inside the reserved menu sidebar; return None."""
        self._screen_mode = 'select'

    def set_gameplay_mode(self):
        """Use the same compact sidebar during gameplay; return None."""
        self._screen_mode = 'gameplay'

    def update(self, ic):
        """Present controller snapshot ic without altering its state; return None."""
        if ic is None:
            return
        ic.refresh()
        error = ic.snap_camera_error
        calibrating = ic.snap_calibrating and not error
        self._progress.enabled = calibrating
        self._lanes.enabled = not calibrating and not error
        if error:
            self._status.text = 'Cámara no disponible'
            self._status.color = config.UI_CREAM
            self._instruction.text = (
                'Comprueba la conexión\ny cierra otras aplicaciones\nque usen la cámara.'
            )
            self._progress.enabled = False
        elif calibrating:
            self._status.text = 'CALIBRACIÓN'
            self._status.color = config.UI_GOLD
            self._instruction.text = (
                'Coloca hombros y caderas\ndentro de la cámara.\nMantén una postura neutral.'
            )
            # PoseThread only exposes a calibration state, not numeric progress.
            self._progress.text = 'Esperando postura neutral...'
        else:
            self._status.text = 'Cámara conectada'
            self._status.color = config.UI_GOLD
            self._instruction.text = 'SALTA · AGÁCHATE\nMuévete entre los carriles.'
            lanes = ('IZQ', 'CEN', 'DER')
            self._lanes.text = '    '.join(
                f'[{name}]' if ic.snap_lane == i else name
                for i, name in enumerate(lanes))
        want_camera = ic.preview_active and not error
        self._cam_root.enabled = want_camera
        self._hint.text = 'Vista previa activa' if want_camera else 'C · Mostrar cámara'
        if want_camera:
            self._refresh_camera(ic.snap_preview_rgb, ic.snap_preview_size)

    def _refresh_camera(self, rgb_bytes, size):
        """Upload a valid RGB frame and preserve its aspect ratio; return None."""
        if not rgb_bytes or min(size) <= 0:
            self._cam.enabled = False
            return
        width, height = size
        image = Image.frombytes('RGB', size, rgb_bytes).convert('RGBA')
        self._texture = Texture(image)
        self._cam.texture = self._texture
        self._cam.color = color.white
        self._cam.enabled = True
        cam_height = config.UI_WEBCAM_HEIGHT
        cam_width = min(config.UI_WEBCAM_MAX_WIDTH, cam_height * width / height)
        cam_height = cam_width * height / width
        self._cam.scale = (cam_width, cam_height)
        self._cam_border.scale = (cam_width + 0.012, cam_height + 0.012)

    def destroy(self):
        """Disable and destroy all pose elements together; return None."""
        self.root.enabled = False
        destroy(self.root)
        self._texture = None
