#!/usr/bin/env python3
"""
NEXT STOP (2026): Locomotive Oblivion
Chud Studios Flagship Production
"""
import sys
import asyncio
import pygame
from src.core.game import Game

async def main():
    pygame.init()
    game = Game()
    # Runs seamlessly on native desktop and in browser WebAssembly (Pygbag)
    await game.run_async()

if __name__ == "__main__":
    asyncio.run(main())
