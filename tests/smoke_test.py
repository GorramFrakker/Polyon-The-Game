#!/usr/bin/env python3
"""Headless smoke test: drives the game through every state and saves
screenshots to tests/shots/ for visual inspection."""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame as pg  # noqa: E402
import polyon_the_game as g  # noqa: E402

SHOTS = os.path.join(os.path.dirname(__file__), "shots")
os.makedirs(SHOTS, exist_ok=True)


def snap(game, name):
    pg.image.save(game.screen, os.path.join(SHOTS, name + ".png"))


def frames(game, n, events=None):
    for _ in range(n):
        assert game.step(1 / 60, events or []) is not False
        events = None


def key_event(key, unicode=""):
    return pg.event.Event(pg.KEYDOWN, key=key, unicode=unicode)


def main():
    game = g.Game(headless=True)

    # Title screen
    frames(game, 30)
    assert game.state == "title"
    snap(game, "01_title")

    # High scores
    frames(game, 2, [key_event(pg.K_h)])
    assert game.state == "scores"
    snap(game, "02_scores")
    frames(game, 2, [key_event(pg.K_SPACE)])
    assert game.state == "title"

    # Start a run -> hole intro
    frames(game, 2, [key_event(pg.K_RETURN)])
    assert game.state == "intro"
    frames(game, 20)
    snap(game, "03_intro")

    # Play hole 1
    frames(game, 200)
    assert game.state == "play"
    snap(game, "04_play_hole1")
    assert game.swarm is not None and game.swarm.count > 0

    # Simulate shooting: force bullets and collisions over many frames
    for _ in range(3000):
        if game.state != "play":
            game.step(1 / 60, [])
            continue
        if game.swarm and game.swarm.count and len(game.bullets) < 3:
            e = game.swarm.alive_enemies()[0]
            r = game.swarm.enemy_rect(e)
            game.bullets.append(g.Shot(game.sprites["bb"],
                                       r.centerx, r.centery, 0, -540))
        game.enemy_shots.clear()  # stay alive
        game.step(1 / 60, [])
        if game.state == "clear":
            break
    assert game.state == "clear", f"expected clear, got {game.state}"
    snap(game, "05_hole_clear")
    frames(game, 150)
    assert game.state == "intro" and game.hole == 2

    # Jump to boss hole 9
    game.hole = 9
    game.start_hole()
    game.set_state("play")
    frames(game, 120)
    assert game.boss is not None
    snap(game, "06_boss9")

    # Kill the boss
    game.boss.hp = 1
    game.bullets.append(g.Shot(game.sprites["bb"], game.boss.x,
                               game.boss.y, 0, 0))
    game.enemy_shots.clear()
    frames(game, 2)
    assert game.state == "clear"
    frames(game, 150)
    assert game.hole == 10 and game.state == "intro"

    # Jump to final boss and win the game
    game.hole = 18
    game.start_hole()
    game.set_state("play")
    frames(game, 60)
    snap(game, "07_boss18")
    game.boss.hp = 1
    game.bullets.append(g.Shot(game.sprites["bb"], game.boss.x,
                               game.boss.y, 0, 0))
    game.enemy_shots.clear()
    frames(game, 2)
    assert game.state == "clear"
    frames(game, 140)
    assert game.state == "victory", f"expected victory, got {game.state}"
    snap(game, "08_victory")

    # Name entry for high score
    game.score = 99999
    frames(game, 70)  # victory screen ignores keys for its first second
    frames(game, 2, [key_event(pg.K_SPACE)])
    assert game.state == "entry", f"expected entry, got {game.state}"
    for ch in "ACE":
        frames(game, 1, [key_event(getattr(pg, "K_" + ch.lower()), ch.lower())])
    snap(game, "09_entry")
    frames(game, 2, [key_event(pg.K_RETURN)])
    assert game.state == "scores"
    assert game.highscores[0]["name"] == "ACE"
    assert game.highscores[0]["score"] == 99999
    snap(game, "10_scores_after")

    # Player death path
    game.reset_run()
    game.hole = 1
    game.start_hole()
    game.set_state("play")
    frames(game, 5)
    game.lives = 1
    game.kill_player()
    assert game.state == "dead"
    frames(game, 120)
    assert game.state in ("gameover", "entry")
    snap(game, "11_gameover")

    # Pause
    game.reset_run()
    game.start_hole()
    game.set_state("play")
    frames(game, 5)
    frames(game, 2, [key_event(pg.K_p)])
    assert game.state == "pause"
    snap(game, "12_pause")

    pg.quit()
    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
