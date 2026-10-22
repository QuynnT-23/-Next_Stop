"""Detailed roguelite upgrade drafting modal with elemental synergy detection and inventory inspector."""
import math
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_STEEL_DARK, COLOR_STEEL_MID,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_WHITE, COLOR_CRIT_YELLOW
)
from src.combat.boons import Boon, get_synergy_preview_for_boon, get_active_synergies

ELEMENT_COLORS = {
    "ELECTRIC": (80, 220, 255),
    "PYRO": (255, 110, 40),
    "CRYO": (150, 235, 255),
    "KINETIC": (230, 200, 90),
    "ALCHEMICAL": (80, 235, 140),
    "DEFENSIVE": (175, 190, 210),
    "MOBILITY": (120, 250, 200),
}

class UpgradeMenu:
    """Renders 3 draftable boon cards with rich stat metrics and an in-draft inventory inspector."""
    def __init__(self):
        pygame.font.init()
        self.font_header = pygame.font.SysFont("Helvetica, Arial, sans-serif", 26, bold=True)
        self.font_card_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 19, bold=True)
        self.font_tag = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_stat_label = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11, bold=True)
        self.font_stat_val = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11)
        self.font_upgrade_badge = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_synergy_badge = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11, bold=True)
        self.font_desc = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13)
        self.font_key = pygame.font.SysFont("Helvetica, Arial, sans-serif", 15, bold=True)
        self.font_tab_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)

        self.active_choices: list[Boon] = []
        self.card_rects: list[pygame.Rect] = []
        self.hovered_index = -1
        self.owned_ids: set[str] = set()
        self.existing_boons: list[Boon] = []
        
        # In-draft inventory inspector state
        self.show_inspector = False
        self.inspector_btn_rect = pygame.Rect(SCREEN_WIDTH - 240, 68, 210, 28)

    def open(self, choices: list[Boon], owned_ids: set[str] = None, existing_boons: list[Boon] = None):
        self.active_choices = choices
        self.owned_ids = owned_ids if owned_ids else set()
        self.existing_boons = existing_boons if existing_boons else []
        self.hovered_index = -1
        self.show_inspector = False

        card_w = 340
        card_h = 470
        gap = 30
        total_w = len(choices) * card_w + (len(choices) - 1) * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = (SCREEN_HEIGHT - card_h) // 2 + 30

        self.card_rects = [
            pygame.Rect(start_x + i * (card_w + gap), start_y, card_w, card_h)
            for i in range(len(choices))
        ]

    def update(self, input_handler) -> Boon | None:
        mouse_pos = input_handler.mouse_pos
        self.hovered_index = -1

        # Check Tab key or inspector button toggle
        if hasattr(input_handler, "tab_pressed") and input_handler.tab_pressed:
            self.show_inspector = not self.show_inspector
            input_handler.tab_pressed = False

        # Mouse click on inspector toggle button
        if input_handler.attack_pressed and self.inspector_btn_rect.collidepoint(mouse_pos):
            self.show_inspector = not self.show_inspector
            return None

        if self.show_inspector:
            # While inspector is open, clicking anywhere or pressing TAB closes it
            if input_handler.attack_pressed and not self.inspector_btn_rect.collidepoint(mouse_pos):
                self.show_inspector = False
            return None

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
        backdrop.fill((10, 12, 16, 225))
        surface.blit(backdrop, (0, 0))

        # 2. Header Title
        title_surf = self.font_header.render("TRAIN CAR SECURED — UPGRADE ARSENAL", True, COLOR_BRASS_HIGHLIGHT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        surface.blit(title_surf, title_rect)

        sub_surf = self.font_tag.render("Select a new synergy or enhance your existing abilities with [1], [2], [3] or Click", True, (180, 195, 215))
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 88)))

        # 3. Inventory Inspector Pill Button (Top Right)
        mouse_pos = pygame.mouse.get_pos()
        hover_insp = self.inspector_btn_rect.collidepoint(mouse_pos)
        insp_bg = (40, 60, 50) if self.show_inspector else ((32, 40, 52) if hover_insp else (22, 28, 38))
        pygame.draw.rect(surface, insp_bg, self.inspector_btn_rect, border_radius=14)
        border_c = (110, 240, 160) if self.show_inspector else (COLOR_BRASS_HIGHLIGHT if hover_insp else (70, 90, 120))
        pygame.draw.rect(surface, border_c, self.inspector_btn_rect, 1, border_radius=14)
        insp_lbl = self.font_tab_btn.render("✦ [TAB] INVENTORY & SYNERGIES", True, (180, 255, 210) if self.show_inspector else COLOR_WHITE)
        surface.blit(insp_lbl, insp_lbl.get_rect(center=self.inspector_btn_rect.center))

        # If Inspector is active, draw the full Inventory & Synergies drawer
        if self.show_inspector:
            self._draw_inventory_inspector(surface)
            return

        # 4. Draw Cards
        for i, (boon, rect) in enumerate(zip(self.active_choices, self.card_rects)):
            is_hovered = (i == self.hovered_index)
            is_upgrade = (boon.id in self.owned_ids)
            draw_rect = rect.inflate(8, 8) if is_hovered else rect

            # Rarity theme
            rarity = boon.rarity
            if rarity == "Legendary":
                card_bg = (38, 28, 12)
                pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
                border_col = (int(225 + 30 * pulse), int(190 + 30 * pulse), 40) if is_hovered else (215, 175, 35)
                border_w = 4 if is_hovered else 3
                rarity_str = "LEGENDARY"
            elif rarity == "Epic":
                card_bg = (30, 18, 44)
                border_col = (215, 100, 255) if is_hovered else (150, 55, 190)
                border_w = 3 if is_hovered else 2
                rarity_str = "EPIC"
            elif rarity == "Rare":
                card_bg = (16, 26, 42)
                border_col = (80, 220, 255) if is_hovered else (45, 125, 175)
                border_w = 3 if is_hovered else 2
                rarity_str = "RARE"
            else:
                card_bg = (24, 26, 32)
                border_col = (195, 205, 225) if is_hovered else (85, 95, 110)
                border_w = 2
                rarity_str = "COMMON"

            # Draw card surface
            pygame.draw.rect(surface, card_bg, draw_rect, border_radius=12)
            if is_upgrade and is_hovered:
                border_col = COLOR_BRASS_HIGHLIGHT
                border_w = 4
            pygame.draw.rect(surface, border_col, draw_rect, border_w, border_radius=12)

            # Element badge at top right
            elem = getattr(boon, "element", "KINETIC").upper()
            elem_color = ELEMENT_COLORS.get(elem, (200, 200, 200))
            elem_rect = pygame.Rect(draw_rect.right - 95, draw_rect.top + 14, 80, 20)
            pygame.draw.rect(surface, (20, 25, 35), elem_rect, border_radius=4)
            pygame.draw.rect(surface, elem_color, elem_rect, 1, border_radius=4)
            elem_surf = self.font_tag.render(elem, True, elem_color)
            surface.blit(elem_surf, elem_surf.get_rect(center=elem_rect.center))

            # Tier diamonds
            dia_str = ""
            for t in range(1, boon.max_level + 1):
                dia_str += "◆ " if t <= boon.level else "◇ "
            dia_surf = self.font_tag.render(dia_str.strip(), True, COLOR_BRASS_HIGHLIGHT)
            surface.blit(dia_surf, (draw_rect.left + 16, draw_rect.top + 14))

            # Upgrade / Synergy badge
            syn_preview = get_synergy_preview_for_boon(boon.id, self.existing_boons)
            if is_upgrade:
                badge_text = f"★ UPGRADE TO TIER {boon.level + 1}"
                badge_col = COLOR_CRIT_YELLOW
            elif syn_preview:
                badge_text = f"✦ SYNERGY: {syn_preview['name'].upper()}!"
                badge_col = (255, 185, 60)
            else:
                badge_text = f"✦ NEW {rarity_str} ABILITY"
                badge_col = (100, 240, 150)
            b_surf = self.font_upgrade_badge.render(badge_text, True, badge_col)
            surface.blit(b_surf, (draw_rect.left + 16, draw_rect.top + 34))

            # Boon Name
            name_str = boon.name
            name_surf = self.font_card_title.render(name_str, True, COLOR_WHITE)
            surface.blit(name_surf, (draw_rect.left + 16, draw_rect.top + 56))

            # Divider line
            pygame.draw.line(surface, COLOR_STEEL_MID, (draw_rect.left + 16, draw_rect.top + 84), (draw_rect.right - 16, draw_rect.top + 84), 1)

            # Description (upgrade or base)
            desc_text = boon.get_upgrade_description() if is_upgrade else boon.description
            self._render_wrapped_text(surface, desc_text, draw_rect.left + 16, draw_rect.top + 94, draw_rect.width - 32)

            # Structured Stat Metrics Box
            stat_box = pygame.Rect(draw_rect.left + 14, draw_rect.top + 175, draw_rect.width - 28, 105)
            pygame.draw.rect(surface, (18, 22, 30), stat_box, border_radius=6)
            pygame.draw.rect(surface, (45, 55, 75), stat_box, 1, border_radius=6)
            
            # Box title
            sb_title = self.font_stat_label.render("TECHNICAL SPECIFICATIONS & SCALING", True, COLOR_BRASS)
            surface.blit(sb_title, (stat_box.left + 10, stat_box.top + 8))
            
            stats = boon.get_stat_breakdown() if hasattr(boon, "get_stat_breakdown") else [("Tier", f"T{boon.level}/{boon.max_level}")]
            sy = stat_box.top + 28
            for label, val in stats[:3]:
                lbl_s = self.font_stat_label.render(label, True, (170, 190, 215))
                val_s = self.font_stat_val.render(val, True, (240, 240, 240))
                surface.blit(lbl_s, (stat_box.left + 10, sy))
                surface.blit(val_s, (stat_box.right - 10 - val_s.get_width(), sy))
                sy += 22

            # Duo Synergy Banner Callout
            if syn_preview:
                syn_rect = pygame.Rect(draw_rect.left + 14, draw_rect.top + 290, draw_rect.width - 28, 48)
                pygame.draw.rect(surface, (36, 28, 16), syn_rect, border_radius=6)
                pygame.draw.rect(surface, (255, 170, 50), syn_rect, 1, border_radius=6)
                syn_title = self.font_synergy_badge.render(f"DUO: {syn_preview['name']}", True, (255, 200, 70))
                surface.blit(syn_title, (syn_rect.left + 8, syn_rect.top + 6))
                syn_sub = self.font_stat_val.render(syn_preview.get("description", "")[:50] + "...", True, (220, 220, 220))
                surface.blit(syn_sub, (syn_rect.left + 8, syn_rect.top + 26))

            # Hotkey Selection Button at Bottom
            key_bg = pygame.Rect(draw_rect.centerx - 65, draw_rect.bottom - 46, 130, 32)
            pygame.draw.rect(surface, (35, 42, 54), key_bg, border_radius=6)
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if is_hovered else COLOR_BRASS, key_bg, 2 if is_hovered else 1, border_radius=6)
            key_text = self.font_key.render(f"SELECT [{i + 1}]", True, COLOR_BRASS_HIGHLIGHT if is_hovered else COLOR_WHITE)
            surface.blit(key_text, key_text.get_rect(center=key_bg.center))

    def _draw_inventory_inspector(self, surface: pygame.Surface):
        """Draws full-screen modal showing all currently owned boons and active synergies."""
        insp_rect = pygame.Rect(120, 110, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 170)
        pygame.draw.rect(surface, (18, 22, 30), insp_rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS, insp_rect, 2, border_radius=12)

        # Title
        i_title = self.font_header.render("★ ACTIVE LOADOUT & SYNERGY MATRIX ★", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(i_title, i_title.get_rect(center=(insp_rect.centerx, insp_rect.top + 30)))

        # Close hint
        c_hint = self.font_tag.render("[PRESS TAB OR CLICK ANYWHERE TO RETURN TO DRAFT]", True, (160, 180, 205))
        surface.blit(c_hint, c_hint.get_rect(center=(insp_rect.centerx, insp_rect.top + 55)))

        # 1. Owned Boons Column (Left)
        b_area = pygame.Rect(insp_rect.left + 25, insp_rect.top + 75, (insp_rect.width - 65) // 2, insp_rect.height - 95)
        pygame.draw.rect(surface, (24, 28, 38), b_area, border_radius=8)
        pygame.draw.rect(surface, (50, 65, 85), b_area, 1, border_radius=8)
        b_hdr = self.font_card_title.render("EQUIPPED BOONS", True, COLOR_WHITE)
        surface.blit(b_hdr, (b_area.left + 16, b_area.top + 14))

        if not self.existing_boons:
            empty_lbl = self.font_desc.render("No boons equipped yet. Draft your first upgrade!", True, (140, 155, 175))
            surface.blit(empty_lbl, (b_area.left + 16, b_area.top + 50))
        else:
            by = b_area.top + 48
            for b in self.existing_boons:
                row_r = pygame.Rect(b_area.left + 12, by, b_area.width - 24, 46)
                pygame.draw.rect(surface, (30, 36, 48), row_r, border_radius=6)
                elem = getattr(b, "element", "KINETIC").upper()
                elem_c = ELEMENT_COLORS.get(elem, (200, 200, 200))
                pygame.draw.rect(surface, elem_c, row_r, 1, border_radius=6)

                # Name & Element
                b_name_surf = self.font_tag.render(f"{b.name} [T{b.level}/{b.max_level}]", True, COLOR_WHITE)
                elem_badge = self.font_stat_label.render(f"[{elem}]", True, elem_c)
                surface.blit(b_name_surf, (row_r.left + 10, row_r.top + 8))
                surface.blit(elem_badge, (row_r.right - 10 - elem_badge.get_width(), row_r.top + 8))

                # Short desc
                short_desc = self.font_stat_val.render(b.description[:55] + "...", True, (180, 195, 215))
                surface.blit(short_desc, (row_r.left + 10, row_r.top + 26))
                by += 52

        # 2. Active Synergies Column (Right)
        s_area = pygame.Rect(b_area.right + 15, insp_rect.top + 75, (insp_rect.width - 65) // 2, insp_rect.height - 95)
        pygame.draw.rect(surface, (24, 28, 38), s_area, border_radius=8)
        pygame.draw.rect(surface, (50, 65, 85), s_area, 1, border_radius=8)
        s_hdr = self.font_card_title.render("UNLOCKED DUO SYNERGIES", True, (255, 200, 70))
        surface.blit(s_hdr, (s_area.left + 16, s_area.top + 14))

        active_syns = get_active_synergies(self.existing_boons)
        if not active_syns:
            no_syn = self.font_desc.render("No active synergies yet. Combine elements to unlock!", True, (140, 155, 175))
            surface.blit(no_syn, (s_area.left + 16, s_area.top + 50))
        else:
            sy = s_area.top + 48
            for syn in active_syns:
                row_r = pygame.Rect(s_area.left + 12, sy, s_area.width - 24, 52)
                pygame.draw.rect(surface, (36, 32, 22), row_r, border_radius=6)
                pygame.draw.rect(surface, (255, 190, 60), row_r, 1, border_radius=6)
                
                syn_title = self.font_tag.render(f"✦ {syn['name']} ({syn['tag']})", True, (255, 210, 80))
                surface.blit(syn_title, (row_r.left + 10, row_r.top + 6))

                syn_desc = self.font_stat_val.render(syn['description'][:58] + "...", True, (220, 225, 235))
                surface.blit(syn_desc, (row_r.left + 10, row_r.top + 28))
                sy += 58

    def _render_wrapped_text(self, surface: pygame.Surface, text: str, x: int, y: int, max_width: int):
        words = text.split(' ')
        line = []
        cur_y = y
        line_height = 18

        for word in words:
            test_line = ' '.join(line + [word])
            w, _ = self.font_desc.size(test_line)
            if w <= max_width:
                line.append(word)
            else:
                rendered = self.font_desc.render(' '.join(line), True, (215, 225, 235))
                surface.blit(rendered, (x, cur_y))
                cur_y += line_height
                line = [word]

        if line:
            rendered = self.font_desc.render(' '.join(line), True, (215, 225, 235))
            surface.blit(rendered, (x, cur_y))
