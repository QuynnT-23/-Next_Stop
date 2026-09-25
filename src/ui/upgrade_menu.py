"""Upgrade drafting modal displaying 3 randomized Boons or Level-Ups (Hades style)."""
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_STEEL_DARK, COLOR_STEEL_MID,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_WHITE, COLOR_CRIT_YELLOW
)
from src.combat.boons import Boon, get_synergy_preview_for_boon

class UpgradeMenu:
    """Renders 3 draftable boon or level-up cards and handles player selection."""
    def __init__(self):
        pygame.font.init()
        self.font_header = pygame.font.SysFont("Helvetica, Arial, sans-serif", 28, bold=True)
        self.font_card_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 20, bold=True)
        self.font_tag = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13, bold=True)
        self.font_upgrade_badge = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_synergy_badge = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_desc = pygame.font.SysFont("Helvetica, Arial, sans-serif", 15)
        self.font_key = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)
        
        self.active_choices: list[Boon] = []
        self.card_rects: list[pygame.Rect] = []
        self.hovered_index = -1
        self.owned_ids: set[str] = set()
        self.existing_boons: list[Boon] = []

    def open(self, choices: list[Boon], owned_ids: set[str] = None, existing_boons: list[Boon] = None):
        self.active_choices = choices
        self.owned_ids = owned_ids if owned_ids else set()
        self.existing_boons = existing_boons if existing_boons else []
        self.hovered_index = -1
        
        # 3 cards centered on screen
        card_w = 330
        card_h = 440
        gap = 35
        total_w = len(choices) * card_w + (len(choices) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = (SCREEN_HEIGHT - card_h) // 2 + 25

        self.card_rects = [
            pygame.Rect(start_x + i * (card_w + gap), start_y, card_w, card_h)
            for i in range(len(choices))
        ]

    def update(self, input_handler) -> Boon | None:
        mouse_pos = input_handler.mouse_pos
        self.hovered_index = -1
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_index = i

        # Mouse click selection
        if input_handler.attack_pressed and self.hovered_index >= 0:
            chosen = self.active_choices[self.hovered_index]
            return chosen

        # Keyboard number selection (1, 2, 3)
        for key in input_handler.num_keys_pressed:
            idx = key - 1
            if 0 <= idx < len(self.active_choices):
                return self.active_choices[idx]

        return None

    def draw(self, surface: pygame.Surface):
        # 1. Dark backdrop overlay
        backdrop = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        backdrop.fill((10, 12, 16, 220))
        surface.blit(backdrop, (0, 0))

        # 2. Header Title
        title_surf = self.font_header.render("TRAIN CAR SECURED — UPGRADE ARSENAL", True, COLOR_BRASS_HIGHLIGHT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 75))
        surface.blit(title_surf, title_rect)

        sub_surf = self.font_tag.render("Select a new synergy or enhance your existing abilities with [1], [2], [3] or Click", True, (180, 190, 205))
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 108))
        surface.blit(sub_surf, sub_rect)

        # 3. Draw Cards
        for i, (boon, rect) in enumerate(zip(self.active_choices, self.card_rects)):
            is_hovered = (i == self.hovered_index)
            is_upgrade = (boon.id in self.owned_ids)
            draw_rect = rect.inflate(10, 10) if is_hovered else rect

            # Distinct Rarity Theming
            rarity = boon.rarity
            if rarity == "Legendary":
                card_bg = (38, 28, 12)
                pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
                border_col = (int(225 + 30 * pulse), int(190 + 30 * pulse), 40) if is_hovered else (215, 175, 35)
                border_w = 4 if is_hovered else 3
                rarity_badge_str = "[** LEGENDARY **]"
            elif rarity == "Epic":
                card_bg = (30, 18, 44)
                border_col = (215, 100, 255) if is_hovered else (150, 55, 190)
                border_w = 3 if is_hovered else 2
                rarity_badge_str = "[== EPIC ==]"
            elif rarity == "Rare":
                card_bg = (16, 26, 42)
                border_col = (80, 220, 255) if is_hovered else (45, 125, 175)
                border_w = 3 if is_hovered else 2
                rarity_badge_str = "[+ RARE +]"
            else:  # Common
                card_bg = (24, 26, 32)
                border_col = (195, 205, 225) if is_hovered else (85, 95, 110)
                border_w = 2
                rarity_badge_str = "[ COMMON ]"

            # Card Background
            pygame.draw.rect(surface, card_bg, draw_rect, border_radius=12)
            
            # Card Border
            if is_upgrade and is_hovered:
                border_col = COLOR_BRASS_HIGHLIGHT
                border_w = 4
            pygame.draw.rect(surface, border_col, draw_rect, border_w, border_radius=12)

            # Legendary / Epic Corner Accents
            if rarity in ["Legendary", "Epic"]:
                c_sz = 14
                # Top left corner bracket
                pygame.draw.line(surface, border_col, (draw_rect.x + 8, draw_rect.y + 8), (draw_rect.x + 8 + c_sz, draw_rect.y + 8), 2)
                pygame.draw.line(surface, border_col, (draw_rect.x + 8, draw_rect.y + 8), (draw_rect.x + 8, draw_rect.y + 8 + c_sz), 2)
                # Top right corner bracket
                pygame.draw.line(surface, border_col, (draw_rect.right - 8, draw_rect.y + 8), (draw_rect.right - 8 - c_sz, draw_rect.y + 8), 2)
                pygame.draw.line(surface, border_col, (draw_rect.right - 8, draw_rect.y + 8), (draw_rect.right - 8, draw_rect.y + 8 + c_sz), 2)

            # Card Header Type Badge (UPGRADE vs DUO SYNERGY vs NEW BOON)
            syn_preview = get_synergy_preview_for_boon(boon.id, self.existing_boons)
            if is_upgrade:
                badge_text = f"[+] UPGRADE: TIER {boon.level} -> {boon.level + 1}"
                badge_col = COLOR_CRIT_YELLOW
            elif syn_preview:
                badge_text = f"[!] DUO SYNERGY: {syn_preview['name'].upper()}!"
                badge_col = (255, 185, 60)
            else:
                badge_text = "[ NEW ABILITY ]"
                badge_col = (100, 240, 150)

            badge_surf = self.font_upgrade_badge.render(badge_text, True, badge_col)
            surface.blit(badge_surf, (draw_rect.x + 20, draw_rect.y + 18))

            # Rarity & Tag Header with custom badge
            rarity_str = f"{rarity_badge_str}  --  {boon.tag.upper()}"
            rarity_surf = self.font_tag.render(rarity_str, True, boon.color)
            surface.blit(rarity_surf, (draw_rect.x + 20, draw_rect.y + 38))

            # Boon Name with stars
            name_str = boon.get_display_name() if is_upgrade else boon.name
            name_surf = self.font_card_title.render(name_str, True, COLOR_WHITE)
            surface.blit(name_surf, (draw_rect.x + 20, draw_rect.y + 60))

            # Horizontal divider
            pygame.draw.line(surface, COLOR_STEEL_MID, (draw_rect.x + 20, draw_rect.y + 92), (draw_rect.right - 20, draw_rect.y + 92), 1)

            # Synergy Icon / Sigil
            icon_center = (draw_rect.centerx, draw_rect.y + 145)
            pygame.draw.circle(surface, COLOR_STEEL_DARK, icon_center, 34)
            pygame.draw.circle(surface, boon.color, icon_center, 30, 3)
            pygame.draw.circle(surface, boon.color, icon_center, 10)

            # If synergy preview available, render synergy callout banner
            desc_y = draw_rect.y + 195
            if syn_preview:
                syn_callout = f"[*] Combines with {syn_preview['tag']}: {syn_preview['name']}"
                syn_surf = self.font_synergy_badge.render(syn_callout, True, (255, 210, 80))
                surface.blit(syn_surf, (draw_rect.x + 20, desc_y))
                desc_y += 20

            # Description (shows upgrade preview if upgrading)
            desc_text = boon.get_upgrade_description() if is_upgrade else boon.description
            self._render_wrapped_text(surface, desc_text, draw_rect.x + 20, desc_y, draw_rect.width - 40)

            # Hotkey Prompt at Bottom
            key_bg = pygame.Rect(draw_rect.centerx - 50, draw_rect.bottom - 46, 100, 30)
            pygame.draw.rect(surface, COLOR_STEEL_DARK, key_bg, border_radius=6)
            pygame.draw.rect(surface, COLOR_BRASS if is_hovered else COLOR_STEEL_MID, key_bg, 1, border_radius=6)
            key_text = self.font_key.render(f"PRESS [{i + 1}]", True, COLOR_BRASS_HIGHLIGHT if is_hovered else COLOR_WHITE)
            key_rect = key_text.get_rect(center=key_bg.center)
            surface.blit(key_text, key_rect)

    def _render_wrapped_text(self, surface: pygame.Surface, text: str, x: int, y: int, max_width: int):
        words = text.split(' ')
        line = []
        cur_y = y
        line_height = 21

        for word in words:
            test_line = ' '.join(line + [word])
            w, _ = self.font_desc.size(test_line)
            if w <= max_width:
                line.append(word)
            else:
                rendered = self.font_desc.render(' '.join(line), True, (220, 225, 235))
                surface.blit(rendered, (x, cur_y))
                cur_y += line_height
                line = [word]

        if line:
            rendered = self.font_desc.render(' '.join(line), True, (220, 225, 235))
            surface.blit(rendered, (x, cur_y))
