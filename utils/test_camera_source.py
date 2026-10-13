"""Tests for camera acquisition only; no MediaPipe or classifier execution."""
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vision.camera_source import open_available_camera


class Stop:
    """Nonblocking event for deterministic acquisition tests."""
    def is_set(self):
        """Return False while the test is active."""
        return False

    def wait(self, seconds):
        """Skip wall-clock waiting and return False."""
        return False


class Frame:
    """Minimal valid-frame metadata."""
    size = 1

    def copy(self):
        """Return stable frame data for the acquisition worker."""
        return self


class Capture:
    """Represent an available/unavailable device with optional startup delay."""
    def __init__(self, working, delayed=0):
        """Store device behavior; return None."""
        self.working = working
        self.delayed = delayed
        self.released = False

    def isOpened(self):
        """Return whether the test device can open."""
        return self.working

    def read(self):
        """Return failed warmup reads followed by a valid frame."""
        if self.delayed:
            self.delayed -= 1
            return False, None
        return True, Frame()

    def release(self):
        """Mark the device released; return None."""
        self.released = True


class CV:
    """OpenCV acquisition double with configurable device availability."""
    CAP_DSHOW = 1
    CAP_MSMF = 2
    CAP_ANY = 3

    def __init__(self, devices):
        """Store device mappings and an acquisition log; return None."""
        self.devices = devices
        self.opened = []

    def VideoCapture(self, index, backend):
        """Return a test capture for the requested index/backend."""
        capture = Capture((index, backend) in self.devices,
                          self.devices.get((index, backend), 0))
        self.opened.append(capture)
        return capture


class CameraTests(unittest.TestCase):
    """Verify integrated, external, backend fallback and device warmup."""
    def test_integrated(self):
        """Choose a working built-in camera at index zero."""
        cv = CV({(0, 1): 0})
        camera, index, backend = open_available_camera(cv, Stop())
        self.assertEqual((index, backend), (0, 'CAP_DSHOW'))
        self.assertFalse(camera.released)

    def test_external_and_warmup(self):
        """Find an external device outside the former 0–3 range after warmup."""
        cv = CV({(4, 2): 3})
        camera, index, backend = open_available_camera(cv, Stop())
        self.assertEqual((index, backend), (4, 'CAP_MSMF'))
        self.assertEqual(camera.delayed, 0)
        self.assertTrue(all(c.released for c in cv.opened if c is not camera))

    def test_no_camera(self):
        """Release all failed captures when no device is available."""
        cv = CV({})
        self.assertEqual(open_available_camera(cv, Stop()), (None, -1, ''))
        self.assertTrue(all(c.released for c in cv.opened))

    def test_signal_loss_clears_stale_frame(self):
        """Release a disconnected device and clear its last frame for recovery."""
        from vision.pose_thread import PoseThread
        import config

        class Detector:
            """Detector stub for capture testing, without any recognition."""
            def __enter__(self):
                """Return this test context."""
                return self

            def __exit__(self, *args):
                """Close the test context; return None."""
                return None

            def detect(self, frame):
                """Return no landmarks."""
                return None

            def torso_center(self, landmarks):
                """Return no torso center."""
                return None

        class Disconnect(Capture):
            """Provide one good frame, followed by a lost camera signal."""
            reads = 0

            def read(self):
                """Count reads and fail after the first frame."""
                self.reads += 1
                return (True, Frame()) if self.reads == 1 else (False, None)

        camera = Disconnect(True)
        controller = PoseThread()
        controller._stop_event = Stop()
        controller._open_camera = lambda cv: (camera, 0, 'TEST')
        cv = SimpleNamespace(flip=lambda frame, axis: frame, waitKey=lambda delay: 0,
                             destroyWindow=lambda name: None)
        detector_module = SimpleNamespace(PoseDetector=Detector)
        with patch.dict(sys.modules, {'cv2': cv, 'vision.pose_detector': detector_module}):
            controller._run()
        self.assertEqual(camera.reads, config.CAMERA_FAILED_READ_LIMIT + 1)
        self.assertTrue(camera.released)
        self.assertIsNone(controller.get_frame())
        self.assertEqual(controller.get_state(), 'NO_POSE')


if __name__ == '__main__':
    unittest.main()

