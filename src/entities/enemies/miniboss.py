"""Mid-run Mini-Boss: The Chief Ticket Inspector. Encountered in Car 5."""
import pygame
import math
import random
from src.entities.enemies.base_enemy import BaseEnemy
from src.combat.damage import DamageEvent
from src.entities.projectile import Projectile
from src.config import (
    COLOR_WHITE, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_STEEL_DARK, COLOR_CRIT_YELLOW, COLOR_EMBER_ORANGE
)

class ChiefInspectorMiniBoss(BaseEnemy):
    """The tyrannical Lead Ticket Inspector who presides over Car 5."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=32, max_health=520, speed=155.0, name="Chief Ticket Inspector")
        self.boss_name = "CHIEF TICKET INSPECTOR"
        self.is_miniboss = True
        self.phase = 1
        
        # State machine
        self.attack_timer = 1.8
        self.current_attack = None
        self.attack_state = 0   # 0: telegraph, 1: executing, 2: recovery
        self.state_timer = 0.0
        
        # Attack parameters
        self.rush_dir = pygame.math.Vector2(0, 0)
        self.has_summoned_reinforcements = False
        self.melee_damage = 22
        self.ticket_projectile_damage = 12

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        was_alive = self.is_alive()
        # 25% passive armor reduction
        damage_event.amount = max(1, int(damage_event.amount * 0.75))
        damage_event.knockback *= 0.25
        
        applied = super().take_damage(damage_event, game_state)
        
        # Check transition to enraged / whistle phase at 50% HP
        if was_alive and self.phase == 1 and self.health <= self.max_health * 0.5:
            self.enter_phase_2(game_state)
            
        return applied

    def enter_phase_2(self, game_state):
        self.phase = 2
        self.base_speed = 190.0
        self.speed = 190.0
        game_state.camera.add_trauma(0.5)
        game_state.audio.play('alert')
        game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=16, color=COLOR_CRIT_YELLOW)
        
        # Summon 2 swift adds if not yet summoned
        if not self.has_summoned_reinforcements:
            self.has_summoned_reinforcements = True
            self.summon_backup(game_state)

    def summon_backup(self, game_state):
        from src.entities.enemies.types import TicketInspector, BoilerImp
        # Spawn two guards from the train doors
        for offset_y, enemy_cls in ((-80, TicketInspector), (80, BoilerImp)):
            guard = enemy_cls(max(150, self.pos.x - 120), self.pos.y + offset_y)
            game_state.enemies.append(guard)
            game_state.particles.spawn_steam(guard.pos.x, guard.pos.y, count=8)

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        dist = to_player.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)

        # Handle active special attack
        if self.current_attack == "rush":
            self._update_rush(dt, player, train_car, game_state)
            self.pos += self.vel * dt
            self.resolve_obstacle_collisions(train_car)
            self.update_physics(dt)
            return

        # Cooldown timer between special attacks
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            # Choose attack: Baton rush if close, Ticket Barrage if at medium/long range
            if dist < 220:
                self._start_rush(to_player.normalize() if dist > 0 else pygame.math.Vector2(1, 0))
            else:
                self._fire_ticket_barrage(to_player, game_state)
            
            # Reset attack cooldown (faster in Phase 2)
            self.attack_timer = random.uniform(1.6, 2.4) if self.phase == 1 else random.uniform(1.1, 1.8)

        # Normal chase positioning
        desired_vel = pygame.math.Vector2(0, 0)
        if dist > 140:
            # Advance towards player
            desired_vel = to_player.normalize() * self.speed
        elif dist < 90:
            # Back up slightly for breathing room
            desired_vel = -to_player.normalize() * (self.speed * 0.7)

        # Flocking separation from other enemies
        sep = self.get_flocking_separation(game_state.enemies)
        move_force = desired_vel + sep * 80.0
        if move_force.length_squared() > 0:
            self.vel = self.vel.lerp(move_force, min(1.0, dt * 6.0))
        else:
            self.vel = self.vel.lerp(pygame.math.Vector2(0, 0), min(1.0, dt * 5.0))

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

        # Contact melee attack if touching player
        if dist <= self.radius + player.radius:
            push = to_player.normalize() * 320.0 if dist > 0 else pygame.math.Vector2(1, 0)
            player.take_damage(DamageEvent(self.melee_damage, source_type="enemy", knockback=push), game_state)

    def _fire_ticket_barrage(self, to_player: pygame.math.Vector2, game_state):
        """Fires 3 razor-sharp ticket blades in a fan towards the player."""
        base_angle = math.atan2(to_player.y, to_player.x)
        spread_angles = [-0.26, 0.0, 0.26]  # ~15 degree fan
        speed = 420.0
        game_state.audio.play('shoot')
        
        for angle_offset in spread_angles:
            ang = base_angle + angle_offset
            vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * speed
            spawn_pos = self.pos + pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (self.radius + 8)
            dmg = DamageEvent(self.ticket_projectile_damage, source_type="enemy", damage_type="normal")
            
            proj = Projectile(
                spawn_pos.x, spawn_pos.y,
                vel=vel,
                damage_event=dmg,
                radius=6.0,
                lifetime=1.8,
                color=COLOR_CRIT_YELLOW,
                owner="enemy"
            )
            game_state.projectiles.append(proj)
            
        game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=6, color=COLOR_BRASS)

    def _start_rush(self, direction: pygame.math.Vector2):
        self.current_attack = "rush"
        self.attack_state = 0
        self.state_timer = 0.65  # Windup telegraph
        self.rush_dir = direction
        self.vel *= 0.1

    def _update_rush(self, dt: float, player, train_car, game_state):
        if self.attack_state == 0:
            # Telegraphing charge
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.attack_state = 1
                self.state_timer = 0.35  # Dash duration
                self.vel = self.rush_dir * 580.0
                game_state.audio.play('swing')
                game_state.camera.add_trauma(0.3)
        elif self.attack_state == 1:
            # Active charge dash
            self.state_timer -= dt
            game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=2, color=COLOR_BRASS)
            
            # Hit player check
            to_p = player.pos - self.pos
            if to_p.length() <= (self.radius + player.radius + 15):
                push = self.rush_dir * 600.0
                player.take_damage(DamageEvent(self.melee_damage + 8, source_type="enemy", knockback=push), game_state)
                game_state.camera.add_trauma(0.4)
                self.attack_state = 2
                self.state_timer = 0.4
                self.vel *= 0.2
                
            if self.state_timer <= 0:
                self.attack_state = 2
                self.state_timer = 0.45  # Recovery cooldown
                self.vel *= 0.2
        elif self.attack_state == 2:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.current_attack = None

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        
        # Hit flash
        if self.flash_timer > 0:
            body_color = COLOR_WHITE
        elif self.phase == 2:
            # Enraged red pulse
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
            body_color = (int(160 + 80 * pulse), 35, 35)
        else:
            body_color = (35, 45, 65)  # Navy conductor coat
            
        # Rush telegraph line
        if self.current_attack == "rush" and self.attack_state == 0:
            prog = 1.0 - (self.state_timer / 0.65)
            line_len = 380 * prog
            end_x = screen_pos[0] + int(self.rush_dir.x * line_len)
            end_y = screen_pos[1] + int(self.rush_dir.y * line_len)
            pygame.draw.line(surface, (255, 60, 60), screen_pos, (end_x, end_y), 3)

        # Base Shadow
        pygame.draw.circle(surface, (15, 15, 20), (screen_pos[0], screen_pos[1] + 8), self.radius)
        
        # Heavy Coat Body
        pygame.draw.circle(surface, body_color, screen_pos, self.radius)
        pygame.draw.circle(surface, COLOR_BRASS, screen_pos, self.radius, 3)

        # Brass Epaulets on shoulders
        perp = pygame.math.Vector2(-math.sin(self.facing_angle), math.cos(self.facing_angle))
        left_ep = screen_pos + perp * (self.radius * 0.75)
        right_ep = screen_pos - perp * (self.radius * 0.75)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(left_ep.x), int(left_ep.y)), 7)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(right_ep.x), int(right_ep.y)), 7)

        # Conductor Peaked Cap Visor
        cap_offset = pygame.math.Vector2(math.cos(self.facing_angle), math.sin(self.facing_angle)) * (self.radius * 0.6)
        cap_pos = screen_pos + cap_offset
        pygame.draw.circle(surface, (20, 25, 35), (int(cap_pos.x), int(cap_pos.y)), int(self.radius * 0.55))
        pygame.draw.circle(surface, COLOR_BRASS, (int(cap_pos.x), int(cap_pos.y)), int(self.radius * 0.55), 2)
        
        # Brass Badge on cap
        badge_pos = cap_pos + pygame.math.Vector2(math.cos(self.facing_angle), math.sin(self.facing_angle)) * 6
        pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(badge_pos.x), int(badge_pos.y)), 4)

        # Glowing Visor / Red Monocle
        eye_pos = screen_pos + pygame.math.Vector2(math.cos(self.facing_angle), math.sin(self.facing_angle)) * (self.radius * 0.4)
        eye_color = (255, 30, 30) if self.phase == 2 else (255, 90, 40)
        pygame.draw.circle(surface, eye_color, (int(eye_pos.x), int(eye_pos.y)), 5)

        # Heavy Gold-Plated Baton
        baton_angle = self.facing_angle + 0.5
        baton_start = screen_pos + pygame.math.Vector2(math.cos(baton_angle), math.sin(baton_angle)) * (self.radius * 0.7)
        baton_end = baton_start + pygame.math.Vector2(math.cos(baton_angle), math.sin(baton_angle)) * 26
        pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, baton_start, baton_end, 5)
        pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(baton_end.x), int(baton_end.y)), 4)
