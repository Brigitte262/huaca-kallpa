"""Map visible body cues to existing Player actions after pose calibration."""
from math import isfinite
import os
import config


class BodyActionBridge:
    """Add arms-up and forward-bend controls without changing MediaPipe classifiers."""

    def __init__(self):
        """Start with no confirmed body action; return None."""
        self.candidate = None
        self.since = 0.0
        self.active = None
        self.last_activation = float('-inf')
        self.crouch_frames = 0
        self.crouch_until = float('-inf')
        self.debug_crouch = os.environ.get('HK_DEBUG_CROUCH') == '1'
        self.next_debug = 0.0

    def _visible(self, points, indices):
        """Return whether the selected landmarks have finite, reliable coordinates."""
        return all(index < len(points)
                   and isfinite(points[index].y) and 0 <= points[index].y <= 1
                   and (getattr(points[index], 'visibility', 0) or 0)
                   >= config.BODY_ACTION_MIN_CONFIDENCE
                   and (getattr(points[index], 'presence', 1) or 0)
                   >= config.BODY_ACTION_MIN_CONFIDENCE for index in indices)

    def classify(self, points, fallback, now, baseline):
        """Return JUMP/CROUCH for confirmed cues, otherwise the existing pose state.

        Args:
            points: Landmarks already produced by the existing MediaPipe detector.
            fallback: Existing classifier output (including lateral or calibration state).
            now: Monotonic capture timestamp.
            baseline: Existing calibrated (shoulder_y, hip_y), or None.
        Returns:
            str: State consumed by the unchanged pose-to-player interface.
        """
        if baseline is None or fallback in ('CALIBRATING', 'NO_POSE', 'NO_CAMERA'):
            self.candidate = self.active = None
            self.crouch_frames = 0
            self.crouch_until = float('-inf')
            return fallback
        if not self._visible(points, config.BODY_ACTION_TORSO_INDICES):
            self.candidate = self.active = None
            self.crouch_frames = 0
            self.crouch_until = float('-inf')
            return fallback
        shoulder = (points[11].y + points[12].y) / 2
        hip = (points[23].y + points[24].y) / 2
        span = max(config.BODY_ACTION_MIN_TORSO_HEIGHT, baseline[1] - baseline[0])
        heads = [i for i in config.BODY_ACTION_HEAD_INDICES
                 if self._visible(points, (i,))]
        arms_up = False
        if heads and self._visible(points, config.BODY_ACTION_WRIST_INDICES):
            head_y = min(points[i].y for i in heads)
            margin = (-config.BODY_ACTION_ARM_RELEASE_MARGIN if self.active == 'JUMP'
                      else config.BODY_ACTION_ARM_MARGIN)
            arms_up = all(points[i].y < head_y - margin * span
                          for i in config.BODY_ACTION_WRIST_INDICES)
        torso_ratio = (hip - shoulder) / span
        shoulder_drop = (shoulder - baseline[0]) / span
        hip_drop = (hip - baseline[1]) / span
        ratio_limit = (config.BODY_ACTION_TORSO_RELEASE_RATIO if self.active == 'CROUCH'
                       else config.BODY_ACTION_TORSO_RATIO)
        drop_limit = (config.BODY_ACTION_SHOULDER_RELEASE_DROP if self.active == 'CROUCH'
                      else config.BODY_ACTION_SHOULDER_DROP)
        hip_limit = (config.BODY_ACTION_HIP_RELEASE_DROP if self.active == 'CROUCH'
                     else config.BODY_ACTION_HIP_DROP)
        # A bend compresses the projected torso; a squat lowers shoulders AND hips.
        bent = shoulder_drop > drop_limit and (torso_ratio < ratio_limit
                                                or hip_drop > hip_limit)
        self.crouch_frames = self.crouch_frames + 1 if bent else 0
        if bent and (self.active == 'CROUCH'
                     or self.crouch_frames >= config.BODY_ACTION_CROUCH_CONFIRM_FRAMES):
            self.active = 'CROUCH'
            self.crouch_until = now + config.BODY_ACTION_CROUCH_HOLD_SECONDS
        held = self.active == 'CROUCH' and now < self.crouch_until
        if self.debug_crouch and now >= self.next_debug:
            print(f'[CROUCH DEBUG] torso={torso_ratio:.3f} '
                  f'shoulder_drop={shoulder_drop:.3f} hip_drop={hip_drop:.3f} '
                  f'frames={self.crouch_frames} active={held}')
            self.next_debug = now + config.BODY_ACTION_CROUCH_DEBUG_INTERVAL
        # Raised arms retain their original confirmation path even during the hold.
        if held and (bent or not arms_up):
            self.candidate = None
            return 'CROUCH'
        candidate = 'JUMP' if arms_up else None
        if candidate != self.candidate:
            self.candidate = candidate
            self.since = now
        if candidate is None:
            self.active = None
            return fallback
        if candidate == self.active:
            return self.active
        if (now - self.since >= config.BODY_ACTION_CONFIRM_SECONDS
                and now - self.last_activation >= config.BODY_ACTION_COOLDOWN_SECONDS):
            self.active = candidate
            self.last_activation = now
            return candidate
        return fallback
