"""Entry point for the web (pygbag/WebAssembly) build of POLYON: The Game.

pygbag requires a `main.py` at the project root with a top-level
`asyncio.run(main())`. Desktop players should run `polyon_the_game.py`
directly (or this file — it works there too).
"""

import asyncio

import polyon_the_game


async def main():
    game = polyon_the_game.Game()
    await game.run()


asyncio.run(main())
