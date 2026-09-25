#!/usr/bin/env python3
"""
NEXT STOP (2026): Locomotive Oblivion
A fast-paced runaway train action roguelite dungeon crawler.
"""
import sys
import pygame
from src.core.game import Game

def main():
    pygame.init()
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
