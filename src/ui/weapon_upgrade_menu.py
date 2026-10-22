"""Arsenal Weapon Upgrade & Selection Workshop Modal."""
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, COLOR_WHITE,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_CRIT_YELLOW,
    COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_EMBER_ORANGE, COLOR_LIGHTNING_CYAN
)
from src.core.progression import WEAPON_UPGRADE_DEFINITIONS

class WeaponUpgradeMenu:
    """Modal dialog allowing players to inspect, equip, and upgrade weapons using Weapon Tokens."""
    def __init__(self, progression):
        self.progression = progression
        self._is_open = False
        self.selected_weapon_id = "rivet_gun"
        self.notification_msg = ""
        self.notification_timer = 0.0

        pygame.font.init()
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 24, bold=True)
        self.font_subtitle = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13)
        self.font_name = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)
        self.font_rank = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_desc = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12)
        self.font_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13, bold=True)

        self.card_rects = {}
        self.upgrade_btn_rects = {}
        self.equip_btn_rects = {}

    @property
    def is_open(self) -> bool:
        return self._is_open

    @is_open.setter
    def is_open(self, val: bool):
        self._is_open = val

    def show(self):
        self._is_open = True
        self.notification_msg = ""

    def open(self):
        self.show()

    def hide(self):
        self._is_open = False

    def close(self):
        self.hide()

    def update(self, dt: float = 0.016):
        if self.notification_timer > 0.0:
            self.notification_timer = max(0.0, self.notification_timer - dt)

    def handle_event(self, event_or_events, hub_station=None, audio_mgr=None) -> bool:
        events = event_or_events if isinstance(event_or_events, list) else [event_or_events]
        return self.handle_input(events, hub_station, audio_mgr)

    def handle_input(self, events: list[pygame.event.Event], hub_station=None, audio_mgr=None) -> bool:
        """Handle clicks and keys within the weapon upgrade modal. Returns True if handled."""
        if not self._is_open:
            return False

        weapons_keys = ["rivet_gun", "stoker_wrench", "coal_scattergun", "tesla_arc_caster"]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_e):
                    self.hide()
                    return True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Close button
                close_rect = pygame.Rect(SCREEN_WIDTH // 2 + 390, 80, 36, 36)
                if close_rect.collidepoint(event.pos):
                    self.hide()
                    return True

                # Card selection
                for w_id, r in self.card_rects.items():
                    if r.collidepoint(event.pos):
                        self.selected_weapon_id = w_id

                # Equip buttons
                for w_id, btn_r in self.equip_btn_rects.items():
                    if btn_r.collidepoint(event.pos):
                        self.progression.equipped_weapon_id = w_id
                        self.selected_weapon_id = w_id
                        if hub_station and hasattr(hub_station, "_set_weapon"):
                            idx = weapons_keys.index(w_id)
                            hub_station._set_weapon(idx)
                        if audio_mgr:
                            audio_mgr.play('door')
                        return True

                # Upgrade buttons
                for w_id, btn_r in self.upgrade_btn_rects.items():
                    if btn_r.collidepoint(event.pos):
                        if self.progression.can_upgrade_weapon(w_id):
                            self.progression.upgrade_weapon(w_id)
                            if hub_station and hasattr(hub_station, "_set_weapon"):
                                hub_station._set_weapon(hub_station.selected_weapon_idx)
                            self.notification_msg = f"★ {WEAPON_UPGRADE_DEFINITIONS[w_id]['name'].upper()} UPGRADED! ★"
                            self.notification_timer = 3.0
                            if audio_mgr:
                                audio_mgr.play('super')
                                audio_mgr.play('boing')
                        else:
                            if self.progression.weapon_tokens < 1:
                                self.notification_msg = "NEED 1 WEAPON TOKEN (EARN BY FULLY CLEARING A 15-CAR EXPEDITION!)"
                                self.notification_timer = 2.5
                                if audio_mgr:
                                    audio_mgr.play('alarm')
                        return True

        return True

    def draw(self, surface: pygame.Surface, active_weapon_idx: int = None):
        if not self._is_open:
            return

        weapons_keys = ["rivet_gun", "stoker_wrench", "coal_scattergun", "tesla_arc_caster"]
        if active_weapon_idx is None:
            cur_eq = getattr(self.progression, "equipped_weapon_id", "rivet_gun")
            active_weapon_idx = weapons_keys.index(cur_eq) if cur_eq in weapons_keys else 0

        # Dim overlay
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((10, 12, 16, 215))
        surface.blit(dim, (0, 0))

        # Main Modal Frame
        modal_w, modal_h = 880, 560
        modal_rect = pygame.Rect((SCREEN_WIDTH - modal_w) // 2, (SCREEN_HEIGHT - modal_h) // 2, modal_w, modal_h)
        pygame.draw.rect(surface, (20, 24, 32), modal_rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS, modal_rect, 2, border_radius=12)

        # Header Title
        title_surf = self.font_title.render("ARMORY WEAPON UPGRADE WORKSHOP", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(title_surf, (modal_rect.left + 30, modal_rect.top + 20))

        tokens_txt = f"WEAPON TOKENS: {self.progression.weapon_tokens}"
        tok_surf = self.font_title.render(tokens_txt, True, COLOR_CRIT_YELLOW)
        surface.blit(tok_surf, (modal_rect.right - 260, modal_rect.top + 20))

        sub_txt = self.font_subtitle.render("Full track completions award 1 Weapon Token. Each upgrade permanently unlocks game-changing perks.", True, (160, 180, 200))
        surface.blit(sub_txt, (modal_rect.left + 30, modal_rect.top + 52))

        # Notification banner
        if self.notification_timer > 0.0:
            notif = self.font_rank.render(self.notification_msg, True, COLOR_CRIT_YELLOW if "UPGRADED" in self.notification_msg else (240, 80, 80))
            surface.blit(notif, (modal_rect.left + 30, modal_rect.top + 72))

        # Close button [X]
        close_rect = pygame.Rect(modal_rect.right - 45, modal_rect.top + 16, 28, 28)
        pygame.draw.rect(surface, (45, 20, 25), close_rect, border_radius=4)
        pygame.draw.rect(surface, (200, 70, 80), close_rect, 1, border_radius=4)
        x_surf = self.font_name.render("X", True, COLOR_WHITE)
        surface.blit(x_surf, x_surf.get_rect(center=close_rect.center))

        # Render 4 weapon cards (2 columns x 2 rows)
        weapons_keys = ["rivet_gun", "stoker_wrench", "coal_scattergun", "tesla_arc_caster"]
        card_w, card_h = 400, 205
        spacing_x, spacing_y = 20, 18
        start_x = modal_rect.left + 30
        start_y = modal_rect.top + 98

        self.card_rects.clear()
        self.upgrade_btn_rects.clear()
        self.equip_btn_rects.clear()

        mouse_pos = pygame.mouse.get_pos()

        for idx, w_id in enumerate(weapons_keys):
            w_data = WEAPON_UPGRADE_DEFINITIONS[w_id]
            rank = self.progression.get_weapon_rank(w_id)
            is_equipped = (idx == active_weapon_idx)

            col = idx % 2
            row = idx // 2
            cx = start_x + col * (card_w + spacing_x)
            cy = start_y + row * (card_h + spacing_y)
            c_rect = pygame.Rect(cx, cy, card_w, card_h)
            self.card_rects[w_id] = c_rect

            # Card background
            bg_col = (28, 34, 46) if is_equipped else (22, 26, 34)
            pygame.draw.rect(surface, bg_col, c_rect, border_radius=8)
            border_col = COLOR_BRASS_HIGHLIGHT if is_equipped else ((60, 90, 120) if rank > 1 else (40, 50, 65))
            pygame.draw.rect(surface, border_col, c_rect, 2 if is_equipped else 1, border_radius=8)

            # Name & Icon
            w_name = self.font_name.render(f"{w_data['icon']} {w_data['name'].upper()}", True, COLOR_WHITE)
            surface.blit(w_name, (c_rect.left + 14, c_rect.top + 12))

            # Rank Diamonds
            diamond_x = c_rect.left + 14
            for r_idx in range(1, 6):
                active_diamond = (r_idx <= rank)
                d_rect = pygame.Rect(diamond_x, c_rect.top + 38, 14, 14)
                pygame.draw.rect(surface, COLOR_CRIT_YELLOW if active_diamond else (40, 48, 60), d_rect, border_radius=2)
                pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if active_diamond else (60, 70, 85), d_rect, 1, border_radius=2)
                diamond_x += 18

            rank_lbl = self.font_rank.render(f"RANK {rank}/5", True, COLOR_CRIT_YELLOW if rank >= 5 else COLOR_BRASS_HIGHLIGHT)
            surface.blit(rank_lbl, (diamond_x + 8, c_rect.top + 38))

            # Current Rank Perk info
            cur_info = w_data["ranks"].get(rank, {})
            p_title = self.font_rank.render(f"Current: {cur_info.get('title', '')}", True, (255, 230, 150))
            surface.blit(p_title, (c_rect.left + 14, c_rect.top + 62))
            p_desc = self.font_desc.render(cur_info.get('desc', ''), True, (200, 210, 225))
            surface.blit(p_desc, (c_rect.left + 14, c_rect.top + 80))

            # Next Rank Perk preview
            if rank < 5:
                next_info = w_data["ranks"].get(rank + 1, {})
                nxt_title = self.font_rank.render(f"Next: {next_info.get('title', '')} — {next_info.get('bonus', '')}", True, (130, 220, 170))
                surface.blit(nxt_title, (c_rect.left + 14, c_rect.top + 104))
                nxt_desc = self.font_desc.render(next_info.get('desc', ''), True, (150, 175, 190))
                surface.blit(nxt_desc, (c_rect.left + 14, c_rect.top + 122))
            else:
                max_txt = self.font_rank.render("★ MAXIMUM WEAPON MASTERY REACHED ★", True, COLOR_CRIT_YELLOW)
                surface.blit(max_txt, (c_rect.left + 14, c_rect.top + 110))

            # Buttons: [EQUIP] & [UPGRADE (1 TOKEN)]
            btn_y = c_rect.bottom - 42
            equip_rect = pygame.Rect(c_rect.left + 14, btn_y, 110, 30)
            self.equip_btn_rects[w_id] = equip_rect
            eq_hover = equip_rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (40, 75, 55) if is_equipped else ((38, 48, 65) if eq_hover else (26, 32, 42)), equip_rect, border_radius=4)
            pygame.draw.rect(surface, (90, 230, 140) if is_equipped else (COLOR_BRASS_HIGHLIGHT if eq_hover else (60, 75, 95)), equip_rect, 1, border_radius=4)
            eq_str = "EQUIPPED" if is_equipped else "EQUIP"
            eq_txt = self.font_btn.render(eq_str, True, COLOR_WHITE if is_equipped or eq_hover else (170, 190, 210))
            surface.blit(eq_txt, eq_txt.get_rect(center=equip_rect.center))

            if rank < 5:
                can_upg = self.progression.can_upgrade_weapon(w_id)
                upg_rect = pygame.Rect(c_rect.right - 180, btn_y, 166, 30)
                self.upgrade_btn_rects[w_id] = upg_rect
                upg_hover = upg_rect.collidepoint(mouse_pos)
                upg_bg = (45, 90, 60) if (can_upg and upg_hover) else ((30, 60, 42) if can_upg else (28, 28, 34))
                pygame.draw.rect(surface, upg_bg, upg_rect, border_radius=4)
                pygame.draw.rect(surface, (100, 255, 160) if can_upg else (55, 55, 65), upg_rect, 1, border_radius=4)
                u_str = "UPGRADE (1 TOKEN)" if can_upg else "1 TOKEN NEEDED"
                u_txt = self.font_btn.render(u_str, True, COLOR_WHITE if can_upg else (120, 120, 130))
                surface.blit(u_txt, u_txt.get_rect(center=upg_rect.center))
