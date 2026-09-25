"""Particle systems and floating damage numbers for combat juice."""
import pygame
import random
import math
from src.config import (
    COLOR_CRIT_YELLOW, COLOR_WHITE, COLOR_LIGHTNING_CYAN,
    COLOR_EMBER_ORANGE, COLOR_HEALTH_GREEN, COLOR_STEAM_WHITE,
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT
)

class DamageNumber:
    """Floating combat text showing damage dealt or healed."""
    def __init__(self, x: float, y: float, amount: int, is_crit: bool = False, damage_type: str = "normal"):
        self.pos = pygame.math.Vector2(x + random.uniform(-10, 10), y - 10)
        # Random upwards burst velocity
        angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
        speed = random.uniform(140, 220) if is_crit else random.uniform(80, 140)
        self.vel = pygame.math.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.amount = amount
        self.is_crit = is_crit
        self.damage_type = damage_type
        
        self.lifetime = 0.8 if is_crit else 0.6
        self.timer = self.lifetime
        
        # Color resolution
        if damage_type == "heal":
            self.color = COLOR_HEALTH_GREEN
        elif damage_type == "buff":
            self.color = COLOR_CRIT_YELLOW
        elif is_crit:
            self.color = COLOR_CRIT_YELLOW
        elif damage_type == "electric":
            self.color = COLOR_LIGHTNING_CYAN
        elif damage_type == "fire" or damage_type == "steam":
            self.color = COLOR_EMBER_ORANGE
        else:
            self.color = COLOR_WHITE

    def update(self, dt: float) -> bool:
        """Update position and gravity. Returns False when dead."""
        self.timer -= dt
        # Upward deceleration
        self.vel.y += 240 * dt
        self.pos += self.vel * dt
        return self.timer > 0

    def draw(self, surface: pygame.Surface, camera, font_normal: pygame.font.Font, font_crit: pygame.font.Font):
        screen_pos = camera.apply(self.pos)
        alpha = max(0.0, min(1.0, self.timer / (self.lifetime * 0.4)))
        font = font_crit if self.is_crit else font_normal
        text = f"{self.amount}!" if self.is_crit else f"{self.amount}"
        if self.damage_type == "heal":
            text = f"+{self.amount}"
        elif self.damage_type == "buff":
            text = "[!] OVERCHARGE!"

        rendered = font.render(text, True, self.color)
        if alpha < 1.0:
            rendered.set_alpha(int(alpha * 255))
            
        # Draw shadow for contrast
        shadow = font.render(text, True, (10, 10, 15))
        shadow.set_alpha(int(alpha * 200))
        surface.blit(shadow, (screen_pos[0] + 1, screen_pos[1] + 1))
        surface.blit(rendered, screen_pos)


class Particle:
    """Individual particle with physics, color fading, and size decay."""
    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: tuple, radius: float, lifetime: float,
                 drag: float = 0.95, gravity: float = 0.0, shape: str = "circle"):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vx, vy)
        self.color = color
        self.max_radius = radius
        self.radius = radius
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.drag = drag
        self.gravity = gravity
        self.shape = shape

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False
        self.vel.y += self.gravity * dt
        self.vel *= (self.drag ** (dt * 60))
        self.pos += self.vel * dt
        self.radius = max(1.0, self.max_radius * (self.lifetime / self.max_lifetime))
        return True

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        progress = self.lifetime / self.max_lifetime
        alpha = int(255 * progress)
        
        # Fast render using circle or rectangle
        r = int(self.radius)
        if r <= 0:
            return
            
        if self.shape == "spark":
            # Draw elongated line in direction of velocity
            end_x = screen_pos[0] - int(self.vel.x * 0.03)
            end_y = screen_pos[1] - int(self.vel.y * 0.03)
            pygame.draw.line(surface, self.color, screen_pos, (end_x, end_y), max(1, r))
        elif self.shape == "square":
            rect = pygame.Rect(screen_pos[0] - r, screen_pos[1] - r, r * 2, r * 2)
            pygame.draw.rect(surface, self.color, rect)
        else:
            pygame.draw.circle(surface, self.color, screen_pos, r)


class ParticleManager:
    """Manages spawning, updating, and drawing all visual effects."""
    def __init__(self):
        self.particles: list[Particle] = []
        self.damage_numbers: list[DamageNumber] = []
        
        pygame.font.init()
        self.font_normal = pygame.font.SysFont("Helvetica, Arial, sans-serif", 16, bold=True)
        self.font_crit = pygame.font.SysFont("Helvetica, Arial, sans-serif", 24, bold=True)

    def spawn_sparks(self, x: float, y: float, count: int = 8, color: tuple = (255, 200, 50), speed: float = 260.0):
        """Spawns energetic spark lines when bullets hit or metal strikes."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            sp = random.uniform(speed * 0.4, speed)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * sp, math.sin(angle) * sp,
                color=color,
                radius=random.uniform(2, 3.5),
                lifetime=random.uniform(0.12, 0.25),
                drag=0.92,
                shape="spark"
            ))

    def spawn_glass_shards(self, x: float, y: float, count: int = 14):
        """Spawns glinting glass shards and fractured slivers when windows shatter."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            sp = random.uniform(80, 260)
            col = random.choice([(200, 240, 255), (160, 215, 245), (255, 255, 255), (130, 190, 230)])
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * sp, math.sin(angle) * sp + random.uniform(20, 60),
                color=col,
                radius=random.uniform(2.0, 4.5),
                lifetime=random.uniform(0.35, 0.70),
                drag=0.91,
                gravity=180.0,
                shape="square"
            ))

    def spawn_wind_streak(self, x: float, y: float, dir_x: float = -1.0):
        """Spawns high-velocity wind streak blowing in through shattered windows."""
        sp = random.uniform(260, 480)
        self.particles.append(Particle(
            x, y,
            dir_x * sp, random.uniform(-25, 25),
            color=(215, 235, 255),
            radius=random.uniform(1.8, 3.2),
            lifetime=random.uniform(0.18, 0.35),
            drag=0.96,
            shape="spark"
        ))

    def spawn_steam(self, x: float, y: float, count: int = 5, color: tuple = COLOR_STEAM_WHITE):
        """Spawns soft billowing steam clouds."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            sp = random.uniform(30, 80)
            self.particles.append(Particle(
                x + random.uniform(-6, 6), y + random.uniform(-6, 6),
                math.cos(angle) * sp, math.sin(angle) * sp - 20,  # upward drift
                color=color,
                radius=random.uniform(6, 14),
                lifetime=random.uniform(0.3, 0.6),
                drag=0.90,
                shape="circle"
            ))

    def spawn_dash_ghost(self, x: float, y: float, radius: float, color: tuple = (100, 200, 255)):
        """Leaves an ethereal ghost image of player after dash."""
        self.particles.append(Particle(
            x, y, 0, 0,
            color=color,
            radius=radius,
            lifetime=0.18,
            drag=1.0,
            shape="circle"
        ))

    def spawn_explosion(self, x: float, y: float, radius: float = 40.0):
        """Massive fiery burst with shockwave fragments."""
        # Core fireballs
        for _ in range(20):
            angle = random.uniform(0, math.tau)
            sp = random.uniform(50, 260)
            color = random.choice([COLOR_EMBER_ORANGE, COLOR_CRIT_YELLOW, (255, 60, 20)])
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * sp, math.sin(angle) * sp,
                color=color,
                radius=random.uniform(8, 18),
                lifetime=random.uniform(0.25, 0.45),
                drag=0.88,
                shape="circle"
            ))
    def spawn_rivet_fire(self, x: float, y: float, dir_vec: pygame.math.Vector2):
        """Pneumatic Riveter fire FX: sharp needle brass sparks + side-vent high pressure steam puff."""
        # Needle sparks forward
        base_angle = math.atan2(dir_vec.y, dir_vec.x)
        for _ in range(5):
            ang = base_angle + random.uniform(-0.15, 0.15)
            sp = random.uniform(280, 420)
            self.particles.append(Particle(
                x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                color=COLOR_BRASS_HIGHLIGHT, radius=random.uniform(2.0, 3.2),
                lifetime=random.uniform(0.10, 0.18), drag=0.91, shape="spark"
            ))
        # Side-vent steam puff
        perp_angle = base_angle + math.pi * 0.5 * random.choice([-1, 1])
        sp_steam = random.uniform(35, 65)
        self.particles.append(Particle(
            x, y, math.cos(perp_angle) * sp_steam, math.sin(perp_angle) * sp_steam,
            color=COLOR_STEAM_WHITE, radius=random.uniform(6, 10),
            lifetime=0.22, drag=0.88, shape="circle"
        ))

    def spawn_cleave_fire(self, cx: float, cy: float, aim_angle: float, arc_span: float, reach: float):
        """Stoker's Cleaver swing FX: fiery ember slash crescent and flying glowing coal sparks."""
        for i in range(14):
            sub_ang = aim_angle - arc_span * 0.5 + (arc_span * i / 13)
            px = cx + math.cos(sub_ang) * reach
            py = cy + math.sin(sub_ang) * reach
            # Fiery blade edge sparks
            color = random.choice([COLOR_EMBER_ORANGE, COLOR_CRIT_YELLOW, (255, 60, 20)])
            sp = random.uniform(40, 160)
            self.particles.append(Particle(
                px, py, math.cos(sub_ang) * sp, math.sin(sub_ang) * sp,
                color=color, radius=random.uniform(2.5, 4.5),
                lifetime=random.uniform(0.18, 0.28), drag=0.90, shape="spark"
            ))

    def spawn_scattergun_fire(self, x: float, y: float, dir_vec: pygame.math.Vector2):
        """Coal Scattergun fire FX: heavy conical muzzle blaze, dark coal smoke, and ember shrapnel."""
        base_angle = math.atan2(dir_vec.y, dir_vec.x)
        # Heavy muzzle flare fire
        for _ in range(10):
            ang = base_angle + random.uniform(-0.45, 0.45)
            sp = random.uniform(160, 380)
            color = random.choice([COLOR_CRIT_YELLOW, COLOR_EMBER_ORANGE, (255, 80, 20)])
            self.particles.append(Particle(
                x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                color=color, radius=random.uniform(3.5, 6.0),
                lifetime=random.uniform(0.15, 0.25), drag=0.86, shape="circle"
            ))
        # Billowing dark coal smoke cloud
        for _ in range(6):
            ang = base_angle + random.uniform(-0.35, 0.35)
            sp = random.uniform(50, 120)
            self.particles.append(Particle(
                x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                color=(55, 52, 50), radius=random.uniform(8, 16),
                lifetime=random.uniform(0.28, 0.45), drag=0.88, shape="circle"
            ))

    def spawn_tesla_fire(self, x: float, y: float, dir_vec: pygame.math.Vector2):
        """Tesla Arc Caster fire FX: crackling cyan electric arcs and expanding plasma rings."""
        base_angle = math.atan2(dir_vec.y, dir_vec.x)
        for _ in range(8):
            ang = base_angle + random.uniform(-0.6, 0.6)
            sp = random.uniform(200, 380)
            color = random.choice([COLOR_LIGHTNING_CYAN, (180, 240, 255), COLOR_WHITE])
            self.particles.append(Particle(
                x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                color=color, radius=random.uniform(2.5, 4.0),
                lifetime=random.uniform(0.12, 0.22), drag=0.89, shape="spark"
            ))
        # Ion plasma ring
        self.particles.append(Particle(
            x, y, dir_vec.x * 90, dir_vec.y * 90,
            color=COLOR_LIGHTNING_CYAN, radius=10.0,
            lifetime=0.18, drag=0.92, shape="circle"
        ))

    def add_damage_number(self, x: float, y: float, amount: int, is_crit: bool = False, damage_type: str = "normal"):
        self.damage_numbers.append(DamageNumber(x, y, amount, is_crit, damage_type))

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.damage_numbers = [d for d in self.damage_numbers if d.update(dt)]

    def draw(self, surface: pygame.Surface, camera):
        for p in self.particles:
            p.draw(surface, camera)
        for d in self.damage_numbers:
            d.draw(surface, camera, self.font_normal, self.font_crit)
