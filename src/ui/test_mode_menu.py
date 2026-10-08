"""In-Game Test Mode & Dev Console modal for testing tracks, cars, levels, scrap, and combat cheats."""
import pygame
import math
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_STEEL_DARK, COLOR_STEEL_MID,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_WHITE, COLOR_CRIT_YELLOW,
    COLOR_EMBER_ORANGE, COLOR_SHADOW, COLOR_STAMINA_CYAN
)
from src.core.progression import ALL_STAGES, SUPER_ABILITIES
from src.combat.weapons import AVAILABLE_WEAPONS
from src.level.car_generator import TRAIN_ROUTES

class TestButton:
    """A clickable button within the test mode console."""
    def __init__(self, rect: pygame.Rect, label: str, action, color=(35, 42, 54),
                 border_color=COLOR_BRASS, active=False, text_color=COLOR_WHITE):
        self.rect = rect
        self.label = label
        self.action = action
        self.color = color
        self.border_color = border_color
        self.active = active
        self.text_color = text_color
        self.hovered = False

    def update(self, mouse_pos: tuple[int, int]) -> bool:
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        # Background
        bg_col = self.color
        if self.active:
            bg_col = (50, 110, 75) if "ON" in self.label or "ACTIVE" in self.label else (60, 75, 100)
        elif self.hovered:
            bg_col = (min(255, bg_col[0] + 35), min(255, bg_col[1] + 35), min(255, bg_col[2] + 45))

        border_col = COLOR_BRASS_HIGHLIGHT if (self.hovered or self.active) else self.border_color
        border_w = 2 if (self.hovered or self.active) else 1

        pygame.draw.rect(surface, bg_col, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.rect, border_w, border_radius=6)

        # Label
        text_surf = font.render(self.label, True, COLOR_WHITE if (self.hovered or self.active) else self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))


class TestModeMenu:
    """Full-featured Art Deco test console modal allowing players to adjust all game parameters."""
    def __init__(self, game):
        self.game = game
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 22, bold=True)
        self.font_section = pygame.font.SysFont("Helvetica, Arial, sans-serif", 15, bold=True)
        self.font_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 13, bold=True)
        self.font_btn_sm = pygame.font.SysFont("Helvetica, Arial, sans-serif", 11, bold=True)
        self.font_val = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)
        self.font_toast = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)

        # Modal bounds
        self.width = 1040
        self.height = 640
        self.rect = pygame.Rect(
            (SCREEN_WIDTH - self.width) // 2,
            (SCREEN_HEIGHT - self.height) // 2,
            self.width,
            self.height
        )

        # Selection state for testing
        self.selected_track_idx = 0
        self.selected_loop_count = 0
        self.selected_car_idx = 0
        self.toast_message = ""
        self.toast_timer = 0.0

        self.buttons: list[TestButton] = []
        self._sync_state_from_game()
        self._rebuild_buttons()

    def _sync_state_from_game(self):
        """Pull initial selection state from active game and progression."""
        prog = self.game.progression
        self.selected_track_idx = prog.current_track_idx
        self.selected_loop_count = prog.loop_count
        rm = getattr(self.game, "run_manager", None)
        if rm:
            self.selected_car_idx = rm.current_car_index
        else:
            self.selected_car_idx = 0

    def open(self):
        """Called when test console is activated."""
        self._sync_state_from_game()
        self._set_toast("Test Console Opened. Adjust any parameter on the fly.")
        self._rebuild_buttons()

    def _set_toast(self, msg: str, duration: float = 2.5):
        self.toast_message = msg
        self.toast_timer = duration

    def _rebuild_buttons(self):
        """Construct all interactive UI buttons positioned within the modal."""
        self.buttons.clear()
        prog = self.game.progression
        in_run = (self.game.state == self.game.STATE_PLAYING and self.game.run_manager is not None)

        left = self.rect.left + 24
        top = self.rect.top + 60
        col_w = (self.width - 72) // 2  # Two-column layout

        # ==============================================================================
        # COLUMN 1: TRACK & CAR DISPATCH (LEVEL SELECTOR)
        # ==============================================================================
        cy = top + 24

        # Track Buttons
        stage_names = ["1: Steam", "2: Derelict", "3: Subway", "4: Cryo", "5: Infernal"]
        btn_w = (col_w - 16) // 5
        for i, name in enumerate(stage_names):
            r = pygame.Rect(left + i * (btn_w + 4), cy, btn_w, 32)
            self.buttons.append(TestButton(
                r, name,
                action=lambda idx=i: self._on_select_track(idx),
                active=(self.selected_track_idx == i)
            ))

        cy += 42
        # Loop Buttons (Loop 0, Loop 1+, Loop 2++)
        loop_labels = ["Base (Loop 0)", "Loop 1 (+)", "Loop 2 (++)"]
        loop_w = (col_w - 8) // 3
        for l_idx, l_lbl in enumerate(loop_labels):
            r = pygame.Rect(left + l_idx * (loop_w + 4), cy, loop_w, 28)
            self.buttons.append(TestButton(
                r, l_lbl,
                action=lambda l=l_idx: self._on_select_loop(l),
                active=(self.selected_loop_count == l_idx)
            ))

        cy += 40
        # Car Stepper [-1] and [+1]
        step_w = 42
        self.buttons.append(TestButton(
            pygame.Rect(left, cy, step_w, 32), "[-]",
            action=lambda: self._on_step_car(-1),
            color=(45, 52, 65)
        ))
        self.buttons.append(TestButton(
            pygame.Rect(left + col_w - step_w, cy, step_w, 32), "[+]",
            action=lambda: self._on_step_car(1),
            color=(45, 52, 65)
        ))

        cy += 40
        # Quick Car Preset Buttons
        car_presets = [("Car 1", 0), ("Car 5 (Mini)", 4), ("Car 10 (Gnt)", 9), ("Car 15 (Boss)", 14)]
        cp_w = (col_w - 12) // 4
        for i, (label, c_idx) in enumerate(car_presets):
            r = pygame.Rect(left + i * (cp_w + 4), cy, cp_w, 28)
            self.buttons.append(TestButton(
                r, label,
                action=lambda idx=c_idx: self._on_set_car(idx),
                active=(self.selected_car_idx == c_idx)
            ))

        cy += 38
        # Action Deploy / Warp Button
        deploy_label = f"⚡ WARP DIRECTLY TO CAR {self.selected_car_idx + 1}" if in_run else f"⚡ DEPLOY EXPEDITION (CAR {self.selected_car_idx + 1})"
        self.buttons.append(TestButton(
            pygame.Rect(left, cy, col_w, 36), deploy_label,
            action=self._on_deploy,
            color=(70, 45, 20),
            border_color=COLOR_BRASS_HIGHLIGHT
        ))

        # ==============================================================================
        # COLUMN 1 LOWER: ARSENAL & SUPER ABILITY TESTING
        # ==============================================================================
        cy += 64
        # Weapon Buttons
        w_names = [("Riveter", 0), ("Cleaver", 1), ("Scattergun", 2), ("Arc Caster", 3)]
        ww_w = (col_w - 12) // 4
        cur_w_idx = 0
        if in_run and self.game.player:
            for i, w_cls in enumerate(AVAILABLE_WEAPONS):
                if isinstance(self.game.player.weapon, w_cls):
                    cur_w_idx = i
                    break
        elif hasattr(self.game.hub_station, "selected_weapon_idx"):
            cur_w_idx = self.game.hub_station.selected_weapon_idx

        for i, (w_lbl, w_idx) in enumerate(w_names):
            r = pygame.Rect(left + i * (ww_w + 4), cy, ww_w, 30)
            self.buttons.append(TestButton(
                r, w_lbl,
                action=lambda idx=w_idx: self._on_select_weapon(idx),
                active=(cur_w_idx == w_idx)
            ))

        cy += 40
        # Super Ability Buttons
        supers = [
            ("Overdrive", "super_boiler_overdrive"),
            ("Tesla Rail", "super_tesla_rail"),
            ("Cataclysm", "super_infernal_cataclysm")
        ]
        sw_w = (col_w - 8) // 3
        cur_super = prog.equipped_super or (self.game.player.equipped_super_id if in_run and self.game.player else None)
        for i, (s_lbl, s_id) in enumerate(supers):
            r = pygame.Rect(left + i * (sw_w + 4), cy, sw_w, 30)
            self.buttons.append(TestButton(
                r, s_lbl,
                action=lambda sid=s_id: self._on_select_super(sid),
                active=(cur_super == s_id)
            ))

        # ==============================================================================
        # COLUMN 2: PROGRESSION, SCRAP & COMBAT CHEATS
        # ==============================================================================
        c2_left = left + col_w + 24
        c2_y = top + 24

        # Level Steppers: [-5], [-1], [+1], [+5], [Lv 1], [Lv 10], [Lv 25]
        lvl_btns = [("-5", -5), ("-1", -1), ("+1", 1), ("+5", 5)]
        lb_w = (col_w - 12) // 4
        for i, (lbl, delta) in enumerate(lvl_btns):
            r = pygame.Rect(c2_left + i * (lb_w + 4), c2_y, lb_w, 28)
            self.buttons.append(TestButton(
                r, lbl, action=lambda d=delta: self._on_delta_level(d),
                color=(40, 48, 60)
            ))

        c2_y += 34
        lvl_presets = [("Set Lv 1", 1), ("Set Lv 5", 5), ("Set Lv 10", 10), ("Set Lv 25", 25)]
        for i, (lbl, target) in enumerate(lvl_presets):
            r = pygame.Rect(c2_left + i * (lb_w + 4), c2_y, lb_w, 26)
            self.buttons.append(TestButton(
                r, lbl, action=lambda t=target: self._on_set_level(t),
                active=(prog.level == target)
            ))

        # Scrap Currency Steppers & Presets
        c2_y += 42
        scrap_btns = [("+100", 100), ("+500", 500), ("+1000", 1000)]
        sc_w = (col_w - 8) // 3
        for i, (lbl, delta) in enumerate(scrap_btns):
            r = pygame.Rect(c2_left + i * (sc_w + 4), c2_y, sc_w, 28)
            self.buttons.append(TestButton(
                r, lbl, action=lambda d=delta: self._on_delta_scrap(d),
                color=(48, 44, 25)
            ))

        c2_y += 34
        scrap_presets = [("Set 0", 0), ("Set 500", 500), ("Set 2000", 2000)]
        for i, (lbl, target) in enumerate(scrap_presets):
            r = pygame.Rect(c2_left + i * (sc_w + 4), c2_y, sc_w, 26)
            self.buttons.append(TestButton(
                r, lbl, action=lambda t=target: self._on_set_scrap(t),
                active=(prog.scrap == target)
            ))

        c2_y += 36
        # Max / Reset Perks
        perk_w = (col_w - 6) // 2
        self.buttons.append(TestButton(
            pygame.Rect(c2_left, c2_y, perk_w, 28), "★ MAX ALL PERKS",
            action=self._on_max_perks,
            color=(40, 60, 40)
        ))
        self.buttons.append(TestButton(
            pygame.Rect(c2_left + perk_w + 6, c2_y, perk_w, 28), "↺ RESET PERKS",
            action=self._on_reset_perks,
            color=(55, 30, 30)
        ))

        # ==============================================================================
        # COLUMN 2 LOWER: COMBAT CHEATS & IN-RUN TOOLS
        # ==============================================================================
        c2_y += 56
        # God Mode Toggle Button
        god_active = getattr(self.game.player, "god_mode", False) if in_run and self.game.player else False
        god_label = "🛡️ GOD MODE: ON" if god_active else "🛡️ GOD MODE: OFF"
        god_col = (25, 90, 45) if god_active else (45, 50, 60)
        self.buttons.append(TestButton(
            pygame.Rect(c2_left, c2_y, (col_w - 6) // 2, 34), god_label,
            action=self._on_toggle_god_mode,
            active=god_active,
            color=god_col
        ))

        # Restore HP & Super
        self.buttons.append(TestButton(
            pygame.Rect(c2_left + (col_w - 6) // 2 + 6, c2_y, (col_w - 6) // 2, 34), "✚ REFILL HP & SUPER",
            action=self._on_refill_stats,
            color=(40, 50, 65)
        ))

        c2_y += 40
        # Kill All Enemies & Trigger Boon Draft
        self.buttons.append(TestButton(
            pygame.Rect(c2_left, c2_y, (col_w - 6) // 2, 32), "☠ KILL ALL FOES",
            action=self._on_kill_all_foes,
            color=(75, 25, 25)
        ))
        self.buttons.append(TestButton(
            pygame.Rect(c2_left + (col_w - 6) // 2 + 6, c2_y, (col_w - 6) // 2, 32), "✨ DRAFT BOON",
            action=self._on_trigger_boon_draft,
            color=(65, 45, 75)
        ))

        # ==============================================================================
        # BOTTOM UTILITY BAR: FRESH SAVE RESET & CLOSE
        # ==============================================================================
        by = self.rect.bottom - 52
        b_w = 260
        self.buttons.append(TestButton(
            pygame.Rect(left, by, b_w, 36), "⚠ RESET TO FRESH LEVEL 1 SAVE",
            action=self._on_reset_save,
            color=(80, 20, 20),
            border_color=(220, 80, 80)
        ))

        close_w = 220
        self.buttons.append(TestButton(
            pygame.Rect(self.rect.right - close_w - 24, by, close_w, 36), "✕ CLOSE CONSOLE (F1)",
            action=self._on_close,
            color=(40, 45, 55),
            border_color=COLOR_BRASS_HIGHLIGHT
        ))

    # ==============================================================================
    # ACTION HANDLERS
    # ==============================================================================

    def _on_select_track(self, idx: int):
        self.selected_track_idx = idx
        self._set_toast(f"Selected Track {idx + 1}: {TRAIN_ROUTES[ALL_STAGES[idx]]['name']}")
        self._rebuild_buttons()

    def _on_select_loop(self, loop: int):
        self.selected_loop_count = loop
        self._set_toast(f"Selected Loop {loop} (Difficulty +{loop * 35}% HP)")
        self._rebuild_buttons()

    def _on_step_car(self, delta: int):
        max_cars = len(TRAIN_ROUTES[ALL_STAGES[self.selected_track_idx]]["cars"])
        self.selected_car_idx = max(0, min(max_cars - 1, self.selected_car_idx + delta))
        car_info = TRAIN_ROUTES[ALL_STAGES[self.selected_track_idx]]["cars"][self.selected_car_idx]
        self._set_toast(f"Target Car {self.selected_car_idx + 1}: {car_info['name']}")
        self._rebuild_buttons()

    def _on_set_car(self, c_idx: int):
        self.selected_car_idx = c_idx
        car_info = TRAIN_ROUTES[ALL_STAGES[self.selected_track_idx]]["cars"][self.selected_car_idx]
        self._set_toast(f"Target Car {c_idx + 1}: {car_info['name']}")
        self._rebuild_buttons()

    def _on_deploy(self):
        route_id = ALL_STAGES[self.selected_track_idx]
        self.game.progression.set_active_track(self.selected_track_idx, self.selected_loop_count)
        
        # Weapon
        if hasattr(self.game.hub_station, "get_selected_weapon"):
            weapon = self.game.hub_station.get_selected_weapon()
        else:
            weapon = AVAILABLE_WEAPONS[0]()

        # If currently in run on the same track, directly warp
        if self.game.state == self.game.STATE_PLAYING and self.game.run_manager and self.game.run_manager.route_id == route_id:
            self.game.warp_to_car(self.selected_car_idx)
            self._set_toast(f"Warped in-game to Car {self.selected_car_idx + 1}!")
        else:
            self.game.deploy_to_stage_and_car(route_id, self.selected_car_idx, weapon, self.selected_loop_count)
            self._set_toast(f"Deployed run to Track {self.selected_track_idx + 1}, Car {self.selected_car_idx + 1}!")

        self.game.test_mode_active = False

    def _on_select_weapon(self, w_idx: int):
        weapon_cls = AVAILABLE_WEAPONS[w_idx]
        new_w = weapon_cls()
        if hasattr(self.game.hub_station, "selected_weapon_idx"):
            self.game.hub_station.selected_weapon_idx = w_idx
            self.game.hub_station.active_weapon = new_w
        if self.game.player:
            self.game.player.equip_weapon(new_w)
        self._set_toast(f"Equipped weapon: {new_w.name}")
        self._rebuild_buttons()

    def _on_select_super(self, super_id: str):
        self.game.progression.set_equipped_super(super_id, force=True)
        if self.game.player:
            self.game.player.equipped_super_id = super_id
        meta = SUPER_ABILITIES.get(super_id, {"name": super_id})
        self._set_toast(f"Equipped super: {meta['name']}")
        self._rebuild_buttons()

    def _on_delta_level(self, delta: int):
        new_lvl = max(1, self.game.progression.level + delta)
        self.game.progression.set_level(new_lvl)
        self._set_toast(f"Conductor Level set to {new_lvl}!")
        self._rebuild_buttons()

    def _on_set_level(self, target: int):
        self.game.progression.set_level(target)
        self._set_toast(f"Conductor Level set to {target}!")
        self._rebuild_buttons()

    def _on_delta_scrap(self, delta: int):
        new_scrap = max(0, self.game.progression.scrap + delta)
        self.game.progression.set_scrap(new_scrap)
        self._set_toast(f"Scrap metal adjusted to {new_scrap}!")
        self._rebuild_buttons()

    def _on_set_scrap(self, target: int):
        self.game.progression.set_scrap(target)
        self._set_toast(f"Scrap metal set to {target}!")
        self._rebuild_buttons()

    def _on_max_perks(self):
        self.game.progression.max_all_perks()
        if self.game.player:
            self.game.progression.apply_perks_to_player(self.game.player)
        self._set_toast("★ All 5 Conductor Workshop perks maximized!")
        self._rebuild_buttons()

    def _on_reset_perks(self):
        self.game.progression.reset_all_perks()
        self._set_toast("↺ All Conductor Workshop perks reset to 0.")
        self._rebuild_buttons()

    def _on_toggle_god_mode(self):
        if self.game.player:
            self.game.player.god_mode = not getattr(self.game.player, "god_mode", False)
            status = "ACTIVATED" if self.game.player.god_mode else "DEACTIVATED"
            self._set_toast(f"🛡️ God Mode {status}!")
        else:
            self._set_toast("God Mode will activate when entering a run.")
        self._rebuild_buttons()

    def _on_refill_stats(self):
        if self.game.player:
            self.game.player.refill_stats()
            self._set_toast("✚ Health restored to full & Super Ability 100% charged!")
        else:
            self._set_toast("Refill stats applicable during a run.")

    def _on_kill_all_foes(self):
        if self.game.state == self.game.STATE_PLAYING:
            self.game.kill_all_enemies()
            self._set_toast("☠ All enemies in car slain!")
        else:
            self._set_toast("Kill foes applicable during active combat.")

    def _on_trigger_boon_draft(self):
        if self.game.state == self.game.STATE_PLAYING:
            self.game.trigger_boon_draft()
            self.game.test_mode_active = False
        else:
            self._set_toast("Boon draft applicable during active runs.")

    def _on_reset_save(self):
        self.game.progression.reset_to_fresh()
        self._sync_state_from_game()
        self._set_toast("⚠ Progression reset to fresh Level 1 save state!")
        self._rebuild_buttons()

    def _on_close(self):
        self.game.test_mode_active = False

    # ==============================================================================
    # INPUT & RENDERING
    # ==============================================================================

    def handle_input(self, events: list[pygame.event.Event]) -> bool:
        """Handle modal mouse clicks and keyboard hotkeys."""
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_F1, pygame.K_ESCAPE, pygame.K_BACKQUOTE):
                    self._on_close()
                    return True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.buttons:
                    if btn.rect.collidepoint(event.pos):
                        self.game.audio.play('shoot')
                        btn.action()
                        return True
        return True

    def update(self, dt: float):
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - dt)

    def draw(self, surface: pygame.Surface):
        # 1. Dark semi-transparent backdrop
        backdrop = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        backdrop.fill((8, 12, 18, 220))
        surface.blit(backdrop, (0, 0))

        # 2. Modal Frame
        pygame.draw.rect(surface, (18, 24, 32), self.rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_BRASS, self.rect, 2, border_radius=12)

        # Header Title
        title_surf = self.font_title.render("✦ DISPATCH TERMINAL — TEST & DEV CONSOLE ✦", True, COLOR_BRASS_HIGHLIGHT)
        surface.blit(title_surf, title_surf.get_rect(center=(self.rect.centerx, self.rect.top + 28)))

        sub_msg = "Real-time inspection of stages, cars, conductor levels, currency, arsenal, and combat mechanics."
        sub_surf = self.font_btn_sm.render(sub_msg, True, (170, 185, 205))
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.rect.centerx, self.rect.top + 48)))

        col_w = (self.width - 72) // 2
        left = self.rect.left + 24
        c2_left = left + col_w + 24
        top = self.rect.top + 60

        # Section Headers
        sec1 = self.font_section.render("STAGE & CAR DISPATCH SELECTOR", True, COLOR_CRIT_YELLOW)
        surface.blit(sec1, (left, top + 4))

        sec2 = self.font_section.render("ARSENAL & SUPER TESTING", True, COLOR_CRIT_YELLOW)
        surface.blit(sec2, (left, top + 224))

        sec3 = self.font_section.render("CONDUCTOR PROGRESSION & CURRENCY", True, COLOR_CRIT_YELLOW)
        surface.blit(sec3, (c2_left, top + 4))

        sec4 = self.font_section.render("IN-RUN COMBAT CHEATS & TOOLS", True, COLOR_CRIT_YELLOW)
        surface.blit(sec4, (c2_left, top + 224))

        # Active Car description display
        route_info = TRAIN_ROUTES[ALL_STAGES[self.selected_track_idx]]
        car_info = route_info["cars"][self.selected_car_idx]
        car_txt = f"Selected: Car {self.selected_car_idx + 1}/15 — {car_info['name']} ({car_info['type'].upper()})"
        car_surf = self.font_val.render(car_txt, True, COLOR_WHITE)
        surface.blit(car_surf, (left + 52, top + 112))

        # Level & Scrap status displays
        prog = self.game.progression
        lvl_str = f"Level: {prog.level} (XP: {prog.xp}/{prog.get_xp_for_next_level()})"
        scrap_str = f"Scrap Metal: {prog.scrap} ⚙"
        surface.blit(self.font_val.render(lvl_str, True, COLOR_WHITE), (c2_left, top + 70))
        surface.blit(self.font_val.render(scrap_str, True, (240, 200, 100)), (c2_left, top + 152))

        # Draw all buttons
        for btn in self.buttons:
            font = self.font_btn_sm if btn.rect.width < 80 else self.font_btn
            btn.draw(surface, font)

        # Toast Message Bar
        if self.toast_timer > 0 and self.toast_message:
            toast_w = 680
            toast_rect = pygame.Rect((SCREEN_WIDTH - toast_w) // 2, self.rect.bottom - 46, toast_w, 28)
            alpha_ratio = min(1.0, self.toast_timer * 2.0)
            t_surf = pygame.Surface((toast_w, 28), pygame.SRCALPHA)
            t_surf.fill((20, 60, 40, int(220 * alpha_ratio)))
            pygame.draw.rect(t_surf, (80, 220, 120, int(255 * alpha_ratio)), (0, 0, toast_w, 28), 1, border_radius=4)
            surface.blit(t_surf, toast_rect.topleft)

            msg_render = self.font_toast.render(self.toast_message, True, COLOR_WHITE)
            surface.blit(msg_render, msg_render.get_rect(center=toast_rect.center))
