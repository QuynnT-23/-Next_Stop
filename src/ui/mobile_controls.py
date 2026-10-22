"""Mobile Virtual On-Screen Controls for Touch / Tablet / Mobile Game Play."""
import pygame
import math
from typing import Optional, Tuple
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_WHITE, COLOR_CRIT_YELLOW
)

class VirtualStick:
    """Analog touch thumbstick with base and floating knob."""
    def __init__(self, center_x: int, center_y: int, radius: int = 70):
        self.center = pygame.math.Vector2(center_x, center_y)
        self.current_pos = pygame.math.Vector2(center_x, center_y)
        self.radius = radius
        self.touch_id = None
        self.active = False
        self.vector = pygame.math.Vector2(0, 0)

    def handle_touch_down(self, touch_id: int, pos: Tuple[int, int]) -> bool:
        p = pygame.math.Vector2(pos)
        if (p - self.center).length() <= self.radius * 1.5:
            self.touch_id = touch_id
            self.active = True
            self._update_knob(p)
            return True
        return False

    def handle_touch_motion(self, touch_id: int, pos: Tuple[int, int]) -> bool:
        if self.active and self.touch_id == touch_id:
            self._update_knob(pygame.math.Vector2(pos))
            return True
        return False

    def handle_touch_up(self, touch_id: int) -> bool:
        if self.active and self.touch_id == touch_id:
            self.active = False
            self.touch_id = None
            self.current_pos = pygame.math.Vector2(self.center)
            self.vector = pygame.math.Vector2(0, 0)
            return True
        return False

    def _update_knob(self, pos: pygame.math.Vector2):
        delta = pos - self.center
        dist = delta.length()
        if dist > self.radius:
            delta = delta.normalize() * self.radius
        self.current_pos = self.center + delta
        if self.radius > 0:
            self.vector = delta / self.radius
        else:
            self.vector = pygame.math.Vector2(0, 0)

    def draw(self, surface: pygame.Surface):
        # Base ring
        base_surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
        center_rel = (self.radius + 5, self.radius + 5)
        pygame.draw.circle(base_surf, (25, 30, 42, 120), center_rel, self.radius)
        pygame.draw.circle(base_surf, (180, 150, 90, 180), center_rel, self.radius, 2)
        pygame.draw.circle(base_surf, (100, 85, 50, 100), center_rel, self.radius // 2, 1)
        surface.blit(base_surf, (int(self.center.x - center_rel[0]), int(self.center.y - center_rel[1])))

        # Knob
        knob_r = 30
        knob_surf = pygame.Surface((knob_r * 2 + 6, knob_r * 2 + 6), pygame.SRCALPHA)
        k_center = (knob_r + 3, knob_r + 3)
        knob_col = (240, 200, 100, 220) if self.active else (180, 140, 70, 160)
        pygame.draw.circle(knob_surf, knob_col, k_center, knob_r)
        pygame.draw.circle(knob_surf, (255, 255, 255, 200), k_center, knob_r, 2)
        surface.blit(knob_surf, (int(self.current_pos.x - k_center[0]), int(self.current_pos.y - k_center[1])))

class VirtualButton:
    """Touch button with visual press state and label."""
    def __init__(self, x: int, y: int, radius: int, label: str, sub: str = "", color: tuple = (50, 60, 80)):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = radius
        self.label = label
        self.sub = sub
        self.color = color
        self.touch_id = None
        self.is_down = False
        self.just_pressed = False

    def handle_touch_down(self, touch_id: int, pos: Tuple[int, int]) -> bool:
        if (pygame.math.Vector2(pos) - self.pos).length() <= self.radius:
            self.touch_id = touch_id
            self.is_down = True
            self.just_pressed = True
            return True
        return False

    def handle_touch_up(self, touch_id: int) -> bool:
        if self.touch_id == touch_id:
            self.is_down = False
            self.touch_id = None
            return True
        return False

    def draw(self, surface: pygame.Surface, font_lbl: pygame.font.Font, font_sub: pygame.font.Font):
        r = self.radius
        btn_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        c = (r + 4, r + 4)
        
        # Color based on pressed state
        alpha = 220 if self.is_down else 130
        r_col = min(255, self.color[0] + (60 if self.is_down else 0))
        g_col = min(255, self.color[1] + (60 if self.is_down else 0))
        b_col = min(255, self.color[2] + (60 if self.is_down else 0))
        
        pygame.draw.circle(btn_surf, (r_col, g_col, b_col, alpha), c, r)
        border_col = (255, 220, 120, 240) if self.is_down else (180, 150, 90, 160)
        pygame.draw.circle(btn_surf, border_col, c, r, 2 if not self.is_down else 3)
        
        surface.blit(btn_surf, (int(self.pos.x - c[0]), int(self.pos.y - c[1])))

        # Text
        lbl_surf = font_lbl.render(self.label, True, COLOR_WHITE if not self.is_down else COLOR_BRASS_HIGHLIGHT)
        surface.blit(lbl_surf, lbl_surf.get_rect(center=(int(self.pos.x), int(self.pos.y - (4 if self.sub else 0)))))
        if self.sub:
            sub_surf = font_sub.render(self.sub, True, (210, 220, 240))
            surface.blit(sub_surf, sub_surf.get_rect(center=(int(self.pos.x), int(self.pos.y + 12))))

class MobileControls:
    """Manages virtual screen touch joystick and action buttons."""
    def __init__(self):
        pygame.font.init()
        self.enabled = False  # Toggleable with [M] or touch detection
        self.font_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13, bold=True)
        self.font_sub = pygame.font.SysFont("Helvetica, Arial, sans-serif", 9, bold=True)
        self.font_hint = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11, bold=True)

        # Left Cluster: Thumbstick
        self.stick = VirtualStick(120, SCREEN_HEIGHT - 120, radius=65)

        # Right Action Cluster:
        # FIRE (Big main button)
        self.btn_fire = VirtualButton(SCREEN_WIDTH - 110, SCREEN_HEIGHT - 115, 42, "FIRE", "AIM", color=(180, 50, 50))
        # DASH
        self.btn_dash = VirtualButton(SCREEN_WIDTH - 185, SCREEN_HEIGHT - 75, 30, "DASH", "SHIFT", color=(40, 120, 160))
        # BLOCK / PARRY
        self.btn_block = VirtualButton(SCREEN_WIDTH - 195, SCREEN_HEIGHT - 150, 28, "BLOCK", "SPACE", color=(140, 110, 30))
        # SUPER
        self.btn_super = VirtualButton(SCREEN_WIDTH - 110, SCREEN_HEIGHT - 205, 28, "SUPER", "Q", color=(130, 40, 150))
        # INTERACT
        self.btn_interact = VirtualButton(SCREEN_WIDTH - 45, SCREEN_HEIGHT - 190, 26, "USE", "E", color=(40, 140, 80))

        self.buttons = [self.btn_fire, self.btn_dash, self.btn_block, self.btn_super, self.btn_interact]

        # Toggle Button (Pill at top right)
        self.toggle_rect = pygame.Rect(SCREEN_WIDTH - 155, 72, 135, 22)

    def toggle(self):
        self.enabled = not self.enabled

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Keyboard toggle hotkey [M]
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.toggle()
            return True

        # Mouse click on top pill
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.toggle_rect.collidepoint(event.pos):
                self.toggle()
                return True

        if not self.enabled:
            return False

        # Support Mouse Emulation for testing on Desktop
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.stick.handle_touch_down(999, pos):
                return True
            for b in self.buttons:
                if b.handle_touch_down(999, pos):
                    return True

        elif event.type == pygame.MOUSEMOTION:
            if event.buttons[0]:
                pos = event.pos
                self.stick.handle_touch_motion(999, pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.stick.handle_touch_up(999)
            for b in self.buttons:
                b.handle_touch_up(999)

        # Native Multi-Touch SDL Finger Events
        elif event.type == pygame.FINGERDOWN:
            touch_id = event.finger_id
            pos = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))
            if self.stick.handle_touch_down(touch_id, pos):
                return True
            for b in self.buttons:
                if b.handle_touch_down(touch_id, pos):
                    return True

        elif event.type == pygame.FINGERMOTION:
            touch_id = event.finger_id
            pos = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))
            self.stick.handle_touch_motion(touch_id, pos)

        elif event.type == pygame.FINGERUP:
            touch_id = event.finger_id
            self.stick.handle_touch_up(touch_id)
            for b in self.buttons:
                b.handle_touch_up(touch_id)

        return False

    def get_move_vector(self) -> pygame.math.Vector2:
        if not self.enabled:
            return pygame.math.Vector2(0, 0)
        return self.stick.vector

    def is_fire_active(self) -> bool:
        return self.enabled and self.btn_fire.is_down

    def is_dash_active(self) -> bool:
        return self.enabled and self.btn_dash.is_down

    def is_block_active(self) -> bool:
        return self.enabled and self.btn_block.is_down

    def is_super_active(self) -> bool:
        return self.enabled and self.btn_super.is_down

    def is_interact_active(self) -> bool:
        return self.enabled and self.btn_interact.is_down

    def post_update_clear(self):
        """Clears single-frame impulse states."""
        for b in self.buttons:
            b.just_pressed = False

    def draw(self, surface: pygame.Surface):
        # Always draw the top toggle pill
        mouse_pos = pygame.mouse.get_pos()
        hover = self.toggle_rect.collidepoint(mouse_pos)
        pill_bg = (30, 60, 50) if self.enabled else ((35, 42, 54) if hover else (22, 28, 38))
        pygame.draw.rect(surface, pill_bg, self.toggle_rect, border_radius=11)
        border_col = (110, 240, 160) if self.enabled else (70, 90, 120)
        pygame.draw.rect(surface, border_col, self.toggle_rect, 1, border_radius=11)
        
        status_txt = "📱 TOUCH UI: ON" if self.enabled else "📱 [M] TOUCH UI"
        txt_col = (180, 255, 210) if self.enabled else (180, 195, 220)
        t_surf = self.font_hint.render(status_txt, True, txt_col)
        surface.blit(t_surf, t_surf.get_rect(center=self.toggle_rect.center))

        if not self.enabled:
            return

        # Render thumbstick
        self.stick.draw(surface)

        # Render action buttons
        for b in self.buttons:
            b.draw(surface, self.font_btn, self.font_sub)
