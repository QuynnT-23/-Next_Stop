"""Conductor Honor Roll Leaderboard Modal (Art Deco Terminal Board)."""
import pygame
import math
import time
from typing import Optional, List, Dict, Any
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_WHITE, COLOR_CRIT_YELLOW, COLOR_EMBER_ORANGE
)
from src.core.leaderboard import LeaderboardClient

class LeaderboardMenu:
    """Full-screen modal displaying the station's Conductor Honor Roll."""
    def __init__(self, leaderboard_client: Optional[LeaderboardClient] = None):
        pygame.font.init()
        self.client = leaderboard_client or LeaderboardClient()
        self.is_open = False
        
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 24, bold=True)
        self.font_header = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)
        self.font_body = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13, bold=True)
        self.font_tag = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11, bold=True)

        self.tab_options = [
            ("all", "ALL TRACKS"),
            ("steam", "TRACK 1: STEAM"),
            ("derelict", "TRACK 2: DERELICT"),
            ("subway", "TRACK 3: SUBWAY"),
            ("cryo", "TRACK 4: CRYO"),
            ("infernal", "TRACK 5: INFERNAL"),
        ]
        self.active_tab_idx = 0
        self.scroll_y = 0

        # Modal bounds
        self.w, self.h = 1000, 580
        self.rect = pygame.Rect((SCREEN_WIDTH - self.w) // 2, (SCREEN_HEIGHT - self.h) // 2, self.w, self.h)

    def open(self):
        self.is_open = True
        self.scroll_y = 0

    def close(self):
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_h):
                self.close()
                return True
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.active_tab_idx = (self.active_tab_idx - 1) % len(self.tab_options)
                self.scroll_y = 0
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.active_tab_idx = (self.active_tab_idx + 1) % len(self.tab_options)
                self.scroll_y = 0
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.scroll_y = max(0, self.scroll_y - 45)
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.scroll_y += 45
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check close button
            close_btn = pygame.Rect(self.rect.right - 44, self.rect.top + 14, 30, 30)
            if close_btn.collidepoint(event.pos):
                self.close()
                return True

            # Check tabs
            tab_x = self.rect.left + 25
            tab_y = self.rect.top + 58
            for idx, (tab_id, tab_label) in enumerate(self.tab_options):
                tab_rect = pygame.Rect(tab_x, tab_y, 145, 28)
                if tab_rect.collidepoint(event.pos):
                    self.active_tab_idx = idx
                    self.scroll_y = 0
                    return True
                tab_x += 152

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - int(event.y * 35))
            return True

        return True

    def draw(self, surface: pygame.Surface):
        if not self.is_open:
            return

        # Dim background
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        surface.blit(dim, (0, 0))

        # Main Board Card
        pygame.draw.rect(surface, (18, 22, 30), self.rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS, self.rect, 2, border_radius=12)

        # Header Title
        title_surf = self.font_title.render("★ GRAND CENTRAL CONDUCTOR HONOR ROLL ★", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(title_surf, title_surf.get_rect(center=(self.rect.centerx, self.rect.top + 28)))

        # Close button
        close_btn = pygame.Rect(self.rect.right - 44, self.rect.top + 14, 30, 30)
        mouse_pos = pygame.mouse.get_pos()
        hover_close = close_btn.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (140, 40, 40) if hover_close else (80, 24, 24), close_btn, border_radius=4)
        c_txt = self.font_body.render("✕", True, COLOR_WHITE)
        surface.blit(c_txt, c_txt.get_rect(center=close_btn.center))

        # Tabs
        tab_x = self.rect.left + 25
        tab_y = self.rect.top + 58
        for idx, (tab_id, tab_label) in enumerate(self.tab_options):
            active = (idx == self.active_tab_idx)
            tab_rect = pygame.Rect(tab_x, tab_y, 145, 28)
            hover = tab_rect.collidepoint(mouse_pos)
            bg = (40, 52, 68) if active else ((28, 36, 48) if hover else (20, 26, 36))
            pygame.draw.rect(surface, bg, tab_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT if active else (70, 90, 115), tab_rect, 2 if active else 1, border_radius=4)
            lbl = self.font_tag.render(tab_label, True, COLOR_BRASS_HIGHLIGHT if active else COLOR_WHITE)
            surface.blit(lbl, lbl.get_rect(center=tab_rect.center))
            tab_x += 152

        # Table Header
        th_rect = pygame.Rect(self.rect.left + 25, self.rect.top + 98, self.rect.width - 50, 30)
        pygame.draw.rect(surface, (26, 34, 46), th_rect, border_radius=4)
        pygame.draw.line(surface, COLOR_BRASS, th_rect.bottomleft, th_rect.bottomright, 1)

        cols = [
            ("RANK", 60),
            ("CONDUCTOR", 220),
            ("TRACK & ROUTE", 200),
            ("CARS", 75),
            ("WEAPON", 160),
            ("STATUS", 100),
            ("SCORE", 110)
        ]
        cx = th_rect.left + 12
        for h_label, h_w in cols:
            h_surf = self.font_tag.render(h_label, True, (170, 195, 225))
            surface.blit(h_surf, (cx, th_rect.centery - 6))
            cx += h_w

        # Scores List
        active_tab_id = self.tab_options[self.active_tab_idx][0]
        scores = self.client.get_top_scores(limit=30, route_id=active_tab_id)

        rows_area = pygame.Rect(self.rect.left + 25, self.rect.top + 134, self.rect.width - 50, self.rect.height - 180)
        row_h = 36

        # Clip scores area
        old_clip = surface.get_clip()
        surface.set_clip(rows_area)

        if not scores:
            empty_lbl = self.font_header.render("NO CONDUCTOR RUNS RECORDED YET FOR THIS TRACK", True, (130, 145, 165))
            surface.blit(empty_lbl, empty_lbl.get_rect(center=rows_area.center))
        else:
            for i, row in enumerate(scores):
                ry = rows_area.top + i * (row_h + 4) - self.scroll_y
                if ry + row_h < rows_area.top or ry > rows_area.bottom:
                    continue
                r_rect = pygame.Rect(rows_area.left, ry, rows_area.width, row_h)
                
                # Highlight top 3
                if i == 0:
                    bg_col = (38, 34, 22)
                    border_col = (255, 215, 0)
                elif i == 1:
                    bg_col = (30, 34, 38)
                    border_col = (210, 220, 230)
                elif i == 2:
                    bg_col = (34, 28, 24)
                    border_col = (205, 127, 50)
                else:
                    bg_col = (22, 28, 38) if i % 2 == 0 else (18, 23, 32)
                    border_col = (45, 60, 80)

                pygame.draw.rect(surface, bg_col, r_rect, border_radius=4)
                pygame.draw.rect(surface, border_col, r_rect, 1, border_radius=4)

                # Render row values
                rx = r_rect.left + 12
                # Rank
                rank_str = f"#{i + 1}"
                if i == 0:
                    rank_str = "🥇 #1"
                elif i == 1:
                    rank_str = "🥈 #2"
                elif i == 2:
                    rank_str = "🥉 #3"
                rank_surf = self.font_body.render(rank_str, True, border_col if i < 3 else (180, 200, 220))
                surface.blit(rank_surf, (rx, r_rect.centery - 8))
                rx += cols[0][1]

                # Name
                name_str = row.get("player_name", "Stoker")
                name_surf = self.font_body.render(name_str[:18], True, COLOR_WHITE)
                surface.blit(name_surf, (rx, r_rect.centery - 8))
                rx += cols[1][1]

                # Route
                rt_str = row.get("route_name", "Steam Line")
                loop = row.get("loop_count", 0)
                if loop > 0:
                    rt_str += f" [L{loop + 1}]"
                rt_surf = self.font_tag.render(rt_str[:20], True, (190, 215, 240))
                surface.blit(rt_surf, (rx, r_rect.centery - 7))
                rx += cols[2][1]

                # Cars
                cars_str = f"{row.get('cars_cleared', 1)}/15"
                cars_surf = self.font_tag.render(cars_str, True, COLOR_WHITE)
                surface.blit(cars_surf, (rx, r_rect.centery - 7))
                rx += cols[3][1]

                # Weapon
                wpn_str = row.get("weapon_name", "Riveter")
                wpn_surf = self.font_tag.render(wpn_str[:16], True, (240, 215, 140))
                surface.blit(wpn_surf, (rx, r_rect.centery - 7))
                rx += cols[4][1]

                # Status
                vic = row.get("is_victory", False)
                st_str = "VICTORY" if vic else "RETIRED"
                st_col = (110, 240, 150) if vic else (230, 110, 110)
                st_surf = self.font_tag.render(st_str, True, st_col)
                surface.blit(st_surf, (rx, r_rect.centery - 7))
                rx += cols[5][1]

                # Score
                sc_str = f"{row.get('score', 0):,}"
                sc_surf = self.font_header.render(sc_str, True, COLOR_BRASS_HIGHLIGHT)
                surface.blit(sc_surf, (rx, r_rect.centery - 9))

        surface.set_clip(old_clip)

        # Footer Hint
        hint_str = "[ESC / E] Close Board | [ARROW KEYS] Switch Track Filter & Scroll | [MOUSE WHEEL] Scroll"
        hint_surf = self.font_tag.render(hint_str, True, (150, 165, 185))
        surface.blit(hint_surf, hint_surf.get_rect(center=(self.rect.centerx, self.rect.bottom - 22)))
