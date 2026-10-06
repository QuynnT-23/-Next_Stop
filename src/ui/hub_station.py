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

class HubStation:
    """Interactive, walkable Grand Central Terminal Hub with docking bays, workshop, and armory."""
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

        # Armory Racks (Right Hall)
        self.armory_rect = pygame.Rect(SCREEN_WIDTH - 270, SCREEN_HEIGHT // 2 - 20, 160, 120)

        # Input / Board buffer
        self.board_cooldown = 0.0

    def reset_player(self):
        """Reset player position and state when returning to Grand Central Terminal Hub."""
        self.player_pos = pygame.math.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180)
        self.player_vel = pygame.math.Vector2(0, 0)
        self.facing_angle = -math.pi / 2
        self.show_workshop = False
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
                else:
                    # Click on gate to board (only single active track is boardable)
                    if self.board_cooldown <= 0.0:
                        for bay in self.docking_bays:
                            if bay["door_rect"].collidepoint(event.pos):
                                if self.progression.get_track_state(bay["route_id"]) == "active":
                                    self.selected_route_id = bay["route_id"]
                                    return True

        # Process movement
        self.update(0.016)

        # Auto-board if walking directly into gate threshold (only single active track)
        if not self.show_workshop and self.board_cooldown <= 0.0:
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

        if not self.show_workshop:
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
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 26)))
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 48)))

        # Scrap Metal Counter (Top Right)
        scrap_bar = pygame.Rect(SCREEN_WIDTH - 220, 16, 200, 48)
        pygame.draw.rect(surface, (18, 22, 30), scrap_bar, border_radius=8)
        pygame.draw.rect(surface, COLOR_BRASS, scrap_bar, 1, border_radius=8)
        sc_lbl = self.font_header.render(f"SCRAP: {self.progression.scrap}", True, (255, 210, 80))
        surface.blit(sc_lbl, (scrap_bar.left + 16, scrap_bar.top + 14))

        # Bottom Controls Hint
        ctrl_str = "[WASD] Move Stoker | [MOUSE] Aim | [1-4] Quick Equip Weapon | [E / STEP IN GATE] Depart on Train | [E AT ANVIL] Workshop Upgrades"
        ctrl_surf = self.font_body.render(ctrl_str, True, (160, 175, 195))
        surface.blit(ctrl_surf, ctrl_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)))

        # 8. Render Workshop Modal if open
        if self.show_workshop:
            self._draw_workshop_modal(surface)

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
