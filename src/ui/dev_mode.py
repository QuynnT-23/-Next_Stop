"""Developer Mode & Secret Maintenance Keypad.

Provides a secret bottom-right corner keypad for developer authorization
and a clean Level Iterator for rapid testing without public cheats.
"""
import math
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_WHITE,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_CRIT_YELLOW,
    COLOR_STEEL_DARK, COLOR_STEEL_MID
)

SECRET_CODE = "CHUDDEV"

class SecretKeypad:
    """Bottom-right maintenance keypad that appears when player approaches the corner."""
    def __init__(self, on_unlock_callback=None):
        self.code_buffer = ""
        self.unlocked = False
        self.notification_timer = 0.0
        self.notification_text = ""
        self.visible_alpha = 0.0
        self.in_corner = False
        self.on_unlock_callback = on_unlock_callback
        self.rect = pygame.Rect(SCREEN_WIDTH - 240, SCREEN_HEIGHT - 250, 220, 230)
        
        # Grid buttons for mouse clicking or touch
        self.buttons = []
        keys = ["C", "H", "U", "D", "E", "V", "1", "2", "3", "CLR", "ENTER"]
        btn_w, btn_h = 44, 32
        start_x, start_y = self.rect.left + 15, self.rect.top + 70
        cols = 4
        for i, k in enumerate(keys):
            row = i // cols
            col = i % cols
            bx = start_x + col * (btn_w + 6)
            by = start_y + row * (btn_h + 6)
            w = btn_w * 2 + 6 if k in ("CLR", "ENTER") and col >= 2 else btn_w
            self.buttons.append({"label": k, "rect": pygame.Rect(bx, by, w, btn_h)})

        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_display = pygame.font.SysFont("Courier New, monospace", 16, bold=True)
        self.font_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_notify = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)

    @property
    def input_text(self) -> str:
        return self.code_buffer

    @input_text.setter
    def input_text(self, val: str):
        self.code_buffer = val

    @property
    def is_active(self) -> bool:
        return self.visible_alpha > 0.05 or self.in_corner

    def update(self, *args, **kwargs):
        """Flexible update supporting (player_pos, dt) or (dt, player_pos, is_hub)."""
        dt = 0.016
        player_pos = None
        is_hub = True

        if len(args) == 2:
            if isinstance(args[0], (int, float)):
                dt = float(args[0])
                player_pos = args[1]
            else:
                player_pos = args[0]
                dt = float(args[1])
        elif len(args) >= 3:
            dt = float(args[0])
            player_pos = args[1]
            is_hub = bool(args[2])

        if player_pos:
            self.in_corner = is_hub and player_pos.x > SCREEN_WIDTH - 270 and player_pos.y > SCREEN_HEIGHT - 270
        else:
            self.in_corner = False

        target_alpha = 1.0 if self.in_corner else 0.0
        self.visible_alpha += (target_alpha - self.visible_alpha) * min(1.0, dt * 8.0)

        if self.notification_timer > 0.0:
            self.notification_timer = max(0.0, self.notification_timer - dt)

    def handle_event(self, event_or_events, audio_mgr=None) -> bool:
        """Process keyboard typing and clicks for the secret code. Accepts single event or list."""
        events = event_or_events if isinstance(event_or_events, list) else [event_or_events]
        return self.handle_input(events, audio_mgr)

    def handle_input(self, events: list[pygame.event.Event], audio_mgr=None) -> bool:
        """Process keyboard typing and clicks for the secret code. Returns True if unlocked."""
        if self.visible_alpha < 0.2 and not self.unlocked:
            # Check global background typing buffer even if keypad is faded
            for event in events:
                if event.type == pygame.KEYDOWN and event.unicode:
                    char = event.unicode.upper()
                    if char.isalnum():
                        self.code_buffer += char
                        if len(self.code_buffer) > 12:
                            self.code_buffer = self.code_buffer[-12:]
                        if SECRET_CODE in self.code_buffer:
                            return self._grant_access(audio_mgr)
            return False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.code_buffer = self.code_buffer[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.code_buffer == SECRET_CODE:
                        return self._grant_access(audio_mgr)
                    else:
                        self._reject_code(audio_mgr)
                elif event.unicode and event.unicode.isalnum():
                    self.code_buffer += event.unicode.upper()
                    if len(self.code_buffer) > 12:
                        self.code_buffer = self.code_buffer[-12:]
                    if self.code_buffer == SECRET_CODE:
                        return self._grant_access(audio_mgr)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.visible_alpha > 0.3:
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(event.pos):
                            k = btn["label"]
                            if k == "CLR":
                                self.code_buffer = ""
                                if audio_mgr:
                                    audio_mgr.play('hit')
                            elif k == "ENTER":
                                if self.code_buffer == SECRET_CODE:
                                    return self._grant_access(audio_mgr)
                                else:
                                    self._reject_code(audio_mgr)
                            else:
                                self.code_buffer += k
                                if audio_mgr:
                                    audio_mgr.play('shoot')
                                if len(self.code_buffer) > 12:
                                    self.code_buffer = self.code_buffer[-12:]
                                if self.code_buffer == SECRET_CODE:
                                    return self._grant_access(audio_mgr)
                            return True

        return self.unlocked

    def _grant_access(self, audio_mgr) -> bool:
        self.unlocked = True
        self.notification_text = "★ DEV MODE UNLOCKED: LEVEL ITERATOR ACTIVE ★"
        self.notification_timer = 4.0
        self.code_buffer = "AUTHORIZED"
        if audio_mgr:
            audio_mgr.play('super')
            audio_mgr.play('boing')
        if self.on_unlock_callback:
            self.on_unlock_callback()
        return True

    def _reject_code(self, audio_mgr):
        self.notification_text = "ACCESS DENIED: INVALID CODE"
        self.notification_timer = 2.0
        self.code_buffer = ""
        if audio_mgr:
            audio_mgr.play('alarm')

    def draw(self, surface: pygame.Surface):
        # 1. Floating notifications
        if self.notification_timer > 0.0:
            notify_surf = self.font_notify.render(self.notification_text, True, COLOR_CRIT_YELLOW if self.unlocked else (240, 70, 70))
            n_rect = notify_surf.get_rect(center=(SCREEN_WIDTH // 2, 85))
            bg_rect = n_rect.inflate(30, 14)
            pygame.draw.rect(surface, (20, 24, 30), bg_rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if self.unlocked else (200, 50, 50), bg_rect, 2, border_radius=6)
            surface.blit(notify_surf, n_rect)

        # 2. Keypad widget in corner
        if self.visible_alpha <= 0.05:
            return

        alpha_int = int(255 * self.visible_alpha)
        pad_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Background
        pygame.draw.rect(pad_surf, (22, 26, 34, alpha_int), (0, 0, self.rect.width, self.rect.height), border_radius=8)
        pygame.draw.rect(pad_surf, (COLOR_BRASS[0], COLOR_BRASS[1], COLOR_BRASS[2], alpha_int), (0, 0, self.rect.width, self.rect.height), 2, border_radius=8)

        # Header
        hdr_txt = self.font_title.render("MAINTENANCE TERMINAL", True, COLOR_BRASS_HIGHLIGHT)
        pad_surf.blit(hdr_txt, (14, 10))

        # Code Display Box
        disp_rect = pygame.Rect(14, 30, self.rect.width - 28, 28)
        pygame.draw.rect(pad_surf, (10, 12, 16, alpha_int), disp_rect, border_radius=4)
        pygame.draw.rect(pad_surf, (60, 80, 100, alpha_int), disp_rect, 1, border_radius=4)
        
        masked = self.code_buffer if self.unlocked else ("•" * len(self.code_buffer) if self.code_buffer else "_ _ _ _")
        col = (100, 255, 140) if self.unlocked else (255, 220, 120)
        disp_txt = self.font_display.render(masked[-10:], True, col)
        pad_surf.blit(disp_txt, (disp_rect.left + 8, disp_rect.top + 5))

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        rel_mouse = (mouse_pos[0] - self.rect.left, mouse_pos[1] - self.rect.top)
        for btn in self.buttons:
            r = pygame.Rect(btn["rect"].left - self.rect.left, btn["rect"].top - self.rect.top, btn["rect"].width, btn["rect"].height)
            is_hover = r.collidepoint(rel_mouse)
            btn_bg = (38, 48, 62, alpha_int) if is_hover else (28, 34, 44, alpha_int)
            pygame.draw.rect(pad_surf, btn_bg, r, border_radius=4)
            pygame.draw.rect(pad_surf, (COLOR_BRASS_HIGHLIGHT[0], COLOR_BRASS_HIGHLIGHT[1], COLOR_BRASS_HIGHLIGHT[2], alpha_int) if is_hover else (70, 80, 95, alpha_int), r, 1, border_radius=4)
            lbl = self.font_btn.render(btn["label"], True, COLOR_WHITE if is_hover else (190, 205, 220))
            pad_surf.blit(lbl, lbl.get_rect(center=r.center))

        surface.blit(pad_surf, self.rect.topleft)


class LevelIteratorDrawer:
    """Minimalist, clean level iterator drawer for authorized developers.
    
    Allows stepping through Track 1-5 and Car 1-15 during gameplay runs.
    """
    def __init__(self, game):
        self.game = game
        self._is_open = False
        self.selected_track = 0  # 0 to 4
        self.selected_car = 1    # 1 to 15
        
        pygame.font.init()
        self.font_hdr = pygame.font.SysFont("Helvetica, Arial, sans-serif", 15, bold=True)
        self.font_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13, bold=True)
        self.font_tag = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11)

    @property
    def is_open(self) -> bool:
        return self._is_open

    @is_open.setter
    def is_open(self, val: bool):
        self._is_open = val

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    @property
    def selected_track_idx(self) -> int:
        return self.selected_track

    @property
    def selected_car_idx(self) -> int:
        return self.selected_car

    def select_track(self, idx: int):
        self.selected_track = max(0, min(4, int(idx)))

    def select_car(self, car_num: int):
        self.selected_car = max(1, min(15, int(car_num)))

    def deploy_selected(self):
        from src.core.progression import ALL_STAGES
        track_id = ALL_STAGES[self.selected_track]
        weapon = self.game.hub_station.get_selected_weapon()
        self.game.deploy_to_stage_and_car(track_id, self.selected_car - 1, weapon)
        self._is_open = False

    def next_car(self):
        self.skip_to_next_car()

    def prev_car(self):
        self.skip_to_prev_car()

    def open_drawer(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def update(self, dt: float = 0.016):
        pass

    def handle_event(self, event, audio_mgr=None) -> bool:
        if not event:
            return False
        return self.handle_input([event])

    def toggle(self):
        self._is_open = not self._is_open
        if self._is_open and getattr(self.game, "run_manager", None):
            self.selected_track = getattr(self.game.progression, "current_track_idx", 0)
            self.selected_car = getattr(self.game.run_manager, "current_car_index", 0) + 1

    def handle_input(self, events: list[pygame.event.Event]) -> bool:
        """Handle hotkeys [N] for next car, [B] for previous car, and iterator clicks."""
        if not getattr(self.game, "dev_mode", False):
            return False

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Hotkey: [N] for Next Car / Level
                if event.key == pygame.K_n:
                    self.skip_to_next_car()
                    return True
                # Hotkey: [B] for Previous Car
                elif event.key == pygame.K_b and self.game.state == self.game.STATE_PLAYING:
                    self.skip_to_prev_car()
                    return True
                # Toggle drawer: [F1] or [`] when dev mode is active
                elif event.key in (pygame.K_F1, pygame.K_BACKQUOTE):
                    self.toggle()
                    return True
                elif self.is_open and event.key == pygame.K_ESCAPE:
                    self.is_open = False
                    return True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_open:
                    if self._handle_drawer_click(event.pos):
                        return True
                else:
                    # Click on small HUD pill button in top-left
                    pill_rect = pygame.Rect(12, 12, 140, 24)
                    if pill_rect.collidepoint(event.pos):
                        self.toggle()
                        return True

        return self.is_open

    def skip_to_next_car(self):
        """Immediately advances to the next car or starts next level."""
        if self.game.state == self.game.STATE_PLAYING and self.game.run_manager:
            self.game.load_next_train_car()
            self.game.audio.play('door')
        elif self.game.state == self.game.STATE_HUB:
            # Advance track
            self.game.progression.advance_track_on_victory()
            self.game.audio.play('boon')

    def skip_to_prev_car(self):
        """Steps back to the previous car."""
        if self.game.state == self.game.STATE_PLAYING and self.game.run_manager:
            cur = self.game.run_manager.current_car_index
            if cur > 0:
                self.game.warp_to_car(cur - 1)
                self.game.audio.play('door')

    def _handle_drawer_click(self, mouse_pos: tuple[int, int]) -> bool:
        drawer_rect = pygame.Rect(12, 42, 320, 210)
        if not drawer_rect.collidepoint(mouse_pos):
            return False

        # Track selector buttons (1 - 5)
        for i in range(5):
            t_rect = pygame.Rect(drawer_rect.left + 16 + i * 56, drawer_rect.top + 45, 50, 28)
            if t_rect.collidepoint(mouse_pos):
                self.selected_track = i
                return True

        # Car stepper buttons
        minus_rect = pygame.Rect(drawer_rect.left + 16, drawer_rect.top + 115, 36, 28)
        plus_rect = pygame.Rect(drawer_rect.left + 160, drawer_rect.top + 115, 36, 28)
        if minus_rect.collidepoint(mouse_pos):
            self.selected_car = max(1, self.selected_car - 1)
            return True
        elif plus_rect.collidepoint(mouse_pos):
            self.selected_car = min(15, self.selected_car + 1)
            return True

        # Quick Car Jump Presets
        p1 = pygame.Rect(drawer_rect.left + 210, drawer_rect.top + 115, 44, 28)
        p5 = pygame.Rect(drawer_rect.left + 260, drawer_rect.top + 115, 44, 28)
        if p1.collidepoint(mouse_pos):
            self.selected_car = 1
            return True
        elif p5.collidepoint(mouse_pos):
            self.selected_car = 5
            return True

        # Warp Button
        warp_rect = pygame.Rect(drawer_rect.left + 16, drawer_rect.top + 160, drawer_rect.width - 32, 34)
        if warp_rect.collidepoint(mouse_pos):
            from src.core.progression import ALL_STAGES
            track_id = ALL_STAGES[self.selected_track]
            weapon = self.game.hub_station.get_selected_weapon()
            self.game.deploy_to_stage_and_car(track_id, self.selected_car - 1, weapon)
            self.is_open = False
            return True

        return True

    def draw(self, surface: pygame.Surface):
        if not getattr(self.game, "dev_mode", False):
            return

        # 1. Top-Left Dev Mode Pill (Clickable)
        pill_rect = pygame.Rect(12, 12, 140, 24)
        pygame.draw.rect(surface, (20, 28, 36), pill_rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, pill_rect, 1, border_radius=12)
        pill_txt = self.font_tag.render("⚡ DEV: [N] SKIP CAR", True, COLOR_CRIT_YELLOW)
        surface.blit(pill_txt, pill_txt.get_rect(center=pill_rect.center))

        # 2. Drawer Modal if open
        if not self.is_open:
            return

        drawer_rect = pygame.Rect(12, 42, 320, 210)
        pygame.draw.rect(surface, (18, 22, 30), drawer_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_BRASS, drawer_rect, 2, border_radius=8)

        # Header
        hdr = self.font_hdr.render("LEVEL ITERATOR (DEV MODE)", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(hdr, (drawer_rect.left + 14, drawer_rect.top + 12))

        # Track selector row
        for i in range(5):
            t_rect = pygame.Rect(drawer_rect.left + 16 + i * 56, drawer_rect.top + 45, 50, 28)
            active = (i == self.selected_track)
            pygame.draw.rect(surface, (40, 60, 80) if active else (24, 30, 40), t_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if active else (60, 75, 90), t_rect, 1, border_radius=4)
            lbl = self.font_btn.render(f"T{i+1}", True, COLOR_WHITE if active else (160, 175, 190))
            surface.blit(lbl, lbl.get_rect(center=t_rect.center))

        # Car Stepper
        lbl_car = self.font_tag.render(f"CAR: {self.selected_car} / 15", True, COLOR_WHITE)
        surface.blit(lbl_car, (drawer_rect.left + 65, drawer_rect.top + 122))
        
        minus_rect = pygame.Rect(drawer_rect.left + 16, drawer_rect.top + 115, 36, 28)
        plus_rect = pygame.Rect(drawer_rect.left + 160, drawer_rect.top + 115, 36, 28)
        pygame.draw.rect(surface, (28, 36, 48), minus_rect, border_radius=4)
        pygame.draw.rect(surface, (28, 36, 48), plus_rect, border_radius=4)
        surface.blit(self.font_btn.render("-", True, COLOR_WHITE), minus_rect.move(14, 5))
        surface.blit(self.font_btn.render("+", True, COLOR_WHITE), plus_rect.move(13, 5))

        # Quick Car Presets
        p1 = pygame.Rect(drawer_rect.left + 210, drawer_rect.top + 115, 44, 28)
        p5 = pygame.Rect(drawer_rect.left + 260, drawer_rect.top + 115, 44, 28)
        pygame.draw.rect(surface, (28, 36, 48), p1, border_radius=4)
        pygame.draw.rect(surface, (28, 36, 48), p5, border_radius=4)
        surface.blit(self.font_tag.render("C1", True, (180, 200, 220)), p1.move(14, 7))
        surface.blit(self.font_tag.render("C5", True, (180, 200, 220)), p5.move(14, 7))

        # Warp Action Button
        warp_rect = pygame.Rect(drawer_rect.left + 16, drawer_rect.top + 160, drawer_rect.width - 32, 34)
        pygame.draw.rect(surface, (30, 80, 50), warp_rect, border_radius=6)
        pygame.draw.rect(surface, (80, 220, 130), warp_rect, 1, border_radius=6)
        warp_txt = self.font_btn.render(f"WARP TO TRACK {self.selected_track+1} - CAR {self.selected_car}", True, COLOR_WHITE)
        surface.blit(warp_txt, warp_txt.get_rect(center=warp_rect.center))
