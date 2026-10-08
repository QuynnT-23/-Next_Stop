"""Heads-Up Display showing player health, dash charges, car progression, enemy count, and radar."""
import pygame
import math
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_WHITE, COLOR_HEALTH_GREEN, COLOR_HEALTH_BG, COLOR_HEALTH_LOST,
    COLOR_STAMINA_CYAN, COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_EMBER_ORANGE
)
from src.combat.boons import get_active_synergies

class HUD:
    """Renders player stats, active weapon, current car, enemy count, and navigation aids."""
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 18, bold=True)
        self.font_body = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)
        self.font_small = pygame.font.SysFont("Helvetica, Arial, sans-serif", 12)
        self.font_boss = pygame.font.SysFont("Helvetica, Arial, sans-serif", 20, bold=True)
        self.font_status = pygame.font.SysFont("Helvetica, Arial, sans-serif", 15, bold=True)

    def draw(self, surface: pygame.Surface, player, run_manager, enemies: list = None, train_car = None, camera = None, boss = None):
        # 1. Health Bar (Top-Left)
        bar_x = 30
        bar_y = 25
        bar_w = 240
        bar_h = 22
        
        # Background frame
        pygame.draw.rect(surface, COLOR_STEEL_DARK, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), border_radius=6)
        pygame.draw.rect(surface, COLOR_BRASS, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), 2, border_radius=6)
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        
        # Health Fill
        health_pct = max(0.0, min(1.0, player.health / player.max_health))
        fill_w = int(bar_w * health_pct)
        if fill_w > 0:
            pygame.draw.rect(surface, COLOR_HEALTH_GREEN, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

        # Health Text
        hp_str = f"{player.health} / {player.max_health} HP"
        hp_surf = self.font_body.render(hp_str, True, COLOR_WHITE)
        surface.blit(hp_surf, (bar_x + 10, bar_y + 3))

        # 2. Dash Charges (Under Health Bar)
        dash_y = bar_y + bar_h + 10
        for i in range(player.max_dash_charges):
            cx = bar_x + 14 + i * 28
            cy = dash_y + 10
            pygame.draw.circle(surface, COLOR_STEEL_DARK, (cx, cy), 10)
            if i < player.dash_charges:
                pygame.draw.circle(surface, COLOR_STAMINA_CYAN, (cx, cy), 8)
            else:
                pygame.draw.circle(surface, (60, 70, 80), (cx, cy), 8)
                if i == player.dash_charges:
                    prog = player.dash_recharge_timer / (player.dash_cooldown_mult * 0.75)
                    pygame.draw.circle(surface, COLOR_STAMINA_CYAN, (cx, cy), max(2, int(8 * min(1.0, prog))))

        dash_label = self.font_small.render("DASH: [2xWASD / R-CLICK]  |  BLOCK: [HOLD SHIFT]", True, (170, 180, 195))
        surface.blit(dash_label, (bar_x + 65, dash_y + 4))

        # 3. Active Weapon Info
        if player.weapon:
            weap_y = dash_y + 28
            weap_text = self.font_body.render(f"WEAPON: {player.weapon.name}", True, COLOR_BRASS_HIGHLIGHT)
            surface.blit(weap_text, (bar_x, weap_y))
            ctrl_text = self.font_small.render("ATTACK: [SPACE / CLICK]", True, (170, 185, 205))
            surface.blit(ctrl_text, (bar_x, weap_y + 18))

            # Timed Overcharge Boost Indicator
            if getattr(player, "attack_boost_timer", 0.0) > 0:
                boost_y = weap_y + 36
                pulse = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
                b_rect = pygame.Rect(bar_x, boost_y, 220, 20)
                pygame.draw.rect(surface, (36, 30, 12), b_rect, border_radius=4)
                border_col = (int(215 + 40 * pulse), 190, 40)
                pygame.draw.rect(surface, border_col, b_rect, 1, border_radius=4)
                boost_str = f"OVERCHARGE: {player.attack_boost_timer:.1f}s (+35% SPD)"
                boost_surf = self.font_small.render(boost_str, True, (255, 230, 110))
                surface.blit(boost_surf, (bar_x + 8, boost_y + 3))

            # 3b. Super Ability Gauge Bar
            super_y = weap_y + 36
            if getattr(player, "attack_boost_timer", 0.0) > 0:
                super_y += 24

            s_bar_w = 220
            s_bar_h = 16
            s_pct = max(0.0, min(1.0, getattr(player, "super_charge", 0.0) / max(1.0, getattr(player, "max_super_charge", 100.0))))
            is_ready = getattr(player, "can_cast_super", lambda: False)()

            pygame.draw.rect(surface, (18, 20, 26), (bar_x - 3, super_y - 3, s_bar_w + 6, s_bar_h + 6), border_radius=4)
            if is_ready:
                pulse = (math.sin(pygame.time.get_ticks() * 0.016) + 1) * 0.5
                border_c = (int(220 + 35 * pulse), int(180 + 50 * pulse), 40)
                pygame.draw.rect(surface, border_c, (bar_x - 3, super_y - 3, s_bar_w + 6, s_bar_h + 6), 2, border_radius=4)
                pygame.draw.rect(surface, (255, 195, 45), (bar_x, super_y, s_bar_w, s_bar_h), border_radius=3)
                super_txt = self.font_small.render("[E] SUPER READY!", True, (20, 20, 24))
                surface.blit(super_txt, (bar_x + 8, super_y + 1))
            else:
                pygame.draw.rect(surface, COLOR_BRASS, (bar_x - 3, super_y - 3, s_bar_w + 6, s_bar_h + 6), 1, border_radius=4)
                s_fill_w = int(s_bar_w * s_pct)
                if s_fill_w > 0:
                    pygame.draw.rect(surface, (175, 110, 25), (bar_x, super_y, s_fill_w, s_bar_h), border_radius=3)
                super_txt = self.font_small.render(f"SUPER: {int(s_pct * 100)}%", True, (200, 195, 180))
                surface.blit(super_txt, (bar_x + 8, super_y + 1))

        # 4. Top-Center Car Tracker & Objective Status
        car_info = run_manager.get_current_car_info()
        track_str = f"{run_manager.route_data['name'].upper()} — CAR {run_manager.current_car_index + 1} OF {run_manager.total_cars}: {car_info['name'].upper()}"
        track_surf = self.font_title.render(track_str, True, COLOR_BRASS_HIGHLIGHT)
        track_rect = track_surf.get_rect(center=(SCREEN_WIDTH // 2, 28))
        
        header_bg = pygame.Rect(track_rect.x - 16, track_rect.y - 6, track_rect.width + 32, track_rect.height + 12)
        bg_surf = pygame.Surface((header_bg.width, header_bg.height), pygame.SRCALPHA)
        bg_surf.fill((15, 18, 24, 210))
        surface.blit(bg_surf, header_bg.topleft)
        pygame.draw.rect(surface, COLOR_BRASS, header_bg, 1, border_radius=4)
        surface.blit(track_surf, track_rect)

        # Objective Banner (Enemies Remaining vs Car Cleared)
        if enemies is not None and train_car is not None:
            living_count = len([e for e in enemies if e.is_alive()])
            if living_count > 0:
                status_str = f"ENEMIES REMAINING: {living_count}"
                status_col = (255, 150, 50)
                status_bg_col = (45, 20, 10, 200)
                border_col = (240, 100, 30)
            else:
                if getattr(train_car, "boon_pedestal_active", False) and not getattr(train_car, "boon_claimed", False):
                    status_str = ">>> CAR SECURED! CLAIM CAR UPGRADE TO UNLOCK EXIT >>>"
                    status_col = (255, 205, 50)
                    status_bg_col = (45, 35, 10, 220)
                    border_col = (235, 175, 40)
                else:
                    status_str = ">>> UPGRADE CLAIMED! EXIT UNLOCKED → NEXT CAR >>>"
                    status_col = (80, 255, 150)
                    status_bg_col = (10, 45, 20, 220)
                    border_col = (50, 220, 110)

            status_surf = self.font_status.render(status_str, True, status_col)
            status_rect = status_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
            
            s_bg = pygame.Rect(status_rect.x - 12, status_rect.y - 3, status_rect.width + 24, status_rect.height + 6)
            s_surf = pygame.Surface((s_bg.width, s_bg.height), pygame.SRCALPHA)
            s_surf.fill(status_bg_col)
            surface.blit(s_surf, s_bg.topleft)
            pygame.draw.rect(surface, border_col, s_bg, 1, border_radius=4)
            surface.blit(status_surf, status_rect)

        # 5. Offscreen Radar Waypoints (Guides player towards offscreen enemies or to the exit!)
        if camera and train_car and enemies is not None:
            self._draw_radar_waypoints(surface, camera, train_car, enemies)

        # 6. Top-Right Active Boons & Duo Synergies
        if player.boons:
            active_syns = get_active_synergies(player.boons)
            
            start_rx = SCREEN_WIDTH - 230
            start_ry = 20
            boons_header = self.font_body.render("ARSENAL ABILITIES:", True, COLOR_WHITE)
            surface.blit(boons_header, (start_rx, start_ry))
            cur_y = start_ry + 22

            # Render Duo Synergies first with highlighted border
            for syn in active_syns:
                badge_rect = pygame.Rect(start_rx, cur_y, 215, 20)
                pygame.draw.rect(surface, (20, 24, 32), badge_rect, border_radius=4)
                pygame.draw.rect(surface, syn["color"], badge_rect, 1, border_radius=4)
                syn_txt = self.font_small.render(f"[DUO] {syn['name']}", True, syn["color"])
                surface.blit(syn_txt, (start_rx + 8, cur_y + 3))
                cur_y += 24

            for i, boon in enumerate(player.boons):
                badge_rect = pygame.Rect(start_rx, cur_y, 215, 18)
                pygame.draw.rect(surface, (25, 28, 35), badge_rect, border_radius=3)
                pygame.draw.rect(surface, boon.color, (start_rx, cur_y, 4, 18))
                b_text = self.font_small.render(boon.get_display_name(), True, COLOR_WHITE)
                surface.blit(b_text, (start_rx + 8, cur_y + 2))
                cur_y += 22

        # 7. Boss Health Bar (Bottom of Screen)
        if boss and boss.is_alive():
            self._draw_boss_bar(surface, boss)

    def _draw_radar_waypoints(self, surface: pygame.Surface, camera, train_car, enemies: list):
        """Draws indicator chevrons on screen edges pointing to off-screen targets."""
        view_left = camera.offset.x
        view_right = camera.offset.x + SCREEN_WIDTH
        
        living_enemies = [e for e in enemies if e.is_alive()]
        if living_enemies:
            # Check if all living enemies are to the right of current screen view
            enemies_ahead = [e for e in living_enemies if e.pos.x > view_right - 40]
            if enemies_ahead:
                # Draw pulsing red chevron on right edge
                pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
                rx = SCREEN_WIDTH - 130
                ry = SCREEN_HEIGHT // 2
                
                badge = pygame.Rect(rx, ry - 18, 115, 36)
                pygame.draw.rect(surface, (50, 15, 15), badge, border_radius=6)
                pygame.draw.rect(surface, (255, 60, 60), badge, 2, border_radius=6)
                
                txt = self.font_small.render("ENEMY AHEAD >>", True, (255, 120, 120))
                surface.blit(txt, txt.get_rect(center=badge.center))
        elif train_car.exit_unlocked:
            # Door is to the right!
            door_world_x = train_car.width - 60
            if door_world_x > view_right - 60:
                # Draw green chevron pointing to exit door
                rx = SCREEN_WIDTH - 140
                ry = SCREEN_HEIGHT // 2
                badge = pygame.Rect(rx, ry - 18, 125, 36)
                pygame.draw.rect(surface, (15, 45, 20), badge, border_radius=6)
                pygame.draw.rect(surface, (50, 230, 110), badge, 2, border_radius=6)
                txt = self.font_small.render("NEXT CAR >>", True, (100, 255, 150))
                surface.blit(txt, txt.get_rect(center=badge.center))

    def _draw_boss_bar(self, surface: pygame.Surface, boss):
        bw = 680
        bh = 22
        bx = (SCREEN_WIDTH - bw) // 2
        by = SCREEN_HEIGHT - 65

        pygame.draw.rect(surface, COLOR_STEEL_DARK, (bx - 4, by - 4, bw + 8, bh + 8), border_radius=6)
        pygame.draw.rect(surface, COLOR_BRASS, (bx - 4, by - 4, bw + 8, bh + 8), 2, border_radius=6)
        pygame.draw.rect(surface, (50, 20, 20), (bx, by, bw, bh), border_radius=4)

        pct = max(0.0, min(1.0, boss.health / boss.max_health))
        fill_w = int(bw * pct)
        if fill_w > 0:
            bar_col = (220, 60, 60) if boss.phase == 1 else (255, 120, 20)
            pygame.draw.rect(surface, bar_col, (bx, by, fill_w, bh), border_radius=4)

        if getattr(boss, "is_miniboss", False):
            title_str = f"=== ENCOUNTER: {boss.name.upper()} (PHASE {boss.phase}) ==="
        else:
            title_str = f"=== THE CONDUCTOR — {boss.name.upper()} (PHASE {boss.phase}) ==="
        title_surf = self.font_boss.render(title_str, True, COLOR_WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, by - 16))
        surface.blit(title_surf, title_rect)
