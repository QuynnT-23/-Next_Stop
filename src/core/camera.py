"""Smooth tracking 2D camera with trauma-based screen shake."""
import pygame
import random
import math
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

class Camera:
    """Handles view offset and screen shake for game rendering."""
    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT):
        self.width = width
        self.height = height
        self.offset = pygame.math.Vector2(0, 0)
        self.target = pygame.math.Vector2(0, 0)
        
        # Smooth follow parameters
        self.smoothness = 8.0  # Lerp speed factor
        
        # Screen shake parameters (trauma-based shake)
        self.trauma = 0.0      # 0.0 to 1.0
        self.trauma_decay = 1.4 # Trauma decay per second
        self.max_shake_offset = 24.0 # Maximum pixels of shake
        self.shake_offset = pygame.math.Vector2(0, 0)
        
        # Bounds clamping (optional, can be None for free scroll)
        self.min_x = 0
        self.max_x = None
        self.min_y = 0
        self.max_y = None

    def add_trauma(self, amount: float):
        """Add screen shake trauma (clamped to 1.0)."""
        self.trauma = min(1.0, self.trauma + amount)

    def set_bounds(self, min_x: float, max_x: float, min_y: float, max_y: float):
        """Constrain camera movement within world bounds."""
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def update(self, dt: float, target_pos: pygame.math.Vector2):
        """Update camera position following target with damping and shake."""
        # Target top-left such that target_pos is centered
        desired_x = target_pos.x - self.width / 2
        desired_y = target_pos.y - self.height / 2
        
        # Clamp to bounds if set
        if self.min_x is not None and self.max_x is not None:
            if self.max_x - self.min_x >= self.width:
                desired_x = max(self.min_x, min(desired_x, self.max_x - self.width))
            else:
                desired_x = self.min_x - (self.width - (self.max_x - self.min_x)) / 2
                
        if self.min_y is not None and self.max_y is not None:
            if self.max_y - self.min_y >= self.height:
                desired_y = max(self.min_y, min(desired_y, self.max_y - self.height))
            else:
                desired_y = self.min_y - (self.height - (self.max_y - self.min_y)) / 2

        # Exponential Lerp for smooth camera follow
        t = min(1.0, dt * self.smoothness)
        self.offset.x += (desired_x - self.offset.x) * t
        self.offset.y += (desired_y - self.offset.y) * t

        # Update screen shake
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - self.trauma_decay * dt)
            shake_intensity = self.trauma * self.trauma  # Quadratic falloff feels punchier
            angle = random.uniform(0, math.tau)
            distance = random.uniform(0, self.max_shake_offset * shake_intensity)
            self.shake_offset = pygame.math.Vector2(math.cos(angle) * distance, math.sin(angle) * distance)
        else:
            self.shake_offset = pygame.math.Vector2(0, 0)

    def apply(self, world_pos: pygame.math.Vector2) -> tuple[int, int]:
        """Convert a world position Vector2 to screen pixel coordinates (x, y)."""
        screen_x = world_pos.x - self.offset.x + self.shake_offset.x
        screen_y = world_pos.y - self.offset.y + self.shake_offset.y
        return int(screen_x), int(screen_y)

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Offset a pygame.Rect from world coordinates to screen coordinates."""
        return pygame.Rect(
            rect.x - int(self.offset.x - self.shake_offset.x),
            rect.y - int(self.offset.y - self.shake_offset.y),
            rect.width,
            rect.height
        )

    def screen_to_world(self, screen_pos: tuple[int, int]) -> pygame.math.Vector2:
        """Convert screen pixel coordinates back into world position Vector2."""
        return pygame.math.Vector2(
            screen_pos[0] + self.offset.x - self.shake_offset.x,
            screen_pos[1] + self.offset.y - self.shake_offset.y
        )
