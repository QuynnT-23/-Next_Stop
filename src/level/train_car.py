"""Train car level geometry, animated window parallax, obstacles, and interactive hazards."""
import pygame
import random
import math
from src.config import (
    CAR_WIDTH, CAR_HEIGHT, CAR_TOP_WALL, CAR_BOTTOM_WALL,
    COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_STEEL_LIGHT,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_WOOD_DARK, COLOR_WOOD_LIGHT,
    COLOR_CARPET_RED, COLOR_WHITE, COLOR_EMBER_ORANGE,
    COLOR_SUBWAY_BG, COLOR_SUBWAY_TILES, COLOR_HEALTH_GREEN,
    COLOR_CRIT_YELLOW, COLOR_LIGHTNING_CYAN
)
from src.combat.damage import DamageEvent

class ExplosiveBarrel:
    """Red pressurized steam/powder barrel that detonates when struck."""
    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, 40, 48)
        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        self.radius = 22.0
        self.health = 1
        self.is_dead = False

    def take_damage(self, damage_event, game_state):
        if self.is_dead:
            return
        self.is_dead = True
        self.detonate(game_state)

    def detonate(self, game_state):
        game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=130)
        game_state.audio.play('explosion')
        game_state.camera.add_trauma(0.60)

        # Blast area damage
        blast_radius = 160.0
        for enemy in game_state.enemies:
            if enemy.is_alive():
                diff = enemy.pos - self.pos
                dist = diff.length()
                if dist <= blast_radius:
                    push = diff.normalize() * 600.0 if dist > 0 else pygame.math.Vector2(1, 0)
                    enemy.take_damage(DamageEvent(120, source_type="hazard", damage_type="fire", knockback=push), game_state)

        # Damage player if close
        if game_state.player and game_state.player.is_alive():
            diff = game_state.player.pos - self.pos
            dist = diff.length()
            if dist <= blast_radius * 0.85:
                push = diff.normalize() * 500.0 if dist > 0 else pygame.math.Vector2(1, 0)
                game_state.player.take_damage(DamageEvent(25, source_type="hazard", damage_type="fire", knockback=push), game_state)

        # Blast damage to nearby train windows
        if hasattr(game_state, "train_car") and hasattr(game_state.train_car, "windows"):
            for win in game_state.train_car.windows:
                if (win.pos - self.pos).length() <= blast_radius + 60:
                    win.take_damage(120, game_state)

    def draw(self, surface: pygame.Surface, camera):
        draw_rect = camera.apply_rect(self.rect)
        # Red hazardous steel drum
        pygame.draw.rect(surface, (180, 30, 25), draw_rect, border_radius=6)
        pygame.draw.rect(surface, (40, 10, 10), draw_rect, 2, border_radius=6)
        
        # Hazard yellow band
        band_rect = pygame.Rect(draw_rect.x, draw_rect.y + 16, draw_rect.width, 14)
        pygame.draw.rect(surface, COLOR_CRIT_YELLOW, band_rect)
        pygame.draw.line(surface, (30, 30, 30), band_rect.topleft, band_rect.bottomright, 2)
        pygame.draw.line(surface, (30, 30, 30), band_rect.bottomleft, band_rect.topright, 2)


class SupplyCrate:
    """Destructible wooden crate dropping health kits or overcharge powerups."""
    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        self.radius = 24.0
        self.health = 24
        self.flash_timer = 0.0
        self.is_dead = False

    def take_damage(self, damage_event, game_state):
        if self.is_dead:
            return
        self.health -= damage_event.amount
        self.flash_timer = 0.12
        game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=4, color=(160, 120, 70))
        game_state.audio.play('hit')

        if self.health <= 0:
            self.is_dead = True
            self.break_open(game_state)

    def break_open(self, game_state):
        game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=12, color=(140, 100, 55))
        # Drop pickup
        drop_type = "medkit" if random.random() < 0.65 else "overcharge"
        pickup = PickupItem(self.pos.x, self.pos.y, drop_type)
        if hasattr(game_state, "pickups"):
            game_state.pickups.append(pickup)

    def update(self, dt: float):
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    def draw(self, surface: pygame.Surface, camera):
        draw_rect = camera.apply_rect(self.rect)
        color = COLOR_WHITE if self.flash_timer > 0 else (115, 80, 48)
        pygame.draw.rect(surface, color, draw_rect, border_radius=4)
        pygame.draw.rect(surface, (45, 30, 15), draw_rect, 2, border_radius=4)
        # Bracing
        pygame.draw.line(surface, (70, 45, 25), draw_rect.topleft, draw_rect.bottomright, 2)
        pygame.draw.line(surface, (70, 45, 25), draw_rect.bottomleft, draw_rect.topright, 2)


class PickupItem:
    """Floating reward item absorbed by player walking into it."""
    def __init__(self, x: float, y: float, item_type: str = "medkit"):
        self.pos = pygame.math.Vector2(x, y)
        self.item_type = item_type  # "medkit" or "overcharge"
        self.radius = 16.0
        self.is_collected = False
        self.spawn_time = pygame.time.get_ticks()

    def update(self, player, game_state) -> bool:
        if self.is_collected:
            return False
        
        # Check collision with player
        dist = (player.pos - self.pos).length()
        if dist <= self.radius + player.radius:
            self.is_collected = True
            self.apply_effect(player, game_state)
            return False
        return True

    def apply_effect(self, player, game_state):
        game_state.audio.play('boon')
        if self.item_type == "medkit":
            player.heal(25)
            game_state.particles.add_damage_number(player.pos.x, player.pos.y, 25, damage_type="heal")
            game_state.particles.spawn_sparks(player.pos.x, player.pos.y, count=10, color=COLOR_HEALTH_GREEN)
        elif self.item_type == "overcharge":
            # Timed attack boost (8 seconds, capped duration)
            player.apply_attack_boost(8.0)
            game_state.particles.spawn_sparks(player.pos.x, player.pos.y, count=16, color=COLOR_CRIT_YELLOW)
            game_state.particles.add_damage_number(player.pos.x, player.pos.y - 12, 0, is_crit=True, damage_type="buff")

    def draw(self, surface: pygame.Surface, camera):
        bob = math.sin((pygame.time.get_ticks() - self.spawn_time) * 0.006) * 5.0
        screen_pos = camera.apply(pygame.math.Vector2(self.pos.x, self.pos.y + bob))
        
        if self.item_type == "medkit":
            # Green cross capsule
            pygame.draw.circle(surface, COLOR_STEEL_DARK, screen_pos, 16)
            pygame.draw.circle(surface, COLOR_HEALTH_GREEN, screen_pos, 14)
            # White plus
            pygame.draw.rect(surface, COLOR_WHITE, (screen_pos[0] - 8, screen_pos[1] - 3, 16, 6))
            pygame.draw.rect(surface, COLOR_WHITE, (screen_pos[0] - 3, screen_pos[1] - 8, 6, 16))
        else:
            # Golden overcharge battery
            pygame.draw.circle(surface, COLOR_STEEL_DARK, screen_pos, 16)
            pygame.draw.circle(surface, COLOR_CRIT_YELLOW, screen_pos, 14)
            pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, screen_pos, 7)


class SteamVent:
    """Floor hazard grate that hisses warning steam, then erupts with scalding heat."""
    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, 64, 64)
        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        self.radius = 32.0
        self.cycle_timer = random.uniform(0.0, 3.0)
        self.is_active = False

    def update(self, dt: float, player, enemies, game_state):
        self.cycle_timer += dt
        cycle_pos = self.cycle_timer % 5.0
        
        # 0.0 - 2.8s: Idle grate
        # 2.8 - 3.6s: Warning hiss (small sparks)
        # 3.6 - 5.0s: Full erupting steam burst!
        if 2.8 <= cycle_pos < 3.6:
            if random.random() < 0.35:
                game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=2, color=COLOR_EMBER_ORANGE)
        elif cycle_pos >= 3.6:
            self.is_active = True
            if random.random() < 0.60:
                game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=4, color=(240, 245, 250))
                
            # Damage entities on grate
            if player and player.is_alive() and self.rect.collidepoint(player.pos.x, player.pos.y):
                player.take_damage(DamageEvent(max(1, int(22 * dt)), source_type="hazard", damage_type="steam"), game_state)

            for enemy in enemies:
                if enemy.is_alive() and self.rect.collidepoint(enemy.pos.x, enemy.pos.y):
                    enemy.take_damage(DamageEvent(max(1, int(35 * dt)), source_type="hazard", damage_type="steam"), game_state)
        else:
            self.is_active = False

    def draw(self, surface: pygame.Surface, camera):
        draw_rect = camera.apply_rect(self.rect)
        pygame.draw.rect(surface, (25, 28, 34), draw_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_STEEL_LIGHT if not self.is_active else COLOR_EMBER_ORANGE, draw_rect, 2, border_radius=4)
        # Grate slots
        for gy in range(draw_rect.top + 10, draw_rect.bottom - 6, 12):
            pygame.draw.line(surface, (15, 18, 22), (draw_rect.left + 8, gy), (draw_rect.right - 8, gy), 3)


class TrainWindow:
    """Destructible glass train window with intact, cracked, and shattered states."""
    STATE_INTACT = 0
    STATE_CRACKED = 1
    STATE_SHATTERED = 2

    def __init__(self, x: float, y: float, width: float = 95.0, height: float = 22.0, wall_side: str = "top"):
        self.rect = pygame.Rect(x, y, width, height)
        self.pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        self.wall_side = wall_side
        self.state = self.STATE_INTACT
        self.health = 35
        self.wind_timer = 0.0

    def take_damage(self, amount: int, game_state):
        if self.state == self.STATE_SHATTERED:
            return
        self.health -= amount
        if self.health <= 0:
            self.state = self.STATE_SHATTERED
            if game_state:
                game_state.audio.play('hit')
                game_state.camera.add_trauma(0.20)
                game_state.particles.spawn_glass_shards(self.pos.x, self.pos.y, count=18)
                inward_y = self.pos.y + (30 if self.wall_side == "top" else -30)
                game_state.particles.spawn_steam(self.pos.x, inward_y, count=6, color=(210, 235, 255))
        elif self.health <= 20 and self.state == self.STATE_INTACT:
            self.state = self.STATE_CRACKED
            if game_state:
                game_state.audio.play('hit')
                game_state.particles.spawn_glass_shards(self.pos.x, self.pos.y, count=6)

    def update(self, dt: float, game_state):
        if self.state == self.STATE_SHATTERED and game_state:
            self.wind_timer += dt
            if random.random() < 0.25:
                inward_y = self.pos.y + random.uniform(15, 60) if self.wall_side == "top" else self.pos.y - random.uniform(15, 60)
                game_state.particles.spawn_wind_streak(self.pos.x + random.uniform(-25, 25), inward_y, dir_x=-1.0)

    def draw(self, surface: pygame.Surface, camera, car_type: str, track_scroll: float):
        draw_rect = camera.apply_rect(self.rect)
        
        # Outer Brass / Steel window frame
        pygame.draw.rect(surface, (28, 25, 24), draw_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BRASS, draw_rect, 2, border_radius=4)
        
        inner_rect = draw_rect.inflate(-4, -4)
        if self.state == self.STATE_INTACT:
            base_col = (165, 220, 255) if car_type == "cold_storage" else (120, 180, 225)
            pygame.draw.rect(surface, base_col, inner_rect, border_radius=2)
            # Glass shine reflection diagonal
            pygame.draw.line(surface, COLOR_WHITE, (inner_rect.left + 8, inner_rect.bottom - 3), (inner_rect.left + 26, inner_rect.top + 3), 2)
            pygame.draw.line(surface, COLOR_WHITE, (inner_rect.left + 32, inner_rect.bottom - 3), (inner_rect.left + 52, inner_rect.top + 3), 1)
        elif self.state == self.STATE_CRACKED:
            base_col = (130, 185, 225)
            pygame.draw.rect(surface, base_col, inner_rect, border_radius=2)
            # Spiderweb fracture lines
            cx, cy = inner_rect.center
            pygame.draw.line(surface, COLOR_WHITE, (cx - 16, cy - 6), (cx + 14, cy + 5), 2)
            pygame.draw.line(surface, COLOR_WHITE, (cx - 6, cy + 7), (cx + 10, cy - 6), 2)
            pygame.draw.line(surface, (240, 240, 240), (cx, cy), (cx - 24, cy), 1)
            pygame.draw.line(surface, (240, 240, 240), (cx, cy), (cx + 26, cy - 3), 1)
        else: # SHATTERED
            # Open night sky / rushing landscape opening
            pygame.draw.rect(surface, (16, 14, 18), inner_rect, border_radius=2)
            # Fast track scenery blur lines racing by
            blur_offset = int(-track_scroll * 1.5) % 24
            for sx in range(inner_rect.left + blur_offset, inner_rect.right, 24):
                pygame.draw.line(surface, (45, 52, 65), (sx, inner_rect.top), (sx - 8, inner_rect.bottom), 2)
            # Jagged perimeter glass teeth
            pts_top = [
                inner_rect.topleft,
                (inner_rect.left + 8, inner_rect.top + 5),
                (inner_rect.left + 20, inner_rect.top + 2),
                (inner_rect.left + 35, inner_rect.top + 7),
                (inner_rect.left + 55, inner_rect.top + 3),
                (inner_rect.right - 12, inner_rect.top + 6),
                inner_rect.topright
            ]
            for p1, p2 in zip(pts_top[:-1], pts_top[1:]):
                pygame.draw.line(surface, (220, 245, 255), p1, p2, 2)
            pts_bot = [
                inner_rect.bottomleft,
                (inner_rect.left + 12, inner_rect.bottom - 6),
                (inner_rect.left + 28, inner_rect.bottom - 2),
                (inner_rect.left + 48, inner_rect.bottom - 7),
                (inner_rect.right - 16, inner_rect.bottom - 4),
                inner_rect.bottomright
            ]
            for p1, p2 in zip(pts_bot[:-1], pts_bot[1:]):
                pygame.draw.line(surface, (220, 245, 255), p1, p2, 2)


class WallLamp:
    """Flickering brass gas sconce casting warm ambient light on the floor and walls."""
    def __init__(self, x: float, y: float, wall_side: str = "top"):
        self.pos = pygame.math.Vector2(x, y)
        self.wall_side = wall_side
        self.flicker_phase = random.uniform(0, 10)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        ticks = pygame.time.get_ticks() * 0.006 + self.flicker_phase
        flicker = 0.85 + 0.15 * math.sin(ticks * 2.3) + 0.10 * math.sin(ticks * 7.1)
        flicker = max(0.65, min(1.15, flicker))

        # Radial warm light cast
        glow_r = int(58 * flicker)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        alpha = int(40 * flicker)
        pygame.draw.circle(glow_surf, (255, 210, 110, alpha), (glow_r, glow_r), glow_r)
        pygame.draw.circle(glow_surf, (255, 235, 160, int(alpha * 1.5)), (glow_r, glow_r), int(glow_r * 0.45))
        surface.blit(glow_surf, (screen_pos[0] - glow_r, screen_pos[1] - glow_r))

        # Brass sconce fixture
        fixture_rect = pygame.Rect(screen_pos[0] - 5, screen_pos[1] - 8, 10, 16)
        pygame.draw.rect(surface, (140, 100, 35), fixture_rect, border_radius=2)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, fixture_rect, 1, border_radius=2)

        # Glowing ember lantern wick
        core_pos = (screen_pos[0], screen_pos[1] + (2 if self.wall_side == "top" else -2))
        pygame.draw.circle(surface, (255, 230, 140), core_pos, max(2, int(3 * flicker)))


class TrainCar:
    """Represents an individual train car arena with walls, windows, and obstacles."""
    def __init__(self, car_index: int, car_type: str, theme: str = "steam"):
        self.car_index = car_index
        self.car_type = car_type       # "caboose", "passenger", "dining", "cold_storage", "cargo", "armory", "engine"
        self.theme = theme             # "steam" or "subway"
        
        self.width = CAR_WIDTH
        self.height = CAR_BOTTOM_WALL - CAR_TOP_WALL
        self.top_wall_y = CAR_TOP_WALL
        self.bottom_wall_y = CAR_BOTTOM_WALL
        
        # Door states
        self.exit_unlocked = False
        self.exit_door_rect = pygame.Rect(self.width - 50, (CAR_TOP_WALL + CAR_BOTTOM_WALL) // 2 - 60, 50, 120)
        self.entrance_door_rect = pygame.Rect(0, (CAR_TOP_WALL + CAR_BOTTOM_WALL) // 2 - 60, 50, 120)
        # Generous exit trigger zone
        self.exit_trigger_rect = pygame.Rect(self.width - 150, (CAR_TOP_WALL + CAR_BOTTOM_WALL) // 2 - 90, 150, 180)
        
        # Upgrade station trigger pedestal (placed near exit door)
        self.boon_pedestal_pos = pygame.math.Vector2(self.width - 180, (CAR_TOP_WALL + CAR_BOTTOM_WALL) // 2)
        self.boon_pedestal_radius = 35.0
        self.boon_pedestal_active = False
        self.boon_claimed = False

        # Destructible Windows & Wall Sconces
        self.windows: list[TrainWindow] = []
        self.wall_lamps: list[WallLamp] = []
        for wx in range(140, self.width - 140, 180):
            self.windows.append(TrainWindow(wx, self.top_wall_y - 14, width=95, height=22, wall_side="top"))
            self.windows.append(TrainWindow(wx, self.bottom_wall_y - 8, width=95, height=22, wall_side="bottom"))
            if wx + 90 < self.width - 120:
                self.wall_lamps.append(WallLamp(wx + 90, self.top_wall_y - 4, wall_side="top"))
                self.wall_lamps.append(WallLamp(wx + 90, self.bottom_wall_y + 4, wall_side="bottom"))

        # Obstacles and interactive props
        self.obstacles = []
        self.barrels = []
        self.crates = []
        self.vents = []
        self.hot_coals = []
        self._generate_obstacles()

        # Parallax background track offset
        self.track_scroll = 0.0
        self.speed_mph = 110.0
        
        # UI Font for prompts
        pygame.font.init()
        self.font_prompt = pygame.font.SysFont("Helvetica, Arial, sans-serif", 14, bold=True)

    def get_playable_bounds(self) -> pygame.Rect:
        return pygame.Rect(20, self.top_wall_y + 10, self.width - 40, self.height - 20)

    def is_inside_playable_area(self, pos: pygame.math.Vector2) -> bool:
        bounds = self.get_playable_bounds()
        return bounds.collidepoint(pos.x, pos.y)

    def can_player_exit(self, player_pos: pygame.math.Vector2, player_radius: float = 22.0) -> bool:
        """Returns True if exit is unlocked and player is at or inside the exit door zone."""
        if self.car_type == "engine":
            return False
        if not self.exit_unlocked:
            return False
        player_box = pygame.Rect(player_pos.x - player_radius, player_pos.y - player_radius, player_radius * 2, player_radius * 2)
        return player_box.colliderect(self.exit_trigger_rect) or player_pos.x >= (self.width - 110)

    def unlock_exit(self, game_state):
        if self.car_type == "engine":
            return
        if not self.exit_unlocked:
            self.exit_unlocked = True
            self.boon_pedestal_active = True
            game_state.audio.play('door')
            game_state.particles.spawn_sparks(self.exit_door_rect.centerx, self.exit_door_rect.centery, count=16, color=COLOR_BRASS)

    def _generate_obstacles(self):
        """Place theme-specific tactical cover, explosive barrels, and supply crates."""
        mid_y = (self.top_wall_y + self.bottom_wall_y) // 2
        
        if self.car_type == "passenger":
            # Rows of passenger train seats along top and bottom lanes
            for x in range(300, self.width - 350, 220):
                self.obstacles.append(pygame.Rect(x, self.top_wall_y + 35, 75, 55))
                self.obstacles.append(pygame.Rect(x, self.bottom_wall_y - 90, 75, 55))
            # Supply crates in luggage alcoves
            self.crates.append(SupplyCrate(580, mid_y - 24))
            self.crates.append(SupplyCrate(1240, mid_y - 24))

        elif self.car_type == "dining":
            # Dining tables with chairs in staggered center lanes
            for x in range(350, self.width - 350, 260):
                self.obstacles.append(pygame.Rect(x, mid_y - 35, 80, 70))
                self.obstacles.append(pygame.Rect(x + 100, self.top_wall_y + 30, 60, 45))
            # Supply crates with snacks
            self.crates.append(SupplyCrate(850, self.bottom_wall_y - 95))
            self.crates.append(SupplyCrate(1450, self.bottom_wall_y - 95))

        elif self.car_type == "cold_storage":
            # Refrigerated Meat Locker: hanging frozen hooks and ice blocks
            for x in range(350, self.width - 350, 280):
                self.obstacles.append(pygame.Rect(x, mid_y - 50, 65, 100))
                self.obstacles.append(pygame.Rect(x + 120, self.top_wall_y + 40, 70, 50))
            self.barrels.append(ExplosiveBarrel(750, mid_y + 60))
            self.crates.append(SupplyCrate(1100, self.bottom_wall_y - 90))

        elif self.car_type == "cargo":
            # Shipping crates maze + explosive red barrels!
            crate_positions = [
                (350, mid_y - 80, 70, 70),
                (350, mid_y + 20, 70, 70),
                (700, self.top_wall_y + 40, 110, 60),
                (700, self.bottom_wall_y - 100, 110, 60),
                (1100, mid_y - 50, 80, 100),
                (1450, self.top_wall_y + 60, 90, 70),
                (1450, self.bottom_wall_y - 120, 90, 70),
                (1750, mid_y - 40, 65, 80),
            ]
            for x, y, w, h in crate_positions:
                self.obstacles.append(pygame.Rect(x, y, w, h))

            # Explosive Barrels placed near choke points!
            self.barrels.append(ExplosiveBarrel(520, mid_y - 24))
            self.barrels.append(ExplosiveBarrel(950, self.bottom_wall_y - 100))
            self.barrels.append(ExplosiveBarrel(1300, self.top_wall_y + 50))
            self.barrels.append(ExplosiveBarrel(1650, mid_y - 24))
            
            # Supply crates
            self.crates.append(SupplyCrate(550, self.top_wall_y + 45))
            self.crates.append(SupplyCrate(1300, self.bottom_wall_y - 90))

        elif self.car_type == "armory":
            # Heavy metal weapon racks, steam vents, and explosive munitions
            for x in range(400, self.width - 350, 300):
                self.obstacles.append(pygame.Rect(x, self.top_wall_y + 40, 80, 50))
                self.obstacles.append(pygame.Rect(x + 100, self.bottom_wall_y - 90, 80, 50))

            # Steam grate hazards
            self.vents.append(SteamVent(650, mid_y - 32))
            self.vents.append(SteamVent(1250, mid_y - 32))
            
            # Barrels
            self.barrels.append(ExplosiveBarrel(800, mid_y - 24))
            self.barrels.append(ExplosiveBarrel(1400, mid_y - 24))
            self.crates.append(SupplyCrate(950, self.top_wall_y + 45))

        elif self.car_type == "inspection":
            # Turnstiles and checkpoint barrier desks for Mini-Boss arena
            for x in (450, 1450):
                self.obstacles.append(pygame.Rect(x, self.top_wall_y + 35, 55, 90))
                self.obstacles.append(pygame.Rect(x, self.bottom_wall_y - 125, 55, 90))
            # Center desk barrier
            self.obstacles.append(pygame.Rect(950, mid_y - 65, 70, 130))
            self.crates.append(SupplyCrate(700, self.top_wall_y + 40))
            self.crates.append(SupplyCrate(1200, self.bottom_wall_y - 90))

        elif self.car_type == "observation":
            # Observation skylight: velvet booth benches & telescope stands
            for x in range(400, self.width - 350, 300):
                self.obstacles.append(pygame.Rect(x, self.top_wall_y + 35, 75, 50))
                self.obstacles.append(pygame.Rect(x, self.bottom_wall_y - 85, 75, 50))
            self.obstacles.append(pygame.Rect(850, mid_y - 35, 90, 70))
            self.crates.append(SupplyCrate(550, mid_y - 24))
            self.crates.append(SupplyCrate(1250, mid_y - 24))

        elif self.car_type == "furnace_tender":
            # Massive coal hopper bins along edges
            for x in (450, 1350):
                self.obstacles.append(pygame.Rect(x, self.top_wall_y + 40, 110, 70))
                self.obstacles.append(pygame.Rect(x, self.bottom_wall_y - 110, 110, 70))
            self.obstacles.append(pygame.Rect(900, mid_y - 50, 130, 100))
            
            # Hot coal beds on floor
            self.hot_coals.append(pygame.Rect(650, mid_y - 40, 160, 80))
            self.hot_coals.append(pygame.Rect(1150, mid_y - 40, 160, 80))

            # Steam vents & barrels
            self.vents.append(SteamVent(720, self.top_wall_y + 45))
            self.vents.append(SteamVent(1250, self.bottom_wall_y - 90))
            self.barrels.append(ExplosiveBarrel(550, mid_y - 24))
            self.barrels.append(ExplosiveBarrel(1450, mid_y - 24))
            self.crates.append(SupplyCrate(850, self.top_wall_y + 45))

        elif self.car_type == "engine":
            # Engine room: massive central furnace boiler + steam vents
            self.obstacles.append(pygame.Rect(800, mid_y - 75, 150, 150))
            self.obstacles.append(pygame.Rect(400, self.top_wall_y + 40, 90, 60))
            self.obstacles.append(pygame.Rect(400, self.bottom_wall_y - 100, 90, 60))
            self.obstacles.append(pygame.Rect(1400, self.top_wall_y + 40, 90, 60))
            self.obstacles.append(pygame.Rect(1400, self.bottom_wall_y - 100, 90, 60))

            self.vents.append(SteamVent(600, mid_y - 32))
            self.vents.append(SteamVent(1100, mid_y - 32))
            self.barrels.append(ExplosiveBarrel(450, mid_y - 24))

    def update(self, dt: float, player=None, enemies=None, game_state=None):
        # Scroll track parallax
        self.track_scroll = (self.track_scroll + self.speed_mph * 12.0 * dt) % 120.0

        # Update barrels & crates
        for c in self.crates:
            c.update(dt)
        self.crates = [c for c in self.crates if not c.is_dead]
        self.barrels = [b for b in self.barrels if not b.is_dead]

        # Update destructible windows
        for win in self.windows:
            win.update(dt, game_state)

        # Update steam vents
        if player and enemies is not None and game_state:
            for v in self.vents:
                v.update(dt, player, enemies, game_state)

        # Ambient frost fog for Cold Storage car
        if self.car_type == "cold_storage" and game_state and random.random() < 0.20:
            fx = random.uniform(player.pos.x - 300, player.pos.x + 300)
            fy = random.uniform(self.top_wall_y + 20, self.bottom_wall_y - 20)
            game_state.particles.spawn_steam(fx, fy, count=2, color=(200, 235, 255))

        # Observation Deck Aerodynamic Headwinds
        if self.car_type == "observation" and player and player.is_alive():
            if not player.is_dashing:
                player.pos.x = max(player.radius + 25, player.pos.x - 65.0 * dt)
            if game_state and random.random() < 0.35:
                wx = random.uniform(player.pos.x - 150, player.pos.x + 450)
                wy = random.uniform(self.top_wall_y + 20, self.bottom_wall_y - 20)
                game_state.particles.spawn_steam(wx, wy, count=1, color=(215, 235, 255))

        # Furnace Tender Hot Coals Damage
        if self.car_type == "furnace_tender" and player and player.is_alive() and not player.is_dashing:
            for coal in self.hot_coals:
                if coal.collidepoint(player.pos.x, player.pos.y):
                    player.take_damage(DamageEvent(max(1, int(18 * dt)), source_type="hazard", damage_type="fire"), game_state)
                    if random.random() < 0.3:
                        game_state.particles.spawn_sparks(player.pos.x, player.pos.y, count=2, color=COLOR_EMBER_ORANGE)
                    break
            if game_state and random.random() < 0.35:
                fx = random.uniform(player.pos.x - 250, player.pos.x + 250)
                fy = random.uniform(self.top_wall_y + 20, self.bottom_wall_y - 20)
                game_state.particles.spawn_sparks(fx, fy, count=1, color=COLOR_EMBER_ORANGE)

    def draw(self, surface: pygame.Surface, camera):
        # 1. Scenery and passing train tracks outside windows
        self._draw_exterior_scenery(surface, camera)

        # 2. Train car interior floor
        floor_world_rect = pygame.Rect(0, self.top_wall_y, self.width, self.height)
        floor_screen_rect = camera.apply_rect(floor_world_rect)

        if self.car_type == "cold_storage":
            # Frosty Icy Floor
            pygame.draw.rect(surface, (28, 42, 58), floor_screen_rect)
            # Frost shine lines
            for gx in range(0, self.width, 100):
                sp = camera.apply(pygame.math.Vector2(gx, self.top_wall_y))
                pygame.draw.line(surface, (50, 75, 105), sp, (sp[0] + 60, sp[1] + self.height), 2)
        elif self.car_type == "inspection":
            # Checkpoint Checkerboard Tile Floor
            pygame.draw.rect(surface, (30, 36, 48), floor_screen_rect)
            tile_sz = 60
            for tx in range(0, self.width, tile_sz):
                for ty in range(self.top_wall_y, self.bottom_wall_y, tile_sz):
                    if ((tx // tile_sz) + (ty // tile_sz)) % 2 == 0:
                        tr = camera.apply_rect(pygame.Rect(tx, ty, tile_sz, tile_sz))
                        pygame.draw.rect(surface, (42, 50, 65), tr)
            # Brass checkpoint dividing line
            mid_line_rect = camera.apply_rect(pygame.Rect(self.width // 2, self.top_wall_y, 6, self.height))
            pygame.draw.rect(surface, COLOR_BRASS, mid_line_rect)
        elif self.car_type == "observation":
            # Panoramic Indigo Skylight Floor with brass inlays
            pygame.draw.rect(surface, (18, 22, 38), floor_screen_rect)
            for gx in range(0, self.width, 140):
                sp = camera.apply(pygame.math.Vector2(gx, self.top_wall_y))
                pygame.draw.line(surface, (35, 45, 75), sp, (sp[0] + 40, sp[1] + self.height), 2)
        elif self.car_type == "furnace_tender":
            # Grated Smelting Catwalk Floor
            pygame.draw.rect(surface, (22, 18, 18), floor_screen_rect)
            for gx in range(0, self.width, 40):
                sp = camera.apply(pygame.math.Vector2(gx, self.top_wall_y))
                pygame.draw.line(surface, (40, 28, 24), sp, (sp[0], sp[1] + self.height), 1)
        elif self.theme == "subway":
            pygame.draw.rect(surface, COLOR_SUBWAY_TILES, floor_screen_rect)
            for gx in range(0, self.width, 60):
                sp = camera.apply(pygame.math.Vector2(gx, self.top_wall_y))
                pygame.draw.line(surface, (25, 30, 38), sp, (sp[0], sp[1] + self.height), 1)
        else:
            # Polished Rich Mahogany Wood Planks
            pygame.draw.rect(surface, (45, 26, 18), floor_screen_rect)
            # Horizontal wood plank seams
            plank_h = 32
            for py in range(self.top_wall_y, self.bottom_wall_y, plank_h):
                sp1 = camera.apply(pygame.math.Vector2(0, py))
                sp2 = camera.apply(pygame.math.Vector2(self.width, py))
                pygame.draw.line(surface, (28, 16, 10), sp1, sp2, 2)
                # Subtle wood luster highlight
                pygame.draw.line(surface, (58, 35, 24), (sp1[0], sp1[1] + 2), (sp2[0], sp2[1] + 2), 1)

            # Central Victorian Damask Velvet Runner Carpet
            carpet_y = (self.top_wall_y + self.bottom_wall_y) // 2 - 75
            carpet_h = 150
            carpet_rect = camera.apply_rect(pygame.Rect(0, carpet_y, self.width, carpet_h))
            pygame.draw.rect(surface, (135, 20, 32), carpet_rect)
            # Carpet inner shadow
            pygame.draw.line(surface, (75, 12, 18), carpet_rect.topleft, carpet_rect.topright, 2)
            pygame.draw.line(surface, (75, 12, 18), carpet_rect.bottomleft, carpet_rect.bottomright, 2)
            # Braided Gold / Brass Fringe borders
            pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (carpet_rect.left, carpet_rect.top - 1), (carpet_rect.right, carpet_rect.top - 1), 3)
            pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (carpet_rect.left, carpet_rect.bottom + 1), (carpet_rect.right, carpet_rect.bottom + 1), 3)

            # Damask diamond pattern down center of carpet
            mid_cy = carpet_rect.centery
            for dx in range(carpet_rect.left + 25, carpet_rect.right - 20, 65):
                pts = [
                    (dx, mid_cy - 18),
                    (dx + 18, mid_cy),
                    (dx, mid_cy + 18),
                    (dx - 18, mid_cy)
                ]
                pygame.draw.polygon(surface, (165, 32, 45), pts)
                pygame.draw.polygon(surface, (200, 155, 45), pts, 1)

            # Brass Floor Rivets along wall borders
            for rx in range(0, self.width, 45):
                sp_top = camera.apply(pygame.math.Vector2(rx, self.top_wall_y + 6))
                sp_bot = camera.apply(pygame.math.Vector2(rx, self.bottom_wall_y - 6))
                pygame.draw.circle(surface, COLOR_BRASS, sp_top, 2)
                pygame.draw.circle(surface, COLOR_BRASS, sp_bot, 2)

        # 3. Hot Coals Floor Beds (Furnace Tender)
        for coal in self.hot_coals:
            c_screen = camera.apply_rect(coal)
            pygame.draw.rect(surface, (48, 18, 12), c_screen, border_radius=6)
            pygame.draw.rect(surface, (200, 60, 25), c_screen, 2, border_radius=6)
            for cx in range(c_screen.left + 15, c_screen.right - 10, 25):
                for cy in range(c_screen.top + 12, c_screen.bottom - 10, 20):
                    pulse = (math.sin(pygame.time.get_ticks() * 0.007 + cx + cy) + 1) * 0.5
                    rad = int(3 + 2 * pulse)
                    col = (int(220 + 35 * pulse), int(90 + 60 * pulse), 30)
                    pygame.draw.circle(surface, col, (cx, cy), rad)

        # 4. Steam Vents on floor
        for v in self.vents:
            v.draw(surface, camera)

        # 5. Obstacles (Seats, Tables, Turnstiles, Crates)
        for obs in self.obstacles:
            obs_screen = camera.apply_rect(obs)
            if self.car_type == "passenger":
                pygame.draw.rect(surface, COLOR_WOOD_LIGHT, obs_screen, border_radius=6)
                pygame.draw.rect(surface, (140, 30, 40), obs_screen.inflate(-6, -6), border_radius=4)
            elif self.car_type == "inspection":
                pygame.draw.rect(surface, (45, 55, 75), obs_screen, border_radius=4)
                pygame.draw.rect(surface, COLOR_BRASS, obs_screen, 2, border_radius=4)
            elif self.car_type == "observation":
                pygame.draw.rect(surface, COLOR_WOOD_DARK, obs_screen, border_radius=6)
                pygame.draw.rect(surface, (30, 80, 140), obs_screen.inflate(-6, -6), border_radius=4)
            elif self.car_type == "furnace_tender":
                pygame.draw.rect(surface, (35, 25, 22), obs_screen, border_radius=4)
                pygame.draw.rect(surface, (160, 65, 30), obs_screen, 2, border_radius=4)
            elif self.car_type == "cargo":
                pygame.draw.rect(surface, (95, 75, 50), obs_screen)
                pygame.draw.rect(surface, COLOR_STEEL_DARK, obs_screen, 2)
                pygame.draw.line(surface, COLOR_STEEL_DARK, obs_screen.topleft, obs_screen.bottomright, 2)
                pygame.draw.line(surface, COLOR_STEEL_DARK, obs_screen.bottomleft, obs_screen.topright, 2)
            elif self.car_type == "cold_storage":
                pygame.draw.rect(surface, (60, 90, 120), obs_screen, border_radius=6)
                pygame.draw.rect(surface, (140, 200, 235), obs_screen.inflate(-6, -6), border_radius=4)
            elif self.car_type == "engine":
                pygame.draw.rect(surface, COLOR_STEEL_MID, obs_screen, border_radius=8)
                pygame.draw.rect(surface, COLOR_EMBER_ORANGE, obs_screen.inflate(-12, -12), border_radius=4)
            else:
                pygame.draw.rect(surface, COLOR_STEEL_MID, obs_screen, border_radius=4)
                pygame.draw.rect(surface, COLOR_BRASS, obs_screen, 2, border_radius=4)

        # 5. Interactive Barrels and Crates
        for b in self.barrels:
            b.draw(surface, camera)
        for c in self.crates:
            c.draw(surface, camera)

        # 6. Train Walls, Destructible Windows & Wall Sconces
        self._draw_walls_and_windows(surface, camera)

        # 7. Entrance & Exit Doors
        self._draw_doors(surface, camera)

        # 8. Boon Upgrade Pedestal
        if self.boon_pedestal_active and not self.boon_claimed:
            self._draw_boon_pedestal(surface, camera)

    def _draw_exterior_scenery(self, surface: pygame.Surface, camera):
        top_strip = camera.apply_rect(pygame.Rect(-200, self.top_wall_y - 75, self.width + 400, 75))
        pygame.draw.rect(surface, (14, 15, 20), top_strip)
        bot_strip = camera.apply_rect(pygame.Rect(-200, self.bottom_wall_y, self.width + 400, 75))
        pygame.draw.rect(surface, (14, 15, 20), bot_strip)

        # Distant mountain silhouettes in scenery strip
        m_step = 160
        m_offset = int(-self.track_scroll * 0.3) % m_step
        for mx in range(-200 + m_offset, self.width + 300, m_step):
            mp1 = camera.apply(pygame.math.Vector2(mx, self.top_wall_y - 25))
            mp2 = camera.apply(pygame.math.Vector2(mx + 80, self.top_wall_y - 65))
            mp3 = camera.apply(pygame.math.Vector2(mx + 160, self.top_wall_y - 25))
            pygame.draw.polygon(surface, (22, 25, 34), [mp1, mp2, mp3])

        # Rushing railway ballast and ties
        tie_spacing = 45.0
        start_x = int(-self.track_scroll)
        for x in range(start_x, self.width + 200, int(tie_spacing)):
            top_pt1 = camera.apply(pygame.math.Vector2(x, self.top_wall_y - 60))
            top_pt2 = camera.apply(pygame.math.Vector2(x, self.top_wall_y - 12))
            pygame.draw.line(surface, (45, 40, 35), top_pt1, top_pt2, 4)

            bot_pt1 = camera.apply(pygame.math.Vector2(x, self.bottom_wall_y + 12))
            bot_pt2 = camera.apply(pygame.math.Vector2(x, self.bottom_wall_y + 60))
            pygame.draw.line(surface, (45, 40, 35), bot_pt1, bot_pt2, 4)

        # Steel Rails
        r1_t = camera.apply(pygame.math.Vector2(-200, self.top_wall_y - 36))
        r2_t = camera.apply(pygame.math.Vector2(self.width + 200, self.top_wall_y - 36))
        pygame.draw.line(surface, (140, 145, 155), r1_t, r2_t, 3)

        r1_b = camera.apply(pygame.math.Vector2(-200, self.bottom_wall_y + 36))
        r2_b = camera.apply(pygame.math.Vector2(self.width + 200, self.bottom_wall_y + 36))
        pygame.draw.line(surface, (140, 145, 155), r1_b, r2_b, 3)

    def _draw_walls_and_windows(self, surface: pygame.Surface, camera):
        top_wall = camera.apply_rect(pygame.Rect(0, self.top_wall_y - 18, self.width, 24))
        pygame.draw.rect(surface, COLOR_STEEL_DARK, top_wall)
        pygame.draw.line(surface, COLOR_BRASS, top_wall.bottomleft, top_wall.bottomright, 3)

        bot_wall = camera.apply_rect(pygame.Rect(0, self.bottom_wall_y - 6, self.width, 24))
        pygame.draw.rect(surface, COLOR_STEEL_DARK, bot_wall)
        pygame.draw.line(surface, COLOR_BRASS, bot_wall.topleft, bot_wall.topright, 3)

        # Structural Steel Rivets
        for rx in range(0, self.width, 90):
            p_top = camera.apply(pygame.math.Vector2(rx, self.top_wall_y - 10))
            p_bot = camera.apply(pygame.math.Vector2(rx, self.bottom_wall_y + 4))
            pygame.draw.circle(surface, (120, 125, 135), p_top, 2)
            pygame.draw.circle(surface, (120, 125, 135), p_bot, 2)

        # Ceiling copper steam pipe with brass couplings
        pipe_y = self.top_wall_y - 2
        pipe_pt1 = camera.apply(pygame.math.Vector2(0, pipe_y))
        pipe_pt2 = camera.apply(pygame.math.Vector2(self.width, pipe_y))
        pygame.draw.line(surface, (130, 85, 45), pipe_pt1, pipe_pt2, 4)
        pygame.draw.line(surface, (190, 140, 70), (pipe_pt1[0], pipe_pt1[1] - 1), (pipe_pt2[0], pipe_pt2[1] - 1), 1)
        for cx in range(60, self.width, 180):
            cp_pt = camera.apply(pygame.math.Vector2(cx, pipe_y))
            pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, (cp_pt[0] - 3, cp_pt[1] - 3, 6, 7), border_radius=1)

        # Draw Destructible Windows
        for win in self.windows:
            win.draw(surface, camera, self.car_type, self.track_scroll)

        # Draw Flickering Wall Sconces
        for lamp in self.wall_lamps:
            lamp.draw(surface, camera)

    def _draw_doors(self, surface: pygame.Surface, camera):
        in_door = camera.apply_rect(self.entrance_door_rect)
        pygame.draw.rect(surface, COLOR_STEEL_DARK, in_door)
        pygame.draw.rect(surface, (180, 40, 40), in_door, 3)

        out_door = camera.apply_rect(self.exit_door_rect)
        if self.car_type == "engine":
            # Locomotive firebox wall / closed furnace front
            pygame.draw.rect(surface, (20, 20, 26), out_door)
            pygame.draw.rect(surface, COLOR_EMBER_ORANGE, out_door, 3)
            # Furnace intake vents
            for vy in range(out_door.top + 15, out_door.bottom - 10, 18):
                pygame.draw.line(surface, (180, 50, 20), (out_door.left + 8, vy), (out_door.right - 8, vy), 3)
            return

        if self.exit_unlocked:
            pygame.draw.rect(surface, (15, 20, 25), out_door)
            pygame.draw.rect(surface, (40, 220, 110), out_door, 3)
            
            pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
            glow_w = int(25 + 15 * pulse)
            door_glow = pygame.Surface((glow_w, out_door.height), pygame.SRCALPHA)
            pygame.draw.rect(door_glow, (40, 220, 110, int(50 + 60 * pulse)), (0, 0, glow_w, out_door.height))
            surface.blit(door_glow, (out_door.x - glow_w, out_door.y))

            prompt_surf = self.font_prompt.render("NEXT CAR → [WALK THROUGH]", True, (80, 255, 140))
            prompt_rect = prompt_surf.get_rect(center=(out_door.centerx - 60, out_door.top - 18))
            surface.blit(prompt_surf, prompt_rect)
        else:
            pygame.draw.rect(surface, COLOR_STEEL_MID, out_door)
            pygame.draw.rect(surface, (220, 50, 50), out_door, 3)

    def _draw_boon_pedestal(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.boon_pedestal_pos)
        r = int(self.boon_pedestal_radius)
        
        pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1) * 0.5
        glow_r = int(r + 8 + 8 * pulse)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, int(70 + 50 * pulse)), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (screen_pos[0] - glow_r, screen_pos[1] - glow_r))

        pygame.draw.circle(surface, COLOR_STEEL_DARK, screen_pos, r)
        pygame.draw.circle(surface, COLOR_BRASS, screen_pos, r - 4)
        pygame.draw.circle(surface, COLOR_WHITE, screen_pos, r - 10)

        txt_surf = self.font_prompt.render(">>> CLAIM UPGRADE [STEP HERE / E] >>>", True, (255, 230, 110))
        txt_rect = txt_surf.get_rect(center=(screen_pos[0], screen_pos[1] - r - 16))
        
        bg_rect = pygame.Rect(txt_rect.x - 6, txt_rect.y - 2, txt_rect.width + 12, txt_rect.height + 4)
        pygame.draw.rect(surface, (15, 18, 24), bg_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_BRASS, bg_rect, 1, border_radius=4)
        surface.blit(txt_surf, txt_rect)
