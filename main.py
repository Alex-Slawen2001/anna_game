# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   ШЕСТЬ ЛЕТ  —  визуальная новелла про медицинский путь       ║
║   Python + Pygame                                            ║
║                                                              ║
║   Запуск:  python main.py                                    ║
║   Управление: мышь. Пробел/Enter — пропустить печать текста. ║
║   F11 — полный экран, M — музыка вкл/выкл, Esc — выход.      ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
import sys
import math
import random
import datetime

import pygame

from content import (
    HERO, V, N, K, RESTAURANT, UNIVERSITY, FROM_WHO,
    CHARACTER_COLORS, CHARACTER_PHOTOS,
    YEARS, FINAL_EXAMS, FINALE_SCENES, FINALE_LETTER,
)
import exam_builder
import live_questions
import save as savemod
from achievements import ACHIEVEMENTS, ACH_ORDER

# ══════════════════════════════ КОНСТАНТЫ ══════════════════════════════
W, H = 1280, 720
FPS = 60

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.join(BASE_DIR, "assets", "photos")
FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")
MUSIC_DIR = os.path.join(BASE_DIR, "assets", "music")
BOOKING_FILE = os.path.join(BASE_DIR, "booking.txt")

# Музыка. Клади файлы в assets/music/
#   Один трек на состояние:      story.mp3, exam.mp3, menu.mp3, final.mp3
#   Несколько (переключаются):   папки assets/music/story/, /exam/, /menu/, /final/
#                                либо story1.mp3, story2.mp3, story_ночь.mp3 ...
#   Один трек на всю игру:       music.mp3
# Форматы: .mp3 .ogg .wav .flac .opus. Нет файла — просто тишина, без ошибок.
MUSIC_VOLUME = 0.45

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (18, 20, 30)
CREAM = (245, 242, 238)
GOLD = (255, 210, 120)
RED = (235, 90, 100)
GREEN = (110, 220, 150)
DIM = (150, 155, 170)


# ══════════════════════════════ ШРИФТЫ ══════════════════════════════
def _font_path(bold=False):
    """Ищем шрифт с поддержкой кириллицы."""
    if os.path.isdir(FONT_DIR):
        files = [f for f in os.listdir(FONT_DIR) if f.lower().endswith((".ttf", ".otf"))]
        pref = [f for f in files if ("bold" in f.lower()) == bold]
        pick = pref or files
        if pick:
            return os.path.join(FONT_DIR, sorted(pick)[0])
    names = ("dejavusans,notosans,arial,verdana,tahoma,freesans,liberationsans")
    return pygame.font.match_font(names, bold=bold)


_FONT_CACHE = {}


def F(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        p = _font_path(bold)
        try:
            f = pygame.font.Font(p, size) if p else pygame.font.SysFont("arial", size, bold=bold)
        except Exception:
            f = pygame.font.SysFont("arial", size, bold=bold)
        if p and bold and "bold" not in (p or "").lower():
            f.set_bold(True)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


# ══════════════════════════════ УТИЛИТЫ ══════════════════════════════
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def ease_out(t):
    return 1 - (1 - t) ** 3


def mix(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def wrap_text(text, font, max_w):
    """Перенос текста по словам, с поддержкой \n."""
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        words = para.split(" ")
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def draw_text(surf, text, font, color, x, y, center=False, alpha=255):
    img = font.render(text, True, color)
    if alpha < 255:
        img.set_alpha(alpha)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(img, r)
    return r


def panel(surf, rect, color, radius=18, alpha=255, border=None, bw=2):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(s, (*border, min(255, alpha + 40)), s.get_rect(),
                         width=bw, border_radius=radius)
    surf.blit(s, rect.topleft)


def glow_circle(surf, pos, radius, color, strength=60, layers=6):
    for i in range(layers, 0, -1):
        a = int(strength * (i / layers) ** 2 / layers * 2)
        r = int(radius * (1 + 0.5 * i / layers))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (r, r), r)
        surf.blit(s, (pos[0] - r, pos[1] - r), special_flags=pygame.BLEND_RGBA_ADD)


def heart(surf, cx, cy, size, color, alpha=255):
    pts = []
    for i in range(40):
        t = i / 39 * math.tau
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * size / 16, cy + y * size / 16))
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(s, (*color, alpha), pts)
    surf.blit(s, (0, 0))


# ══════════════════════════════ ФОН ══════════════════════════════
class Background:
    """Живой градиентный фон + боке + бегущая ЭКГ."""

    def __init__(self):
        self.color = (40, 40, 70)
        self.target = (40, 40, 70)
        self.accent = (255, 255, 255)
        self.t_accent = (255, 255, 255)
        self.bokeh = [self._new_bokeh(True) for _ in range(26)]
        self.t = 0.0
        self.ecg_phase = 0.0
        self._grad = None
        self._grad_key = None

    def _new_bokeh(self, spread=False):
        return {
            "x": random.uniform(0, W),
            "y": random.uniform(0, H) if spread else H + 30,
            "r": random.uniform(5, 34),
            "sp": random.uniform(6, 26),
            "a": random.uniform(0.05, 0.22),
            "w": random.uniform(0.3, 1.1),
            "ph": random.uniform(0, math.tau),
        }

    def set_theme(self, color, accent):
        self.target = color
        self.t_accent = accent

    def update(self, dt):
        self.t += dt
        self.ecg_phase += dt * 190
        self.color = mix(self.color, self.target, clamp(dt * 2.2, 0, 1))
        self.accent = mix(self.accent, self.t_accent, clamp(dt * 2.2, 0, 1))
        for b in self.bokeh:
            b["y"] -= b["sp"] * dt
            b["x"] += math.sin(self.t * b["w"] + b["ph"]) * 10 * dt
            if b["y"] < -50:
                b.update(self._new_bokeh())

    def _gradient(self):
        top = mix(self.color, BLACK, 0.45)
        bot = mix(self.color, BLACK, 0.78)
        key = (top, bot)
        if key != self._grad_key:
            g = pygame.Surface((1, H))
            for y in range(H):
                g.set_at((0, y), mix(top, bot, y / H))
            self._grad = pygame.transform.smoothscale(g, (W, H))
            self._grad_key = key
        return self._grad

    def draw(self, surf):
        surf.blit(self._gradient(), (0, 0))
        glow_circle(surf, (W // 2, -40), 260, self.accent, strength=42, layers=5)
        bl = pygame.Surface((W, H), pygame.SRCALPHA)
        for b in self.bokeh:
            pygame.draw.circle(bl, (*self.accent, int(255 * b["a"])),
                               (int(b["x"]), int(b["y"])), int(b["r"]))
        surf.blit(bl, (0, 0))
        self._ecg(surf)
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.rect(v, (0, 0, 0, 90), (0, 0, W, 60))
        pygame.draw.rect(v, (0, 0, 0, 110), (0, H - 70, W, 70))
        surf.blit(v, (0, 0))

    def _ecg(self, surf):
        base = H - 26
        pts = []
        for px in range(0, W + 4, 4):
            x = (px + self.ecg_phase) % 340
            y = 0
            if 140 <= x < 152:
                y = -6
            elif 156 <= x < 162:
                y = 10
            elif 162 <= x < 172:
                y = -46
            elif 172 <= x < 182:
                y = 20
            elif 186 <= x < 200:
                y = -10
            pts.append((px, base + y))
        if len(pts) > 1:
            pygame.draw.lines(surf, (*self.accent, 255), False, pts, 2)


# ══════════════════════════════ ПОРТРЕТЫ ══════════════════════════════
def _cover_crop_square(img, size):
    iw, ih = img.get_size()
    scale = size / min(iw, ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    img = pygame.transform.smoothscale(img, (nw, nh))
    rect = pygame.Rect(0, 0, size, size)
    rect.center = (nw // 2, nh // 2)
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    out.blit(img, (0, 0), rect)
    return out


def _circle_mask(img, size):
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
    out = img.convert_alpha()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def _procedural_avatar(name, color, size):
    """Аватар-заглушка, если фото не положили."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(s, mix(color, BLACK, 0.55), (c, c), c)
    pygame.draw.circle(s, mix(color, BLACK, 0.30), (c, c), c - 4)
    pygame.draw.circle(s, (238, 240, 245), (c, int(size * 1.02)), int(size * 0.42))
    skin = (247, 216, 195)
    pygame.draw.circle(s, skin, (c, int(size * 0.46)), int(size * 0.23))
    hair = mix(color, BLACK, 0.45)
    pygame.draw.circle(s, hair, (c, int(size * 0.40)), int(size * 0.245))
    pygame.draw.rect(s, skin, (c - size * 0.20, size * 0.44, size * 0.40, size * 0.20))
    pygame.draw.circle(s, hair, (int(c - size * 0.22), int(size * 0.52)), int(size * 0.09))
    pygame.draw.circle(s, hair, (int(c + size * 0.22), int(size * 0.52)), int(size * 0.09))
    ey = int(size * 0.47)
    pygame.draw.circle(s, INK, (int(c - size * 0.08), ey), max(2, size // 55))
    pygame.draw.circle(s, INK, (int(c + size * 0.08), ey), max(2, size // 55))
    pygame.draw.arc(s, (190, 110, 110),
                    (c - size * 0.07, size * 0.50, size * 0.14, size * 0.09),
                    math.pi, math.tau, max(2, size // 70))
    f = F(int(size * 0.16), True)
    draw_text(s, name[0].upper(), f, (255, 255, 255), c, int(size * 0.86), center=True)
    return _circle_mask(s, size)


class Portraits:
    def __init__(self):
        self.cache = {}
        self.real = {}

    def get(self, name, size=210):
        key = (name, size)
        if key in self.cache:
            return self.cache[key]
        color = CHARACTER_COLORS.get(name, (200, 200, 210))
        raw_path = CHARACTER_PHOTOS.get(name, "") or ""
        # принимаем и имя файла, и полный путь — ищем в нескольких местах
        candidates = []
        if raw_path:
            candidates.append(raw_path)
            candidates.append(os.path.join(BASE_DIR, raw_path))
            candidates.append(os.path.join(PHOTO_DIR, os.path.basename(raw_path)))
            candidates.append(os.path.join(PHOTO_DIR, raw_path))
        path = next((p for p in candidates if os.path.isfile(p)), None)
        img = None
        if path:
            try:
                raw = pygame.image.load(path).convert_alpha()
                img = _circle_mask(_cover_crop_square(raw, size), size)
                self.real[name] = True
            except Exception as e:
                print(f"[фото] не удалось загрузить {path}: {e}")
                img = None
        if img is None:
            img = _procedural_avatar(name, color, size)
        self.cache[key] = img
        return img

    def draw(self, surf, name, cx, cy, size=210, active=True, bob=0.0):
        img = self.get(name, size)
        color = CHARACTER_COLORS.get(name, (200, 200, 210))
        y = cy + math.sin(bob) * (3 if active else 1.5)
        scale = 1.0 if active else 0.92
        s = int(size * scale)
        im = pygame.transform.smoothscale(img, (s, s))
        if not active:
            dark = pygame.Surface((s, s), pygame.SRCALPHA)
            dark.fill((10, 10, 25, 130))
            im = im.copy()
            im.blit(dark, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        if active:
            glow_circle(surf, (cx, int(y)), s // 2, color, strength=55, layers=4)
        pygame.draw.circle(surf, mix(color, WHITE, 0.25 if active else -0.0),
                           (cx, int(y)), s // 2 + 4, 3)
        surf.blit(im, (cx - s // 2, int(y) - s // 2))
        nf = F(19, True)
        tag = nf.render(name, True, WHITE if active else DIM)
        tr = tag.get_rect(center=(cx, int(y) + s // 2 + 22))
        bg = tr.inflate(20, 8)
        panel(surf, bg, mix(color, BLACK, 0.55), radius=12,
              alpha=210 if active else 110, border=color if active else None, bw=1)
        surf.blit(tag, tr)


# ══════════════════════════════ КНОПКА ══════════════════════════════
class Button:
    def __init__(self, rect, text, accent=GOLD, font_size=22, align="center", tag=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.accent = accent
        self.fs = font_size
        self.align = align
        self.tag = tag
        self.hov = 0.0
        self.enabled = True
        self.state = "idle"
        self.appear = 0.0

    def update(self, dt, mouse):
        target = 1.0 if (self.enabled and self.rect.collidepoint(mouse)) else 0.0
        self.hov = lerp(self.hov, target, clamp(dt * 12, 0, 1))
        self.appear = clamp(self.appear + dt * 3.2, 0, 1)

    def hovered(self, mouse):
        return self.enabled and self.rect.collidepoint(mouse)

    def draw(self, surf):
        a = ease_out(self.appear)
        r = self.rect.copy()
        r.y += int((1 - a) * 16)
        lift = int(self.hov * 4)
        r.y -= lift
        if self.state == "correct":
            base, bord, txt = mix(GREEN, BLACK, 0.55), GREEN, WHITE
        elif self.state == "wrong":
            base, bord, txt = mix(RED, BLACK, 0.55), RED, WHITE
        elif self.state == "faded":
            base, bord, txt = (28, 30, 44), (60, 64, 84), DIM
        else:
            base = mix((26, 28, 42), self.accent, 0.10 + 0.22 * self.hov)
            bord = mix((70, 74, 96), self.accent, self.hov)
            txt = mix(CREAM, WHITE, self.hov)
        alpha = int(255 * a)
        if self.hov > 0.05 and self.state == "idle":
            glow_circle(surf, r.center, r.height // 2 + 6, self.accent,
                        strength=int(40 * self.hov), layers=3)
        panel(surf, r, base, radius=14, alpha=alpha, border=bord, bw=2)
        f = F(self.fs, True)
        lines = wrap_text(self.text, f, r.width - 44)
        total = len(lines) * (f.get_height() + 2)
        y = r.centery - total // 2
        for ln in lines:
            if self.align == "center":
                draw_text(surf, ln, f, txt, r.centerx, y + f.get_height() // 2,
                          center=True, alpha=alpha)
            else:
                draw_text(surf, ln, f, txt, r.x + 22, y, alpha=alpha)
            y += f.get_height() + 2


# ══════════════════════════════ ЧАСТИЦЫ ══════════════════════════════
class Particles:
    def __init__(self):
        self.p = []

    def burst(self, x, y, color, n=26, kind="spark"):
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(80, 330)
            self.p.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * sp, "vy": math.sin(ang) * sp - 60,
                "life": random.uniform(0.5, 1.1), "max": 1.1,
                "c": color, "r": random.uniform(2, 5), "kind": kind,
            })

    def confetti(self, n=3):
        cols = [GOLD, (255, 138, 170), (150, 220, 255), (160, 255, 190), WHITE]
        for _ in range(n):
            self.p.append({
                "x": random.uniform(0, W), "y": -12,
                "vx": random.uniform(-40, 40), "vy": random.uniform(60, 170),
                "life": 6.0, "max": 6.0, "c": random.choice(cols),
                "r": random.uniform(3, 7), "kind": "conf",
                "rot": random.uniform(0, math.tau), "rs": random.uniform(-6, 6),
            })

    def hearts(self, n=1):
        for _ in range(n):
            self.p.append({
                "x": random.uniform(0, W), "y": H + 20,
                "vx": random.uniform(-14, 14), "vy": random.uniform(-70, -30),
                "life": 6.0, "max": 6.0, "c": (255, 120, 160),
                "r": random.uniform(8, 18), "kind": "heart",
            })

    def update(self, dt):
        for p in self.p:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["kind"] == "spark":
                p["vy"] += 620 * dt
                p["vx"] *= 0.97
            elif p["kind"] == "conf":
                p["vy"] += 60 * dt
                p["vx"] += math.sin(p["y"] * 0.02) * 22 * dt
                p["rot"] += p["rs"] * dt
        self.p = [p for p in self.p if p["life"] > 0 and p["y"] < H + 60]

    def draw(self, surf):
        if not self.p:
            return
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        for p in self.p:
            a = int(255 * clamp(p["life"] / p["max"], 0, 1))
            if p["kind"] == "conf":
                w_, h_ = p["r"] * 2, p["r"]
                rect = pygame.Surface((w_, h_), pygame.SRCALPHA)
                rect.fill((*p["c"], a))
                rect = pygame.transform.rotate(rect, math.degrees(p["rot"]))
                s.blit(rect, (p["x"], p["y"]))
            elif p["kind"] == "heart":
                heart(s, p["x"], p["y"], p["r"], p["c"], a)
            else:
                pygame.draw.circle(s, (*p["c"], a), (int(p["x"]), int(p["y"])), int(p["r"]))
        surf.blit(s, (0, 0))


# ══════════════════════════════ ПЕРЕХОДЫ ══════════════════════════════
class Transition:
    def __init__(self):
        self.active = False
        self.t = 0.0
        self.dur = 0.55
        self.phase = "out"
        self.cb = None
        self.label = ""

    def start(self, cb, label="", dur=0.55):
        if self.active:
            return
        self.active = True
        self.t = 0.0
        self.phase = "out"
        self.cb = cb
        self.label = label
        self.dur = dur

    def update(self, dt):
        if not self.active:
            return
        self.t += dt
        if self.phase == "out" and self.t >= self.dur:
            self.phase = "in"
            self.t = 0.0
            if self.cb:
                self.cb()
                self.cb = None
        elif self.phase == "in" and self.t >= self.dur:
            self.active = False

    def draw(self, surf):
        if not self.active:
            return
        k = clamp(self.t / self.dur, 0, 1)
        a = ease_out(k) if self.phase == "out" else 1 - ease_out(k)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((6, 7, 14, int(255 * a)))
        surf.blit(ov, (0, 0))
        if self.label and a > 0.35:
            f = F(40, True)
            draw_text(surf, self.label, f, mix(CREAM, GOLD, 0.4), W // 2, H // 2,
                      center=True, alpha=int(255 * clamp((a - 0.35) / 0.65, 0, 1)))


# ══════════════════════════════ ДОСТИЖЕНИЯ (тосты) ══════════════════════════════
def _draw_ach_icon(surf, kind, cx, cy, r, color):
    if kind == "star" or kind == "trophy" or kind == "perfectionist":
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        pygame.draw.polygon(surf, color, pts)
    elif kind == "heart":
        heart(surf, cx, cy, r * 1.1, color, 255)
    elif kind == "moon":
        pygame.draw.circle(surf, color, (cx, cy), r)
        pygame.draw.circle(surf, mix(color, BLACK, 0.7), (int(cx + r * 0.4), cy), r)
    elif kind == "cross":
        w = r * 0.5
        pygame.draw.rect(surf, color, (cx - w / 2, cy - r, w, 2 * r), border_radius=3)
        pygame.draw.rect(surf, color, (cx - r, cy - w / 2, 2 * r, w), border_radius=3)
    elif kind == "bolt":
        pygame.draw.polygon(surf, color, [
            (cx + r * 0.2, cy - r), (cx - r * 0.5, cy + r * 0.15),
            (cx, cy + r * 0.1), (cx - r * 0.2, cy + r),
            (cx + r * 0.5, cy - r * 0.15), (cx, cy - r * 0.1)])
    elif kind == "flask":
        pygame.draw.polygon(surf, color, [
            (cx - r * 0.3, cy - r), (cx - r * 0.3, cy - r * 0.2),
            (cx - r * 0.7, cy + r), (cx + r * 0.7, cy + r),
            (cx + r * 0.3, cy - r * 0.2), (cx + r * 0.3, cy - r)], 0)
        pygame.draw.line(surf, mix(color, WHITE, 0.5),
                         (cx - r * 0.3, cy - r), (cx + r * 0.3, cy - r), 3)
    elif kind == "spark":
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            pygame.draw.line(surf, color, (cx, cy),
                             (cx + math.cos(a) * r, cy + math.sin(a) * r), 3)
    elif kind == "people":
        pygame.draw.circle(surf, color, (int(cx - r * 0.4), int(cy - r * 0.2)), int(r * 0.35))
        pygame.draw.circle(surf, color, (int(cx + r * 0.4), int(cy - r * 0.2)), int(r * 0.35))
        pygame.draw.circle(surf, color, (int(cx - r * 0.4), int(cy + r * 0.5)), int(r * 0.5))
        pygame.draw.circle(surf, color, (int(cx + r * 0.4), int(cy + r * 0.5)), int(r * 0.5))
    else:  # book
        pygame.draw.rect(surf, color, (cx - r * 0.7, cy - r * 0.6, r * 1.4, r * 1.2),
                         border_radius=3)
        pygame.draw.line(surf, mix(color, BLACK, 0.6), (cx, cy - r * 0.6), (cx, cy + r * 0.6), 2)


class Toasts:
    def __init__(self):
        self.queue = []
        self.active = []

    def push(self, key):
        self.queue.append({"key": key, "t": 0.0, "life": 4.2})

    def update(self, dt):
        if self.queue and len(self.active) < 2:
            self.active.append(self.queue.pop(0))
        for a in self.active:
            a["t"] += dt
        self.active = [a for a in self.active if a["t"] < a["life"]]

    def draw(self, surf):
        for i, a in enumerate(self.active):
            info = ACHIEVEMENTS.get(a["key"], {})
            k = a["t"] / a["life"]
            if k < 0.12:
                slide = ease_out(k / 0.12)
            elif k > 0.85:
                slide = ease_out((1 - k) / 0.15)
            else:
                slide = 1.0
            slide = clamp(slide, 0, 1)
            w, h = 340, 78
            x = W - 20 - w + int((1 - slide) * (w + 40))
            y = 90 + i * (h + 12)
            rect = pygame.Rect(x, y, w, h)
            panel(surf, rect, (22, 24, 40), radius=16, alpha=int(240 * slide),
                  border=GOLD, bw=2)
            glow_circle(surf, (x + 40, y + h // 2), 26, GOLD,
                        strength=int(30 * slide), layers=3)
            _draw_ach_icon(surf, info.get("icon", "book"), x + 40, y + h // 2, 18, GOLD)
            draw_text(surf, "Достижение получено", F(12, True), GOLD,
                      x + 74, y + 14, alpha=int(255 * slide))
            draw_text(surf, info.get("title", ""), F(19, True), CREAM,
                      x + 74, y + 30, alpha=int(255 * slide))
            draw_text(surf, info.get("desc", ""), F(13), DIM,
                      x + 74, y + 55, alpha=int(230 * slide))


# ══════════════════════════════ МУЗЫКА ══════════════════════════════
AUDIO_EXT = (".mp3", ".ogg", ".wav", ".flac", ".opus")
MUSIC_END_EVENT = pygame.USEREVENT + 7


class Music:
    def __init__(self):
        self.enabled = True
        self.muted = False
        self.vol = MUSIC_VOLUME
        self.key = None
        self.playlist = []
        self.idx = 0
        self.notice = ""
        self.notice_t = 0.0
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        except pygame.error as e:
            print(f"[музыка] mixer недоступен: {e}")
            self.enabled = False

    def _scan(self, key):
        found = []
        sub = os.path.join(MUSIC_DIR, key)
        if os.path.isdir(sub):
            for f in sorted(os.listdir(sub)):
                if f.lower().endswith(AUDIO_EXT):
                    found.append(os.path.join(sub, f))
        if os.path.isdir(MUSIC_DIR):
            for f in sorted(os.listdir(MUSIC_DIR)):
                low = f.lower()
                if not low.endswith(AUDIO_EXT):
                    continue
                stem = os.path.splitext(low)[0]
                if stem == key or stem.startswith(key + "_") or (
                        stem.startswith(key) and stem[len(key):].isdigit()):
                    p = os.path.join(MUSIC_DIR, f)
                    if p not in found:
                        found.append(p)
        if not found and os.path.isdir(MUSIC_DIR):
            for f in sorted(os.listdir(MUSIC_DIR)):
                low = f.lower()
                if low.endswith(AUDIO_EXT) and os.path.splitext(low)[0].startswith("music"):
                    found.append(os.path.join(MUSIC_DIR, f))
        return found

    def _start(self, fade=800):
        if not self.enabled or not self.playlist:
            pygame.mixer.music.stop()
            return
        self.idx %= len(self.playlist)
        path = self.playlist[self.idx]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0 if self.muted else self.vol)
            pygame.mixer.music.play(0, fade_ms=fade)
        except pygame.error as e:
            print(f"[музыка] не удалось запустить {path}: {e}")

    def play(self, key):
        if not self.enabled or key == self.key:
            return
        self.key = key
        self.playlist = self._scan(key)
        self.idx = 0
        self._start()

    def next_track(self, announce=True):
        if not self.enabled or len(self.playlist) < 1:
            return
        self.idx = (self.idx + 1) % len(self.playlist)
        self._start(fade=300)
        if announce and self.playlist:
            self.notice = self.track_name()
            self.notice_t = 2.6

    def track_ended(self):
        self.next_track(announce=False)

    def track_name(self):
        if not self.playlist:
            return ""
        return os.path.splitext(os.path.basename(self.playlist[self.idx]))[0]

    def change_volume(self, delta):
        if not self.enabled:
            return
        self.vol = clamp(self.vol + delta, 0.0, 1.0)
        self.muted = False
        pygame.mixer.music.set_volume(self.vol)
        self.notice = f"Громкость {int(self.vol * 100)}%"
        self.notice_t = 1.6

    def toggle_mute(self):
        if not self.enabled:
            return
        self.muted = not self.muted
        pygame.mixer.music.set_volume(0 if self.muted else self.vol)
        self.notice = "Музыка выключена" if self.muted else "Музыка включена"
        self.notice_t = 1.6

    def update(self, dt):
        if self.notice_t > 0:
            self.notice_t = max(0.0, self.notice_t - dt)

    def draw(self, surf):
        if self.notice_t <= 0 or not self.notice:
            return
        a = clamp(self.notice_t / 0.5, 0, 1)
        f = F(15, True)
        label = self.notice
        if self.playlist and len(self.playlist) > 1 and not self.notice.startswith("Гром"):
            label = f"{self.notice}  ({self.idx + 1}/{len(self.playlist)})"
        w = f.size(label)[0] + 54
        rect = pygame.Rect(24, H - 62, w, 36)
        panel(surf, rect, (18, 20, 32), radius=12, alpha=int(225 * a),
              border=mix((70, 74, 96), GOLD, 0.5), bw=2)
        cx = rect.x + 20
        cy = rect.centery
        col = mix(DIM, GOLD, 0.7)
        pygame.draw.circle(surf, col, (cx - 2, cy + 5), 4)
        pygame.draw.line(surf, col, (cx + 2, cy + 5), (cx + 2, cy - 7), 2)
        pygame.draw.line(surf, col, (cx + 2, cy - 7), (cx + 9, cy - 9), 2)
        draw_text(surf, label, f, mix(CREAM, WHITE, 0.3), rect.x + 38,
                  rect.centery - f.get_height() // 2, alpha=int(255 * a))


# ══════════════════════════════ ИГРА ══════════════════════════════
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"Шесть лет — история {HERO}")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.full = False

        self.bg = Background()
        self.fx = Particles()
        self.tr = Transition()
        self.por = Portraits()
        self.music = Music()
        self.toasts = Toasts()

        self.state = "MENU"
        self.buttons = []
        self.time = 0.0

        self.year_i = 0
        self.unlocked = 0
        self.energy = 100
        self.confidence = 50
        self.results = {}
        self.gradebook = []
        self.earned = set()
        self.flawless_streak = 0
        self.night_studier = False

        live_questions.start_fetching()

        self.scenes = []
        self.si = 0
        self.typed = 0.0
        self.speaker = None
        self.after_story = None
        self.choice_reply = None

        self.exam = None
        self.qi = 0
        self.lives = 3
        self.correct = 0
        self.answered = None
        self.q_timer = 0.0
        self.final_stage = 0
        self.shake = 0.0
        self._skip_rect = None
        self._grades_from = "MENU"

        self.letter_t = 0.0
        self.time_input = ""
        self.input_err = ""
        self.saved_time = None

        self._menu()
        self.music.play("menu")

    def reset(self):
        self.year_i = 0
        self.unlocked = 0
        self.energy = 100
        self.confidence = 50
        self.results = {}
        self.gradebook = []
        self.earned = set()
        self.flawless_streak = 0
        self.night_studier = False
        self.saved_time = None
        self.time_input = ""
        self.fx.p.clear()
        savemod.clear()
        self.go("MENU", "")

    def grant(self, key):
        if key in self.earned:
            return
        self.earned.add(key)
        self.toasts.push(key)
        self.fx.burst(W - 60, 120, GOLD, 20)

    def save_progress(self):
        savemod.save({
            "unlocked": self.unlocked,
            "energy": self.energy,
            "confidence": self.confidence,
            "results": {str(k): v for k, v in self.results.items()},
            "gradebook": self.gradebook,
            "earned": list(self.earned),
            "night_studier": self.night_studier,
            "flawless_streak": self.flawless_streak,
        })

    def load_progress(self):
        data = savemod.load()
        if not data:
            return False
        self.unlocked = data.get("unlocked", 0)
        self.energy = data.get("energy", 100)
        self.confidence = data.get("confidence", 50)
        self.results = {int(k): v for k, v in data.get("results", {}).items()}
        self.gradebook = data.get("gradebook", [])
        self.earned = set(data.get("earned", []))
        self.night_studier = data.get("night_studier", False)
        self.flawless_streak = data.get("flawless_streak", 0)
        return True

    # ─────────────────────── ХЕЛПЕРЫ ───────────────────────
    def go(self, state, label="", dur=0.55):
        def _do():
            self.state = state
            self.buttons = []
            self._enter(state)
        self.tr.start(_do, label, dur)

    def _enter(self, state):
        track = {"MENU": "menu", "MAP": "story", "STORY": "story",
                 "EXAM": "exam", "RESULT": "exam", "ACH": "menu", "GRADES": "menu",
                 "LETTER": "final", "INPUT": "final", "THANKS": "final"}.get(state)
        if track:
            self.music.play(track)
        if state == "MENU":
            self._menu()
        elif state == "ACH":
            self._ach_screen()
        elif state == "GRADES":
            self._grades_screen()
        elif state == "MAP":
            self._map()
        elif state == "STORY":
            self.typed = 0.0
        elif state == "EXAM":
            self._exam_ui()
        elif state == "RESULT":
            self._result_ui()
        elif state == "LETTER":
            self.letter_t = 0.0
        elif state == "INPUT":
            self.time_input = ""
            self.input_err = ""

    def cur_year(self):
        return YEARS[self.year_i]

    # ─────────────────────── МЕНЮ ───────────────────────
    def _menu(self):
        self.bg.set_theme((60, 45, 95), (255, 150, 180))
        has = savemod.has_save()
        self.buttons = []
        y0 = 436
        if has:
            self.buttons.append(Button((W // 2 - 150, y0, 300, 52), "Продолжить", GOLD, 23, tag="continue"))
            y0 += 60
            self.buttons.append(Button((W // 2 - 150, y0, 300, 46), "Начать заново", (200, 160, 190), 19, tag="restart"))
            y0 += 54
        else:
            self.buttons.append(Button((W // 2 - 150, y0, 300, 56), "Начать путь", GOLD, 24, tag="start"))
            y0 += 64
        self.buttons.append(Button((W // 2 - 154, y0, 148, 44), "Зачётка", (220, 200, 160), 18, tag="grades"))
        self.buttons.append(Button((W // 2 + 6, y0, 148, 44), "Достижения", (150, 180, 220), 18, tag="ach"))
        y0 += 52
        self.buttons.append(Button((W // 2 - 150, y0, 300, 42), "Выход", (150, 150, 170), 18, tag="quit"))

    def draw_menu(self, s):
        t = self.time
        f1 = F(76, True)
        f2 = F(26)
        f3 = F(18)
        glow_circle(s, (W // 2, 200), 150, (255, 150, 180), strength=70, layers=6)
        p = 1 + 0.03 * math.sin(t * 2.4)
        heart(s, W // 2, 180, 46 * p, (255, 110, 150), 235)
        draw_text(s, "ШЕСТЬ ЛЕТ", f1, CREAM, W // 2, 288, center=True)
        draw_text(s, f"история {HERO}", f2, mix(CREAM, GOLD, 0.5), W // 2, 340, center=True)
        draw_text(s, UNIVERSITY, f3, DIM, W // 2, 380, center=True)
        for i, name in enumerate([V, N, K]):
            self.por.draw(s, name, 150 + i * 110, 632, 70, active=False, bob=t * 2 + i)
        self.por.draw(s, HERO, W - 175, 624, 96, active=True, bob=t * 2)
        if savemod.has_save():
            got = len(self.earned)
            draw_text(s, f"собрано достижений: {got} / {len(ACHIEVEMENTS)}",
                      F(14), (150, 155, 175), W // 2, H - 62, center=True)
        draw_text(s, "F11 — экран · M — звук · N — сменить трек · −/+ громкость · S — пропуск · Esc — выход",
                  F(14), (110, 115, 135), W // 2, H - 38, center=True)

    # ─────────────────────── ДОСТИЖЕНИЯ ───────────────────────
    def _ach_screen(self):
        self.bg.set_theme((40, 40, 70), (255, 200, 130))
        self.buttons = [Button((W // 2 - 110, H - 76, 220, 48), "Назад", (170, 170, 190), 20, tag="menu_back")]

    def draw_ach(self, s):
        draw_text(s, "ДОСТИЖЕНИЯ", F(46, True), CREAM, W // 2, 62, center=True)
        got = len(self.earned)
        draw_text(s, f"{got} из {len(ACHIEVEMENTS)}", F(20), mix(CREAM, GOLD, 0.5),
                  W // 2, 108, center=True)
        cols, cw, ch, gap = 2, 500, 92, 18
        x0 = W // 2 - (cols * cw + (cols - 1) * gap) // 2
        y0 = 150
        for idx, key in enumerate(ACH_ORDER):
            info = ACHIEVEMENTS[key]
            col = idx % cols
            row = idx // cols
            rect = pygame.Rect(x0 + col * (cw + gap), y0 + row * (ch + gap), cw, ch)
            unlocked = key in self.earned
            base = (26, 30, 48) if unlocked else (18, 19, 28)
            bord = GOLD if unlocked else (55, 58, 76)
            panel(s, rect, base, radius=14, alpha=245, border=bord, bw=2)
            icol = GOLD if unlocked else (70, 74, 92)
            if unlocked:
                glow_circle(s, (rect.x + 46, rect.centery), 26, GOLD, strength=26, layers=3)
            _draw_ach_icon(s, info["icon"], rect.x + 46, rect.centery, 20, icol)
            tcol = CREAM if unlocked else (95, 100, 120)
            draw_text(s, info["title"], F(20, True), tcol, rect.x + 86, rect.y + 24)
            draw_text(s, info["desc"] if unlocked else "— ещё не открыто —",
                      F(15), DIM if unlocked else (80, 84, 104), rect.x + 86, rect.y + 52)

    # ─────────────────────── ЗАЧЁТКА ───────────────────────
    def _expected_exams(self):
        out = []
        for y in YEARS:
            if y.get("exam"):
                nm = y["exam"]["name"]
                for pref in ("Экзамен: ", "Экзамен ", "экзамен: "):
                    if nm.startswith(pref):
                        nm = nm[len(pref):]
                        break
                out.append((y["num"], nm))
        for e in FINAL_EXAMS:
            out.append((6, e["name"]))
        return out

    def _grade_words(self, score):
        if score >= 0.9:
            return "отлично", 5, (40, 110, 70)
        if score >= 0.7:
            return "хорошо", 4, (55, 85, 140)
        if score >= 0.5:
            return "удовлетв.", 3, (140, 100, 40)
        return "неудовл.", 2, (150, 50, 50)

    def _grades_screen(self):
        self.bg.set_theme((32, 34, 52), (220, 200, 160))
        self.buttons = [Button((W // 2 - 110, H - 52, 220, 42), "Назад",
                               (170, 170, 190), 19, tag="grades_back")]

    def _signature(self, s, x, y, seed, color):
        pts = []
        n = 16
        for i in range(n):
            t = i / (n - 1)
            px = x + t * 52
            py = y + math.sin(t * 7.0 + seed * 1.7) * 5 * (1 - abs(t - 0.5)) \
                 + math.sin(t * 3.1 + seed) * 3
            pts.append((px, py))
        if len(pts) > 1:
            pygame.draw.lines(s, color, False, pts, 2)
        pygame.draw.line(s, color, (x + 4, y + 7), (x + 44, y + 6), 1)

    def draw_grades(self, s):
        PAPER = (243, 238, 226)
        INK = (38, 42, 58)
        GREY = (120, 118, 112)
        LINE = (198, 190, 174)
        PEN = (44, 62, 120)

        card = pygame.Rect(120, 40, W - 240, H - 110)
        shadow = card.copy()
        shadow.move_ip(6, 8)
        panel(s, shadow, (0, 0, 0), radius=10, alpha=90)
        panel(s, card, PAPER, radius=10, alpha=255, border=(205, 196, 178), bw=2)
        pygame.draw.line(s, (222, 214, 198), (card.x + 26, card.y + 10),
                         (card.x + 26, card.bottom - 10), 2)

        draw_text(s, "ЗАЧЁТНАЯ КНИЖКА", F(30, True), INK, card.centerx, card.y + 34, center=True)
        draw_text(s, UNIVERSITY, F(15), GREY, card.centerx, card.y + 62, center=True)
        pygame.draw.line(s, LINE, (card.x + 60, card.y + 82), (card.right - 60, card.y + 82), 1)
        draw_text(s, f"Студент:  {HERO}", F(17, True), INK, card.x + 62, card.y + 94)

        done = {e["name"]: e for e in self.gradebook}
        expected = self._expected_exams()

        x = card.x + 62
        colw = [34, 400, 150, 105, 90]
        head_y = card.y + 128
        heads = ["№", "Наименование дисциплины", "Оценка", "Дата", "Подпись"]
        cx = x
        for i, h in enumerate(heads):
            draw_text(s, h, F(13, True), GREY, cx, head_y)
            cx += colw[i]
        pygame.draw.line(s, LINE, (x, head_y + 20), (card.right - 62, head_y + 20), 1)

        row_h = 40
        y0 = head_y + 30
        total_pts, cnt = 0, 0
        for idx, (course, name) in enumerate(expected):
            ry = y0 + idx * row_h
            rec = done.get(name)
            cx = x
            draw_text(s, str(idx + 1), F(15), GREY if rec else (185, 180, 168), cx, ry + 10)
            cx += colw[0]
            nm = name if len(name) < 42 else name[:39] + "…"
            draw_text(s, nm, F(16, True) if rec else F(16),
                      INK if rec else (176, 170, 158), cx, ry + 8)
            draw_text(s, f"{course} курс", F(11), (168, 162, 150), cx, ry + 26)
            cx += colw[1]
            if rec:
                word, num, gcol = self._grade_words(rec["score"])
                draw_text(s, word, F(16, True), gcol, cx, ry + 8)
                draw_text(s, f"{int(rec['score'] * 100)}%", F(11), (168, 162, 150), cx, ry + 26)
                total_pts += num
                cnt += 1
                cx += colw[2]
                draw_text(s, rec["date"], F(14), INK, cx, ry + 10)
                cx += colw[3]
                self._signature(s, cx + 6, ry + 20, idx, PEN)
            else:
                draw_text(s, "—", F(16), (196, 190, 176), cx, ry + 8)
            pygame.draw.line(s, (226, 219, 204), (x, ry + row_h - 4),
                             (card.right - 62, ry + row_h - 4), 1)

        foot_y = y0 + len(expected) * row_h + 10
        if cnt:
            avg = total_pts / cnt
            draw_text(s, f"Сдано экзаменов: {cnt} из {len(expected)}", F(15), GREY, x, foot_y)
            draw_text(s, f"Средний балл: {avg:.2f}", F(20, True), INK,
                      card.right - 240, foot_y - 4)
            if cnt == len(expected):
                self._stamp(s, card.right - 130, foot_y + 4)
        else:
            draw_text(s, "Пока ни одного экзамена. Всё впереди.", F(15), GREY, x, foot_y)

    def _stamp(self, s, cx, cy):
        col = (158, 46, 54)
        st = pygame.Surface((150, 150), pygame.SRCALPHA)
        pygame.draw.circle(st, (*col, 190), (75, 75), 52, 3)
        pygame.draw.circle(st, (*col, 190), (75, 75), 44, 1)
        f = F(13, True)
        for i, ln in enumerate(["ДОПУЩЕНА", "К РАБОТЕ", "ВРАЧОМ"]):
            img = f.render(ln, True, col)
            img.set_alpha(200)
            st.blit(img, img.get_rect(center=(75, 58 + i * 17)))
        st = pygame.transform.rotate(st, -13)
        s.blit(st, st.get_rect(center=(cx, cy)))

    # ─────────────────────── КАРТА ───────────────────────
    def _map(self):
        self.bg.set_theme((25, 35, 60), (140, 200, 255))
        self.buttons = []
        for i, y in enumerate(YEARS):
            x = 130 + i * 170
            yy = 380 + int(math.sin(i * 0.9) * 46)
            b = Button((x - 66, yy - 40, 132, 92), f"{y['num']} курс",
                       (255, 210, 130) if i <= self.unlocked else (90, 95, 115),
                       21, tag=("year", i))
            b.enabled = i <= self.unlocked
            b.state = "idle" if i <= self.unlocked else "faded"
            self.buttons.append(b)

    def draw_map(self, s):
        draw_text(s, "ПУТЬ", F(48, True), CREAM, W // 2, 80, center=True)
        draw_text(s, "шесть лет, шесть испытаний", F(19), DIM, W // 2, 126, center=True)
        pts = []
        for i in range(len(YEARS)):
            x = 130 + i * 170
            yy = 380 + int(math.sin(i * 0.9) * 46)
            pts.append((x, yy))
        if len(pts) > 1:
            pygame.draw.lines(s, (70, 80, 110), False, pts, 4)
            done = [p for i, p in enumerate(pts) if i <= self.unlocked]
            if len(done) > 1:
                pygame.draw.lines(s, GOLD, False, done, 4)
        for i, y in enumerate(YEARS):
            x = 130 + i * 170
            yy = 380 + int(math.sin(i * 0.9) * 46)
            if i in self.results:
                r = self.results[i]
                col = GREEN if r >= 0.8 else GOLD if r >= 0.5 else RED
                draw_text(s, f"{int(r*100)}%", F(16, True), col, x, yy + 66, center=True)
            elif i == self.unlocked:
                pulse = int(120 + 80 * math.sin(self.time * 4))
                draw_text(s, "▼", F(20, True), (255, 255, 255), x, yy - 62,
                          center=True, alpha=pulse)
        if self.unlocked < len(YEARS):
            draw_text(s, YEARS[self.unlocked]["subtitle"], F(20),
                      mix(CREAM, GOLD, 0.35), W // 2, 545, center=True)
        self._hud(s, 540)

    def _hud(self, s, y):
        for i, (label, val, col) in enumerate([
            ("Энергия", self.energy, (120, 220, 180)),
            ("Уверенность", self.confidence, (255, 190, 120)),
        ]):
            x = W // 2 - 230 + i * 260
            draw_text(s, label, F(15), DIM, x, y + 45)
            bar = pygame.Rect(x, y + 68, 200, 12)
            panel(s, bar, (30, 34, 50), radius=6, alpha=220)
            fill = bar.copy()
            fill.width = int(200 * clamp(val / 100, 0, 1))
            if fill.width > 2:
                panel(s, fill, col, radius=6)
            draw_text(s, f"{int(clamp(val,0,100))}", F(14, True), col, x + 210, y + 66)

    # ─────────────────────── НОВЕЛЛА ───────────────────────
    def start_story(self, scenes, after, label=""):
        self.scenes = list(scenes)
        self.si = 0
        self.typed = 0.0
        self.after_story = after
        self.choice_reply = None
        self.go("STORY", label)

    def _cur_scene(self):
        if self.si < len(self.scenes):
            return self.scenes[self.si]
        return None

    def _story_advance(self):
        sc = self._cur_scene()
        if sc is None:
            return
        if "choice" in sc:
            return
        full = sc.get("text", "")
        if self.typed < len(full):
            self.typed = len(full)
            return
        self.si += 1
        self.typed = 0.0
        self.buttons = []
        if self.si >= len(self.scenes):
            if self.after_story:
                self.after_story()
            return
        nxt = self._cur_scene()
        if nxt and "choice" in nxt:
            self._choice_ui(nxt)

    def _skip_story(self):
        guard = 0
        while True:
            guard += 1
            if guard > 500:
                return
            sc = self._cur_scene()
            if sc is None:
                if self.after_story:
                    self.after_story()
                return
            if "choice" in sc:
                self.buttons = []
                self._choice_ui(sc)
                self.typed = 0.0
                return
            self.si += 1
        # unreachable

    def _choice_ui(self, sc):
        self.buttons = []
        n = len(sc["options"])
        top = H - 250 - (n - 1) * 8
        for i, op in enumerate(sc["options"]):
            self.buttons.append(Button(
                (W // 2 - 400, top + i * 66, 800, 56), op["text"],
                self.cur_year()["accent"], 20, tag=("opt", i)))

    def _pick(self, i):
        sc = self._cur_scene()
        op = sc["options"][i]
        self.energy = clamp(self.energy + op.get("energy", 0), 0, 100)
        self.confidence = clamp(self.confidence + op.get("confidence", 0), 0, 100)
        txt = op.get("text", "").lower()
        rpl = op.get("reply", "").lower()
        if ("утра" in txt or "ноч" in txt or "утра" in rpl
                or "4 утра" in rpl or "3:40" in rpl):
            self.night_studier = True
        self.fx.burst(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1],
                      self.cur_year()["accent"], 18)
        self.scenes[self.si] = {"who": None, "text": op.get("reply", "")}
        self.typed = 0.0
        self.buttons = []

    def _mini_hud(self, s):
        x0 = W - 250
        y0 = 30
        for i, (label, val, col) in enumerate([
            ("Энергия", self.energy, (120, 220, 180)),
            ("Уверенность", self.confidence, (255, 190, 120)),
        ]):
            yy = y0 + i * 26
            draw_text(s, label, F(13), DIM, x0, yy)
            bar = pygame.Rect(x0 + 96, yy + 4, 110, 9)
            panel(s, bar, (30, 34, 50), radius=5, alpha=210)
            fill = bar.copy()
            fill.width = int(110 * clamp(val / 100, 0, 1))
            if fill.width > 2:
                panel(s, fill, col, radius=5)

    def draw_story(self, s):
        y = self.cur_year() if self.state == "STORY" and self.year_i < len(YEARS) else YEARS[-1]
        sc = self._cur_scene()
        draw_text(s, y["title"].upper(), F(20, True), mix(CREAM, y["accent"], 0.5), 40, 34)
        draw_text(s, y["subtitle"], F(15), DIM, 40, 62)
        self._mini_hud(s)
        cast = [HERO] + y["cast"]
        who = sc.get("who") if sc else None
        n = len(cast)
        for i, name in enumerate(cast):
            cx = int(W / (n + 1) * (i + 1))
            self.por.draw(s, name, cx, 300, 170,
                          active=(who == name), bob=self.time * 1.8 + i)
        if not sc:
            return
        box = pygame.Rect(80, H - 230, W - 160, 170)
        panel(s, box, (12, 14, 24), radius=20, alpha=228,
              border=mix(y["accent"], BLACK, 0.3), bw=2)
        if "choice" in sc:
            draw_text(s, sc["choice"], F(23, True), mix(CREAM, y["accent"], 0.25),
                      W // 2, H - 285, center=True)
            for b in self.buttons:
                b.draw(s)
            return
        if who:
            col = CHARACTER_COLORS.get(who, GOLD)
            tag = F(21, True).render(who, True, WHITE)
            tr = tag.get_rect(topleft=(box.x + 26, box.y - 17))
            panel(s, tr.inflate(28, 12), mix(col, BLACK, 0.35), radius=10,
                  alpha=250, border=col, bw=1)
            s.blit(tag, tr)
        full = sc.get("text", "")
        shown = full[:int(self.typed)]
        font = F(23) if who else F(22)
        color = CREAM if who else mix(CREAM, y["accent"], 0.35)
        lines = wrap_text(shown, font, box.width - 60)
        ty = box.y + 32
        for ln in lines[:4]:
            if who:
                draw_text(s, ln, font, color, box.x + 30, ty)
            else:
                draw_text(s, ln, font, color, box.centerx, ty + font.get_height() // 2,
                          center=True)
            ty += font.get_height() + 8
        if self.typed >= len(full):
            a = int(140 + 100 * math.sin(self.time * 5))
            draw_text(s, "▸", F(24, True), y["accent"], box.right - 40, box.bottom - 32,
                      center=True, alpha=a)
        pw = int((W - 160) * (self.si / max(1, len(self.scenes))))
        pygame.draw.rect(s, (60, 66, 88), (80, H - 40, W - 160, 3))
        pygame.draw.rect(s, y["accent"], (80, H - 40, pw, 3))
        # кнопка «Пропустить →»
        self._skip_rect = pygame.Rect(W - 168, 92, 128, 34)
        mouse = pygame.mouse.get_pos()
        hov = self._skip_rect.collidepoint(mouse)
        panel(s, self._skip_rect, mix((26, 28, 42), y["accent"], 0.14 if hov else 0.05),
              radius=10, alpha=230, border=mix((70, 74, 96), y["accent"], 0.6 if hov else 0.2), bw=2)
        draw_text(s, "Пропустить →", F(16, True),
                  mix(CREAM, WHITE, 0.4) if hov else DIM,
                  self._skip_rect.centerx, self._skip_rect.centery, center=True)

    # ─────────────────────── ЭКЗАМЕН ───────────────────────
    def start_exam(self, exam, accent, lives=3, timer=None, final_stage=None):
        self.exam = dict(exam)
        self.exam["accent"] = accent
        self.exam["timer"] = timer
        self.qi = 0
        self.lives = lives
        self.correct = 0
        self.answered = None
        self.q_timer = timer or 0
        self.final_stage = final_stage
        self.go("EXAM", exam["name"], 0.6)

    def _exam_ui(self):
        self.buttons = []
        q = self.exam["questions"][self.qi]
        acc = self.exam["accent"]
        top = 400
        for i, ans in enumerate(q["a"]):
            col = i % 2
            row = i // 2
            self.buttons.append(Button(
                (150 + col * 500, top + row * 84, 470, 68), ans, acc, 20, tag=("ans", i)))
        self.q_timer = self.exam["timer"] or 0
        self.answered = None

    def _answer(self, i):
        if self.answered is not None:
            return
        q = self.exam["questions"][self.qi]
        self.answered = i
        ok = (i == q["correct"])
        for b in self.buttons:
            if not isinstance(b.tag, tuple) or b.tag[0] != "ans":
                continue
            if b.tag[1] == q["correct"]:
                b.state = "correct"
            elif b.tag[1] == i:
                b.state = "wrong"
            else:
                b.state = "faded"
            b.enabled = False
        if ok:
            self.correct += 1
            self.fx.burst(W // 2, 300, GREEN, 34)
            self.confidence = clamp(self.confidence + 3, 0, 100)
        else:
            self.lives -= 1
            self.shake = 0.45
            self.fx.burst(W // 2, 300, RED, 22)
            self.confidence = clamp(self.confidence - 3, 0, 100)
        self.buttons.append(Button(
            (W // 2 - 110, 660, 220, 46),
            "Далее" if self.qi + 1 < len(self.exam["questions"]) else "Результат",
            self.exam["accent"], 20, tag="next"))

    def _next_q(self):
        if self.lives <= 0 or self.qi + 1 >= len(self.exam["questions"]):
            self.go("RESULT", "")
            return
        self.qi += 1
        self.buttons = []
        self._exam_ui()

    def draw_exam(self, s):
        acc = self.exam["accent"]
        q = self.exam["questions"][self.qi]
        off = 0
        if self.shake > 0:
            off = int(math.sin(self.shake * 60) * self.shake * 18)
        draw_text(s, self.exam["name"].upper(), F(22, True), mix(CREAM, acc, 0.55),
                  W // 2, 46, center=True)
        if self.exam.get("prof") and self.qi == 0 and self.answered is None:
            draw_text(s, self.exam["prof"], F(16), DIM, W // 2, 76, center=True)
        elif self.exam.get("subtitle"):
            draw_text(s, self.exam["subtitle"], F(16), DIM, W // 2, 76, center=True)
        for i in range(self.lives):
            heart(s, 60 + i * 34, 46, 13, RED, 255)
        draw_text(s, f"Вопрос {self.qi+1} / {len(self.exam['questions'])}",
                  F(17, True), DIM, W - 60, 46, center=True)
        if self.exam["timer"] and self.answered is None:
            frac = clamp(self.q_timer / self.exam["timer"], 0, 1)
            bar = pygame.Rect(W // 2 - 200, 100, 400, 8)
            panel(s, bar, (35, 38, 55), radius=4)
            f = bar.copy()
            f.width = int(400 * frac)
            if f.width > 2:
                panel(s, f, GREEN if frac > 0.35 else RED, radius=4)
        card = pygame.Rect(150, 150, W - 300, 210)
        panel(s, card, (14, 16, 28), radius=20, alpha=235,
              border=mix(acc, BLACK, 0.35), bw=2)
        font = F(26, True)
        lines = wrap_text(q["q"], font, card.width - 80)
        ty = card.centery - len(lines) * (font.get_height() + 6) // 2
        for ln in lines:
            draw_text(s, ln, font, CREAM, card.centerx + off, ty + font.get_height() // 2,
                      center=True)
            ty += font.get_height() + 6
        for b in self.buttons:
            b.draw(s)
        if self.answered is not None:
            ok = self.answered == q["correct"]
            box = pygame.Rect(150, 590, W - 300, 56)
            panel(s, box, mix(GREEN if ok else RED, BLACK, 0.72), radius=14,
                  alpha=235, border=GREEN if ok else RED, bw=2)
            head = "Верно!" if ok else "Ошибка"
            draw_text(s, head, F(18, True), GREEN if ok else RED, box.x + 24, box.y + 8)
            draw_text(s, q.get("fact", ""), F(16), CREAM, box.x + 24, box.y + 31)

    # ─────────────────────── РЕЗУЛЬТАТ ───────────────────────
    def _result_ui(self):
        total = len(self.exam["questions"])
        score = self.correct / total
        passed = self.lives > 0 and score >= 0.5
        self.buttons = []
        if passed:
            self.buttons.append(Button((W // 2 - 130, 560, 260, 54), "Дальше",
                                       GREEN, 22, tag="pass"))
            self.fx.confetti(40)
        else:
            self.buttons.append(Button((W // 2 - 130, 560, 260, 54), "Пересдача",
                                       GOLD, 22, tag="retry"))

    def draw_result(self, s):
        total = len(self.exam["questions"])
        score = self.correct / total
        passed = self.lives > 0 and score >= 0.5
        if score >= 0.9:
            grade, col = "ОТЛИЧНО", GREEN
        elif score >= 0.7:
            grade, col = "ХОРОШО", (170, 220, 140)
        elif score >= 0.5:
            grade, col = "УДОВЛЕТВОРИТЕЛЬНО", GOLD
        else:
            grade, col = "НЕЗАЧЁТ", RED
        if self.lives <= 0:
            grade, col = "НЕЗАЧЁТ", RED
        card = pygame.Rect(W // 2 - 300, 160, 600, 360)
        panel(s, card, (14, 16, 28), radius=24, alpha=240, border=col, bw=3)
        glow_circle(s, card.center, 220, col, strength=30, layers=4)
        draw_text(s, self.exam["name"], F(20), DIM, W // 2, 200, center=True)
        draw_text(s, grade, F(50, True), col, W // 2, 265, center=True)
        draw_text(s, f"{self.correct} из {total} · {int(score*100)}%",
                  F(26, True), CREAM, W // 2, 330, center=True)
        cx, cy, r = W // 2, 425, 46
        pygame.draw.circle(s, (40, 44, 62), (cx, cy), r, 8)
        ang = -math.pi / 2
        pts = [(cx + math.cos(ang + score * math.tau * (i / 40)) * r,
                cy + math.sin(ang + score * math.tau * (i / 40)) * r) for i in range(41)]
        if score > 0.02 and len(pts) > 1:
            pygame.draw.lines(s, col, False, pts, 8)
        msg = ("Ты справилась." if passed else "Ничего. Пересдача — это тоже часть пути.")
        draw_text(s, msg, F(18), mix(CREAM, col, 0.3), W // 2, 522, center=True)

    def _record_grade(self, score):
        name = self.exam.get("name", "")
        for pref in ("Экзамен: ", "Экзамен ", "экзамен: "):
            if name.startswith(pref):
                name = name[len(pref):]
                break
        if self.final_stage is None:
            course = self.cur_year()["num"]
        else:
            course = 6
        entry = {
            "name": name,
            "score": round(score, 3),
            "course": course,
            "date": datetime.datetime.now().strftime("%d.%m.%Y"),
        }
        for i, e in enumerate(self.gradebook):
            if e.get("name") == name:
                self.gradebook[i] = entry
                return
        self.gradebook.append(entry)

    def _after_result(self):
        total = len(self.exam["questions"])
        score = self.correct / total
        flawless = (self.correct == total)
        self._record_grade(score)

        self.grant("first_exam")
        if flawless:
            self.grant("flawless")
            self.flawless_streak += 1
        else:
            self.flawless_streak = 0
        if self.lives == 1:
            self.grant("survivor")
        if self.night_studier:
            self.grant("night_watch")

        if self.final_stage is None:
            self.results[self.year_i] = score
            self.energy = clamp(self.energy + 15, 0, 100)
            y = self.cur_year()
            if y["num"] == 3:
                self.grant("pharma")
            if y["num"] == 4:
                self.grant("friends")
            if y["num"] == 5:
                self.grant("burnout")
            if self.flawless_streak >= 5:
                self.grant("perfectionist")
            after = y.get("after") or []

            def then():
                self.unlocked = max(self.unlocked, self.year_i + 1)
                if self.unlocked >= len(YEARS):
                    self.unlocked = len(YEARS) - 1
                self.save_progress()
                self.go("MAP", "")
            if after:
                self.start_story(after, then, "")
            else:
                then()
        else:
            e = FINAL_EXAMS[self.final_stage]
            if e.get("timer"):
                self.grant("speed")
            nxt = self.final_stage + 1
            if nxt < len(FINAL_EXAMS):
                self._launch_final(nxt)
            else:
                self.grant("doctor")
                savemod.clear()
                self.start_story(FINALE_SCENES, lambda: self.go("LETTER", ""), "")

    def _launch_final(self, i):
        e = dict(FINAL_EXAMS[i])
        e["questions"] = exam_builder.build_final_exam(FINAL_EXAMS[i])
        self.bg.set_theme((20, 30, 60), e["accent"])
        self.start_exam(e, e["accent"], e.get("lives", 3), e.get("timer"), final_stage=i)

    # ─────────────────────── ФИНАЛ ───────────────────────
    def draw_letter(self, s):
        self.letter_t += 1 / FPS
        card = pygame.Rect(W // 2 - 380, 70, 760, 540)
        panel(s, card, (16, 14, 26), radius=24, alpha=240, border=(255, 150, 180), bw=2)
        f = F(22)
        shown = int(self.letter_t / 0.35)
        yy = card.y + 46
        for i, ln in enumerate(FINALE_LETTER):
            if i > shown:
                break
            a = int(255 * clamp((self.letter_t / 0.35 - i) * 2.2, 0, 1))
            draw_text(s, ln, f, CREAM if ln else DIM, card.centerx, yy, center=True, alpha=a)
            yy += 30
        if shown >= len(FINALE_LETTER):
            draw_text(s, FROM_WHO, F(17), mix(CREAM, GOLD, 0.5),
                      card.centerx, card.bottom - 46, center=True)
            if not self.buttons:
                self.buttons = [Button((W // 2 - 150, 630, 300, 54),
                                       "Ответить", (255, 150, 180), 22, tag="answer")]

    def draw_input(self, s):
        draw_text(s, "Во сколько ты в воскресенье свободна?", F(38, True), CREAM,
                  W // 2, 190, center=True)
        draw_text(s, f"Я забронирую столик в «{RESTAURANT}»", F(22),
                  mix(CREAM, GOLD, 0.45), W // 2, 245, center=True)
        box = pygame.Rect(W // 2 - 170, 320, 340, 82)
        glow_circle(s, box.center, 130, (255, 150, 180), strength=34, layers=4)
        panel(s, box, (18, 16, 30), radius=18, alpha=245, border=(255, 150, 180), bw=3)
        txt = self.time_input if self.time_input else "__:__"
        col = CREAM if self.time_input else (90, 94, 115)
        draw_text(s, txt, F(46, True), col, box.centerx, box.centery, center=True)
        if int(self.time * 2) % 2 == 0 and len(self.time_input) < 5:
            wpx = F(46, True).size(self.time_input)[0]
            x = box.centerx - wpx // 2 + wpx + 4
            pygame.draw.rect(s, (255, 150, 180), (x, box.centery - 22, 3, 44))
        draw_text(s, "формат  ЧЧ:ММ   ·   например  19:30", F(16), DIM,
                  W // 2, 428, center=True)
        if self.input_err:
            draw_text(s, self.input_err, F(18, True), RED, W // 2, 462, center=True)
        if not self.buttons:
            self.buttons = [Button((W // 2 - 130, 500, 260, 56), "Отправить",
                                   (255, 150, 180), 22, tag="send")]

    def _submit_time(self):
        t = self.time_input.strip()
        parts = t.split(":")
        ok = (len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()
              and 0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59 and len(parts[1]) == 2)
        if not ok:
            self.input_err = "Хм, не похоже на время. Попробуй так: 19:30"
            self.shake = 0.4
            return
        self.saved_time = f"{int(parts[0]):02d}:{parts[1]}"
        try:
            with open(BOOKING_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] "
                        f"{HERO} выбрала время: {self.saved_time} — ресторан «{RESTAURANT}»\n")
        except Exception:
            pass
        self.fx.confetti(120)
        self.go("THANKS", "")

    def draw_thanks(self, s):
        self.fx.confetti(1)
        if random.random() < 0.08:
            self.fx.hearts(1)
        p = 1 + 0.05 * math.sin(self.time * 3)
        heart(s, W // 2, 175, 52 * p, (255, 110, 150), 240)
        draw_text(s, f"Столик забронирован", F(46, True), CREAM, W // 2, 285, center=True)
        draw_text(s, f"«{RESTAURANT}»  ·  в воскресенье в {self.saved_time}",
                  F(30, True), GOLD, W // 2, 345, center=True)
        card = pygame.Rect(W // 2 - 330, 400, 660, 150)
        panel(s, card, (16, 14, 26), radius=20, alpha=225, border=(255, 150, 180), bw=2)
        for i, ln in enumerate([
            "Шесть лет позади.",
            f"В воскресенье вечером я жду тебя, доктор {HERO}.",
            "Я так тобой горжусь.",
        ]):
            draw_text(s, ln, F(22), CREAM if i != 2 else mix(CREAM, GOLD, 0.5),
                      card.centerx, card.y + 36 + i * 38, center=True)
        draw_text(s, "(время сохранено в booking.txt)", F(14), (100, 105, 125),
                  W // 2, 600, center=True)
        if not self.buttons:
            self.buttons = [
                Button((W // 2 - 226, 630, 216, 46), "Моя зачётка",
                       (220, 200, 160), 19, tag="grades"),
                Button((W // 2 + 10, 630, 216, 46), "В меню",
                       (150, 150, 180), 19, tag="menu"),
            ]

    # ─────────────────────── КЛИКИ ───────────────────────
    def _click(self, pos):
        if self.tr.active:
            return
        for b in self.buttons:
            if not b.hovered(pos):
                continue
            tag = b.tag
            if tag == "start":
                self.go("MAP", "Сентябрь. Первый курс.")
            elif tag == "continue":
                self.load_progress()
                self.go("MAP", "С возвращением")
            elif tag == "restart":
                self.reset()
            elif tag == "ach":
                self.go("ACH", "")
            elif tag == "grades":
                self._grades_from = self.state
                self.go("GRADES", "")
            elif tag == "grades_back":
                self.go(getattr(self, "_grades_from", "MENU") or "MENU", "")
            elif tag == "menu_back":
                self.go("MENU", "")
            elif tag == "quit":
                pygame.quit(); sys.exit()
            elif isinstance(tag, tuple) and tag[0] == "year":
                self.year_i = tag[1]
                y = self.cur_year()
                self.bg.set_theme(y["theme"], y["accent"])
                self.start_story(y["scenes"], self._year_story_done,
                                 f"{y['num']} курс")
            elif isinstance(tag, tuple) and tag[0] == "opt":
                self._pick(tag[1])
            elif isinstance(tag, tuple) and tag[0] == "ans":
                self._answer(tag[1])
            elif tag == "next":
                self._next_q()
            elif tag == "pass":
                self._after_result()
            elif tag == "retry":
                self.energy = clamp(self.energy - 10, 0, 100)
                if self.final_stage is None:
                    y = self.cur_year()
                    exam = dict(y["exam"])
                    exam["questions"] = exam_builder.build_year_exam(y)
                    self.start_exam(exam, self.exam["accent"], 3)
                else:
                    self._launch_final(self.final_stage)
            elif tag == "answer":
                self.go("INPUT", "")
            elif tag == "send":
                self._submit_time()
            elif tag == "menu":
                self.reset()
            return

        if self.state == "LETTER" and self.letter_t < len(FINALE_LETTER) * 0.35:
            self.letter_t = len(FINALE_LETTER) * 0.35 + 1
            return

        if self.state == "STORY":
            if getattr(self, "_skip_rect", None) and self._skip_rect.collidepoint(pos):
                self._skip_story()
                return
            sc = self._cur_scene()
            if sc and "choice" not in sc:
                self._story_advance()

    def _year_story_done(self):
        y = self.cur_year()
        if y["exam"]:
            exam = dict(y["exam"])
            exam["questions"] = exam_builder.build_year_exam(y)
            self.start_exam(exam, y["accent"], 3)
        else:
            self._launch_final(0)

    # ─────────────────────── ЦИКЛ ───────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self.time += dt
            mouse = pygame.mouse.get_pos()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    elif e.key == pygame.K_F11:
                        self.full = not self.full
                        self.screen = pygame.display.set_mode(
                            (W, H), pygame.FULLSCREEN | pygame.SCALED if self.full else 0)
                    elif e.key == pygame.K_m:
                        self.music.toggle_mute()
                    elif e.key == pygame.K_n:
                        self.music.next_track()
                    elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.music.change_volume(-0.1)
                    elif e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        self.music.change_volume(+0.1)
                    elif e.key == pygame.K_s and self.state == "STORY":
                        sc = self._cur_scene()
                        if not (sc and "choice" in sc):
                            self._skip_story()
                    elif self.state == "INPUT":
                        if e.key == pygame.K_BACKSPACE:
                            self.time_input = self.time_input[:-1]
                            self.input_err = ""
                        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self._submit_time()
                        else:
                            ch = e.unicode
                            if ch and len(self.time_input) < 5 and (ch.isdigit() or ch == ":"):
                                self.time_input += ch
                                if len(self.time_input) == 2 and ":" not in self.time_input:
                                    self.time_input += ":"
                                self.input_err = ""
                    elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if self.state == "STORY":
                            sc = self._cur_scene()
                            if sc and "choice" not in sc:
                                self._story_advance()
                elif e.type == MUSIC_END_EVENT:
                    self.music.track_ended()
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self._click(mouse)

            self.bg.update(dt)
            self.fx.update(dt)
            self.tr.update(dt)
            self.toasts.update(dt)
            self.music.update(dt)
            self.shake = max(0, self.shake - dt)
            for b in self.buttons:
                b.update(dt, mouse)

            if self.state == "STORY":
                sc = self._cur_scene()
                if sc and "choice" not in sc:
                    self.typed = min(len(sc.get("text", "")), self.typed + dt * 45)
                elif sc and "choice" in sc and not self.buttons:
                    self._choice_ui(sc)

            if self.state == "EXAM" and self.exam.get("timer") and self.answered is None \
                    and not self.tr.active:
                self.q_timer -= dt
                if self.q_timer <= 0:
                    wrong = 0 if self.exam["questions"][self.qi]["correct"] != 0 else 1
                    self._answer(wrong)

            s = self.screen
            self.bg.draw(s)
            if self.state == "MENU":
                self.draw_menu(s)
            elif self.state == "MAP":
                self.draw_map(s)
            elif self.state == "STORY":
                self.draw_story(s)
            elif self.state == "EXAM":
                self.draw_exam(s)
            elif self.state == "RESULT":
                self.draw_result(s)
            elif self.state == "LETTER":
                self.draw_letter(s)
            elif self.state == "INPUT":
                self.draw_input(s)
            elif self.state == "THANKS":
                self.draw_thanks(s)
            elif self.state == "ACH":
                self.draw_ach(s)
            elif self.state == "GRADES":
                self.draw_grades(s)

            if self.state in ("MENU", "MAP", "LETTER", "INPUT", "THANKS",
                              "RESULT", "ACH", "GRADES"):
                for b in self.buttons:
                    b.draw(s)

            self.fx.draw(s)
            self.music.draw(s)
            self.toasts.draw(s)
            self.tr.draw(s)
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
