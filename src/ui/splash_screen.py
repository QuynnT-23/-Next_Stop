"""Goofy animated intro splash screen for Chud Studios featuring Lil' Chud."""
import math
import random
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_WHITE,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_EMBER_ORANGE
)

class SmokePuff:
    """Cartoon smoke ring puffing from Lil' Chud's smokestack."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-25, 25)
        self.vy = random.uniform(-90, -140)
        self.radius = random.uniform(14, 22)
        self.max_life = random.uniform(0.7, 1.1)
        self.life = self.max_life

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.radius += 18 * dt
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        alpha = max(0, min(255, int(230 * (self.life / self.max_life))))
        ring_surf = pygame.Surface((int(self.radius * 2 + 8), int(self.radius * 2 + 8)), pygame.SRCALPHA)
        center = (ring_surf.get_width() // 2, ring_surf.get_height() // 2)
        pygame.draw.circle(ring_surf, (240, 245, 255, alpha), center, int(self.radius), 4)
        pygame.draw.circle(ring_surf, (200, 215, 235, alpha // 2), center, int(self.radius * 0.5), 2)
        surface.blit(ring_surf, (self.x - center[0], self.y - center[1]))


class SplashScreen:
    """Renders the goofy Chud Studios animated intro featuring Lil' Chud."""
    def __init__(self, audio_manager=None):
        self.audio = audio_manager
        self.timer = 0.0
        self.duration = 3.2  # Auto-transition duration
        self.finished = False
        self.skipped = False
        
        # Audio triggers
        self.played_boing = False
        self.played_whistle = False
        
        # Interactive click squish
        self.click_squish = 0.0

        # Smoke particles
        self.smoke_puffs: list[SmokePuff] = []
        self.smoke_timer = 0.0

        # Fonts
        pygame.font.init()
        self.font_title_big = pygame.font.SysFont("Impact, Arial Black, sans-serif", 64)
        self.font_tagline = pygame.font.SysFont("Helvetica, Arial, sans-serif", 18, bold=True)
        self.font_skip = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14)

    def handle_input(self, events: list[pygame.event.Event]) -> bool:
        """Returns True if the splash screen was completed or skipped."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_e):
                    self.finish()
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.timer > 0.4:
                        self.finish()
                        return True
                    else:
                        self.click_squish = 0.35
        return self.finished

    def finish(self):
        self.finished = True
        if self.audio:
            self.audio.play('shoot')

    def update(self, dt: float) -> bool:
        """Update animation and return True when splash is complete."""
        if self.finished:
            return True

        dt = min(dt, 0.05)
        self.timer += dt

        # Sound cues
        if self.timer >= 0.2 and not self.played_boing:
            self.played_boing = True
            if self.audio:
                self.audio.play('boing')

        if self.timer >= 1.0 and not self.played_whistle:
            self.played_whistle = True
            if self.audio:
                self.audio.play('whistle')

        # Puff smoke rings
        self.smoke_timer += dt
        if 0.4 <= self.timer <= 2.8 and self.smoke_timer >= 0.22:
            self.smoke_timer = 0.0
            puff_x = SCREEN_WIDTH // 2 - 45 + random.uniform(-6, 6)
            puff_y = SCREEN_HEIGHT // 2 - 120
            self.smoke_puffs.append(SmokePuff(puff_x, puff_y))

        # Update smoke
        self.smoke_puffs = [p for p in self.smoke_puffs if p.update(dt)]

        if self.click_squish > 0.0:
            self.click_squish = max(0.0, self.click_squish - dt * 2.0)

        if self.timer >= self.duration:
            self.finished = True

        return self.finished

    def draw(self, surface: pygame.Surface):
        """Draw the animated goofy mascot Lil' Chud and title."""
        surface.fill(COLOR_BG)

        # Draw retro background grid lines
        grid_alpha = 25
        grid_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(grid_surf, (80, 100, 140, grid_alpha), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(grid_surf, (80, 100, 140, grid_alpha), (0, y), (SCREEN_WIDTH, y), 1)
        surface.blit(grid_surf, (0, 0))

        # Draw smoke puffs behind train
        for puff in self.smoke_puffs:
            puff.draw(surface)

        # Entrance bounce calculation
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 - 25

        t = min(1.0, self.timer / 0.7)
        # Elastic drop in
        drop_y = (1.0 - math.cos(t * math.pi * 0.5)) if t < 1.0 else 1.0
        bounce_offset = math.sin(max(0.0, self.timer - 0.7) * 8.0) * 8.0
        train_y = cy - (1.0 - drop_y) * 350 + bounce_offset

        # Wobble and squash
        wobble_angle = math.sin(self.timer * 7.0) * 3.5
        squash = 1.0 + math.sin(self.timer * 14.0) * 0.06 + self.click_squish

        self._draw_mascot(surface, cx, train_y, wobble_angle, squash)

        # Text banner animation
        if self.timer >= 0.5:
            text_fade = min(1.0, (self.timer - 0.5) / 0.4)
            text_scale = 1.0 + math.sin((self.timer - 0.5) * 6.0) * 0.04
            self._draw_banner(surface, cx, cy + 130, text_fade, text_scale)

        # Skip prompt at bottom
        if self.timer >= 0.8:
            pulse = (math.sin(self.timer * 5.0) + 1.0) * 0.5
            skip_color = (int(130 + 70 * pulse), int(130 + 70 * pulse), int(150 + 70 * pulse))
            skip_surf = self.font_skip.render("Press [SPACE], [ENTER] or CLICK to skip", True, skip_color)
            surface.blit(skip_surf, skip_surf.get_rect(center=(cx, SCREEN_HEIGHT - 35)))

    def _draw_mascot(self, surface: pygame.Surface, cx: float, cy: float, wobble_angle: float, squash: float):
        """Draw goofy Lil' Chud procedural cartoon locomotive."""
        mascot_surf = pygame.Surface((320, 260), pygame.SRCALPHA)
        mcx, mcy = 160, 150

        # 1. Wheels (chunky cartoon style)
        wheel_rot = self.timer * 12.0
        wheel_radius = 28
        for wx_off in (-65, 0, 65):
            wx = mcx + wx_off
            wy = mcy + 45
            pygame.draw.circle(mascot_surf, (20, 22, 28), (wx, wy), wheel_radius)
            pygame.draw.circle(mascot_surf, COLOR_BRASS, (wx, wy), wheel_radius, 4)
            pygame.draw.circle(mascot_surf, (220, 70, 50), (wx, wy), 10)
            # Wheel spokes
            for spk in (0, math.pi / 2, math.pi / 4, 3 * math.pi / 4):
                sx = wx + math.cos(wheel_rot + spk) * (wheel_radius - 6)
                sy = wy + math.sin(wheel_rot + spk) * (wheel_radius - 6)
                pygame.draw.line(mascot_surf, COLOR_BRASS_HIGHLIGHT, (wx, wy), (sx, sy), 2)

        # 2. Boiler Body (curved chubby locomotive)
        body_rect = pygame.Rect(mcx - 100, mcy - 45, 175, 80)
        pygame.draw.rect(mascot_surf, (45, 120, 195), body_rect, border_radius=22)
        pygame.draw.rect(mascot_surf, (25, 45, 75), body_rect, 4, border_radius=22)

        # Cab (back cabin)
        cab_rect = pygame.Rect(mcx + 10, mcy - 85, 75, 95)
        pygame.draw.rect(mascot_surf, (225, 85, 60), cab_rect, border_radius=12)
        pygame.draw.rect(mascot_surf, (110, 25, 20), cab_rect, 4, border_radius=12)
        
        # Smokestack (chubby top pipe)
        stack_rect = pygame.Rect(mcx - 70, mcy - 95, 34, 55)
        pygame.draw.rect(mascot_surf, (35, 40, 50), stack_rect, border_radius=6)
        pygame.draw.rect(mascot_surf, COLOR_BRASS, stack_rect, 3, border_radius=6)
        stack_lip = pygame.Rect(mcx - 76, mcy - 102, 46, 12)
        pygame.draw.rect(mascot_surf, COLOR_BRASS_HIGHLIGHT, stack_lip, border_radius=4)

        # Cowcatcher (goofy front teeth grill)
        grill_pts = [(mcx - 100, mcy + 35), (mcx - 125, mcy + 45), (mcx - 90, mcy + 45)]
        pygame.draw.polygon(mascot_surf, COLOR_EMBER_ORANGE, grill_pts)
        pygame.draw.polygon(mascot_surf, (20, 20, 20), grill_pts, 3)

        # 3. Big Cartoon Googly Eyes! (Pupils actively track the mouse cursor)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - (cx - 30)
        dy = mouse_y - (cy - 10)
        dist = math.hypot(dx, dy)
        eye_look_x = (dx / dist * 7) if dist > 0 else 0
        eye_look_y = (dy / dist * 7) if dist > 0 else 0

        # Left Eye (huge oval)
        left_eye_center = (mcx - 45, mcy - 15)
        pygame.draw.ellipse(mascot_surf, COLOR_WHITE, (left_eye_center[0] - 22, left_eye_center[1] - 28, 44, 56))
        pygame.draw.ellipse(mascot_surf, (20, 20, 20), (left_eye_center[0] - 22, left_eye_center[1] - 28, 44, 56), 3)
        # Left Pupil (tracks mouse!)
        lp_x = int(left_eye_center[0] + eye_look_x)
        lp_y = int(left_eye_center[1] + eye_look_y)
        pygame.draw.circle(mascot_surf, (15, 15, 20), (lp_x, lp_y), 11)
        pygame.draw.circle(mascot_surf, COLOR_WHITE, (lp_x - 3, lp_y - 3), 4)

        # Right Eye (slightly higher & silly)
        right_eye_center = (mcx - 5, mcy - 20)
        pygame.draw.ellipse(mascot_surf, COLOR_WHITE, (right_eye_center[0] - 20, right_eye_center[1] - 26, 40, 52))
        pygame.draw.ellipse(mascot_surf, (20, 20, 20), (right_eye_center[0] - 20, right_eye_center[1] - 26, 40, 52), 3)
        # Right Pupil
        rp_x = int(right_eye_center[0] + eye_look_x)
        rp_y = int(right_eye_center[1] + eye_look_y)
        pygame.draw.circle(mascot_surf, (15, 15, 20), (rp_x, rp_y), 10)
        pygame.draw.circle(mascot_surf, COLOR_WHITE, (rp_x - 3, rp_y - 3), 3)

        # 4. Goofy Smile
        smile_rect = pygame.Rect(mcx - 55, mcy + 10, 48, 22)
        pygame.draw.arc(mascot_surf, (20, 20, 20), smile_rect, math.pi * 1.05, math.pi * 1.95, 4)
        # Rosy cartoon cheeks
        pygame.draw.circle(mascot_surf, (255, 120, 140, 160), (mcx - 58, mcy + 14), 7)
        pygame.draw.circle(mascot_surf, (255, 120, 140, 160), (mcx + 2, mcy + 12), 7)

        # 5. Crooked Conductor Hat on Top
        hat_center = (mcx - 20, mcy - 48)
        hat_pts = [
            (hat_center[0] - 22, hat_center[1] + 6),
            (hat_center[0] + 28, hat_center[1] - 4),
            (hat_center[0] + 18, hat_center[1] - 28),
            (hat_center[0] - 24, hat_center[1] - 22)
        ]
        pygame.draw.polygon(mascot_surf, (25, 30, 45), hat_pts)
        pygame.draw.polygon(mascot_surf, COLOR_BRASS, hat_pts, 2)
        # Gold badge on hat with "CHUD"
        pygame.draw.circle(mascot_surf, COLOR_BRASS_HIGHLIGHT, (hat_center[0] - 2, hat_center[1] - 12), 6)

        # Apply squash & stretch and wobble rotation
        squash_clamped = max(0.4, min(2.5, squash))
        scaled_w = int(mascot_surf.get_width() / squash_clamped)
        scaled_h = int(mascot_surf.get_height() * squash_clamped)
        scaled_surf = pygame.transform.scale(mascot_surf, (scaled_w, scaled_h))
        rotated_surf = pygame.transform.rotate(scaled_surf, wobble_angle)

        dest_rect = rotated_surf.get_rect(center=(cx, cy))
        surface.blit(rotated_surf, dest_rect)

    def _draw_banner(self, surface: pygame.Surface, cx: float, cy: float, alpha_scale: float, scale: float):
        """Draw bouncy colorful Chud Studios lettering."""
        title_text = "CHUD STUDIOS"
        shadow_surf = self.font_title_big.render(title_text, True, (15, 15, 20))
        gold_surf = self.font_title_big.render(title_text, True, COLOR_BRASS_HIGHLIGHT)
        
        sw, sh = gold_surf.get_size()
        banner_surf = pygame.Surface((sw + 20, sh + 20), pygame.SRCALPHA)
        banner_surf.blit(shadow_surf, (14, 14))
        banner_surf.blit(gold_surf, (10, 10))

        tagline_text = "★  CERTIFIED RUNAWAY TRAIN WRECK PRODUCTIONS  ★"
        tag_surf = self.font_tagline.render(tagline_text, True, COLOR_EMBER_ORANGE)

        b_rect = banner_surf.get_rect(center=(cx, cy))
        t_rect = tag_surf.get_rect(center=(cx, cy + 46))
        surface.blit(banner_surf, b_rect)
        surface.blit(tag_surf, t_rect)
