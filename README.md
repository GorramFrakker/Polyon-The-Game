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
- **Power-ups** dropped by fallen enemies (and every bonus cart):
  Multishot (double prills per volley), Power Shot (double damage), and
  Rapid Fire (double fire rate) — each lasts 12 seconds and they stack
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

## Play it

**In your browser:** the game is built with [pygbag](https://pygame-web.github.io)
(pygame compiled to WebAssembly) and deployed to **Azure Static Web Apps**
on every push — open the site's `*.azurestaticapps.net` URL and play.
Click once to unlock sound. High scores persist in your browser
(localStorage).

One-time setup to enable deployment:
1. Azure Portal → create a **Static Web App** (Free plan, deployment
   source "Other").
2. Copy its deployment token into this repo's secret
   `AZURE_STATIC_WEB_APPS_API_TOKEN`.
3. Push (or re-run the workflow) — done. Until the secret exists, CI
   still builds and uploads the web bundle as the `PolyonTheGame-Web`
   artifact and simply skips the deploy step.

**Windows executable (legacy):** the v1–v3 single-file
`PolyonTheGame.exe` builds remain on the [releases page](../../releases);
new versions are web-only.

**From source** (any OS):

```sh
pip install -r requirements.txt
python polyon_the_game.py
```

Desktop high scores are saved to `%APPDATA%\PolyonTheGame\highscores.json`
on Windows (`~/.polyon_the_game/` elsewhere).

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

*Clubhouse legend: regulars whisper that typing the year Harrell's was
founded on the title screen reveals something the greenskeeper doesn't
want you to have. Such runs are barred from the leaderboard.*

## Development

Run the headless smoke test (also runs in CI before each build):

```sh
python tests/smoke_test.py
```

It drives the game through every state and saves screenshots to
`tests/shots/`.
