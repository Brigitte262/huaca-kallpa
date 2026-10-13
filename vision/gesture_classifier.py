"""Gestos verticales; umbrales expresados como fracción de la altura del torso."""
from math import isfinite
from collections import deque
from statistics import median

CALIBRATION_SECONDS = 2.5
JUMP_THRESHOLD = 0.075
CROUCH_THRESHOLD = 0.09
RELEASE_RATIO = 0.50
CONFIRM_SECONDS = 0.06
COOLDOWN_SECONDS = 0.80
NEUTRAL_SECONDS = 0.12
MIN_CONFIDENCE = 0.50
WINDOW_FRAMES = 5
WINDOW_SECONDS = 0.22


class GestureClassifier:
    def __init__(self):
        self.recalibrate()

    def recalibrate(self):
        self.window = deque(maxlen=WINDOW_FRAMES)
        self.baseline = None
        self.samples = []
        self.calibration_since = None
        self.candidate = 'RUN'
        self.since = 0.0
        self.gesture = 'RUN'
        self.shoulder_delta = None
        self.hip_delta = None
        self.progress = 0.0
        self._last_activation = float('-inf')
        self._armed = True
        self._neutral_since = None

    def classify(self, landmarks, now):
        if len(landmarks) < 25 or any(
            not isfinite(landmarks[i].y) or not 0 <= landmarks[i].y <= 1
            or (landmarks[i].visibility or 0) < MIN_CONFIDENCE
            or (landmarks[i].presence or 0) < MIN_CONFIDENCE
            for i in (11, 12, 23, 24)
        ):
            self.window.clear()
            self.candidate = self.gesture = 'RUN'
            self.shoulder_delta = self.hip_delta = None
            self.samples.clear()
            self.calibration_since = None
            self._neutral_since = None
            if self.baseline is None:
                self.progress = 0.0
                return 'CALIBRANDO...'
            return 'SIN POSTURA'
        shoulder = (landmarks[11].y + landmarks[12].y) / 2
        hip = (landmarks[23].y + landmarks[24].y) / 2
        if self.baseline is None:
            if self.calibration_since is None:
                self.calibration_since = now
            self.samples.append((shoulder, hip))
            recent = self.samples[-15:]
            if len(recent) >= 5 and any(max(p[i] for p in recent) - min(p[i] for p in recent) > .04 for i in (0, 1)):
                self.samples = [(shoulder, hip)]
                self.calibration_since = now
            self.progress = min(1.0, (now - self.calibration_since) / CALIBRATION_SECONDS)
            if self.progress < 1.0 or len(self.samples) < 10:
                return 'CALIBRANDO...'
            self.baseline = tuple(sum(p[i] for p in self.samples) / len(self.samples) for i in (0, 1))
            self.samples.clear()
        self.window.append((now, shoulder, hip))
        while self.window and now - self.window[0][0] > WINDOW_SECONDS:
            self.window.popleft()
        if len(self.window) < 3:
            return self.gesture
        shoulder = median(p[1] for p in self.window)
        hip = median(p[2] for p in self.window)
        base_shoulder, base_hip = self.baseline
        scale = max(.1, base_hip - base_shoulder)
        self.shoulder_delta = (base_shoulder - shoulder) / scale
        self.hip_delta = (base_hip - hip) / scale
        ds, dh = self.shoulder_delta, self.hip_delta
        neutral = max(abs(ds), abs(dh)) < min(JUMP_THRESHOLD, CROUCH_THRESHOLD) * RELEASE_RATIO
        if neutral:
            if self._neutral_since is None:
                self._neutral_since = now
            if now - self._neutral_since >= NEUTRAL_SECONDS:
                self._armed = True
        else:
            self._neutral_since = None
        jump_limit = JUMP_THRESHOLD * (RELEASE_RATIO if self.gesture == 'JUMP' else 1)
        crouch_limit = CROUCH_THRESHOLD * (RELEASE_RATIO if self.gesture == 'CROUCH' else 1)
        if ds > jump_limit and dh > jump_limit:
            candidate = 'JUMP'
        elif ds < -crouch_limit and dh < -crouch_limit:
            candidate = 'CROUCH'
        else:
            candidate = 'RUN'
        if candidate != self.candidate:
            self.candidate, self.since = candidate, now
        if now - self.since >= CONFIRM_SECONDS:
            if candidate == 'RUN':
                self.gesture = 'RUN'
            elif candidate != self.gesture:
                if self._armed and now - self._last_activation >= COOLDOWN_SECONDS:
                    self.gesture = candidate
                    self._last_activation = now
                    self._armed = False
                else:
                    self.gesture = 'RUN'
        return self.gesture
