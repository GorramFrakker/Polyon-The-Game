#!/usr/bin/env python3
"""
POLYON: THE GAME
A Space Invaders style arcade game themed around POLYON(R) Controlled-Release
Fertilizer by Harrell's. Defend the turf through 18 holes of golf-course
mayhem armed with a bag of POLYON and an endless supply of green prills.

Controls:
    LEFT / RIGHT or A / D ... move
    SPACE ................... fire
    P or ESC ................ pause
    ENTER ................... confirm / start
    H ....................... high scores (title screen)

All artwork is drawn in code (no external assets required).
"""

import array
import json
import math
import os
import random
import sys

import pygame as pg

# ---------------------------------------------------------------------------
# Constants & palette (POLYON / Harrell's colors)
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 960, 720
FPS = 60
HUD_H = 54
PLAYER_Y = HEIGHT - 78
INVASION_Y = PLAYER_Y - 46
TOTAL_HOLES = 18

GREEN_DARK = (0, 84, 42)
GREEN = (0, 132, 61)
GREEN_BRIGHT = (40, 168, 92)
BB_GREEN = (52, 184, 100)
BB_LIGHT = (160, 228, 178)
BLUE = (31, 94, 142)
BLUE_LIGHT = (96, 164, 208)
WHITE = (246, 249, 247)
CREAM = (228, 236, 230)
BG_TOP = (6, 28, 17)
BG_BOTTOM = (13, 54, 31)
RED = (198, 62, 50)
YELLOW = (240, 202, 84)
GRAY = (122, 130, 126)
GRAY_DARK = (70, 76, 73)
DARK = (18, 24, 20)

HOLE_NAMES = [
    "The First Tee", "Dimple Downs", "Fairway Frenzy", "Sprinkler Alley",
    "Mulligan's Revenge", "Into the Rough", "Clippings Corner", "Dogleg Left",
    "THE TURN: Marshal's Cart", "Back Nine Blues", "Water Hazard",
    "Beverage Cart Blitz", "Triple Bogey", "Greenskeeper's Wrath",
    "The Sand Trap", "Sudden Death", "The Island Green",
    "FINAL HOLE: The Mega Mower",
]

DEFAULT_SCORES = [
    {"name": "TURF", "score": 18000, "hole": 18},
    {"name": "AGRO", "score": 15000, "hole": 16},
    {"name": "PRIL", "score": 12500, "hole": 14},
    {"name": "GREE", "score": 10000, "hole": 12},
    {"name": "MOWR", "score": 8000, "hole": 10},
    {"name": "FERT", "score": 6000, "hole": 8},
    {"name": "ROOT", "score": 4500, "hole": 6},
    {"name": "SOIL", "score": 3000, "hole": 4},
    {"name": "SEED", "score": 1500, "hole": 2},
    {"name": "DIVT", "score": 500, "hole": 1},
]


def scores_path():
    """High score file lives in a per-user data directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        folder = os.path.join(base, "PolyonTheGame")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".polyon_the_game")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "highscores.json")


def load_scores():
    try:
        with open(scores_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        scores = [s for s in data if "name" in s and "score" in s]
        if scores:
            return sorted(scores, key=lambda s: -s["score"])[:10]
    except Exception:
        pass
    return list(DEFAULT_SCORES)


def save_scores(scores):
    try:
        with open(scores_path(), "w", encoding="utf-8") as fh:
            json.dump(scores[:10], fh, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

_font_cache = {}


def get_font(size, bold=True, italic=False):
    key = (size, bold, italic)
    if key not in _font_cache:
        try:
            f = pg.font.SysFont("arial,helvetica,dejavusans,freesans",
                                size, bold=bold, italic=italic)
        except Exception:
            f = pg.font.Font(None, size)
        _font_cache[key] = f
    return _font_cache[key]


def text(surf, msg, size, color, *, center=None, topleft=None, midtop=None,
         bold=True, italic=False, shadow=None):
    f = get_font(size, bold, italic)
    img = f.render(msg, True, color)
    rect = img.get_rect()
    if center:
        rect.center = center
    elif topleft:
        rect.topleft = topleft
    elif midtop:
        rect.midtop = midtop
    if shadow:
        sh = f.render(msg, True, shadow)
        surf.blit(sh, rect.move(2, 2))
    surf.blit(img, rect)
    return rect


# ---------------------------------------------------------------------------
# Sound synthesis (no asset files)
# ---------------------------------------------------------------------------

class Sounds:
    RATE = 22050

    def __init__(self):
        self.enabled = False
        self.bank = {}
        try:
            pg.mixer.init(frequency=self.RATE, size=-16, channels=1)
            self.enabled = True
        except Exception:
            return
        self.bank["shoot"] = self._tone([(880, 480)], 70, vol=0.18)
        self.bank["hit"] = self._tone([(300, 180)], 90, vol=0.25)
        self.bank["boom"] = self._noise(220, vol=0.3)
        self.bank["player_boom"] = self._noise(550, vol=0.4)
        self.bank["bonus"] = self._tone([(660, 990), (990, 1320)], 240, vol=0.22)
        self.bank["clear"] = self._tone([(523, 659), (659, 784), (784, 1046)],
                                        420, vol=0.25)
        self.bank["life"] = self._tone([(784, 1046), (1046, 1568)], 300, vol=0.25)
        self.bank["boss_hit"] = self._tone([(180, 140)], 70, vol=0.25)

    def _tone(self, sweeps, ms, vol=0.3):
        n = int(self.RATE * ms / 1000)
        per = max(1, n // len(sweeps))
        buf = array.array("h")
        phase = 0.0
        for seg, (f0, f1) in enumerate(sweeps):
            for i in range(per):
                t = i / per
                freq = f0 + (f1 - f0) * t
                phase += 2 * math.pi * freq / self.RATE
                v = 1.0 if math.sin(phase) >= 0 else -1.0
                env = 1.0 - (seg * per + i) / n
                buf.append(int(v * env * vol * 32767))
        return pg.mixer.Sound(buffer=buf.tobytes())

    def _noise(self, ms, vol=0.3):
        n = int(self.RATE * ms / 1000)
        buf = array.array("h")
        v = 0.0
        for i in range(n):
            v = 0.6 * v + 0.4 * random.uniform(-1, 1)
            env = (1.0 - i / n) ** 1.5
            buf.append(int(v * env * vol * 32767))
        return pg.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.enabled and name in self.bank:
            try:
                self.bank[name].play()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Sprite factories — everything is drawn in code
# ---------------------------------------------------------------------------

def make_bb(radius=5):
    """A single green POLYON prill (the player's ammo)."""
    d = radius * 2
    s = pg.Surface((d + 4, d + 4), pg.SRCALPHA)
    c = (d + 4) // 2
    pg.draw.circle(s, (*BB_GREEN, 60), (c, c), radius + 2)
    pg.draw.circle(s, GREEN_DARK, (c, c), radius)
    pg.draw.circle(s, BB_GREEN, (c - 1, c - 1), radius - 1)
    pg.draw.circle(s, BB_LIGHT, (c - radius // 2, c - radius // 2),
                   max(1, radius // 3))
    return s


def make_player_bag(w=58, h=70):
    """The POLYON 25KG fertilizer bag, ready for battle."""
    s = pg.Surface((w, h), pg.SRCALPHA)
    body = pg.Rect(3, 6, w - 6, h - 8)
    pg.draw.rect(s, WHITE, body, border_radius=8)
    pg.draw.rect(s, (205, 215, 208), body, width=2, border_radius=8)
    # crimped bag top
    pg.draw.rect(s, CREAM, (w // 2 - 14, 0, 28, 9), border_radius=3)
    pg.draw.rect(s, (190, 200, 192), (w // 2 - 14, 0, 28, 9), 1, border_radius=3)
    # top green wave banner
    pts = [(4, 8)]
    for i in range(11):
        x = 4 + i * (w - 8) / 10
        y = 20 + 6 * math.sin(i * 0.9)
        pts.append((x, y))
    pts.append((w - 4, 8))
    pg.draw.polygon(s, GREEN, pts)
    pg.draw.polygon(s, GREEN_BRIGHT,
                    [(p[0], p[1] - 2) for p in pts[1:-1]] + [(w - 4, 8), (4, 8)])
    # center POLYON band
    band = pg.Rect(6, h // 2 - 9, w - 12, 18)
    pg.draw.ellipse(s, GREEN, band)
    f = get_font(11, bold=True, italic=True)
    word = f.render("POLYON", True, WHITE)
    s.blit(word, word.get_rect(center=band.center))
    # bottom green swoosh
    pg.draw.arc(s, GREEN, (-w // 2, h - 26, w * 2, 40), math.pi * 0.15,
                math.pi * 0.85, 7)
    pg.draw.rect(s, GREEN, (4, h - 8, w - 8, 6), border_radius=3)
    # a few prills spilling near the top
    for i, (px, py) in enumerate([(w // 2 - 9, 26), (w // 2 + 2, 29),
                                  (w // 2 + 10, 25)]):
        pg.draw.circle(s, BB_GREEN, (px, py), 2)
    return s


def make_golf_ball(size=34):
    s = pg.Surface((size, size), pg.SRCALPHA)
    c = size // 2
    r = c - 2
    pg.draw.circle(s, (210, 214, 211), (c + 1, c + 2), r)
    pg.draw.circle(s, WHITE, (c, c), r)
    pg.draw.circle(s, (252, 253, 252), (c - r // 3, c - r // 3), r // 2)
    for ang in range(0, 360, 45):
        for rr in (r * 0.35, r * 0.68):
            x = c + rr * math.cos(math.radians(ang + rr * 9))
            y = c + rr * math.sin(math.radians(ang + rr * 9))
            pg.draw.circle(s, (196, 202, 198), (int(x), int(y)), 2)
    # angry little eyes so it reads as an enemy
    pg.draw.circle(s, DARK, (c - 6, c - 3), 3)
    pg.draw.circle(s, DARK, (c + 6, c - 3), 3)
    pg.draw.line(s, DARK, (c - 10, c - 9), (c - 3, c - 6), 2)
    pg.draw.line(s, DARK, (c + 10, c - 9), (c + 3, c - 6), 2)
    pg.draw.arc(s, DARK, (c - 6, c + 2, 12, 8), math.pi * 0.15, math.pi * 0.85, 2)
    return s


def make_flag(size=38):
    """Golf hole flagstick on a green mound."""
    s = pg.Surface((size, size + 4), pg.SRCALPHA)
    h = size + 4
    # mound + cup
    pg.draw.ellipse(s, GREEN_BRIGHT, (2, h - 12, size - 4, 11))
    pg.draw.ellipse(s, GREEN_DARK, (size // 2 - 7, h - 10, 14, 5))
    # pole
    px = size // 2
    pg.draw.line(s, CREAM, (px, h - 8), (px, 4), 3)
    # flag
    pg.draw.polygon(s, RED, [(px + 1, 4), (px + 1, 16), (size - 2, 10)])
    pg.draw.polygon(s, (230, 90, 75), [(px + 1, 4), (px + 1, 10), (size - 6, 8)])
    return s


def make_sprinkler(size=38):
    s = pg.Surface((size, size + 2), pg.SRCALPHA)
    h = size + 2
    cx = size // 2
    # base
    pg.draw.rect(s, GRAY_DARK, (cx - 9, h - 10, 18, 8), border_radius=3)
    pg.draw.rect(s, GRAY, (cx - 7, h - 9, 14, 4), border_radius=2)
    # riser
    pg.draw.rect(s, GRAY, (cx - 3, h - 22, 6, 14))
    # head
    pg.draw.circle(s, GRAY_DARK, (cx, h - 24), 6)
    pg.draw.circle(s, BLUE_LIGHT, (cx, h - 24), 3)
    # spray arcs
    for i, ang in enumerate((-70, -35, 0, 35, 70)):
        rad = math.radians(ang - 90)
        for dist in (9, 14, 19):
            x = cx + dist * math.cos(rad)
            y = (h - 26) + dist * math.sin(rad)
            pg.draw.circle(s, (*BLUE_LIGHT, 220 - dist * 6), (int(x), int(y)), 2)
    return s


def make_mower(w=46, h=36):
    """A push lawn mower, the heavy of the fairway."""
    s = pg.Surface((w, h), pg.SRCALPHA)
    # handle
    pg.draw.line(s, GRAY_DARK, (w - 10, h - 12), (w - 3, 3), 3)
    pg.draw.line(s, GRAY_DARK, (w - 8, 3), (w - 1, 5), 3)
    # deck
    deck = pg.Rect(2, h - 18, w - 14, 12)
    pg.draw.rect(s, RED, deck, border_radius=4)
    pg.draw.rect(s, (160, 45, 38), deck, 2, border_radius=4)
    # engine
    pg.draw.rect(s, GRAY, (8, h - 26, 16, 9), border_radius=3)
    pg.draw.rect(s, GRAY_DARK, (12, h - 29, 8, 4), border_radius=2)
    # wheels
    for wx in (8, w - 18):
        pg.draw.circle(s, DARK, (wx, h - 5), 5)
        pg.draw.circle(s, GRAY, (wx, h - 5), 2)
    # grass bits flying
    for gx, gy in ((w - 24, h - 24), (w - 30, h - 28), (w - 20, h - 30)):
        pg.draw.line(s, GREEN_BRIGHT, (gx, gy), (gx + 2, gy - 4), 2)
    return s


def make_cart(w=66, h=42, roof=YELLOW):
    """Golf cart — bonus saucer and (scaled up) the hole 9 boss."""
    s = pg.Surface((w, h), pg.SRCALPHA)
    # body
    pg.draw.rect(s, WHITE, (4, h - 22, w - 8, 13), border_radius=5)
    pg.draw.rect(s, GREEN, (4, h - 13, w - 8, 4), border_radius=2)
    # seat + dash
    pg.draw.rect(s, GREEN_DARK, (w // 2 - 4, h - 30, 10, 10), border_radius=2)
    pg.draw.rect(s, GRAY_DARK, (10, h - 27, 5, 7), border_radius=1)
    # roof + posts
    pg.draw.rect(s, roof, (2, 2, w - 4, 7), border_radius=3)
    pg.draw.line(s, GRAY_DARK, (8, 8), (10, h - 22), 3)
    pg.draw.line(s, GRAY_DARK, (w - 8, 8), (w - 10, h - 22), 3)
    # wheels
    for wx in (14, w - 14):
        pg.draw.circle(s, DARK, (wx, h - 7), 7)
        pg.draw.circle(s, GRAY, (wx, h - 7), 3)
    return s


def make_mega_mower(w=190, h=110):
    """Hole 18 boss: a riding greens mower with attitude."""
    s = pg.Surface((w, h), pg.SRCALPHA)
    # rear roller housing
    pg.draw.rect(s, GRAY_DARK, (6, h - 44, 40, 26), border_radius=6)
    # main body
    pg.draw.rect(s, RED, (34, h - 56, w - 70, 36), border_radius=10)
    pg.draw.rect(s, (150, 42, 36), (34, h - 56, w - 70, 36), 3, border_radius=10)
    # hood
    pg.draw.rect(s, (170, 50, 42), (w - 52, h - 50, 44, 30), border_radius=8)
    pg.draw.rect(s, YELLOW, (w - 16, h - 44, 8, 8), border_radius=2)  # headlight
    # seat & roll bar
    pg.draw.rect(s, DARK, (44, h - 78, 22, 24), border_radius=5)
    pg.draw.line(s, GRAY_DARK, (40, h - 80), (40, h - 52), 5)
    pg.draw.line(s, GRAY_DARK, (40, h - 80), (76, h - 80), 5)
    pg.draw.line(s, GRAY_DARK, (76, h - 80), (76, h - 56), 5)
    # steering wheel
    pg.draw.circle(s, DARK, (92, h - 66), 9, 3)
    pg.draw.line(s, GRAY_DARK, (92, h - 66), (98, h - 52), 3)
    # cutting reel up front
    pg.draw.rect(s, GRAY, (w - 60, h - 22, 56, 14), border_radius=4)
    for i in range(5):
        x = w - 56 + i * 11
        pg.draw.line(s, GRAY_DARK, (x, h - 20), (x + 6, h - 10), 2)
    # wheels
    pg.draw.circle(s, DARK, (52, h - 16), 15)
    pg.draw.circle(s, GRAY, (52, h - 16), 7)
    pg.draw.circle(s, YELLOW, (52, h - 16), 3)
    pg.draw.circle(s, DARK, (w - 78, h - 14), 12)
    pg.draw.circle(s, GRAY, (w - 78, h - 14), 5)
    # angry eyes on the hood
    pg.draw.circle(s, WHITE, (w - 40, h - 42), 6)
    pg.draw.circle(s, DARK, (w - 38, h - 42), 3)
    pg.draw.line(s, DARK, (w - 48, h - 50), (w - 32, h - 46), 3)
    # flying clippings
    for gx, gy in ((w - 30, h - 4), (w - 14, h - 8), (w - 44, h - 2)):
        pg.draw.line(s, GREEN_BRIGHT, (gx, gy), (gx + 4, gy - 7), 2)
    return s


def make_droplet():
    """Enemy projectile: a fat water droplet."""
    s = pg.Surface((10, 16), pg.SRCALPHA)
    pg.draw.polygon(s, BLUE_LIGHT, [(5, 0), (9, 9), (1, 9)])
    pg.draw.circle(s, BLUE_LIGHT, (5, 10), 5)
    pg.draw.circle(s, WHITE, (4, 9), 2)
    return s


def make_mini_ball():
    """Boss projectile: a small golf ball."""
    s = pg.Surface((14, 14), pg.SRCALPHA)
    pg.draw.circle(s, WHITE, (7, 7), 6)
    pg.draw.circle(s, (200, 206, 202), (9, 9), 6, 2)
    pg.draw.circle(s, (196, 202, 198), (5, 5), 1)
    pg.draw.circle(s, (196, 202, 198), (9, 6), 1)
    return s


def make_polyon_logo(scale=1.0):
    """Recreation of the POLYON(R) Controlled-Release Fertilizer banner."""
    w, h = int(360 * scale), int(120 * scale)
    s = pg.Surface((w, h), pg.SRCALPHA)
    banner = pg.Rect(0, int(h * 0.12), w, int(h * 0.6))
    pg.draw.rect(s, GREEN_DARK, banner.move(0, 3), border_radius=int(14 * scale))
    pg.draw.rect(s, GREEN, banner, border_radius=int(14 * scale))
    pg.draw.rect(s, GREEN_BRIGHT, banner.inflate(-8, -8), 2,
                 border_radius=int(12 * scale))
    # leafy sweep across the top of the banner
    for i in range(7):
        x = int(w * (0.08 + i * 0.14))
        r = int(5 * scale) + (i % 3)
        pg.draw.circle(s, GREEN_BRIGHT, (x, banner.top + 4), r)
    f = get_font(int(52 * scale), bold=True, italic=True)
    word = f.render("POLYON", True, WHITE)
    rect = word.get_rect(center=(w // 2, banner.centery))
    s.blit(word, rect)
    fr = get_font(int(14 * scale), bold=True)
    reg = fr.render("(R)", True, WHITE)
    s.blit(reg, (rect.right + 2, rect.top + 2))
    f2 = get_font(int(16 * scale), bold=True)
    sub = f2.render("Controlled-Release Fertilizer", True, CREAM)
    s.blit(sub, sub.get_rect(midtop=(w // 2, banner.bottom + int(6 * scale))))
    return s


def make_harrells_logo(scale=1.0):
    """Recreation of the Harrell's 'Growing a Better World' lockup."""
    w, h = int(420 * scale), int(110 * scale)
    s = pg.Surface((w, h), pg.SRCALPHA)
    # The double-bar 'H' emblem with the green dot
    bx, by = int(10 * scale), int(8 * scale)
    bw, bh = int(20 * scale), int(70 * scale)
    skew = int(12 * scale)
    gap = int(16 * scale)
    for off in (0, bw + gap):
        pts = [(bx + off + skew, by), (bx + off + bw + skew, by),
               (bx + off + bw - skew, by + bh), (bx + off - skew, by + bh)]
        pg.draw.polygon(s, BLUE, pts)
    midy = by + bh // 2
    pg.draw.rect(s, BLUE, (bx - skew // 2, midy - int(8 * scale),
                           bw * 2 + gap + skew, int(16 * scale)))
    pg.draw.circle(s, WHITE, (bx + bw + gap // 2 + int(2 * scale), midy),
                   int(11 * scale))
    pg.draw.circle(s, GREEN, (bx + bw + gap // 2 + int(2 * scale), midy),
                   int(8 * scale))
    # Wordmark
    tx = bx + bw * 2 + gap + int(26 * scale)
    f = get_font(int(46 * scale), bold=True)
    word = f.render("Harrell's", True, GREEN)
    s.blit(word, (tx, by - int(2 * scale)))
    f2 = get_font(int(20 * scale), bold=False, italic=True)
    tag = f2.render("Growing a Better World", True, BLUE)
    s.blit(tag, (tx + int(4 * scale), by + int(48 * scale)))
    return s


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

def make_background():
    """Night-time fairway: gradient sky-to-turf with mowing stripes."""
    s = pg.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        col = [int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)]
        pg.draw.line(s, col, (0, y), (WIDTH, y))
    # diagonal mowing stripes
    stripe = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
    for i in range(-8, 16):
        x = i * 130
        pg.draw.polygon(stripe, (255, 255, 255, 7),
                        [(x, HEIGHT), (x + 65, HEIGHT), (x + 265, 0), (x + 200, 0)])
    s.blit(stripe, (0, 0))
    # scattered prills resting on the turf
    rnd = random.Random(7)
    for _ in range(40):
        x, y = rnd.randint(0, WIDTH), rnd.randint(HEIGHT - 60, HEIGHT - 6)
        pg.draw.circle(s, (30, 90, 52), (x, y), rnd.randint(1, 3))
    return s


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

ENEMY_STATS = {
    # type: (hp, points)
    "ball": (1, 10),
    "flag": (2, 25),
    "sprinkler": (2, 30),
    "mower": (3, 40),
}


class Enemy:
    def __init__(self, kind, col, row):
        self.kind = kind
        self.col = col
        self.row = row
        hp, pts = ENEMY_STATS[kind]
        self.hp = hp
        self.points = pts
        self.flash = 0.0
        self.alive = True


class Swarm:
    """Classic invaders grid that drifts, reverses and descends."""

    SPACING_X = 72
    SPACING_Y = 58

    def __init__(self, hole, sprites):
        cfg = hole_config(hole)
        self.rows = cfg["rows"]
        self.cols = cfg["cols"]
        self.base_speed = cfg["speed"]
        self.descend = cfg["descend"]
        self.fire_interval = cfg["fire"]
        self.sprites = sprites
        self.enemies = []
        for r, kind in enumerate(cfg["row_types"]):
            for c in range(self.cols):
                self.enemies.append(Enemy(kind, c, r))
        self.total = len(self.enemies)
        grid_w = (self.cols - 1) * self.SPACING_X
        self.x = (WIDTH - grid_w) / 2
        self.y = HUD_H + 70.0
        self.dir = 1
        self.fire_timer = self.fire_interval * random.uniform(0.6, 1.2)
        self.wiggle = 0.0

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    @property
    def count(self):
        return sum(1 for e in self.enemies if e.alive)

    def speed(self):
        thinning = 1.0 - self.count / max(1, self.total)
        return self.base_speed * (1.0 + 2.4 * thinning)

    def enemy_pos(self, e):
        return (self.x + e.col * self.SPACING_X,
                self.y + e.row * self.SPACING_Y + 4 * math.sin(
                    self.wiggle + e.col * 0.6))

    def enemy_rect(self, e):
        img = self.sprites[e.kind]
        x, y = self.enemy_pos(e)
        return img.get_rect(center=(x, y))

    def update(self, dt):
        self.wiggle += dt * 2.2
        alive = self.alive_enemies()
        if not alive:
            return
        self.x += self.dir * self.speed() * dt
        min_x = min(self.enemy_pos(e)[0] for e in alive)
        max_x = max(self.enemy_pos(e)[0] for e in alive)
        if max_x > WIDTH - 46 and self.dir > 0:
            self.dir = -1
            self.y += self.descend
        elif min_x < 46 and self.dir < 0:
            self.dir = 1
            self.y += self.descend
        for e in alive:
            e.flash = max(0.0, e.flash - dt)

    def lowest_y(self):
        alive = self.alive_enemies()
        if not alive:
            return 0
        return max(self.enemy_rect(e).bottom for e in alive)

    def pick_shooter(self):
        """Bottom-most enemy of a random occupied column; sprinklers eager."""
        cols = {}
        for e in self.alive_enemies():
            cur = cols.get(e.col)
            if cur is None or e.row > cur.row:
                cols[e.col] = e
        if not cols:
            return None
        pool = []
        for e in cols.values():
            pool.extend([e] * (3 if e.kind == "sprinkler" else 1))
        return random.choice(pool)

    def draw(self, surf):
        for e in self.alive_enemies():
            img = self.sprites[e.kind]
            rect = self.enemy_rect(e)
            surf.blit(img, rect)
            if e.flash > 0:
                glow = pg.Surface(rect.size, pg.SRCALPHA)
                glow.fill((255, 255, 255, 110))
                surf.blit(glow, rect)


def hole_config(hole):
    """Wave layout for each of the 16 regular holes (9 and 18 are bosses)."""
    h = hole
    rows = 3 if h <= 2 else (4 if h <= 7 else 5)
    cols = 8 + (1 if h >= 6 else 0) + (1 if h >= 12 else 0)
    layouts = {
        1: ["ball", "ball", "ball"],
        2: ["flag", "ball", "ball"],
        3: ["flag", "flag", "ball", "ball"],
        4: ["sprinkler", "flag", "ball", "ball"],
        5: ["sprinkler", "flag", "flag", "ball"],
        6: ["sprinkler", "flag", "ball", "mower"],
        7: ["sprinkler", "sprinkler", "flag", "mower"],
        8: ["sprinkler", "flag", "ball", "ball", "mower"],
        10: ["sprinkler", "flag", "flag", "ball", "mower"],
        11: ["sprinkler", "sprinkler", "flag", "ball", "mower"],
        12: ["sprinkler", "flag", "flag", "mower", "mower"],
        13: ["sprinkler", "sprinkler", "flag", "flag", "mower"],
        14: ["sprinkler", "sprinkler", "flag", "mower", "mower"],
        15: ["sprinkler", "sprinkler", "sprinkler", "flag", "mower"],
        16: ["sprinkler", "sprinkler", "flag", "mower", "mower"],
        17: ["sprinkler", "sprinkler", "mower", "mower", "mower"],
    }
    return {
        "rows": rows,
        "cols": cols,
        "row_types": layouts.get(h, ["ball"] * rows),
        "speed": 26 + h * 4,
        "descend": 14 + (h // 3) * 2,
        "fire": max(0.42, 1.65 - h * 0.07),
    }


class Boss:
    def __init__(self, kind, sprites, hole):
        self.kind = kind  # "cart" or "mower"
        self.image = sprites["boss_cart" if kind == "cart" else "boss_mower"]
        self.max_hp = 70 if kind == "cart" else 110
        self.hp = self.max_hp
        self.points = 1500 if kind == "cart" else 3000
        self.x = WIDTH / 2
        self.y = HUD_H + 110
        self.phase = 0.0
        self.fire_timer = 1.2
        self.burst = 0
        self.flash = 0.0
        self.name = ("THE MARSHAL'S CART" if kind == "cart"
                     else "MEGA MOWER 9000")

    @property
    def rect(self):
        return self.image.get_rect(center=(int(self.x), int(self.y)))

    def enraged(self):
        return self.hp < self.max_hp * 0.45

    def update(self, dt, player_x, shots, sprites, snd):
        self.flash = max(0.0, self.flash - dt)
        speed = 1.0 + (0.9 if self.enraged() else 0.0)
        self.phase += dt * speed
        span = WIDTH / 2 - 140
        self.x = WIDTH / 2 + span * math.sin(self.phase * 0.7)
        self.y = HUD_H + 110 + 26 * math.sin(self.phase * 1.7)
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self._fire(player_x, shots, sprites)
            snd.play("hit")
            base = 1.25 if self.kind == "cart" else 1.05
            if self.enraged():
                base *= 0.62
            self.fire_timer = base * random.uniform(0.8, 1.2)

    def _fire(self, player_x, shots, sprites):
        cx, cy = self.x, self.rect.bottom - 6
        if self.kind == "cart":
            # 3-way golf ball spread + occasional aimed shot
            for vx in (-110, 0, 110):
                shots.append(Shot(sprites["mini_ball"], cx, cy, vx, 240))
            if self.enraged():
                dx = player_x - cx
                shots.append(Shot(sprites["mini_ball"], cx, cy,
                                  max(-200, min(200, dx)), 290))
        else:
            # mower spews fans of clippings/droplets
            n = 5 if self.enraged() else 4
            for i in range(n):
                ang = -0.62 + 1.24 * i / (n - 1)
                shots.append(Shot(sprites["droplet"], cx, cy,
                                  280 * math.sin(ang), 280 * math.cos(ang)))
            if self.enraged():
                dx = player_x - cx
                shots.append(Shot(sprites["mini_ball"], cx, cy,
                                  max(-230, min(230, dx)), 320))

    def draw(self, surf):
        rect = self.rect
        surf.blit(self.image, rect)
        if self.flash > 0:
            glow = pg.Surface(rect.size, pg.SRCALPHA)
            glow.fill((255, 255, 255, 90))
            surf.blit(glow, rect)
        # HP bar
        bar = pg.Rect(WIDTH // 2 - 180, HUD_H + 10, 360, 14)
        pg.draw.rect(surf, DARK, bar, border_radius=7)
        fill = bar.inflate(-4, -4)
        fill.width = max(0, int(fill.width * self.hp / self.max_hp))
        pg.draw.rect(surf, RED if self.enraged() else GREEN_BRIGHT, fill,
                     border_radius=5)
        text(surf, self.name, 14, WHITE, midtop=(WIDTH // 2, HUD_H + 26))


class Shot:
    """A projectile (player prill or enemy shot)."""

    def __init__(self, image, x, y, vx, vy):
        self.image = image
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    @property
    def rect(self):
        return self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def offscreen(self):
        return (self.y < HUD_H - 20 or self.y > HEIGHT + 20 or
                self.x < -20 or self.x > WIDTH + 20)


class Particle:
    def __init__(self, x, y, color, speed=160, life=0.6, size=3):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(0.3, 1.0) * speed
        self.x, self.y = x, y
        self.vx = spd * math.cos(ang)
        self.vy = spd * math.sin(ang)
        self.life = self.max_life = random.uniform(0.5, 1.0) * life
        self.color = color
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 240 * dt
        self.life -= dt

    def draw(self, surf):
        if self.life > 0:
            r = max(1, int(self.size * self.life / self.max_life))
            pg.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


class BonusCart:
    """Crosses the top of the screen for bonus points."""

    def __init__(self, sprites):
        self.image = sprites["cart"]
        self.dir = random.choice((-1, 1))
        self.x = -50 if self.dir > 0 else WIDTH + 50
        self.y = HUD_H + 34
        self.points = random.choice((100, 150, 200, 300))
        self.alive = True

    @property
    def rect(self):
        img = self.image if self.dir > 0 else pg.transform.flip(
            self.image, True, False)
        return img.get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt):
        self.x += self.dir * 170 * dt
        if self.x < -70 or self.x > WIDTH + 70:
            self.alive = False

    def draw(self, surf):
        img = self.image if self.dir > 0 else pg.transform.flip(
            self.image, True, False)
        surf.blit(img, self.rect)


# ---------------------------------------------------------------------------
# The Game
# ---------------------------------------------------------------------------

class Game:
    def __init__(self, headless=False):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pg.init()
        flags = 0
        self.screen = pg.display.set_mode((WIDTH, HEIGHT), flags)
        pg.display.set_caption("POLYON: The Game")
        self.headless = headless
        self.clock = pg.time.Clock()
        self.snd = Sounds()

        self.sprites = {
            "player": make_player_bag(),
            "bb": make_bb(5),
            "ball": make_golf_ball(),
            "flag": make_flag(),
            "sprinkler": make_sprinkler(),
            "mower": make_mower(),
            "cart": make_cart(),
            "boss_cart": pg.transform.scale(make_cart(76, 48, roof=GREEN), (152, 96)),
            "boss_mower": make_mega_mower(),
            "droplet": make_droplet(),
            "mini_ball": make_mini_ball(),
        }
        pg.display.set_icon(self.sprites["bb"])
        self.background = make_background()
        self.logo_polyon = make_polyon_logo(1.0)
        self.logo_harrells = make_harrells_logo(0.8)
        self.life_icon = pg.transform.smoothscale(self.sprites["player"], (20, 24))

        self.highscores = load_scores()
        self.title_prills = [
            [random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
             random.uniform(20, 80), random.randint(2, 4)]
            for _ in range(60)
        ]
        self.state = "title"
        self.state_t = 0.0
        self.reset_run()

    # -- run / state management ---------------------------------------------

    def reset_run(self):
        self.score = 0
        self.lives = 3
        self.hole = 1
        self.next_life_at = 10000
        self.player_x = WIDTH / 2
        self.player_cooldown = 0.0
        self.invuln = 0.0
        self.bullets = []
        self.enemy_shots = []
        self.particles = []
        self.swarm = None
        self.boss = None
        self.bonus = None
        self.bonus_timer = random.uniform(14, 22)
        self.popups = []  # (text, x, y, life)

    def start_hole(self):
        self.bullets.clear()
        self.enemy_shots.clear()
        self.bonus = None
        self.bonus_timer = random.uniform(14, 22)
        if self.hole in (9, 18):
            self.boss = Boss("cart" if self.hole == 9 else "mower",
                             self.sprites, self.hole)
            self.swarm = None
        else:
            self.swarm = Swarm(self.hole, self.sprites)
            self.boss = None

    def set_state(self, state):
        self.state = state
        self.state_t = 0.0

    def add_score(self, pts):
        self.score += pts
        if self.score >= self.next_life_at and self.lives < 5:
            self.lives += 1
            self.next_life_at += 10000
            self.snd.play("life")
            self.popups.append(["EXTRA BAG!", WIDTH / 2, HEIGHT / 2, 1.6])

    def is_high_score(self):
        return (len(self.highscores) < 10 or
                self.score > self.highscores[-1]["score"]) and self.score > 0

    # -- main loop ------------------------------------------------------------

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 20)
            events = pg.event.get()
            for ev in events:
                if ev.type == pg.QUIT:
                    running = False
            if not self.step(dt, events):
                running = False
            pg.display.flip()
        pg.quit()

    def step(self, dt, events):
        """Advance one frame. Returns False to quit."""
        self.state_t += dt
        keys = pg.key.get_pressed()
        handler = getattr(self, "state_" + self.state)
        if handler(dt, events, keys) is False:
            return False
        return True

    # -- title / menus ----------------------------------------------------------

    def state_title(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN:
                if ev.key in (pg.K_RETURN, pg.K_SPACE, pg.K_KP_ENTER):
                    self.reset_run()
                    self.set_state("intro")
                    self.start_hole()
                elif ev.key == pg.K_h:
                    self.set_state("scores")
                elif ev.key == pg.K_ESCAPE:
                    return False
        self._update_title_prills(dt)
        self.draw_title()

    def state_scores(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN:
                self.set_state("title")
        self._update_title_prills(dt)
        self.draw_scores()

    def _update_title_prills(self, dt):
        for p in self.title_prills:
            p[1] += p[2] * dt
            if p[1] > HEIGHT + 5:
                p[0] = random.uniform(0, WIDTH)
                p[1] = -5

    # -- gameplay ----------------------------------------------------------------

    def state_intro(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN and self.state_t > 0.4:
                self.set_state("play")
        if self.state_t > 2.6:
            self.set_state("play")
        self.draw_play(dim=True)
        self.draw_intro_card()

    def state_play(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN and ev.key in (pg.K_p, pg.K_ESCAPE):
                self.set_state("pause")
                return
        self.update_player(dt, keys)
        self.update_world(dt)
        self.handle_collisions()
        if self.state != "play":  # died during collision handling
            self.draw_play(hide_player=True)
            return
        # win / lose checks
        cleared = ((self.swarm and self.swarm.count == 0) or
                   (self.boss and self.boss.hp <= 0))
        if cleared:
            bonus = 100 + 25 * self.hole
            if self.boss:
                bonus += self.boss.points
            self.add_score(bonus)
            self.popups.append([f"HOLE {self.hole} CLEAR  +{bonus}",
                                WIDTH / 2, HEIGHT / 2 - 40, 2.0])
            self.snd.play("clear")
            self.set_state("clear")
        elif self.swarm and self.swarm.lowest_y() >= INVASION_Y:
            self.kill_player(invasion=True)
        self.draw_play()

    def state_clear(self, dt, events, keys):
        self.update_world(dt, freeze_enemies=True)
        if self.state_t > 2.0:
            if self.hole >= TOTAL_HOLES:
                self.add_score(self.lives * 1000)
                self.set_state("victory")
            else:
                self.hole += 1
                self.set_state("intro")
                self.start_hole()
        self.draw_play()

    def state_dead(self, dt, events, keys):
        self.update_world(dt, freeze_enemies=True)
        if self.state_t > 1.4:
            if self.lives <= 0:
                self.set_state("entry" if self.is_high_score() else "gameover")
            else:
                self.invuln = 2.2
                self.player_x = WIDTH / 2
                self.set_state("play")
        self.draw_play(hide_player=True)

    def state_pause(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN:
                if ev.key in (pg.K_p, pg.K_ESCAPE, pg.K_RETURN, pg.K_SPACE):
                    self.set_state("play")
                elif ev.key == pg.K_q:
                    self.set_state("title")
        self.draw_play(dim=True)
        text(self.screen, "PAUSED", 54, WHITE, center=(WIDTH / 2, HEIGHT / 2 - 20),
             shadow=DARK)
        text(self.screen, "P / ESC to resume   -   Q to quit to title", 20,
             CREAM, center=(WIDTH / 2, HEIGHT / 2 + 30))

    def state_victory(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN and self.state_t > 1.0:
                self.set_state("entry" if self.is_high_score() else "title")
        self._update_title_prills(dt)
        self.draw_victory()

    def state_gameover(self, dt, events, keys):
        for ev in events:
            if ev.type == pg.KEYDOWN and self.state_t > 0.8:
                self.set_state("title")
        self.draw_play(dim=True, hide_player=True)
        text(self.screen, "GAME OVER", 60, RED, center=(WIDTH / 2, HEIGHT / 2 - 40),
             shadow=DARK)
        text(self.screen, f"FINAL SCORE  {self.score}", 28, WHITE,
             center=(WIDTH / 2, HEIGHT / 2 + 16))
        text(self.screen, "The course wins this round...", 18, CREAM,
             center=(WIDTH / 2, HEIGHT / 2 + 52), italic=True)
        if self.state_t > 0.8:
            text(self.screen, "PRESS ANY KEY", 20, YELLOW,
                 center=(WIDTH / 2, HEIGHT / 2 + 100))

    def state_entry(self, dt, events, keys):
        if not hasattr(self, "entry_name") or self.entry_name is None:
            self.entry_name = ""
        for ev in events:
            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_RETURN and self.entry_name:
                    self.highscores.append({
                        "name": self.entry_name, "score": self.score,
                        "hole": self.hole})
                    self.highscores.sort(key=lambda s: -s["score"])
                    self.highscores = self.highscores[:10]
                    save_scores(self.highscores)
                    self.entry_name = None
                    self.set_state("scores")
                    return
                elif ev.key == pg.K_BACKSPACE:
                    self.entry_name = self.entry_name[:-1]
                elif ev.unicode and ev.unicode.isalnum() and len(self.entry_name) < 6:
                    self.entry_name += ev.unicode.upper()
        self._update_title_prills(dt)
        self.draw_entry()

    # -- updates ---------------------------------------------------------------

    def update_player(self, dt, keys):
        speed = 330
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.player_x -= speed * dt
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.player_x += speed * dt
        self.player_x = max(34, min(WIDTH - 34, self.player_x))
        self.player_cooldown = max(0.0, self.player_cooldown - dt)
        self.invuln = max(0.0, self.invuln - dt)
        if (keys[pg.K_SPACE] and self.player_cooldown == 0
                and len(self.bullets) < 3):
            self.bullets.append(Shot(self.sprites["bb"], self.player_x,
                                     PLAYER_Y - 36, 0, -540))
            self.player_cooldown = 0.3
            self.snd.play("shoot")

    def update_world(self, dt, freeze_enemies=False):
        if not freeze_enemies:
            if self.swarm:
                self.swarm.update(dt)
                self.swarm.fire_timer -= dt
                if self.swarm.fire_timer <= 0:
                    shooter = self.swarm.pick_shooter()
                    if shooter:
                        rect = self.swarm.enemy_rect(shooter)
                        spd = 190 + self.hole * 7
                        self.enemy_shots.append(Shot(
                            self.sprites["droplet"], rect.centerx, rect.bottom,
                            0, spd))
                    self.swarm.fire_timer = (self.swarm.fire_interval *
                                             random.uniform(0.6, 1.3))
            if self.boss:
                self.boss.update(dt, self.player_x, self.enemy_shots,
                                 self.sprites, self.snd)
            # bonus golf cart (regular holes only)
            if not self.boss:
                self.bonus_timer -= dt
                if self.bonus_timer <= 0 and self.bonus is None:
                    self.bonus = BonusCart(self.sprites)
                    self.bonus_timer = random.uniform(16, 26)
        if self.bonus:
            self.bonus.update(dt)
            if not self.bonus.alive:
                self.bonus = None
        for shot in self.bullets[:]:
            shot.update(dt)
            if shot.offscreen():
                self.bullets.remove(shot)
        for shot in self.enemy_shots[:]:
            shot.update(dt)
            if shot.offscreen():
                self.enemy_shots.remove(shot)
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)
        for pop in self.popups[:]:
            pop[3] -= dt
            pop[2] -= 24 * dt
            if pop[3] <= 0:
                self.popups.remove(pop)

    def explode(self, x, y, color, n=14, speed=170):
        for _ in range(n):
            self.particles.append(Particle(x, y, color, speed))

    def handle_collisions(self):
        # player prills vs enemies / boss / bonus cart
        for shot in self.bullets[:]:
            rect = shot.rect
            hit = False
            if self.swarm:
                for e in self.swarm.alive_enemies():
                    er = self.swarm.enemy_rect(e)
                    if er.colliderect(rect):
                        e.hp -= 1
                        e.flash = 0.1
                        hit = True
                        if e.hp <= 0:
                            e.alive = False
                            self.add_score(e.points)
                            col = {"ball": WHITE, "flag": RED,
                                   "sprinkler": BLUE_LIGHT,
                                   "mower": RED}[e.kind]
                            self.explode(er.centerx, er.centery, col)
                            self.explode(er.centerx, er.centery, BB_GREEN, 6)
                            self.snd.play("boom")
                        else:
                            self.snd.play("hit")
                        break
            if not hit and self.boss:
                if self.boss.rect.colliderect(rect):
                    self.boss.hp -= 1
                    self.boss.flash = 0.08
                    hit = True
                    self.snd.play("boss_hit")
                    if self.boss.hp <= 0:
                        br = self.boss.rect
                        self.explode(br.centerx, br.centery, RED, 40, 260)
                        self.explode(br.centerx, br.centery, YELLOW, 30, 220)
                        self.snd.play("boom")
            if not hit and self.bonus:
                if self.bonus.rect.colliderect(rect):
                    self.add_score(self.bonus.points)
                    self.popups.append([f"+{self.bonus.points}",
                                        self.bonus.x, self.bonus.y, 1.2])
                    self.explode(self.bonus.x, self.bonus.y, YELLOW, 18)
                    self.snd.play("bonus")
                    self.bonus = None
                    hit = True
            if hit:
                self.bullets.remove(shot)
        # enemy shots vs player
        if self.invuln <= 0:
            prect = self.sprites["player"].get_rect(
                center=(int(self.player_x), PLAYER_Y)).inflate(-14, -10)
            for shot in self.enemy_shots[:]:
                if prect.colliderect(shot.rect):
                    self.enemy_shots.remove(shot)
                    self.kill_player()
                    return
            if self.swarm:
                for e in self.swarm.alive_enemies():
                    if self.swarm.enemy_rect(e).colliderect(prect):
                        self.kill_player(invasion=True)
                        return

    def kill_player(self, invasion=False):
        if self.state != "play":
            return
        self.lives -= 1
        self.explode(self.player_x, PLAYER_Y, WHITE, 24, 240)
        self.explode(self.player_x, PLAYER_Y, BB_GREEN, 24, 220)
        self.snd.play("player_boom")
        if invasion and self.swarm:
            # push the swarm back up so the run can continue
            self.swarm.y = max(HUD_H + 70.0, self.swarm.y - 170)
        self.set_state("dead")

    # -- drawing ----------------------------------------------------------------

    def draw_prill_rain(self):
        for x, y, _, r in self.title_prills:
            pg.draw.circle(self.screen, GREEN_DARK, (int(x), int(y) + 1), r)
            pg.draw.circle(self.screen, BB_GREEN, (int(x), int(y)), r - 1)

    def draw_title(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_prill_rain()
        cx = WIDTH // 2
        self.screen.blit(self.logo_harrells,
                         self.logo_harrells.get_rect(midtop=(cx, 26)))
        # big game title
        wob = math.sin(self.state_t * 2.0) * 4
        text(self.screen, "POLYON", 96, GREEN_BRIGHT,
             center=(cx, 196 + wob), italic=True, shadow=DARK)
        text(self.screen, "T H E   G A M E", 30, WHITE,
             center=(cx, 258 + wob), shadow=DARK)
        self.screen.blit(self.logo_polyon,
                         self.logo_polyon.get_rect(midtop=(cx, 296)))
        # marquee enemies
        for i, kind in enumerate(["ball", "flag", "sprinkler", "mower"]):
            img = self.sprites[kind]
            x = cx - 210 + i * 140
            self.screen.blit(img, img.get_rect(center=(x, 482)))
            pts = ENEMY_STATS[kind][1]
            text(self.screen, f"{pts} PTS", 15, CREAM, center=(x, 514))
        if int(self.state_t * 2) % 2 == 0:
            text(self.screen, "PRESS ENTER TO TEE OFF", 28, YELLOW,
                 center=(cx, 572), shadow=DARK)
        text(self.screen, "ARROWS / A-D move    SPACE fire    P pause", 18,
             CREAM, center=(cx, 618))
        text(self.screen, "H - HIGH SCORES", 18, BLUE_LIGHT, center=(cx, 648))
        text(self.screen, "18 holes stand between you and a perfect lawn.",
             16, GREEN_BRIGHT, center=(cx, 688), italic=True)

    def draw_scores(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_prill_rain()
        cx = WIDTH // 2
        text(self.screen, "CLUBHOUSE LEADERBOARD", 44, GREEN_BRIGHT,
             center=(cx, 70), shadow=DARK)
        text(self.screen, "RANK      NAME        SCORE      HOLE", 22, CREAM,
             center=(cx, 140))
        for i, s in enumerate(self.highscores[:10]):
            col = YELLOW if i == 0 else WHITE
            row = f"{i + 1:>2}.       {s['name']:<8}  {s['score']:>7}       {s.get('hole', 1):>2}"
            text(self.screen, row, 22, col, center=(cx, 180 + i * 36))
        text(self.screen, "PRESS ANY KEY", 20, YELLOW, center=(cx, 600))
        self.screen.blit(self.logo_harrells, self.logo_harrells.get_rect(
            midtop=(cx, 630)))

    def draw_entry(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_prill_rain()
        cx = WIDTH // 2
        text(self.screen, "NEW CLUBHOUSE RECORD!", 44, YELLOW,
             center=(cx, 150), shadow=DARK)
        text(self.screen, f"SCORE  {self.score}", 30, WHITE, center=(cx, 220))
        text(self.screen, "ENTER YOUR INITIALS", 22, CREAM, center=(cx, 300))
        name = (self.entry_name or "") + ("_" if int(self.state_t * 2) % 2 == 0
                                          else " ")
        text(self.screen, name, 52, GREEN_BRIGHT, center=(cx, 360))
        text(self.screen, "ENTER to confirm", 18, CREAM, center=(cx, 430))

    def draw_victory(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_prill_rain()
        cx = WIDTH // 2
        text(self.screen, "COURSE COMPLETE!", 60, GREEN_BRIGHT,
             center=(cx, 140), shadow=DARK)
        text(self.screen, "All 18 holes defended. The turf has never", 22,
             WHITE, center=(cx, 220))
        text(self.screen, "looked greener. POLYON delivers - season-long.", 22,
             WHITE, center=(cx, 252))
        text(self.screen, f"FINAL SCORE  {self.score}", 40, YELLOW,
             center=(cx, 330), shadow=DARK)
        text(self.screen, f"(includes {self.lives} spare bag bonus x 1000)",
             16, CREAM, center=(cx, 372), italic=True)
        img = self.sprites["player"]
        self.screen.blit(img, img.get_rect(center=(cx, 450)))
        self.screen.blit(self.logo_polyon, self.logo_polyon.get_rect(
            midtop=(cx, 500)))
        if self.state_t > 1.0:
            text(self.screen, "PRESS ANY KEY", 20, YELLOW, center=(cx, 650))

    def draw_intro_card(self):
        cx = WIDTH // 2
        name = HOLE_NAMES[self.hole - 1]
        par = 3 + (self.hole % 3)
        card = pg.Rect(0, 0, 560, 170)
        card.center = (cx, HEIGHT // 2 - 20)
        pg.draw.rect(self.screen, DARK, card.move(0, 4), border_radius=14)
        pg.draw.rect(self.screen, GREEN_DARK, card, border_radius=14)
        pg.draw.rect(self.screen, GREEN_BRIGHT, card, 3, border_radius=14)
        text(self.screen, f"HOLE {self.hole} of {TOTAL_HOLES}", 36, WHITE,
             center=(cx, card.top + 44))
        text(self.screen, f'"{name}"', 26, YELLOW,
             center=(cx, card.top + 92), italic=True)
        text(self.screen, f"PAR {par}", 20, CREAM, center=(cx, card.top + 132))

    def draw_hud(self):
        pg.draw.rect(self.screen, DARK, (0, 0, WIDTH, HUD_H))
        pg.draw.line(self.screen, GREEN, (0, HUD_H), (WIDTH, HUD_H), 2)
        text(self.screen, f"SCORE  {self.score}", 22, WHITE, topleft=(16, 16))
        hi = max([s["score"] for s in self.highscores] + [self.score])
        text(self.screen, f"HI  {hi}", 22, YELLOW, center=(WIDTH // 2 - 60, 27))
        text(self.screen, f"HOLE  {self.hole}/{TOTAL_HOLES}", 22, GREEN_BRIGHT,
             center=(WIDTH // 2 + 110, 27))
        for i in range(self.lives):
            self.screen.blit(self.life_icon, (WIDTH - 36 - i * 26, 15))

    def draw_play(self, dim=False, hide_player=False):
        self.screen.blit(self.background, (0, 0))
        # invasion line
        for x in range(0, WIDTH, 24):
            pg.draw.line(self.screen, (40, 90, 60), (x, INVASION_Y + 40),
                         (x + 10, INVASION_Y + 40), 1)
        if self.swarm:
            self.swarm.draw(self.screen)
        if self.boss:
            self.boss.draw(self.screen)
        if self.bonus:
            self.bonus.draw(self.screen)
        for shot in self.bullets:
            self.screen.blit(shot.image, shot.rect)
        for shot in self.enemy_shots:
            self.screen.blit(shot.image, shot.rect)
        if not hide_player and not (self.invuln > 0 and
                                    int(self.invuln * 10) % 2 == 0):
            img = self.sprites["player"]
            self.screen.blit(img, img.get_rect(center=(int(self.player_x),
                                                       PLAYER_Y)))
        for p in self.particles:
            p.draw(self.screen)
        for msg, x, y, life in self.popups:
            text(self.screen, msg, 24, YELLOW, center=(int(x), int(y)),
                 shadow=DARK)
        self.draw_hud()
        if dim:
            veil = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            veil.fill((6, 20, 12, 160))
            self.screen.blit(veil, (0, 0))


def main():
    headless = "--smoke" in sys.argv
    if headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    game = Game(headless=headless)
    if headless:
        for _ in range(180):
            game.step(1 / 60, [])
        pg.quit()
        print("smoke ok")
        return
    game.run()


if __name__ == "__main__":
    main()
