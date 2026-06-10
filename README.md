# POLYON: The Game

A Space Invaders style arcade game themed around **POLYON® Controlled-Release
Fertilizer** by **Harrell's** — *Growing a Better World*.

You are a 25KG bag of POLYON. Eighteen holes of golf-course mayhem stand
between you and a perfect lawn. Blast angry golf balls, flagsticks,
sprinklers and lawn mowers with an endless supply of green prills, survive
the Marshal's Cart at the turn, and take down the Mega Mower 9000 on 18.

## Features

- **18 holes** (waves) of escalating difficulty — a full round takes about
  20 minutes
- **Two boss fights**: the Marshal's Cart (hole 9) and the Mega Mower 9000
  (hole 18)
- **Bonus golf cart** flybys, extra-bag lives, hole-clear bonuses
- **Persistent high score leaderboard** with arcade-style initials entry
- All artwork drawn in code in the POLYON green / Harrell's blue palette —
  no asset files needed
- Retro synthesized sound effects

## Controls

| Key | Action |
| --- | --- |
| ← / → or A / D | Move |
| SPACE | Fire prills |
| P or ESC | Pause |
| ENTER | Start / confirm |
| H | High scores (title screen) |

## Play it on Windows

**Option 1 — download the executable:** every push builds
`PolyonTheGame.exe` via GitHub Actions. Grab the
`PolyonTheGame-Windows` artifact from the latest
[Actions run](../../actions), unzip, and double-click `PolyonTheGame.exe`.
No install needed.

**Option 2 — build it yourself:** on a Windows machine with Python 3.10+,
run `build_windows.bat`. The executable lands in `dist\PolyonTheGame.exe`.

**Option 3 — run from source** (any OS):

```sh
pip install -r requirements.txt
python polyon_the_game.py
```

High scores are saved to `%APPDATA%\PolyonTheGame\highscores.json` on
Windows (`~/.polyon_the_game/` elsewhere).

## Scoring

| Target | Points |
| --- | --- |
| Golf ball | 10 |
| Flagstick | 25 |
| Sprinkler | 30 |
| Lawn mower | 40 |
| Bonus golf cart | 100–300 |
| Hole clear | 100 + 25 × hole |
| Marshal's Cart (boss) | 1500 |
| Mega Mower 9000 (boss) | 3000 |
| Spare bags at victory | 1000 each |

Extra bag (life) every 10,000 points.

## Development

Run the headless smoke test (also runs in CI before each build):

```sh
python tests/smoke_test.py
```

It drives the game through every state and saves screenshots to
`tests/shots/`.
