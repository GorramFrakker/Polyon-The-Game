"""Entry point for the web (pygbag/WebAssembly) build of POLYON: The Game.

pygbag requires a `main.py` at the project root with a top-level
`asyncio.run(main())`. Desktop players should run `polyon_the_game.py`
directly (or this file — it works there too).
"""

import asyncio
import traceback


async def main():
    try:
        import polyon_the_game
        game = polyon_the_game.Game()
        await game.run()
    except Exception:
        # surface startup failures in the browser console instead of a
        # silent gray canvas
        traceback.print_exc()
        raise


asyncio.run(main())
