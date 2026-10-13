"""Negative cases for body action mapping, without MediaPipe or game state changes."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from types import SimpleNamespace
import unittest
from vision.body_action_bridge import BodyActionBridge


class BodyActionTests(unittest.TestCase):
    """Check confirmation, visibility and neutral false-positive suppression."""
    def pose(self, arms=False):
        """Return stable landmarks with optional raised wrists."""
        points = [SimpleNamespace(y=0.2, visibility=1, presence=1) for _ in range(33)]
        for i in (11, 12):
            points[i].y = 0.4
        for i in (23, 24):
            points[i].y = 0.7
        for i in (15, 16):
            points[i].y = 0.08 if arms else 0.65
        return points

    def test_neutral(self):
        """Neutral shoulders and lowered wrists never become a new action."""
        bridge = BodyActionBridge()
        for i in range(60):
            self.assertEqual(bridge.classify(self.pose(), 'CENTER', i / 60, (0.4, 0.7)),
                             'CENTER')

    def test_one_arm(self):
        """One raised arm is insufficient to trigger JUMP."""
        bridge = BodyActionBridge()
        points = self.pose(True)
        points[16].y = 0.65
        for i in range(60):
            self.assertEqual(bridge.classify(points, 'CENTER', i / 60, (0.4, 0.7)),
                             'CENTER')

    def test_low_confidence(self):
        """Unreliable raised wrists must not trigger JUMP."""
        bridge = BodyActionBridge()
        points = self.pose(True)
        points[16].presence = 0.1
        for i in range(60):
            self.assertEqual(bridge.classify(points, 'CENTER', i / 60, (0.4, 0.7)),
                             'CENTER')

    def test_brief_raise(self):
        """A short jitter pulse cannot pass the confirmation interval."""
        bridge = BodyActionBridge()
        for i in range(3):
            self.assertEqual(bridge.classify(self.pose(True), 'CENTER', i / 60,
                                             (0.4, 0.7)), 'CENTER')
        self.assertEqual(bridge.classify(self.pose(), 'CENTER', 0.06, (0.4, 0.7)),
                         'CENTER')

    def test_calibration_blocks_action(self):
        """Raised arms do not bypass the startup calibration gate."""
        bridge = BodyActionBridge()
        self.assertEqual(bridge.classify(self.pose(True), 'CALIBRATING', 1, None),
                         'CALIBRATING')

    def bent_pose(self, shoulder=0.475, hip=0.7):
        """Return a moderate forward bend or squat relative to the neutral pose."""
        points = self.pose()
        for index in (11, 12):
            points[index].y = shoulder
        for index in (23, 24):
            points[index].y = hip
        return points

    def test_crouch_three_frames(self):
        """Confirm a bend that was below the old threshold only on frame three."""
        bridge = BodyActionBridge()
        baseline = (0.4, 0.7)
        for i in range(2):
            self.assertEqual(bridge.classify(self.bent_pose(), 'CENTER', i / 30,
                                             baseline), 'CENTER')
        self.assertEqual(bridge.classify(self.bent_pose(), 'CENTER', 2 / 30,
                                         baseline), 'CROUCH')
        self.assertEqual(baseline, (0.4, 0.7))

    def test_crouch_hold_and_release(self):
        """Hold crouch through neutral readings for 0.70 s, then release."""
        bridge = BodyActionBridge()
        for i in range(3):
            bridge.classify(self.bent_pose(), 'CENTER', i / 30, (0.4, 0.7))
        self.assertEqual(bridge.classify(self.pose(), 'CENTER', 0.60, (0.4, 0.7)),
                         'CROUCH')
        self.assertEqual(bridge.classify(self.pose(), 'CENTER', 0.78, (0.4, 0.7)),
                         'CENTER')

    def test_combined_bend_and_knee_flexion(self):
        """A modest combined shoulder/hip descent confirms on the third frame."""
        bridge = BodyActionBridge()
        points = self.bent_pose(0.445, 0.727)
        for i in range(2):
            self.assertEqual(bridge.classify(points, 'CENTER', i / 30, (0.4, 0.7)),
                             'CENTER')
        self.assertEqual(bridge.classify(points, 'CENTER', 2 / 30, (0.4, 0.7)),
                         'CROUCH')

    def test_small_neutral_noise(self):
        """Small neutral tracking variations keep lateral outputs unchanged."""
        bridge = BodyActionBridge()
        for i in range(60):
            points = self.bent_pose(0.41 if i % 2 else 0.39, 0.71)
            self.assertEqual(bridge.classify(points, 'LEFT', i / 30, (0.4, 0.7)),
                             'LEFT')

    def test_crouch_hysteresis(self):
        """A weaker bend retains confirmed crouch but cannot initiate it."""
        bridge = BodyActionBridge()
        weak = self.bent_pose(0.44)
        for i in range(3):
            self.assertEqual(bridge.classify(weak, 'CENTER', i / 30, (0.4, 0.7)),
                             'CENTER')
        for i in range(3):
            bridge.classify(self.bent_pose(), 'CENTER', 1 + i / 30, (0.4, 0.7))
        self.assertEqual(bridge.classify(weak, 'CENTER', 2, (0.4, 0.7)), 'CROUCH')

    def test_squat_and_jitter(self):
        """Lowered hips allow squats; isolated shoulder jitter cannot confirm crouch."""
        bridge = BodyActionBridge()
        for i in range(3):
            result = bridge.classify(self.bent_pose(0.46, 0.76), 'CENTER', i / 30,
                                     (0.4, 0.7))
        self.assertEqual(result, 'CROUCH')
        bridge = BodyActionBridge()
        for i in range(20):
            points = self.bent_pose() if i % 2 else self.pose()
            self.assertEqual(bridge.classify(points, 'RIGHT', i / 30, (0.4, 0.7)),
                             'RIGHT')

    def test_jump_interrupts_crouch_hold(self):
        """The original raised-arm confirmation still works after a bend."""
        bridge = BodyActionBridge()
        for i in range(3):
            bridge.classify(self.bent_pose(), 'CENTER', i / 30, (0.4, 0.7))
        for i in range(10):
            result = bridge.classify(self.pose(True), 'CENTER', 0.1 + i / 30,
                                     (0.4, 0.7))
        self.assertEqual(result, 'JUMP')


if __name__ == '__main__':
    unittest.main()
