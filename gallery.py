# -*- coding: utf-8 -*-
import os
import re

import pygame

_DIR = os.path.dirname(os.path.abspath(__file__))
GALLERY_DIR = os.path.join(_DIR, "assets", "gallery")
EXT = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


def caption_from(filename):
    name = os.path.splitext(os.path.basename(filename))[0]
    name = re.sub(r"^\s*\d+\s*[._-]*\s*", "", name)
    name = name.replace("_", " ").strip()
    return name


def list_photos():
    if not os.path.isdir(GALLERY_DIR):
        return []
    files = [f for f in os.listdir(GALLERY_DIR) if f.lower().endswith(EXT)]
    files.sort(key=lambda f: (f.lower()))
    return [os.path.join(GALLERY_DIR, f) for f in files]


def has_photos():
    return len(list_photos()) > 0


def _fit(img, box_w, box_h):
    iw, ih = img.get_size()
    if iw <= 0 or ih <= 0:
        return img
    k = min(box_w / iw, box_h / ih)
    return pygame.transform.smoothscale(img, (max(1, int(iw * k)), max(1, int(ih * k))))


class Gallery:
    def __init__(self, box_w=880, box_h=470):
        self.box = (box_w, box_h)
        self.paths = list_photos()
        self.cache = {}
        self.idx = 0
        self.fade = 1.0
        self.prev = None

    def reload(self):
        self.paths = list_photos()
        self.cache.clear()
        self.idx = 0
        self.fade = 1.0
        self.prev = None

    def count(self):
        return len(self.paths)

    def caption(self):
        if not self.paths:
            return ""
        return caption_from(self.paths[self.idx])

    def image(self, i=None):
        if not self.paths:
            return None
        i = self.idx if i is None else i % len(self.paths)
        if i in self.cache:
            return self.cache[i]
        try:
            raw = pygame.image.load(self.paths[i]).convert_alpha()
            img = _fit(raw, *self.box)
        except Exception:
            img = None
        self.cache[i] = img
        return img

    def step(self, delta):
        if len(self.paths) < 2:
            return
        self.prev = self.idx
        self.idx = (self.idx + delta) % len(self.paths)
        self.fade = 0.0

    def update(self, dt, auto_after=0.0):
        if self.fade < 1.0:
            self.fade = min(1.0, self.fade + dt * 2.4)
