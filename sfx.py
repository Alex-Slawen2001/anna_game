# -*- coding: utf-8 -*-
import os
import math
import struct
import wave

import pygame

_DIR = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.path.join(_DIR, "assets", "sfx")
RATE = 44100

NAMES = ("click", "correct", "wrong", "achieve", "heartbeat", "page", "stamp")
EXT = (".wav", ".ogg", ".mp3")


def _env(i, n, attack=0.01, release=0.35):
    a = int(RATE * attack)
    r = int(n * release)
    if i < a:
        return i / max(1, a)
    if i > n - r:
        return max(0.0, (n - i) / max(1, r))
    return 1.0


def _write(path, samples):
    w = wave.open(path, "w")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    frames = bytearray()
    for v in samples:
        v = max(-1.0, min(1.0, v))
        frames += struct.pack("<h", int(v * 26000))
    w.writeframes(bytes(frames))
    w.close()


def _tone(freqs, dur, vol=0.5, decay=0.35, wobble=0.0):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        v = 0.0
        for k, f in enumerate(freqs):
            ff = f * (1 + wobble * math.sin(t * 9))
            v += math.sin(2 * math.pi * ff * t) / (k + 1.6)
        out.append(v * vol * _env(i, n, 0.006, decay))
    return out


def _sequence(steps):
    out = []
    for freqs, dur, vol, decay in steps:
        out += _tone(freqs, dur, vol, decay)
    return out


def _thump(dur=0.16, f0=92.0, vol=0.85):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        f = f0 * (1.0 - 0.55 * (t / dur))
        v = math.sin(2 * math.pi * f * t)
        out.append(v * vol * math.exp(-t * 16))
    return out


def _generate_defaults():
    os.makedirs(SFX_DIR, exist_ok=True)
    made = []
    plan = {
        "click": lambda: _tone([620, 930], 0.055, 0.30, 0.7),
        "correct": lambda: _sequence([([784], 0.075, 0.34, 0.5),
                                      ([1047], 0.075, 0.34, 0.5),
                                      ([1319], 0.19, 0.32, 0.55)]),
        "wrong": lambda: _sequence([([196, 233], 0.10, 0.34, 0.4),
                                    ([155, 185], 0.24, 0.30, 0.5)]),
        "achieve": lambda: _sequence([([659], 0.08, 0.30, 0.5),
                                      ([880], 0.08, 0.30, 0.5),
                                      ([1109], 0.08, 0.30, 0.5),
                                      ([1319, 1760], 0.34, 0.28, 0.6)]),
        "heartbeat": lambda: _thump(0.13, 96, 0.80) + [0.0] * int(RATE * 0.10)
                             + _thump(0.16, 78, 0.55),
        "page": lambda: _tone([1500, 2100], 0.05, 0.16, 0.85, wobble=0.35),
        "stamp": lambda: _thump(0.11, 150, 0.9),
    }
    for name, fn in plan.items():
        path = os.path.join(SFX_DIR, name + ".wav")
        if os.path.isfile(path):
            continue
        try:
            _write(path, fn())
            made.append(name)
        except Exception:
            pass
    return made


class Sfx:
    def __init__(self, volume=0.55):
        self.enabled = True
        self.vol = volume
        self.muted = False
        self.snd = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.enabled = False
            return
        try:
            _generate_defaults()
        except Exception:
            pass
        self._load()

    def _find(self, name):
        for e in EXT:
            p = os.path.join(SFX_DIR, name + e)
            if os.path.isfile(p):
                return p
        return None

    def _load(self):
        for name in NAMES:
            p = self._find(name)
            if not p:
                continue
            try:
                s = pygame.mixer.Sound(p)
                s.set_volume(self.vol)
                self.snd[name] = s
            except pygame.error:
                pass

    def play(self, name, vol=1.0):
        if not self.enabled or self.muted:
            return
        s = self.snd.get(name)
        if not s:
            return
        try:
            s.set_volume(max(0.0, min(1.0, self.vol * vol)))
            s.play()
        except pygame.error:
            pass

    def set_muted(self, flag):
        self.muted = bool(flag)
