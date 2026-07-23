# -*- coding: utf-8 -*-
import os
import math
import datetime

import pygame

_DIR = os.path.dirname(os.path.abspath(__file__))

DW, DH = 1600, 1130
PAPER = (247, 243, 232)
EDGE = (206, 178, 118)
INK = (34, 38, 54)
GREY = (122, 118, 110)
SEAL = (158, 46, 54)
PEN = (44, 62, 120)


def _font(size, bold=False):
    from main import F
    return F(size, bold)


def _text(surf, txt, font, color, x, y, center=False):
    img = font.render(txt, True, color)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(img, r)
    return r


def _ornament(s, x, y, w, col):
    pygame.draw.line(s, col, (x, y), (x + w, y), 2)
    cx = x + w // 2
    pygame.draw.circle(s, col, (cx, y), 6, 2)
    pygame.draw.circle(s, col, (cx - 22, y), 3)
    pygame.draw.circle(s, col, (cx + 22, y), 3)


def _seal(s, cx, cy, r=118):
    st = pygame.Surface((r * 2 + 40, r * 2 + 40), pygame.SRCALPHA)
    c = (r + 20, r + 20)
    pygame.draw.circle(st, (*SEAL, 205), c, r, 5)
    pygame.draw.circle(st, (*SEAL, 205), c, r - 14, 2)
    pygame.draw.circle(st, (*SEAL, 160), c, r - 46, 2)
    f = _font(21, True)
    for i, ln in enumerate(["ДИПЛОМ", "ВРАЧА"]):
        img = f.render(ln, True, SEAL)
        img.set_alpha(215)
        st.blit(img, img.get_rect(center=(c[0], c[1] - 14 + i * 28)))
    small = _font(13, True)
    txt = "• МЕДИЦИНСКИЙ УНИВЕРСИТЕТ •"
    for i, ch in enumerate(txt):
        ang = -math.pi / 2 + (i - len(txt) / 2) * 0.115
        img = small.render(ch, True, SEAL)
        img.set_alpha(190)
        rr = r - 30
        pos = (c[0] + math.cos(ang) * rr, c[1] + math.sin(ang) * rr)
        img = pygame.transform.rotate(img, -math.degrees(ang) - 90)
        st.blit(img, img.get_rect(center=pos))
    st = pygame.transform.rotate(st, -11)
    s.blit(st, st.get_rect(center=(cx, cy)))


def _signature(s, x, y, seed, scale=1.0):
    pts = []
    n = 26
    for i in range(n):
        t = i / (n - 1)
        px = x + t * 150 * scale
        py = y + (math.sin(t * 8.5 + seed * 2.1) * 13
                  + math.sin(t * 3.3 + seed) * 8) * (1 - abs(t - 0.5) * 1.1) * scale
        pts.append((px, py))
    if len(pts) > 1:
        pygame.draw.lines(s, PEN, False, pts, 3)
    pygame.draw.line(s, PEN, (x + 8, y + 20 * scale), (x + 140 * scale, y + 17 * scale), 2)


def build(hero, gradebook, university, avg=None, date_str=None):
    s = pygame.Surface((DW, DH))
    s.fill(PAPER)

    for i in range(70):
        a = 10 - i % 5
        pygame.draw.rect(s, (238, 232, 218), (0, i * 17, DW, 1))

    pygame.draw.rect(s, EDGE, (34, 34, DW - 68, DH - 68), 4)
    pygame.draw.rect(s, EDGE, (52, 52, DW - 104, DH - 104), 1)
    for cx, cy in ((60, 60), (DW - 60, 60), (60, DH - 60), (DW - 60, DH - 60)):
        pygame.draw.circle(s, EDGE, (cx, cy), 15, 3)
        pygame.draw.circle(s, EDGE, (cx, cy), 5)

    _text(s, "ДИПЛОМ", _font(86, True), INK, DW // 2, 168, center=True)
    _ornament(s, DW // 2 - 210, 224, 420, EDGE)
    _text(s, "о высшем медицинском образовании", _font(28), GREY, DW // 2, 262, center=True)

    _text(s, "Настоящим удостоверяется, что", _font(27), GREY, DW // 2, 352, center=True)
    _text(s, hero, _font(78, True), INK, DW // 2, 434, center=True)
    pygame.draw.line(s, EDGE, (DW // 2 - 300, 486), (DW // 2 + 300, 486), 2)

    lines = [
        "прошла полный курс обучения длиной в шесть лет,",
        "выдержала все положенные испытания",
        "и решением экзаменационной комиссии",
    ]
    for i, ln in enumerate(lines):
        _text(s, ln, _font(27), INK, DW // 2, 536 + i * 42, center=True)

    _text(s, "ДОПУЩЕНА К РАБОТЕ ВРАЧОМ", _font(44, True), INK, DW // 2, 700, center=True)

    if date_str is None:
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")

    passed = len(gradebook)
    if avg is None and passed:
        tot = 0
        for e in gradebook:
            sc = e.get("score", 0)
            tot += 5 if sc >= 0.9 else 4 if sc >= 0.7 else 3 if sc >= 0.5 else 2
        avg = tot / passed

    box_y = 786
    if passed:
        _text(s, f"Сдано экзаменов:  {passed}", _font(25), GREY, 150, box_y)
        _text(s, f"Средний балл:  {avg:.2f}", _font(25, True), INK, 150, box_y + 42)
        if avg >= 4.75:
            _text(s, "с отличием", _font(24, True), SEAL, 150, box_y + 84)

    _text(s, university, _font(24, True), INK, 150, DH - 176)
    _text(s, f"Дата выдачи:  {date_str}", _font(22), GREY, 150, DH - 138)

    _signature(s, DW - 560, DH - 168, 3.0)
    pygame.draw.line(s, GREY, (DW - 570, DH - 132), (DW - 380, DH - 132), 1)
    _text(s, "Ректор", _font(19), GREY, DW - 545, DH - 124)

    _seal(s, DW - 250, DH - 250)
    return s


def save(hero, gradebook, university, out_dir=None):
    surf = build(hero, gradebook, university)
    out_dir = out_dir or _DIR
    safe = "".join(ch for ch in hero if ch.isalnum() or ch in " -_").strip() or "врач"
    path = os.path.join(out_dir, f"Диплом_{safe}.png")
    try:
        pygame.image.save(surf, path)
        return path
    except Exception:
        return None
