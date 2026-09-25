"""Grand Central Hub / Main Menu allowing train route and weapon selection."""
import pygame
import math
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_WHITE, COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_CARPET_RED,
    COLOR_LIGHTNING_CYAN, COLOR_EMBER_ORANGE
)
from src.combat.weapons import AVAILABLE_WEAPONS
from src.level.car_generator import TRAIN_ROUTES

class HubStation:
    """The central train station where players choose routes and armaments before departure."""
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 40, bold=True)
        self.font_subtitle = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)
        self.font_section = pygame.font.SysFont("Helvetica, Arial, sans-serif", 18, bold=True)
        self.font_body = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14)
        self.font_tag = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_prompt = pygame.font.SysFont("Helvetica, Arial, sans-serif", 20, bold=True)

        self.routes = list(TRAIN_ROUTES.keys())
        self.selected_route_idx = 0
        
        self.weapon_classes = AVAILABLE_WEAPONS
        self.selected_weapon_idx = 0

        # UI rects for mouse picking
        self.board_btn_rect = pygame.Rect((SCREEN_WIDTH - 360) // 2, SCREEN_HEIGHT - 105, 360, 50)
        self.route_tab_rects = []
        self.weapon_card_rects = []

    def handle_input(self, events: list[pygame.event.Event]) -> bool:
        """Process menu navigation. Returns True if the player boards the train."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Toggle Route with [Q] / [E] or Left / Right (Subway is locked to Iron Express)
                if event.key in (pygame.K_q, pygame.K_LEFT, pygame.K_e, pygame.K_RIGHT):
                    self.selected_route_idx = 0
                
                # Toggle Weapon with [W] / [S] or Up / Down
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.selected_weapon_idx = (self.selected_weapon_idx - 1) % len(self.weapon_classes)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.selected_weapon_idx = (self.selected_weapon_idx + 1) % len(self.weapon_classes)
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self.selected_weapon_idx = 0
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.selected_weapon_idx = 1
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.selected_weapon_idx = 2
                elif event.key in (pygame.K_4, pygame.K_KP4):
                    self.selected_weapon_idx = 3

                # Start Game
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                # Click board button
                if self.board_btn_rect.collidepoint(mouse_pos):
                    return True
                
                # Click route tabs (Subway is locked)
                for idx, r_rect in enumerate(self.route_tab_rects):
                    if r_rect.collidepoint(mouse_pos):
                        if self.routes[idx] == "steam":
                            self.selected_route_idx = idx
                        break

                # Click weapon cards
                for idx, w_rect in enumerate(self.weapon_card_rects):
                    if w_rect.collidepoint(mouse_pos):
                        self.selected_weapon_idx = idx
                        break

        return False

    def get_selected_route_id(self) -> str:
        return "steam"

    def get_selected_weapon(self):
        return self.weapon_classes[self.selected_weapon_idx]()

    def draw(self, surface: pygame.Surface):
        # 1. Background (Art Deco Grand Station)
        surface.fill((14, 16, 22))
        
        # Golden trim header
        pygame.draw.rect(surface, (20, 24, 32), (0, 0, SCREEN_WIDTH, 120))
        pygame.draw.line(surface, COLOR_BRASS, (0, 120), (SCREEN_WIDTH, 120), 3)

        # Title
        title_surf = self.font_title.render("NEXT STOP (2026)", True, COLOR_BRASS_HIGHLIGHT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 45))
        surface.blit(title_surf, title_rect)

        sub_surf = self.font_subtitle.render("GRAND CENTRAL TERMINAL — SELECT DEPARTURE & ARSENAL", True, (180, 195, 215))
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 88))
        surface.blit(sub_surf, sub_rect)

        # Panel Dimensions
        panel_w = 490
        panel_h = 440
        ry = 145
        rx = 110

        # 2. Train Route Selection (Left Panel)
        route_rect = pygame.Rect(rx, ry, panel_w, panel_h)
        pygame.draw.rect(surface, (22, 26, 36), route_rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS, route_rect, 2, border_radius=10)

        route_header = self.font_section.render("1. SELECT TRAIN ROUTE  [The Iron Express]", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(route_header, (rx + 22, ry + 18))

        # Route Tabs (Clickable)
        self.route_tab_rects.clear()
        tab_w = (panel_w - 55) // len(self.routes)
        for i, r_key in enumerate(self.routes):
            r_data = TRAIN_ROUTES[r_key]
            is_locked = (r_key == "subway")
            is_sel = (i == self.selected_route_idx and not is_locked)
            tab_rect = pygame.Rect(rx + 22 + i * (tab_w + 10), ry + 52, tab_w, 40)
            self.route_tab_rects.append(tab_rect)

            if is_locked:
                tab_bg = (24, 20, 26)
                tab_border = (75, 48, 65)
                tab_text_str = f"[LOCKED] {r_data['name']}"
                tab_text_col = (145, 120, 135)
            elif is_sel:
                tab_bg = (48, 42, 28)
                tab_border = COLOR_BRASS_HIGHLIGHT
                tab_text_str = r_data["name"]
                tab_text_col = COLOR_WHITE
            else:
                tab_bg = COLOR_STEEL_DARK
                tab_border = COLOR_STEEL_MID
                tab_text_str = r_data["name"]
                tab_text_col = (180, 185, 195)

            pygame.draw.rect(surface, tab_bg, tab_rect, border_radius=6)
            pygame.draw.rect(surface, tab_border, tab_rect, 2 if is_sel else 1, border_radius=6)

            tab_text = self.font_body.render(tab_text_str, True, tab_text_col)
            surface.blit(tab_text, tab_text.get_rect(center=tab_rect.center))

        cur_route = TRAIN_ROUTES[self.get_selected_route_id()]
        
        # Route Tagline / Description
        desc_surf = self.font_body.render(cur_route["description"], True, (215, 225, 235))
        surface.blit(desc_surf, (rx + 22, ry + 105))

        # Highlights Badges
        tags = [("10 CARS", (40, 70, 95)), ("CAR 5 MINI-BOSS", (95, 45, 30)), ("ENGINE BOSS", (90, 30, 30)), ("[EVENT ROUTE LOCKED]", (70, 35, 65))]

        bx = rx + 22
        for t_text, t_color in tags:
            t_surf = self.font_tag.render(t_text, True, COLOR_WHITE)
            t_rect = pygame.Rect(bx, ry + 132, t_surf.get_width() + 14, 22)
            pygame.draw.rect(surface, t_color, t_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BRASS, t_rect, 1, border_radius=4)
            surface.blit(t_surf, (bx + 7, ry + 136))
            bx += t_rect.width + 8

        # Stops Card (Compact 2-Column Grid that never overflows)
        stops_box = pygame.Rect(rx + 20, ry + 168, panel_w - 40, 248)
        pygame.draw.rect(surface, (16, 20, 28), stops_box, border_radius=8)
        pygame.draw.rect(surface, (38, 48, 64), stops_box, 1, border_radius=8)

        stops_title = self.font_tag.render("CAMPAIGN STOPS & SPECIAL HAZARDS:", True, COLOR_BRASS)
        surface.blit(stops_title, (stops_box.left + 15, stops_box.top + 10))

        cars = cur_route["cars"]
        # Display stops cleanly in two columns
        half = (len(cars) + 1) // 2
        for ci, c in enumerate(cars):
            col = 0 if ci < half else 1
            row = ci if ci < half else (ci - half)
            cx = stops_box.left + 15 + col * 225
            cy = stops_box.top + 34 + row * 38

            # Indicator dot
            dot_color = (240, 90, 90) if "engine" in c["type"] or "inspection" in c["type"] else COLOR_BRASS
            pygame.draw.circle(surface, dot_color, (cx + 4, cy + 8), 4)

            name_str = f"{ci + 1}. {c['name']}"
            if len(name_str) > 22:
                name_str = name_str[:20] + ".."
            name_surf = self.font_body.render(name_str, True, COLOR_WHITE)
            surface.blit(name_surf, (cx + 14, cy))

            # Hazard label
            sub_text = ""
            if c["type"] == "cold_storage":
                sub_text = "Ice Drift Physics"
            elif c["type"] == "inspection":
                sub_text = "Chief Ticket Inspector"
            elif c["type"] == "observation":
                sub_text = "Headwind Crosswinds"
            elif c["type"] == "furnace_tender":
                sub_text = "Hot Coal Catwalks"
            elif c["type"] == "engine":
                sub_text = "The Conductor Climax"
            elif c["type"] == "cargo":
                sub_text = "Explosive Barrels"

            if sub_text:
                sub_surf = self.font_tag.render(sub_text, True, (240, 180, 110) if "Inspector" in sub_text or "Conductor" in sub_text else (150, 180, 200))
                surface.blit(sub_surf, (cx + 14, cy + 18))

        # 3. Weapon Selection (Right Panel)
        wx = SCREEN_WIDTH - panel_w - 110
        weap_rect = pygame.Rect(wx, ry, panel_w, panel_h)
        pygame.draw.rect(surface, (22, 26, 36), weap_rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS, weap_rect, 2, border_radius=10)

        weap_header = self.font_section.render("2. SELECT WEAPON  [W / S, 1-4, or Click]", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(weap_header, (wx + 22, ry + 18))

        self.weapon_card_rects.clear()
        for wi, w_cls in enumerate(self.weapon_classes):
            inst = w_cls()
            is_w_sel = (wi == self.selected_weapon_idx)
            w_box = pygame.Rect(wx + 20, ry + 52 + wi * 94, panel_w - 40, 84)
            self.weapon_card_rects.append(w_box)

            box_bg = (42, 38, 26) if is_w_sel else COLOR_STEEL_DARK
            box_border = COLOR_BRASS_HIGHLIGHT if is_w_sel else COLOR_STEEL_MID
            pygame.draw.rect(surface, box_bg, w_box, border_radius=8)
            pygame.draw.rect(surface, box_border, w_box, 2 if is_w_sel else 1, border_radius=8)

            w_name = self.font_section.render(f"[{wi + 1}] {inst.name.upper()}", True, COLOR_BRASS_HIGHLIGHT if is_w_sel else COLOR_WHITE)
            surface.blit(w_name, (w_box.x + 14, w_box.y + 8))

            w_desc = self.font_body.render(inst.desc, True, (200, 210, 225) if is_w_sel else (160, 175, 190))
            surface.blit(w_desc, (w_box.x + 14, w_box.y + 34))

            # Stats pill
            stats_str = f"Base Dmg: {inst.base_damage}  |  Fire Rate: {inst.fire_rate:.2f}s"
            stats_surf = self.font_tag.render(stats_str, True, COLOR_BRASS if is_w_sel else (140, 150, 165))
            surface.blit(stats_surf, (w_box.x + 14, w_box.y + 58))

        # 4. Board Train Button / Prompt (Bottom Center)
        board_btn = self.board_btn_rect
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
        btn_bg = (int(160 + 40 * pulse), int(30 + 20 * pulse), 40)
        pygame.draw.rect(surface, btn_bg, board_btn, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, board_btn, 2, border_radius=10)

        prompt_surf = self.font_prompt.render("ALL ABOARD! [PRESS ENTER / SPACE]", True, COLOR_WHITE)
        surface.blit(prompt_surf, prompt_surf.get_rect(center=board_btn.center))

        ctrl_note = self.font_body.render("Controls: WASD Move (Double-Tap to Dash) | Space / Left-Click Attack | Shift Dash | E Interact", True, (160, 175, 195))
        surface.blit(ctrl_note, ctrl_note.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 26)))
