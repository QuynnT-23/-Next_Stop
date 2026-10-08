"""Walkable Grand Central Terminal Hub (Lego Star Wars / Hades style).
Allows the player to explore the station, visit train docking bays to depart on stages,
upgrade perks at the Conductor Workshop Anvil, and equip weapons at the Armory.
"""
import pygame
import math
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_WHITE, COLOR_CRIT_YELLOW, COLOR_EMBER_ORANGE, COLOR_STEEL_DARK,
    COLOR_STEEL_MID, COLOR_SHADOW
)
from src.combat.weapons import AVAILABLE_WEAPONS
from src.level.car_generator import TRAIN_ROUTES
from src.core.progression import ProgressionManager, PERK_DEFINITIONS
from src.ui.sprite_renderer import draw_stoker_player
from src.combat.enemy_codex import ENEMY_CODEX_DATA, DummyPreviewCamera, get_all_codex_entries

class HubStation:
    """Interactive, walkable Grand Central Terminal Hub with docking bays, workshop, armory, and enemy codex."""
    def __init__(self, progression: ProgressionManager = None):
        pygame.font.init()
        self.progression = progression or ProgressionManager()
        
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 24, bold=True)
        self.font_header = pygame.font.SysFont("Helvetica, Arial, sans-serif", 18, bold=True)
        self.font_body = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)
        self.font_tag = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12, bold=True)
        self.font_prompt = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)

        # Player physical presence in Hub
        self.player_pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180)
        self.player_vel = pygame.math.Vector2(0, 0)
        self.player_speed = 280.0
        self.facing_angle = -math.pi / 2  # Looking north toward train gates
        self.is_dashing = False
        self.dash_timer = 0.0

        # Weapons
        self.weapon_classes = AVAILABLE_WEAPONS
        self.selected_weapon_idx = 0
        self.active_weapon = self.weapon_classes[self.selected_weapon_idx]()

        # Active departure selection
        self.selected_route_id = self.progression.get_active_route_id()
        self.boarded = False

        # Modals / Interacting
        self.show_workshop = False
        self.hovered_perk_id = None

        # Docking Bays along north wall (5 gates)
        self.docking_bays = []
        gate_w = 210
        gap = 25
        total_w = 5 * gate_w + 4 * gap
        start_x = (SCREEN_WIDTH - total_w) // 2
        stage_keys = ["steam", "derelict", "subway", "cryo", "infernal"]
        for i, sk in enumerate(stage_keys):
            bx = start_x + i * (gate_w + gap)
            by = 85
            self.docking_bays.append({
                "route_id": sk,
                "name": TRAIN_ROUTES[sk]["name"],
                "rect": pygame.Rect(bx, by, gate_w, 150),
                "door_rect": pygame.Rect(bx + 15, by + 50, gate_w - 30, 95),
                "platform_num": i + 1
            })

        # Workshop Anvil Station (Left Hall)
        self.workshop_rect = pygame.Rect(110, SCREEN_HEIGHT // 2 - 20, 160, 120)

        # Dispatch Archives / Field Bestiary Desk (Between Workshop and Concourse)
        self.codex_rect = pygame.Rect(345, SCREEN_HEIGHT // 2 - 20, 160, 120)

        # Dispatch Test Console Terminal (Between Concourse and Armory)
        self.test_terminal_rect = pygame.Rect(SCREEN_WIDTH - 505, SCREEN_HEIGHT // 2 - 20, 160, 120)

        # Armory Racks (Right Hall)
        self.armory_rect = pygame.Rect(SCREEN_WIDTH - 270, SCREEN_HEIGHT // 2 - 20, 160, 120)

        # Top HUD Test Mode Button (safely above north docking gates)
        self.hud_test_btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 95, 52, 190, 24)
        self.request_test_mode = False

        # Enemy Threat Codex Modal State
        self.show_codex = False
        self.selected_codex_id = "ticket_inspector"
        self.codex_category_filter = "ALL"  # "ALL", "Standard", "Mini-Boss", "Climax Boss"
        self.codex_scroll_offset = 0
        self.codex_preview_cache = {}
        self.dummy_preview_camera = DummyPreviewCamera()

        # Input / Board buffer
        self.board_cooldown = 0.0

    def reset_player(self):
        """Reset player position and state when returning to Grand Central Terminal Hub."""
        self.player_pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180)
        self.player_vel = pygame.math.Vector2(0, 0)
        self.facing_angle = -math.pi / 2
        self.show_workshop = False
        self.show_codex = False
        self.request_test_mode = False
        self.is_dashing = False
        self.dash_timer = 0.0
        self.board_cooldown = 0.4
        self.boarded = False
        self.selected_route_id = self.progression.get_active_route_id()

    def get_selected_route_id(self) -> str:
        return self.selected_route_id

    def get_selected_weapon(self):
        return self.weapon_classes[self.selected_weapon_idx]()

    def handle_input(self, events: list[pygame.event.Event]) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        to_mouse = pygame.math.Vector2(mouse_pos) - self.player_pos
        if to_mouse.length_squared() > 0:
            self.facing_angle = math.atan2(to_mouse.y, to_mouse.x)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.show_workshop:
                    if event.key in (pygame.K_ESCAPE, pygame.K_e):
                        self.show_workshop = False
                    elif event.key in (pygame.K_1, pygame.K_KP1):
                        self._try_buy_perk_by_idx(0)
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self._try_buy_perk_by_idx(1)
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self._try_buy_perk_by_idx(2)
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        self._try_buy_perk_by_idx(3)
                    elif event.key in (pygame.K_5, pygame.K_KP5):
                        self._try_buy_perk_by_idx(4)
                    return False

                if self.show_codex:
                    filtered = self._get_filtered_codex_entries()
                    cur_idx = 0
                    for idx, e in enumerate(filtered):
                        if e["id"] == self.selected_codex_id:
                            cur_idx = idx
                            break

                    if event.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_b):
                        self.show_codex = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if filtered:
                            new_idx = (cur_idx - 1) % len(filtered)
                            self.selected_codex_id = filtered[new_idx]["id"]
                            self.codex_scroll_offset = max(0, min(len(filtered) * 62, (new_idx - 3) * 62))
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if filtered:
                            new_idx = (cur_idx + 1) % len(filtered)
                            self.selected_codex_id = filtered[new_idx]["id"]
                            self.codex_scroll_offset = max(0, min(len(filtered) * 62, (new_idx - 3) * 62))
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        cats = ["ALL", "Standard", "Mini-Boss", "Climax Boss"]
                        c_i = cats.index(self.codex_category_filter) if self.codex_category_filter in cats else 0
                        self.codex_category_filter = cats[(c_i - 1) % len(cats)]
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        cats = ["ALL", "Standard", "Mini-Boss", "Climax Boss"]
                        c_i = cats.index(self.codex_category_filter) if self.codex_category_filter in cats else 0
                        self.codex_category_filter = cats[(c_i + 1) % len(cats)]
                    elif event.key in (pygame.K_1, pygame.K_KP1):
                        self.codex_category_filter = "ALL"
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self.codex_category_filter = "Standard"
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self.codex_category_filter = "Mini-Boss"
                    elif event.key in (pygame.K_4, pygame.K_KP4):
                        self.codex_category_filter = "Climax Boss"
                    return False

                # Quick codex toggle with [B] anywhere in hub
                if event.key == pygame.K_b:
                    self.show_codex = not self.show_codex
                    return False

                # Quick weapon cycle with 1, 2, 3, 4
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self._set_weapon(0)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self._set_weapon(1)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self._set_weapon(2)
                elif event.key in (pygame.K_4, pygame.K_KP4):
                    self._set_weapon(3)

                # Interact Key [E] or Spacebar
                if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                    # Check near workshop
                    if (self.player_pos - pygame.math.Vector2(self.workshop_rect.center)).length() < 130:
                        self.show_workshop = not self.show_workshop
                        return False

                    # Check near dispatch archives (Enemy Codex)
                    if (self.player_pos - pygame.math.Vector2(self.codex_rect.center)).length() < 130:
                        self.show_codex = not self.show_codex
                        return False

                    # Check near test console terminal desk
                    if (self.player_pos - pygame.math.Vector2(self.test_terminal_rect.center)).length() < 130:
                        self.request_test_mode = True
                        return False

                    # Check near armory
                    if (self.player_pos - pygame.math.Vector2(self.armory_rect.center)).length() < 130:
                        self.selected_weapon_idx = (self.selected_weapon_idx + 1) % len(self.weapon_classes)
                        self._set_weapon(self.selected_weapon_idx)
                        return False

                    # Check near any Docking Bay gate
                    if self.board_cooldown <= 0.0:
                        for bay in self.docking_bays:
                            if bay["door_rect"].collidepoint(self.player_pos.x, self.player_pos.y):
                                if self.progression.get_track_state(bay["route_id"]) == "active":
                                    self.selected_route_id = bay["route_id"]
                                    return True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.show_workshop:
                    # Check close button
                    close_btn = pygame.Rect(SCREEN_WIDTH // 2 + 260, SCREEN_HEIGHT // 2 - 210, 40, 40)
                    if close_btn.collidepoint(event.pos):
                        self.show_workshop = False
                        return False
                    # Check perk purchase buttons
                    if self.hovered_perk_id:
                        self.progression.purchase_perk(self.hovered_perk_id)
                        return False
                elif self.show_codex:
                    mw, mh = 1080, 610
                    mx = (SCREEN_WIDTH - mw) // 2
                    my = (SCREEN_HEIGHT - mh) // 2
                    close_btn = pygame.Rect(mx + mw - 45, my + 14, 30, 30)
                    if close_btn.collidepoint(event.pos):
                        self.show_codex = False
                        return False

                    # Check category tabs
                    tab_cats = ["ALL", "Standard", "Mini-Boss", "Climax Boss"]
                    cur_tab_x = mx + 25
                    for cat_key in tab_cats:
                        t_rect = pygame.Rect(cur_tab_x, my + 54, 150, 28)
                        if t_rect.collidepoint(event.pos):
                            self.codex_category_filter = cat_key
                            self.codex_scroll_offset = 0
                            return False
                        cur_tab_x += 158

                    # Check list card clicks
                    list_rect = pygame.Rect(mx + 25, my + 90, 320, mh - 135)
                    if list_rect.collidepoint(event.pos):
                        filtered = self._get_filtered_codex_entries()
                        for i, entry in enumerate(filtered):
                            card_y = list_rect.top + 8 + i * 62 - self.codex_scroll_offset
                            c_rect = pygame.Rect(list_rect.left + 8, card_y, list_rect.width - 16, 56)
                            if c_rect.collidepoint(event.pos):
                                self.selected_codex_id = entry["id"]
                                return False
                else:
                    # Click on archives desk to open codex
                    if self.codex_rect.collidepoint(event.pos):
                        self.show_codex = True
                        return False

                    # Click on test console terminal desk or top HUD pill button
                    if self.test_terminal_rect.collidepoint(event.pos) or self.hud_test_btn_rect.collidepoint(event.pos):
                        self.request_test_mode = True
                        return False

                    # Click on workshop anvil
                    if self.workshop_rect.collidepoint(event.pos):
                        self.show_workshop = True
                        return False

                    # Click on armory rack
                    if self.armory_rect.collidepoint(event.pos):
                        self.selected_weapon_idx = (self.selected_weapon_idx + 1) % len(self.weapon_classes)
                        self._set_weapon(self.selected_weapon_idx)
                        return False

                    # Click on gate to board (only single active track is boardable)
                    if self.board_cooldown <= 0.0:
                        for bay in self.docking_bays:
                            if bay["door_rect"].collidepoint(event.pos):
                                if self.progression.get_track_state(bay["route_id"]) == "active":
                                    self.selected_route_id = bay["route_id"]
                                    return True

            elif event.type == pygame.MOUSEBUTTONDOWN and self.show_codex:
                if event.button == 4:
                    self.codex_scroll_offset = max(0, self.codex_scroll_offset - 35)
                elif event.button == 5:
                    self.codex_scroll_offset += 35

            elif event.type == pygame.MOUSEWHEEL and self.show_codex:
                self.codex_scroll_offset = max(0, self.codex_scroll_offset - int(event.y * 35))

        # Process movement
        self.update(0.016)

        # Auto-board if walking directly into gate threshold (only single active track)
        if not self.show_workshop and not self.show_codex and self.board_cooldown <= 0.0:
            for bay in self.docking_bays:
                if bay["door_rect"].collidepoint(self.player_pos.x, self.player_pos.y):
                    if self.progression.get_track_state(bay["route_id"]) == "active":
                        self.selected_route_id = bay["route_id"]
                        return True

        return False

    def update(self, dt: float = 0.016):
        """Update player movement and positioning in Hub Station."""
        if self.board_cooldown > 0.0:
            self.board_cooldown = max(0.0, self.board_cooldown - dt)

        if not self.show_workshop and not self.show_codex:
            keys = pygame.key.get_pressed()
            move = pygame.math.Vector2(0, 0)
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                move.y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                move.y += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move.x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move.x += 1

            if move.length_squared() > 0:
                self.player_vel = move.normalize() * self.player_speed
            else:
                self.player_vel *= 0.6

            self.player_pos += self.player_vel * dt

            # Keep inside Terminal walls
            self.player_pos.x = max(70, min(SCREEN_WIDTH - 70, self.player_pos.x))
            self.player_pos.y = max(190, min(SCREEN_HEIGHT - 60, self.player_pos.y))

    def _set_weapon(self, idx: int):
        self.selected_weapon_idx = idx
        self.active_weapon = self.weapon_classes[idx]()

    def _try_buy_perk_by_idx(self, idx: int):
        perk_keys = list(PERK_DEFINITIONS.keys())
        if 0 <= idx < len(perk_keys):
            self.progression.purchase_perk(perk_keys[idx])

    def draw(self, surface: pygame.Surface):
        # 1. Art Deco Grand Terminal Station Floor
        surface.fill((16, 18, 24))
        
        # Checkerboard Marble Floor
        tile_sz = 64
        for x in range(0, SCREEN_WIDTH, tile_sz):
            for y in range(160, SCREEN_HEIGHT, tile_sz):
                color = (24, 28, 38) if ((x // tile_sz) + (y // tile_sz)) % 2 == 0 else (18, 22, 30)
                pygame.draw.rect(surface, color, (x, y, tile_sz, tile_sz))

        # Golden Inlay Trim down center aisle
        pygame.draw.rect(surface, (120, 20, 30), (SCREEN_WIDTH // 2 - 80, 200, 160, SCREEN_HEIGHT - 200))
        pygame.draw.line(surface, COLOR_BRASS, (SCREEN_WIDTH // 2 - 80, 200), (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT), 2)
        pygame.draw.line(surface, COLOR_BRASS, (SCREEN_WIDTH // 2 + 80, 200), (SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT), 2)

        # 2. Train Platform Rail Tracks (North Strip)
        pygame.draw.rect(surface, (28, 32, 42), (0, 0, SCREEN_WIDTH, 175))
        pygame.draw.line(surface, COLOR_BRASS, (0, 175), (SCREEN_WIDTH, 175), 4)
        for rx in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, (15, 18, 22), (rx, 0), (rx, 175), 2)

        # 3. Draw 5 Docking Bays
        active_route_id = self.progression.get_active_route_id()
        for bay in self.docking_bays:
            state = self.progression.get_track_state(bay["route_id"])
            d_rect = bay["rect"]
            door = bay["door_rect"]
            p_num = bay["platform_num"]

            if state == "active":
                # Active Gate: Glowing Art Deco archway with animated emerald/brass pulse
                pulse = (math.sin(pygame.time.get_ticks() * 0.008 + p_num) + 1) * 0.5
                arch_bg = (24, 32, 42)
                pygame.draw.rect(surface, arch_bg, d_rect, border_radius=8)
                pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, d_rect, 3, border_radius=8)

                # Platform Sign with Loop Notation (e.g. TRACK 1, TRACK 1+)
                track_display = self.progression.get_track_display_name(bay["route_id"])
                p_badge = self.font_tag.render(track_display, True, COLOR_BRASS_HIGHLIGHT)
                surface.blit(p_badge, p_badge.get_rect(center=(d_rect.centerx, d_rect.top + 16)))

                # Stage Name (Fully written and centered)
                s_name = bay["name"]
                n_surf = self.font_body.render(s_name, True, COLOR_WHITE)
                surface.blit(n_surf, n_surf.get_rect(center=(d_rect.centerx, d_rect.top + 34)))

                # Active modifiers tag if loop >= 1
                if self.progression.loop_count >= 1:
                    mod_tag = self.font_tag.render("✦ MODIFIERS ACTIVE ✦", True, COLOR_CRIT_YELLOW)
                    surface.blit(mod_tag, mod_tag.get_rect(center=(d_rect.centerx, d_rect.top + 48)))

                # Door Threshold Zone (Open, Glowing)
                thresh_col = (int(30 + 30 * pulse), int(80 + 40 * pulse), int(55 + 25 * pulse))
                pygame.draw.rect(surface, thresh_col, door, border_radius=6)
                pygame.draw.rect(surface, (90, 240, 160), door, 2, border_radius=6)
                b_prompt = self.font_tag.render("[STEP TO BOARD]", True, (180, 255, 210))
                surface.blit(b_prompt, b_prompt.get_rect(center=(door.centerx, door.centery - 8)))
                act_sub = self.font_tag.render("ACTIVE EXPEDITION", True, (130, 220, 170))
                surface.blit(act_sub, act_sub.get_rect(center=(door.centerx, door.centery + 10)))

            elif state == "completed":
                # Completed Gate: Scissor gates closed, train departed
                pygame.draw.rect(surface, (28, 26, 28), d_rect, border_radius=8)
                pygame.draw.rect(surface, (130, 105, 65), d_rect, 1, border_radius=8)

                # Platform Sign
                track_display = self.progression.get_track_display_name(bay["route_id"])
                p_badge = self.font_tag.render(track_display, True, (170, 140, 90))
                surface.blit(p_badge, p_badge.get_rect(center=(d_rect.centerx, d_rect.top + 16)))

                # Stage Name (Fully written and centered)
                s_name = bay["name"]
                n_surf = self.font_body.render(s_name, True, (160, 160, 160))
                surface.blit(n_surf, n_surf.get_rect(center=(d_rect.centerx, d_rect.top + 34)))

                # Door Threshold Zone (Closed, Scissor Lattice)
                pygame.draw.rect(surface, (20, 18, 20), door, border_radius=6)
                pygame.draw.rect(surface, (90, 75, 55), door, 1, border_radius=6)
                # Diamond scissor lattice lines
                for lx in range(door.left + 10, door.right, 24):
                    pygame.draw.line(surface, (60, 50, 40), (lx, door.top), (lx + 20, door.bottom), 1)
                    pygame.draw.line(surface, (60, 50, 40), (lx + 20, door.top), (lx, door.bottom), 1)

                dep_badge = self.font_tag.render("[TRAIN DEPARTED]", True, (240, 190, 80))
                surface.blit(dep_badge, dep_badge.get_rect(center=(door.centerx, door.centery - 8)))
                comp_sub = self.font_tag.render("✓ STAGE CLEARED", True, (150, 190, 140))
                surface.blit(comp_sub, comp_sub.get_rect(center=(door.centerx, door.centery + 10)))

            else:
                # Locked Gate: Upcoming route, hazard tape
                pygame.draw.rect(surface, (20, 20, 24), d_rect, border_radius=8)
                pygame.draw.rect(surface, (60, 45, 50), d_rect, 1, border_radius=8)

                # Platform Sign
                track_display = self.progression.get_track_display_name(bay["route_id"])
                p_badge = self.font_tag.render(track_display, True, (110, 100, 110))
                surface.blit(p_badge, p_badge.get_rect(center=(d_rect.centerx, d_rect.top + 16)))

                # Stage Name (Fully written and centered)
                s_name = bay["name"]
                n_surf = self.font_body.render(s_name, True, (110, 110, 115))
                surface.blit(n_surf, n_surf.get_rect(center=(d_rect.centerx, d_rect.top + 34)))

                # Door Threshold Zone (Locked with red hazard tape)
                pygame.draw.rect(surface, (26, 18, 20), door, border_radius=6)
                pygame.draw.rect(surface, (80, 40, 45), door, 1, border_radius=6)
                pygame.draw.line(surface, (140, 45, 50), door.topleft, door.bottomright, 2)
                pygame.draw.line(surface, (140, 45, 50), door.bottomleft, door.topright, 2)
                l_prompt = self.font_tag.render("[LOCKED]", True, (210, 80, 90))
                surface.blit(l_prompt, l_prompt.get_rect(center=(door.centerx, door.centery - 8)))
                req_sub = self.font_tag.render(f"CLEAR TRACK {p_num - 1}", True, (160, 90, 95))
                surface.blit(req_sub, req_sub.get_rect(center=(door.centerx, door.centery + 10)))

        # 4. Workshop / License Desk (Left Hall)
        ws = self.workshop_rect
        near_ws = (self.player_pos - pygame.math.Vector2(ws.center)).length() < 130
        pygame.draw.rect(surface, (32, 26, 22), ws, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if near_ws else COLOR_BRASS, ws, 3 if near_ws else 2, border_radius=10)
        ws_title = self.font_body.render("STOKER WORKSHOP", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(ws_title, ws_title.get_rect(center=(ws.centerx, ws.top + 22)))
        ws_sub = self.font_tag.render("LICENSE & PERKS", True, COLOR_WHITE)
        surface.blit(ws_sub, ws_sub.get_rect(center=(ws.centerx, ws.top + 45)))
        ws_prompt = self.font_prompt.render("[PRESS E / CLICK]", True, COLOR_CRIT_YELLOW if near_ws else (160, 160, 160))
        surface.blit(ws_prompt, ws_prompt.get_rect(center=(ws.centerx, ws.top + 80)))

        # 4b. Dispatch Archives / Field Bestiary Desk (Between Workshop and Concourse)
        arch = self.codex_rect
        near_arch = (self.player_pos - pygame.math.Vector2(arch.center)).length() < 130
        pygame.draw.rect(surface, (28, 24, 20), arch, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if near_arch else COLOR_BRASS, arch, 3 if near_arch else 2, border_radius=10)
        # Decorative banker's lamp & dossier stacks
        arch_title = self.font_body.render("DISPATCH ARCHIVES", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(arch_title, arch_title.get_rect(center=(arch.centerx, arch.top + 22)))
        arch_sub = self.font_tag.render("ENEMY THREAT CODEX", True, COLOR_WHITE)
        surface.blit(arch_sub, arch_sub.get_rect(center=(arch.centerx, arch.top + 45)))
        arch_prompt = self.font_prompt.render("[PRESS E / B / CLICK]", True, COLOR_CRIT_YELLOW if near_arch else (160, 160, 160))
        surface.blit(arch_prompt, arch_prompt.get_rect(center=(arch.centerx, arch.top + 80)))

        # 4c. Dispatch Test Console Terminal (Between Concourse and Armory)
        term = self.test_terminal_rect
        near_term = (self.player_pos - pygame.math.Vector2(term.center)).length() < 130
        pygame.draw.rect(surface, (22, 28, 36), term, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if near_term else (60, 100, 140), term, 3 if near_term else 2, border_radius=10)
        term_title = self.font_body.render("TEST CONSOLE", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(term_title, term_title.get_rect(center=(term.centerx, term.top + 22)))
        term_sub = self.font_tag.render("STAGES & CHEATS", True, (130, 220, 255))
        surface.blit(term_sub, term_sub.get_rect(center=(term.centerx, term.top + 45)))
        term_prompt = self.font_prompt.render("[PRESS F1 / E / CLICK]", True, COLOR_CRIT_YELLOW if near_term else (160, 160, 160))
        surface.blit(term_prompt, term_prompt.get_rect(center=(term.centerx, term.top + 80)))

        # 5. Armory Racks (Right Hall)
        ar = self.armory_rect
        near_ar = (self.player_pos - pygame.math.Vector2(ar.center)).length() < 130
        pygame.draw.rect(surface, (24, 28, 38), ar, border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if near_ar else COLOR_BRASS, ar, 3 if near_ar else 2, border_radius=10)
        ar_title = self.font_body.render("ARMORY RACK", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(ar_title, ar_title.get_rect(center=(ar.centerx, ar.top + 22)))
        wpn_text = self.font_tag.render(self.active_weapon.name.upper(), True, COLOR_WHITE)
        surface.blit(wpn_text, wpn_text.get_rect(center=(ar.centerx, ar.top + 45)))
        ar_prompt = self.font_prompt.render("[PRESS E TO SWAP]", True, COLOR_CRIT_YELLOW if near_ar else (160, 160, 160))
        surface.blit(ar_prompt, ar_prompt.get_rect(center=(ar.centerx, ar.top + 80)))

        # 6. Draw Player Stoker
        is_moving = self.player_vel.length_squared() > 100.0
        draw_stoker_player(
            surface=surface,
            screen_pos=(int(self.player_pos.x), int(self.player_pos.y)),
            aim_angle=self.facing_angle,
            walk_dist=0.0,
            weapon=self.active_weapon,
            is_moving=is_moving,
            recoil_timer=0.0,
            attack_boost_timer=0.0,
            flash_timer=0.0,
            invuln_timer=0.0,
            radius=22.0
        )

        # 7. Station Status Header (Top Left / Right Badges & Center Marquee)
        header_bar = pygame.Rect(20, 16, 340, 48)
        pygame.draw.rect(surface, (18, 22, 30), header_bar, border_radius=8)
        pygame.draw.rect(surface, COLOR_BRASS, header_bar, 1, border_radius=8)
        
        # Conductor License Badge
        lvl_str = f"CONDUCTOR LICENSE: LVL {self.progression.level}"
        lvl_surf = self.font_header.render(lvl_str, True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(lvl_surf, (header_bar.left + 14, header_bar.top + 6))
        
        # XP Bar
        cur_xp = self.progression.xp
        max_xp = self.progression.get_xp_for_next_level()
        xp_pct = min(1.0, cur_xp / max(1, max_xp))
        bar_w = 200
        pygame.draw.rect(surface, (30, 35, 45), (header_bar.left + 14, header_bar.top + 28, bar_w, 10), border_radius=3)
        pygame.draw.rect(surface, (60, 190, 255), (header_bar.left + 14, header_bar.top + 28, int(bar_w * xp_pct), 10), border_radius=3)
        xp_num = self.font_tag.render(f"{cur_xp}/{max_xp} XP", True, (170, 200, 225))
        surface.blit(xp_num, (header_bar.left + bar_w + 22, header_bar.top + 26))

        # Center Station Marquee
        title_surf = self.font_header.render("✦ GRAND CENTRAL TERMINAL ✦", True, COLOR_BRASS_HIGHLIGHT)
        active_track_display = self.progression.get_track_display_name(self.progression.current_track_idx)
        active_route_name = TRAIN_ROUTES[self.progression.get_active_route_id()]["name"]
        loop_str = f" [LOOP {self.progression.loop_count + 1}]" if self.progression.loop_count >= 1 else ""
        sub_str = f"ACTIVE EXPEDITION: {active_track_display} ({active_route_name.upper()}){loop_str}"
        sub_col = (255, 220, 110) if self.progression.loop_count >= 1 else (175, 185, 200)
        sub_surf = self.font_tag.render(sub_str, True, sub_col)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 16)))
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 34)))

        # Top HUD Test Mode Button
        mouse_pos = pygame.mouse.get_pos()
        hover_test_btn = self.hud_test_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (30, 48, 65) if hover_test_btn else (20, 28, 38), self.hud_test_btn_rect, border_radius=13)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if hover_test_btn else (70, 120, 160), self.hud_test_btn_rect, 1, border_radius=13)
        t_btn_surf = self.font_tag.render("⚡ [F1] TEST & DEV CONSOLE", True, COLOR_WHITE if hover_test_btn else (180, 220, 255))
        surface.blit(t_btn_surf, t_btn_surf.get_rect(center=self.hud_test_btn_rect.center))

        # Scrap Metal Counter (Top Right)
        scrap_bar = pygame.Rect(SCREEN_WIDTH - 220, 16, 200, 48)
        pygame.draw.rect(surface, (18, 22, 30), scrap_bar, border_radius=8)
        pygame.draw.rect(surface, COLOR_BRASS, scrap_bar, 1, border_radius=8)
        sc_lbl = self.font_header.render(f"SCRAP: {self.progression.scrap}", True, (255, 210, 80))
        surface.blit(sc_lbl, (scrap_bar.left + 16, scrap_bar.top + 14))

        # Chud Studios Production Plaque (Art Deco Brass Inlay)
        plaque_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT - 52, 280, 20)
        pygame.draw.rect(surface, (20, 24, 32), plaque_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BRASS, plaque_rect, 1, border_radius=4)
        plaque_txt = self.font_tag.render("⚡ CHUD STUDIOS PRODUCTION ⚡", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(plaque_txt, plaque_txt.get_rect(center=plaque_rect.center))

        # Bottom Controls Hint
        ctrl_str = "[WASD] Move Stoker | [MOUSE] Aim | [F1] Test Console | [E AT ARCHIVES / B] Codex | [E AT ANVIL] Workshop | [STEP IN GATE] Depart"
        ctrl_surf = self.font_body.render(ctrl_str, True, (160, 175, 195))
        surface.blit(ctrl_surf, ctrl_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 18)))

        # 8. Render Workshop Modal if open
        if self.show_workshop:
            self._draw_workshop_modal(surface)

        # 9. Render Enemy Codex Modal if open
        if self.show_codex:
            self._draw_enemy_codex_modal(surface)

    def _get_filtered_codex_entries(self):
        all_entries = get_all_codex_entries()
        if self.codex_category_filter == "ALL":
            return all_entries
        elif self.codex_category_filter == "Standard":
            return [e for e in all_entries if e["category"] in ("Standard", "Elite")]
        else:
            return [e for e in all_entries if e["category"] == self.codex_category_filter]

    def _draw_multiline_text(self, surface: pygame.Surface, text: str, x: int, y: int, max_w: int, font: pygame.font.Font, color: tuple, line_spacing: int = 16) -> int:
        words = text.split(" ")
        lines = []
        cur_line = []
        for word in words:
            test_line = " ".join(cur_line + [word])
            if font.size(test_line)[0] <= max_w:
                cur_line.append(word)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [word]
        if cur_line:
            lines.append(" ".join(cur_line))

        for line in lines:
            rendered = font.render(line, True, color)
            surface.blit(rendered, (x, y))
            y += line_spacing
        return y

    def _draw_enemy_codex_modal(self, surface: pygame.Surface):
        # Semi-transparent dark vignette backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 14, 235))
        surface.blit(overlay, (0, 0))

        mw, mh = 1080, 610
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2
        m_rect = pygame.Rect(mx, my, mw, mh)

        # Modal outer chassis with Art Deco double border
        pygame.draw.rect(surface, (18, 22, 30), m_rect, border_radius=12)
        pygame.draw.rect(surface, (30, 36, 48), m_rect.inflate(-6, -6), border_radius=10)
        pygame.draw.rect(surface, COLOR_BRASS, m_rect, 3, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, m_rect.inflate(-4, -4), 1, border_radius=10)

        # 1. Header Bar
        all_entries = get_all_codex_entries()
        encountered_count = len([e for e in all_entries if e["id"] in self.progression.encountered_enemies])
        
        t_title = self.font_title.render("✦ CONDUCTOR'S FIELD LOG & THREAT INDEX ✦", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(t_title, (mx + 25, my + 18))

        enc_pill = pygame.Rect(mx + mw - 340, my + 16, 280, 28)
        pygame.draw.rect(surface, (25, 35, 45), enc_pill, border_radius=6)
        pygame.draw.rect(surface, (60, 190, 255), enc_pill, 1, border_radius=6)
        enc_text = self.font_tag.render(f"ENCOUNTERED IN FIELD: {encountered_count} / {len(all_entries)} HOSTILES", True, (190, 230, 255))
        surface.blit(enc_text, enc_text.get_rect(center=enc_pill.center))

        # Close button [X]
        close_btn = pygame.Rect(mx + mw - 45, my + 14, 30, 30)
        pygame.draw.rect(surface, (50, 25, 30), close_btn, border_radius=6)
        pygame.draw.rect(surface, (200, 60, 70), close_btn, 1, border_radius=6)
        c_x = self.font_header.render("X", True, COLOR_WHITE)
        surface.blit(c_x, c_x.get_rect(center=close_btn.center))

        # 2. Category Filter Tabs
        tab_names = [
            ("ALL", f"ALL ({len(all_entries)})"),
            ("Standard", "COMMON (6)"),
            ("Mini-Boss", "MINI-BOSSES (5)"),
            ("Climax Boss", "CLIMAX BOSSES (5)")
        ]
        cur_tab_x = mx + 25
        mouse_pos = pygame.mouse.get_pos()
        for cat_key, cat_label in tab_names:
            is_active = (self.codex_category_filter == cat_key)
            tab_btn = pygame.Rect(cur_tab_x, my + 54, 150, 28)
            t_col = (140, 105, 35) if is_active else ((38, 44, 58) if tab_btn.collidepoint(mouse_pos) else (26, 30, 40))
            pygame.draw.rect(surface, t_col, tab_btn, border_radius=5)
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if is_active else (60, 70, 90), tab_btn, 2 if is_active else 1, border_radius=5)
            lbl = self.font_tag.render(cat_label, True, COLOR_WHITE if is_active else (180, 190, 205))
            surface.blit(lbl, lbl.get_rect(center=tab_btn.center))
            cur_tab_x += 158

        filtered_entries = self._get_filtered_codex_entries()
        if not any(e["id"] == self.selected_codex_id for e in filtered_entries) and filtered_entries:
            self.selected_codex_id = filtered_entries[0]["id"]

        # 3. Left Column: Enemy List Cards
        list_rect = pygame.Rect(mx + 25, my + 90, 320, mh - 135)
        pygame.draw.rect(surface, (14, 18, 24), list_rect, border_radius=8)
        pygame.draw.rect(surface, (45, 55, 75), list_rect, 1, border_radius=8)

        card_h = 56
        gap = 6
        total_list_h = len(filtered_entries) * (card_h + gap)
        max_scroll = max(0, total_list_h - list_rect.height)
        self.codex_scroll_offset = max(0, min(max_scroll, self.codex_scroll_offset))

        surface.set_clip(list_rect)
        for i, entry in enumerate(filtered_entries):
            card_y = list_rect.top + 8 + i * (card_h + gap) - self.codex_scroll_offset
            c_rect = pygame.Rect(list_rect.left + 8, card_y, list_rect.width - 16, card_h)
            
            # Skip if outside clip
            if c_rect.bottom < list_rect.top or c_rect.top > list_rect.bottom:
                continue

            is_sel = (entry["id"] == self.selected_codex_id)
            is_enc = (entry["id"] in self.progression.encountered_enemies)
            is_hover = c_rect.collidepoint(mouse_pos)

            bg_col = (48, 38, 26) if is_sel else ((32, 38, 52) if is_hover else (20, 24, 34))
            pygame.draw.rect(surface, bg_col, c_rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if is_sel else ((100, 115, 140) if is_hover else (45, 55, 70)), c_rect, 2 if is_sel else 1, border_radius=6)

            # Left status pill
            status_pill = pygame.Rect(c_rect.left + 8, c_rect.top + 8, 96, 18)
            if is_enc:
                pygame.draw.rect(surface, (18, 48, 28), status_pill, border_radius=4)
                pygame.draw.rect(surface, (50, 190, 95), status_pill, 1, border_radius=4)
                s_txt = self.font_tag.render("✓ ENCOUNTERED", True, (80, 240, 140))
            else:
                pygame.draw.rect(surface, (45, 34, 16), status_pill, border_radius=4)
                pygame.draw.rect(surface, (220, 160, 40), status_pill, 1, border_radius=4)
                s_txt = self.font_tag.render("✦ UNSEEN", True, (255, 205, 90))
            surface.blit(s_txt, s_txt.get_rect(center=status_pill.center))

            # Category tag pill
            cat_pill = pygame.Rect(c_rect.right - 88, c_rect.top + 8, 80, 18)
            pygame.draw.rect(surface, (28, 32, 44), cat_pill, border_radius=4)
            cat_lbl = self.font_tag.render(entry["category"].upper(), True, (170, 185, 205))
            surface.blit(cat_lbl, cat_lbl.get_rect(center=cat_pill.center))

            # Enemy Name
            name_col = COLOR_BRASS_HIGHLIGHT if is_sel else COLOR_WHITE
            name_surf = self.font_body.render(entry["name"], True, name_col)
            surface.blit(name_surf, (c_rect.left + 10, c_rect.top + 30))

        surface.set_clip(None)

        # 4. Right Column: Detailed Dossier
        cur_data = ENEMY_CODEX_DATA.get(self.selected_codex_id, all_entries[0])
        dossier_rect = pygame.Rect(mx + 360, my + 90, mw - 385, mh - 135)
        pygame.draw.rect(surface, (16, 20, 28), dossier_rect, border_radius=8)
        pygame.draw.rect(surface, (45, 55, 75), dossier_rect, 1, border_radius=8)

        # A. Live Preview Box (Observation Chamber)
        p_box = pygame.Rect(dossier_rect.left + 14, dossier_rect.top + 14, 250, 205)
        pygame.draw.rect(surface, (10, 13, 18), p_box, border_radius=8)
        pygame.draw.rect(surface, COLOR_BRASS, p_box, 2, border_radius=8)
        
        # Grid/Radar lines
        cx, cy = p_box.centerx, p_box.centery + 10
        pygame.draw.circle(surface, (22, 28, 38), (cx, cy), 75, 1)
        pygame.draw.circle(surface, (22, 28, 38), (cx, cy), 45, 1)
        pygame.draw.line(surface, (22, 28, 38), (cx - 85, cy), (cx + 85, cy), 1)
        pygame.draw.line(surface, (22, 28, 38), (cx, cy - 85), (cx, cy + 85), 1)

        # Live Animated Enemy Drawing
        surface.set_clip(p_box)
        inst = self.codex_preview_cache.get(cur_data["id"])
        if not inst:
            inst = cur_data["factory"](cx, cy)
            self.codex_preview_cache[cur_data["id"]] = inst

        inst.pos = pygame.math.Vector2(cx, cy)
        t = pygame.time.get_ticks() * 0.002
        inst.walk_distance = (pygame.time.get_ticks() * 0.04) % 1000.0
        inst.facing_angle = math.sin(t * 0.7) * 0.25 + math.pi * 0.5
        inst.flash_timer = 0.0
        inst.state = "chase"
        inst.state_timer = 1.0

        # Draw the animated model!
        inst.draw(surface, self.dummy_preview_camera)
        surface.set_clip(None)

        # Top-right status ribbon on preview box
        is_cur_enc = (cur_data["id"] in self.progression.encountered_enemies)
        prev_ribbon = pygame.Rect(p_box.left + 6, p_box.top + 6, p_box.width - 12, 22)
        if is_cur_enc:
            pygame.draw.rect(surface, (18, 48, 28), prev_ribbon, border_radius=4)
            r_txt = self.font_tag.render("✓ RECORDED IN FIELD LOG", True, (80, 240, 140))
        else:
            pygame.draw.rect(surface, (45, 34, 16), prev_ribbon, border_radius=4)
            r_txt = self.font_tag.render("✦ UNSEEN RECON INTEL", True, (255, 205, 90))
        surface.blit(r_txt, r_txt.get_rect(center=prev_ribbon.center))

        # B. Vitals & Profile Panel
        v_left = p_box.right + 16
        v_w = dossier_rect.right - v_left - 14
        
        # Name & Subtitle
        name_surf = self.font_title.render(cur_data["name"], True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(name_surf, (v_left, dossier_rect.top + 14))
        sub_surf = self.font_body.render(f"— {cur_data['subtitle']}", True, (180, 210, 240))
        surface.blit(sub_surf, (v_left, dossier_rect.top + 40))

        # Habitat & Threat
        hab_surf = self.font_tag.render(f"HABITAT: {cur_data['stage']}", True, (210, 180, 140))
        surface.blit(hab_surf, (v_left, dossier_rect.top + 62))

        # Stars
        stars_str = "★" * cur_data["threat_stars"] + "☆" * (5 - cur_data["threat_stars"])
        threat_surf = self.font_tag.render(f"THREAT LEVEL: {stars_str}", True, COLOR_CRIT_YELLOW)
        surface.blit(threat_surf, (v_left, dossier_rect.top + 80))

        # Vitals Pill Box
        vitals_bar = pygame.Rect(v_left, dossier_rect.top + 102, v_w, 32)
        pygame.draw.rect(surface, (22, 28, 38), vitals_bar, border_radius=6)
        pygame.draw.rect(surface, (50, 60, 80), vitals_bar, 1, border_radius=6)
        vit_txt = self.font_tag.render(
            f"BASE HEALTH: {cur_data['base_health']} HP   |   SPEED: {cur_data['base_speed']:.0f} px/s   |   TIER: {cur_data['category'].upper()}",
            True, COLOR_WHITE
        )
        surface.blit(vit_txt, vit_txt.get_rect(center=vitals_bar.center))

        # Lore Quote Box
        lore_box = pygame.Rect(v_left, dossier_rect.top + 142, v_w, 75)
        pygame.draw.rect(surface, (18, 22, 30), lore_box, border_radius=6)
        pygame.draw.rect(surface, (40, 50, 65), lore_box, 1, border_radius=6)
        l_hdr = self.font_tag.render("CONDUCTOR DISPATCH NOTE:", True, (150, 175, 205))
        surface.blit(l_hdr, (lore_box.left + 10, lore_box.top + 6))
        self._draw_multiline_text(
            surface, f'"{cur_data["lore"]}"',
            lore_box.left + 10, lore_box.top + 24,
            lore_box.width - 20, self.font_tag, (190, 205, 225), line_spacing=15
        )

        # C. Bottom Section: Attack Patterns & Behaviors
        atk_top_y = dossier_rect.top + 230
        pygame.draw.line(surface, (45, 55, 75), (dossier_rect.left + 14, atk_top_y), (dossier_rect.right - 14, atk_top_y), 1)

        atk_hdr = self.font_header.render("✦ RECONNAISSANCE ATTACK PATTERNS & BEHAVIORS ✦", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(atk_hdr, (dossier_rect.left + 14, atk_top_y + 10))

        cur_atk_y = atk_top_y + 36
        for atk in cur_data["attacks"]:
            a_title = self.font_body.render(f"• {atk['name']}  [{atk['type'].upper()}]", True, COLOR_WHITE)
            surface.blit(a_title, (dossier_rect.left + 14, cur_atk_y))
            cur_atk_y += 18
            cur_atk_y = self._draw_multiline_text(
                surface, atk["desc"],
                dossier_rect.left + 26, cur_atk_y,
                dossier_rect.width - 50, self.font_tag, (175, 190, 210), line_spacing=15
            )
            cur_atk_y += 6

        # Tactical Counter-Measures Box
        tact_box = pygame.Rect(dossier_rect.left + 14, dossier_rect.bottom - 60, dossier_rect.width - 28, 48)
        pygame.draw.rect(surface, (36, 30, 20), tact_box, border_radius=6)
        pygame.draw.rect(surface, COLOR_BRASS, tact_box, 1, border_radius=6)
        t_hdr = self.font_tag.render("TACTICAL ADVICE:", True, COLOR_CRIT_YELLOW)
        surface.blit(t_hdr, (tact_box.left + 10, tact_box.top + 6))
        self._draw_multiline_text(
            surface, cur_data["tactics"],
            tact_box.left + 10, tact_box.top + 22,
            tact_box.width - 20, self.font_tag, (230, 240, 255), line_spacing=14
        )

        # 5. Footer Hint
        f_hint = self.font_body.render("[↑/↓] Select Hostile | [←/→] Filter Category | [CLICK] Inspect | [ESC / E / B] Close Codex", True, (160, 180, 205))
        surface.blit(f_hint, f_hint.get_rect(center=(mx + mw // 2, my + mh - 16)))

    def _draw_workshop_modal(self, surface: pygame.Surface):
        # Dark backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 16, 225))
        surface.blit(overlay, (0, 0))

        mw, mh = 660, 480
        mx = (SCREEN_WIDTH - mw) // 2
        my = (SCREEN_HEIGHT - mh) // 2
        m_rect = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(surface, (22, 26, 36), m_rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS, m_rect, 3, border_radius=12)

        # Header
        t_surf = self.font_title.render("STOKER WORKSHOP — PERMANENT PERKS", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(t_surf, (mx + 25, my + 20))
        sc_text = self.font_header.render(f"Available Scrap: {self.progression.scrap}", True, (255, 215, 80))
        surface.blit(sc_text, (mx + mw - 220, my + 24))

        # Close button [X]
        close_btn = pygame.Rect(mx + mw - 45, my + 15, 30, 30)
        pygame.draw.rect(surface, (45, 25, 30), close_btn, border_radius=6)
        c_x = self.font_header.render("X", True, COLOR_WHITE)
        surface.blit(c_x, c_x.get_rect(center=close_btn.center))

        mouse_pos = pygame.mouse.get_pos()
        self.hovered_perk_id = None
        cur_y = my + 65

        for i, (pk, pdata) in enumerate(PERK_DEFINITIONS.items()):
            cur_rank = self.progression.perks.get(pk, 0)
            max_rank = pdata["max_rank"]
            cost = self.progression.get_perk_cost(pk)
            can_afford = (cost > 0 and self.progression.scrap >= cost)

            p_box = pygame.Rect(mx + 25, cur_y, mw - 50, 70)
            is_hover = p_box.collidepoint(mouse_pos)
            pygame.draw.rect(surface, (30, 35, 48) if is_hover else (26, 30, 42), p_box, border_radius=8)
            pygame.draw.rect(surface, COLOR_BRASS if is_hover else (50, 60, 80), p_box, 1, border_radius=8)

            # Name and rank
            n_text = self.font_header.render(f"[{i + 1}] {pdata['name']} (Rank {cur_rank}/{max_rank})", True, COLOR_BRASS_HIGHLIGHT if cur_rank > 0 else COLOR_WHITE)
            surface.blit(n_text, (p_box.left + 14, p_box.top + 8))

            # Description
            d_text = self.font_tag.render(pdata["desc"], True, (180, 195, 210))
            surface.blit(d_text, (p_box.left + 14, p_box.top + 34))

            # Buy button
            btn_w = 120
            btn_rect = pygame.Rect(p_box.right - btn_w - 14, p_box.top + 16, btn_w, 38)
            if cur_rank >= max_rank:
                pygame.draw.rect(surface, (40, 50, 45), btn_rect, border_radius=6)
                b_lbl = self.font_tag.render("MAX RANK", True, (130, 200, 160))
            elif can_afford:
                if btn_rect.collidepoint(mouse_pos):
                    self.hovered_perk_id = pk
                    pygame.draw.rect(surface, (160, 120, 40), btn_rect, border_radius=6)
                else:
                    pygame.draw.rect(surface, (120, 90, 30), btn_rect, border_radius=6)
                pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, btn_rect, 2, border_radius=6)
                b_lbl = self.font_body.render(f"{cost} Scrap", True, COLOR_WHITE)
            else:
                pygame.draw.rect(surface, (35, 38, 45), btn_rect, border_radius=6)
                b_lbl = self.font_tag.render(f"{cost} Scrap", True, (130, 130, 130))

            surface.blit(b_lbl, b_lbl.get_rect(center=btn_rect.center))
            cur_y += 78

        # Footer Hint
        hint = self.font_body.render("Press [1-5] or Click to upgrade perk. Press [E] or [ESC] to exit workshop.", True, (170, 185, 205))
        surface.blit(hint, hint.get_rect(center=(mx + mw // 2, my + mh - 22)))
