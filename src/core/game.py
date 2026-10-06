"""Master Game controller orchestrating the loop, FSM states, physics, and rendering."""
import pygame
import math
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    COLOR_BG, COLOR_WHITE, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_CARPET_RED
)
from src.core.camera import Camera
from src.core.input_handler import InputHandler
from src.core.sound import audio
from src.ui.particles import ParticleManager
from src.ui.hud import HUD
from src.ui.upgrade_menu import UpgradeMenu
from src.ui.hub_station import HubStation
from src.entities.player import Player
from src.level.car_generator import RunManager
from src.combat.boons import get_random_boon_choices
from src.core.progression import ProgressionManager

class Game:
    """Central engine managing all subsystems, game states, and loop execution."""
    STATE_HUB = "hub"
    STATE_PLAYING = "playing"
    STATE_BOON_DRAFT = "boon_draft"
    STATE_PAUSED = "paused"
    STATE_GAME_OVER = "game_over"
    STATE_VICTORY = "victory"

    def __init__(self, headless: bool = False, progression: ProgressionManager = None):
        self.headless = headless
        self.running = True
        self.state = self.STATE_HUB
        
        # Display setup
        if not headless:
            pygame.display.set_caption(TITLE)
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            
        self.clock = pygame.time.Clock()

        # Core subsystems
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.input_handler = InputHandler()
        self.particles = ParticleManager()
        self.audio = audio
        self.hud = HUD()
        self.upgrade_menu = UpgradeMenu()
        self.progression = progression or ProgressionManager()
        self.hub_station = HubStation(self.progression)

        # Gameplay entities & progression
        self.player = None
        self.enemies = []
        self.projectiles = []
        self.shockwaves = []
        self.fire_hazards = []
        self.pickups = []
        self.train_car = None
        self.run_manager = None
        
        # Fonts for overlays
        pygame.font.init()
        self.font_overlay_title = pygame.font.SysFont("Helvetica, Arial, sans-serif", 38, bold=True)
        self.font_overlay_sub = pygame.font.SysFont("Helvetica, Arial, sans-serif", 17)
        self.font_overlay_stat = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)
        self.font_overlay_btn = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)

        # Run statistics & Victory flow
        self.run_start_ticks = 0
        self.run_duration_sec = 0.0
        self.enemies_killed = 0
        self.damage_dealt = 0
        self.earned_xp = 0
        self.earned_scrap = 0
        self.newly_unlocked_stage = None
        self.victory_transition_timer = 0.0
        self.return_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 110, 360, 48)
        self.overlay_input_delay = 0.0

    def return_to_hub(self):
        """Cleanly transition from Game Over / Victory / Pause back to Grand Central Terminal Hub."""
        self.state = self.STATE_HUB
        self.overlay_input_delay = 0.0
        self.hub_station.reset_player()
        self.audio.play('shoot')
        pygame.event.clear()

    def start_new_run(self, route_id: str, starter_weapon):
        """Initialize a new train departure run."""
        self.input_handler = InputHandler()
        self.run_manager = RunManager(route_id, loop_count=self.progression.loop_count)
        self.train_car = self.run_manager.create_current_car()
        
        # Reset run metrics
        self.run_start_ticks = pygame.time.get_ticks()
        self.run_duration_sec = 0.0
        self.enemies_killed = 0
        self.damage_dealt = 0
        self.earned_xp = 0
        self.earned_scrap = 0
        self.newly_unlocked_stage = None
        self.victory_transition_timer = 0.0
        self.progression.total_runs += 1
        self.progression.save()

        # Setup player at left entrance of caboose
        start_y = (self.train_car.top_wall_y + self.train_car.bottom_wall_y) // 2
        self.player = Player(120, start_y)
        self.player.equip_weapon(starter_weapon)
        self.progression.apply_perks_to_player(self.player)

        # Clear active objects
        self.projectiles.clear()
        self.shockwaves.clear()
        self.fire_hazards.clear()
        self.pickups.clear()
        self.enemies = self.run_manager.spawn_enemies_for_car(self.train_car)
        
        # Set camera bounds to current train car
        self.camera.set_bounds(0, self.train_car.width, 0, SCREEN_HEIGHT)
        self.state = self.STATE_PLAYING
        self.audio.play('door')

    def load_next_train_car(self):
        """Advance player through the bulkhead door into the next train car."""
        # Grant room secured XP & Scrap
        self.progression.gain_xp(25)
        self.earned_xp += 25
        self.progression.gain_scrap(3)
        self.earned_scrap += 3

        has_next = self.run_manager.advance_to_next_car()
        if not has_next:
            # Won the game!
            self.state = self.STATE_VICTORY
            self.audio.play('boon')
            return

        self.train_car = self.run_manager.create_current_car()
        self.camera.set_bounds(0, self.train_car.width, 0, SCREEN_HEIGHT)
        
        # Position player at start of new car
        start_y = (self.train_car.top_wall_y + self.train_car.bottom_wall_y) // 2
        self.player.pos = pygame.math.Vector2(120, start_y)
        self.player.vel = pygame.math.Vector2(0, 0)
        
        # Snap camera directly to entrance of new car
        self.camera.offset.x = 0
        self.camera.offset.y = 0
        
        # Clear old projectiles, hazards, and spawn new enemies
        self.projectiles.clear()
        self.shockwaves.clear()
        self.fire_hazards.clear()
        self.pickups.clear()
        self.enemies = self.run_manager.spawn_enemies_for_car(self.train_car)
        self.audio.play('door')

    def handle_events(self) -> bool:
        """Poll events from pygame queue."""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return False

        if self.state == self.STATE_HUB:
            boarded = self.hub_station.handle_input(events)
            if boarded:
                route = self.hub_station.get_selected_route_id()
                weapon = self.hub_station.get_selected_weapon()
                self.start_new_run(route, weapon)

        elif self.state in (self.STATE_PLAYING, self.STATE_BOON_DRAFT):
            self.input_handler.process_events(events, self.camera)
            if self.input_handler.pause_pressed:
                if self.state == self.STATE_PLAYING:
                    self.state = self.STATE_PAUSED
                elif self.state == self.STATE_PAUSED:
                    self.state = self.STATE_PLAYING

        elif self.state == self.STATE_PAUSED:
            for event in events:
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_p):
                    self.state = self.STATE_PLAYING

        elif self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
            if self.overlay_input_delay > 0.0:
                return True
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e, pygame.K_ESCAPE):
                        self.return_to_hub()
                        return True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.return_button_rect.collidepoint(event.pos):
                        self.return_to_hub()
                        return True

        return True

    def update(self, dt: float):
        """Update game physics, entities, and states."""
        # Cap max dt to avoid physics spiral on lag spike
        dt = min(dt, 0.05)

        if self.state == self.STATE_PLAYING:
            self.run_duration_sec = (pygame.time.get_ticks() - self.run_start_ticks) / 1000.0
            self.train_car.update(dt, self.player, self.enemies, self)
            self.camera.update(dt, self.player.pos)
            self.player.update(dt, self.input_handler, self.train_car, self)
            
            # Check player death
            if not self.player.is_alive():
                self.state = self.STATE_GAME_OVER
                self.overlay_input_delay = 0.5
                self.audio.play('explosion')
                return

            # Update hazards & props
            self.shockwaves = [s for s in self.shockwaves if s.update(dt, self.player, self)]
            self.fire_hazards = [f for f in self.fire_hazards if f.update(dt, self.player, self.enemies, self)]
            self.pickups = [p for p in self.pickups if p.update(self.player, self)]

            # Update enemies
            for enemy in self.enemies:
                enemy.update(dt, self.player, self.train_car, self)
            # Filter dead enemies and grant XP / Scrap
            alive_enemies = []
            for e in self.enemies:
                if e.is_alive():
                    alive_enemies.append(e)
                else:
                    self.enemies_killed += 1
                    base_xp = 75 if getattr(e, "is_miniboss", False) else (15 if getattr(e, "is_elite", False) else 5)
                    self.progression.gain_xp(base_xp)
                    self.earned_xp += base_xp
                    self.progression.gain_scrap(1)
                    self.earned_scrap += 1
            self.enemies = alive_enemies

            # Check if train car is cleared!
            if len(self.enemies) == 0:
                if self.run_manager.is_final_car():
                    # Locomotive Engine Boss Cleared! Immediate victory transition sequence!
                    if self.victory_transition_timer == 0.0:
                        self.victory_transition_timer = 1.0
                        self.audio.play('explosion')
                        self.audio.play('boon')
                        self.camera.add_trauma(0.8)
                        self.progression.gain_xp(200)
                        self.earned_xp += 200
                        self.progression.gain_scrap(50)
                        self.earned_scrap += 50
                        self.progression.total_bosses_slain += 1
                        self.newly_unlocked_stage = self.progression.advance_track_on_victory()
                    else:
                        self.victory_transition_timer -= dt
                        if self.victory_transition_timer <= 0:
                            self.state = self.STATE_VICTORY
                            self.overlay_input_delay = 0.5
                elif not self.train_car.exit_unlocked:
                    self.train_car.unlock_exit(self)

            # Check Boon Pedestal interaction
            if self.train_car.boon_pedestal_active and not self.train_car.boon_claimed:
                dist_to_pedestal = (self.player.pos - self.train_car.boon_pedestal_pos).length()
                pedestal_walk_on = (dist_to_pedestal <= self.train_car.boon_pedestal_radius + self.player.radius + 15)
                pedestal_interact = (self.input_handler.interact_pressed and dist_to_pedestal <= 140)
                if pedestal_walk_on or pedestal_interact:
                    # Open upgrade draft modal with both new and upgradeable boons!
                    choices = get_random_boon_choices(count=3, existing_boons=self.player.boons)
                    self.upgrade_menu.open(choices, owned_ids={b.id for b in self.player.boons}, existing_boons=self.player.boons)
                    self.state = self.STATE_BOON_DRAFT
                    self.audio.play('boon')

            # Check exit door progression
            if self.train_car.exit_unlocked:
                door_walk_through = self.train_car.can_player_exit(self.player.pos, self.player.radius)
                door_interact = (self.input_handler.interact_pressed and self.player.pos.x >= self.train_car.width - 240)
                if door_walk_through or door_interact:
                    self.load_next_train_car()

            # Update projectiles & check collisions
            surviving_projs = []
            for proj in self.projectiles:
                # Check destructible train windows before wall clip
                hit_window = False
                if hasattr(self.train_car, "windows"):
                    for win in self.train_car.windows:
                        if win.state != win.STATE_SHATTERED and win.rect.inflate(8, 20).collidepoint(proj.pos.x, proj.pos.y):
                            win.take_damage(proj.damage_event.amount, self)
                            self.particles.spawn_sparks(proj.pos.x, proj.pos.y, count=4)
                            hit_window = True
                            break
                if hit_window:
                    continue

                if not proj.update(dt, self.train_car):
                    continue

                hit_something = False
                if proj.owner == "player":
                    for enemy in self.enemies:
                        if enemy not in proj.hit_entities and enemy.is_alive():
                            if (enemy.pos - proj.pos).length() <= (enemy.radius + proj.radius):
                                proj.hit_entities.add(enemy)
                                # Apply damage
                                enemy.take_damage(proj.damage_event, self)
                                # Trigger player boon on_hit hooks
                                for boon in self.player.boons:
                                    boon.on_hit(self.player, enemy, proj.damage_event, self)
                                
                                self.particles.spawn_sparks(proj.pos.x, proj.pos.y, count=6)
                                self.audio.play('hit')

                                if proj.pierce > 0:
                                    proj.pierce -= 1
                                else:
                                    hit_something = True
                                    break
                elif proj.owner == "enemy":
                    if (self.player.pos - proj.pos).length() <= (self.player.radius + proj.radius):
                        self.player.take_damage(proj.damage_event, self)
                        self.particles.spawn_sparks(proj.pos.x, proj.pos.y, count=6)
                        hit_something = True

                # Check explosive barrels
                if not hit_something:
                    for barrel in self.train_car.barrels:
                        if not barrel.is_dead and barrel.rect.collidepoint(proj.pos.x, proj.pos.y):
                            barrel.take_damage(proj.damage_event, self)
                            hit_something = True
                            break

                # Check supply crates
                if not hit_something:
                    for crate in self.train_car.crates:
                        if not crate.is_dead and crate.rect.collidepoint(proj.pos.x, proj.pos.y):
                            crate.take_damage(proj.damage_event, self)
                            hit_something = True
                            break

                if not hit_something:
                    surviving_projs.append(proj)

            self.projectiles = surviving_projs
            self.particles.update(dt)

        elif self.state == self.STATE_BOON_DRAFT:
            # Upgrade menu update
            selected_boon = self.upgrade_menu.update(self.input_handler)
            if selected_boon:
                self.player.add_boon(selected_boon)
                self.train_car.boon_claimed = True
                self.particles.spawn_explosion(self.player.pos.x, self.player.pos.y, radius=50)
                self.audio.play('boon')
                self.state = self.STATE_PLAYING

        elif self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
            if self.overlay_input_delay > 0.0:
                self.overlay_input_delay = max(0.0, self.overlay_input_delay - dt)

    def render(self):
        """Draw everything based on current state."""
        self.screen.fill(COLOR_BG)

        if self.state == self.STATE_HUB:
            self.hub_station.draw(self.screen)

        elif self.state in (self.STATE_PLAYING, self.STATE_BOON_DRAFT, self.STATE_PAUSED, self.STATE_GAME_OVER, self.STATE_VICTORY):
            # 1. World & Train Car
            self.train_car.draw(self.screen, self.camera)

            # 2. Floor Fire Hazards
            for f in self.fire_hazards:
                f.draw(self.screen, self.camera)

            # 3. Floating Pickups
            for p in self.pickups:
                p.draw(self.screen, self.camera)

            # 4. Projectiles
            for proj in self.projectiles:
                proj.draw(self.screen, self.camera)

            # 5. Enemies
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)

            # 6. Player
            if self.player:
                self.player.draw(self.screen, self.camera)

            # 7. Ground Shockwaves
            for s in self.shockwaves:
                s.draw(self.screen, self.camera)

            # 8. Particles & Combat Text
            self.particles.draw(self.screen, self.camera)

            # 9. HUD
            # Look for active boss
            boss = next((e for e in self.enemies if hasattr(e, "phase")), None)
            self.hud.draw(
                self.screen, self.player, self.run_manager,
                enemies=self.enemies, train_car=self.train_car,
                camera=self.camera, boss=boss
            )

            # State overlays
            if self.state == self.STATE_BOON_DRAFT:
                self.upgrade_menu.draw(self.screen)
            elif self.state == self.STATE_PAUSED:
                self._draw_pause_overlay()
            elif self.state == self.STATE_GAME_OVER:
                self._draw_game_over_overlay()
            elif self.state == self.STATE_VICTORY:
                self._draw_victory_overlay()

        if not self.headless:
            pygame.display.flip()

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        p_text = self.font_overlay_title.render("GAME PAUSED", True, COLOR_BRASS_HIGHLIGHT)
        p_sub = self.font_overlay_sub.render("Press ESC or P to Resume", True, COLOR_WHITE)
        self.screen.blit(p_text, p_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))
        self.screen.blit(p_sub, p_sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))

    def _draw_game_over_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((25, 6, 6, 230))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 680, 360
        card_rect = pygame.Rect((SCREEN_WIDTH - card_w) // 2, (SCREEN_HEIGHT - card_h) // 2 - 30, card_w, card_h)
        pygame.draw.rect(self.screen, (28, 12, 12), card_rect, border_radius=12)
        pygame.draw.rect(self.screen, (220, 60, 60), card_rect, 2, border_radius=12)

        t_text = self.font_overlay_title.render("DERAILED — RUN OVER", True, (240, 70, 70))
        self.screen.blit(t_text, t_text.get_rect(center=(SCREEN_WIDTH // 2, card_rect.top + 55)))

        car_info = self.run_manager.get_current_car_info() if self.run_manager else None
        car_name = car_info['name'] if car_info else "Train Car"
        car_num = (self.run_manager.current_car_index + 1) if self.run_manager else 1
        t_sub = self.font_overlay_sub.render(f"Fallen in Car {car_num}: {car_name}", True, COLOR_WHITE)
        self.screen.blit(t_sub, t_sub.get_rect(center=(SCREEN_WIDTH // 2, card_rect.top + 105)))

        # Foes slain & time
        m = int(self.run_duration_sec // 60)
        s = int(self.run_duration_sec % 60)
        stats_text = self.font_overlay_stat.render(f"Enemies Defeated: {self.enemies_killed}  |  Survival Time: {m:02d}:{s:02d}", True, (220, 180, 180))
        self.screen.blit(stats_text, stats_text.get_rect(center=(SCREEN_WIDTH // 2, card_rect.top + 145)))

        # Return Button
        btn_w, btn_h = 360, 48
        self.return_button_rect = pygame.Rect((SCREEN_WIDTH - btn_w) // 2, card_rect.bottom - 75, btn_w, btn_h)
        btn_rect = self.return_button_rect
        pygame.draw.rect(self.screen, (160, 40, 40), btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, (240, 100, 100), btn_rect, 2, border_radius=8)
        btn_text = self.font_overlay_btn.render("RETURN TO GRAND CENTRAL HUB", True, COLOR_WHITE)
        self.screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        key_prompt = self.font_overlay_stat.render("Click or press [SPACE] / [E] / [ENTER] / [R]", True, (200, 180, 180))
        self.screen.blit(key_prompt, key_prompt.get_rect(center=(btn_rect.centerx, btn_rect.bottom + 16)))

    def _draw_victory_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 18, 14, 238))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 860, 560
        card_rect = pygame.Rect((SCREEN_WIDTH - card_w) // 2, (SCREEN_HEIGHT - card_h) // 2 - 10, card_w, card_h)
        pygame.draw.rect(self.screen, (15, 24, 20), card_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_BRASS, card_rect, 3, border_radius=12)

        # Title Banner
        v_text = self.font_overlay_title.render("=== LOCOMOTIVE LIBERATED! ===", True, COLOR_BRASS_HIGHLIGHT)
        v_rect = v_text.get_rect(center=(SCREEN_WIDTH // 2, card_rect.top + 38))
        self.screen.blit(v_text, v_rect)

        sub_msg = f"{self.run_manager.route_data['name']} has been secured! Runaway train brought to a halt."
        v_sub = self.font_overlay_sub.render(sub_msg, True, COLOR_WHITE)
        self.screen.blit(v_sub, v_sub.get_rect(center=(SCREEN_WIDTH // 2, card_rect.top + 72)))

        # New Stage Unlocked Callout Banner
        banner_offset = 0
        if self.newly_unlocked_stage:
            from src.level.car_generator import TRAIN_ROUTES
            if isinstance(self.newly_unlocked_stage, dict):
                info = self.newly_unlocked_stage
                if info.get("new_loop"):
                    msg = f"★ EXPEDITION CYCLE COMPLETED! ADVANCING TO {info['display_name']} (LOOP {info['loop_count'] + 1}) ★"
                else:
                    active_name = TRAIN_ROUTES.get(info['active_route'], {}).get("name", info['active_route'])
                    msg = f"★ TRACK {info['previous_track_idx'] + 1} DEPARTED! NEXT: {info['display_name']} ({active_name.upper()}) ★"
            else:
                new_name = TRAIN_ROUTES.get(self.newly_unlocked_stage, {}).get("name", self.newly_unlocked_stage)
                msg = f"★ NEW TRACK OPENED AT DOCKING BAY: {new_name.upper()}! ★"

            unl_rect = pygame.Rect(card_rect.left + 40, card_rect.top + 94, card_w - 80, 28)
            pygame.draw.rect(self.screen, (32, 60, 40), unl_rect, border_radius=4)
            pygame.draw.rect(self.screen, (100, 240, 150), unl_rect, 1, border_radius=4)
            unl_txt = self.font_overlay_stat.render(msg, True, (130, 255, 180))
            self.screen.blit(unl_txt, unl_txt.get_rect(center=unl_rect.center))
            banner_offset = 32

        # Run Statistics Box
        stats_top = card_rect.top + 105 + banner_offset
        stats_rect = pygame.Rect(card_rect.left + 40, stats_top, card_w - 80, 105)
        pygame.draw.rect(self.screen, (22, 34, 28), stats_rect, border_radius=8)
        pygame.draw.rect(self.screen, (40, 70, 55), stats_rect, 1, border_radius=8)

        m = int(self.run_duration_sec // 60)
        s = int(self.run_duration_sec % 60)
        time_str = f"{m:02d}:{s:02d}"
        
        route_lbl = self.run_manager.route_data['name']
        if len(route_lbl) > 17:
            route_lbl = route_lbl[:15] + ".."
        stat_items = [
            ("ROUTE", route_lbl),
            ("CARS SECURED", f"{self.run_manager.current_car_index + 1} / {self.run_manager.total_cars}"),
            ("EXP EARNED", f"+{self.earned_xp} XP"),
            ("SCRAP BANKED", f"+{self.earned_scrap} Scrap"),
        ]
        col_w = stats_rect.width // len(stat_items)
        for i, (label, val) in enumerate(stat_items):
            cx = stats_rect.left + i * col_w + col_w // 2
            lbl_surf = self.font_overlay_stat.render(label, True, COLOR_BRASS)
            val_surf = self.font_overlay_btn.render(val, True, COLOR_WHITE)
            self.screen.blit(lbl_surf, lbl_surf.get_rect(center=(cx, stats_top + 28)))
            self.screen.blit(val_surf, val_surf.get_rect(center=(cx, stats_top + 65)))

        # Final Arsenal & Boons
        loadout_y = stats_top + 125
        wpn_name = self.player.weapon.name if self.player and self.player.weapon else "None"
        wpn_lbl = self.font_overlay_sub.render(f"Arsenal Weapon: {wpn_name}  |  Enemies Slain: {self.enemies_killed}", True, COLOR_BRASS_HIGHLIGHT)
        self.screen.blit(wpn_lbl, (card_rect.left + 40, loadout_y))

        # Boons summary badges with multi-line wrapping
        boon_y = loadout_y + 30
        cur_bx = card_rect.left + 40
        max_rx = card_rect.right - 40
        if self.player and self.player.boons:
            for boon in self.player.boons:
                tier_str = f"T{boon.level}/{boon.max_level}"
                b_text = f"{boon.name} [{tier_str}]"
                b_surf = self.font_overlay_stat.render(b_text, True, COLOR_WHITE)
                badge_w = b_surf.get_width() + 14
                if cur_bx + badge_w > max_rx:
                    cur_bx = card_rect.left + 40
                    boon_y += 28
                b_bg = pygame.Rect(cur_bx, boon_y, badge_w, 24)
                pygame.draw.rect(self.screen, (30, 48, 38), b_bg, border_radius=4)
                pygame.draw.rect(self.screen, COLOR_BRASS, b_bg, 1, border_radius=4)
                self.screen.blit(b_surf, (cur_bx + 7, boon_y + 4))
                cur_bx += badge_w + 8
        else:
            no_b = self.font_overlay_stat.render("No boons equipped", True, (160, 160, 160))
            self.screen.blit(no_b, (card_rect.left + 40, boon_y))

        # Return Button (Inside card bounds at bottom)
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
        btn_w, btn_h = 380, 48
        self.return_button_rect = pygame.Rect((SCREEN_WIDTH - btn_w) // 2, card_rect.bottom - 72, btn_w, btn_h)
        btn_rect = self.return_button_rect
        btn_color = (int(35 + 25 * pulse), int(120 + 35 * pulse), int(70 + 20 * pulse))
        pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_BRASS_HIGHLIGHT, btn_rect, 2, border_radius=8)
        
        btn_text = self.font_overlay_btn.render("RETURN TO GRAND CENTRAL HUB", True, COLOR_WHITE)
        self.screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

        key_prompt = self.font_overlay_stat.render("Click or press [SPACE] / [E] / [ENTER] / [R] to return & bank rewards", True, (170, 215, 185))
        self.screen.blit(key_prompt, key_prompt.get_rect(center=(btn_rect.centerx, btn_rect.bottom + 14)))

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            if not self.handle_events():
                break
            self.update(dt)
            self.render()

        pygame.quit()
