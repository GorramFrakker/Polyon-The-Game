#!/usr/bin/env python3
"""Pre-process the game's images and sounds into the baked/ directory.

Run at build time (CI) before pygbag packaging. The processed assets let
the web build skip the per-pixel startup work that is painfully slow
under WebAssembly. Desktop runs work with or without baked assets.
"""

import os
import sys
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame as pg  # noqa: E402
import polyon_the_game as g  # noqa: E402


def main():
    pg.init()
    pg.display.set_mode((100, 100))
    g._USE_BAKED = False  # force the loaders to compute from the originals

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "baked")
    os.makedirs(out, exist_ok=True)

    images = {
        "player.png": g.load_player_bag(),
        "bb.png": g.load_bb_bullet(),
        "harrells_380.png": g.load_harrells_logo(380),
        "harrells_260.png": g.load_harrells_logo(260),
        "polyon.png": g.load_polyon_badge(),
        "pu_multi.png": g.load_powerup_token("multi"),
        "pu_power.png": g.load_powerup_token("power"),
        "pu_rapid.png": g.load_powerup_token("rapid"),
    }
    for name, surf in images.items():
        pg.image.save(surf, os.path.join(out, name))
        print("baked", name, surf.get_size())

    for name in g.SOUND_RECIPES:
        data = g.synth_sound_bytes(name)
        path = os.path.join(out, "snd_%s.wav" % name)
        with wave.open(path, "wb") as fh:
            fh.setnchannels(1)
            fh.setsampwidth(2)
            fh.setframerate(g.SOUND_RATE)
            fh.writeframes(data)
        print("baked snd_%s.wav (%d bytes)" % (name, len(data)))

    print("ALL ASSETS BAKED ->", os.path.abspath(out))


if __name__ == "__main__":
    main()
