"""Specialized high-detail sprite rendering module for Next Stop (2026).
Provides layered, animated procedural character and enemy models.
"""
import pygame
import math
import random
from src.config import (
    COLOR_WHITE, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_STEEL_LIGHT, COLOR_EMBER_ORANGE,
    COLOR_LIGHTNING_CYAN, COLOR_CRIT_YELLOW, COLOR_CARPET_RED, COLOR_SHADOW
)

# Palette definitions for Stoker Hero
COLOR_DIRTY_SHIRT = (215, 212, 198)
COLOR_SHIRT_SHADOW = (165, 160, 145)
COLOR_SOOT = (35, 33, 33)
COLOR_STOKER_SKIN = (215, 160, 125)
COLOR_STOKER_SKIN_SHADOW = (175, 125, 95)
COLOR_PANTS = (46, 48, 54)
COLOR_PANTS_PATCH = (32, 34, 38)
COLOR_BOOT_LEATHER = (48, 32, 22)
COLOR_BOOT_SOLE = (24, 18, 14)
COLOR_CAP_TWEED = (42, 44, 48)
COLOR_GOGGLE_BRASS = (210, 170, 50)
COLOR_GOGGLE_LENS = (245, 195, 60)
COLOR_LEATHER_BELT = (60, 40, 25)

# Enemy Palette definitions
COLOR_CONDUCTOR_NAVY = (22, 36, 62)
COLOR_CONDUCTOR_NAVY_DARK = (14, 24, 44)
COLOR_PORTER_BURGUNDY = (105, 28, 38)
COLOR_PORTER_BURGUNDY_DARK = (70, 18, 25)
COLOR_AUTOMATON_IRON = (65, 70, 80)
COLOR_AUTOMATON_DARK = (40, 44, 52)
COLOR_IMP_SCRAP = (90, 55, 35)
COLOR_IMP_FIRE = (255, 110, 20)
COLOR_BRUTE_IRON = (75, 48, 42)
COLOR_GOLEM_BASALT = (45, 38, 35)


def draw_stoker_player(surface: pygame.Surface, screen_pos: tuple, aim_angle: float,
                       walk_dist: float, weapon, is_moving: bool, recoil_timer: float,
                       attack_boost_timer: float, flash_timer: float, invuln_timer: float,
                       radius: float = 22.0, is_blocking: bool = False,
                       block_timer: float = 0.0, parry_flash_timer: float = 0.0,
                       melee_swing_timer: float = 0.0, melee_swing_duration: float = 0.22,
                       melee_swing_arc: float = math.pi * 0.65):
    """Renders the rugged train stoker hero with dynamic melee swings, defensive guard stances, dirty shirt, burly arms, pants, boots, and held weapon."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    
    # Idle breathing bobbing & weight-shift (braced and lowered when blocking)
    ticks = pygame.time.get_ticks()
    breath_bob = math.sin(ticks * 0.005) * 1.5 if (not is_moving and not is_blocking) else 0.0
    breath_sway = math.cos(ticks * 0.003) * 0.8 if (not is_moving and not is_blocking) else 0.0
    lean_x = math.cos(aim_angle) * 2.5 if is_moving else 0.0
    lean_y = math.sin(aim_angle) * 2.5 if is_moving else 0.0

    cx += int(breath_sway + lean_x)
    cy += int(breath_bob + lean_y) + (2 if is_blocking else 0)

    # 1. Soft Oval Drop Shadow (widened when braced for block)
    shadow_w = int(radius * (2.4 if is_blocking else 2.1))
    shadow_h = int(radius * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 95), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(radius * 0.45) - int(breath_bob)))

    # Direction vectors
    aim_cos = math.cos(aim_angle)
    aim_sin = math.sin(aim_angle)
    perp_cos = -aim_sin
    perp_sin = aim_cos

    # Recoil offset on arms & weapon
    recoil = max(0.0, recoil_timer * 18.0)
    recoil_x = -aim_cos * recoil
    recoil_y = -aim_sin * recoil

    # Dynamic Melee Weapon Angle & Slash Trail
    if is_blocking:
        weapon_angle = aim_angle + math.pi * 0.45
    elif melee_swing_timer > 0:
        swing_prog = 1.0 - (melee_swing_timer / max(0.01, melee_swing_duration))
        swing_curve = math.sin(swing_prog * math.pi - math.pi * 0.5) * 0.5 + 0.5
        swing_offset = (swing_curve - 0.5) * melee_swing_arc * 1.6
        weapon_angle = aim_angle + swing_offset
    else:
        weapon_angle = aim_angle

    wpn_cos = math.cos(weapon_angle)
    wpn_sin = math.sin(weapon_angle)
    wpn_perp_cos = -wpn_sin
    wpn_perp_sin = wpn_cos

    # 2. Work Boots & Animated Walk Cycle (braced wide when blocking)
    stride = math.sin(walk_dist * 0.22) * 8.0 if is_moving else 0.0
    left_boot_offset = stride
    right_boot_offset = -stride

    stance_spread = 12.0 if is_blocking else 9.0
    for foot_idx, offset in enumerate([left_boot_offset, right_boot_offset]):
        side_sign = -1 if foot_idx == 0 else 1
        # Position boots behind torso relative to view
        bx = cx + int(perp_cos * (side_sign * stance_spread) - aim_cos * (4.0 - offset))
        by = cy + int(perp_sin * (side_sign * stance_spread) - aim_sin * (4.0 - offset) + 10)
        
        # Heavy leather work boot
        boot_rect = pygame.Rect(bx - 5, by - 4, 10, 8)
        pygame.draw.rect(surface, COLOR_BOOT_SOLE, (bx - 6, by - 1, 12, 6), border_radius=2)
        pygame.draw.rect(surface, COLOR_BOOT_LEATHER, boot_rect, border_radius=3)
        # Steel toe cap
        pygame.draw.circle(surface, (65, 55, 50), (bx + 2, by + 1), 3)

    # 3. Coal-Dusted Canvas Work Trousers
    legs_surf = pygame.Surface((32, 22), pygame.SRCALPHA)
    pygame.draw.ellipse(legs_surf, COLOR_PANTS, (2, 2, 28, 18))
    pygame.draw.circle(legs_surf, COLOR_PANTS_PATCH, (10, 10), 4)
    pygame.draw.circle(legs_surf, COLOR_SOOT, (22, 12), 3)
    surface.blit(legs_surf, (cx - 16, cy + 2))

    # 4. Heavy Leather Work Belt & Brass Buckle
    belt_y = cy + 4
    pygame.draw.rect(surface, COLOR_LEATHER_BELT, (cx - 12, belt_y - 2, 24, 6), border_radius=2)
    pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, (cx - 4, belt_y - 3, 8, 8), 2, border_radius=1)

    # 5. Dirty White Stoker Undershirt & Burly Torso
    torso_color = COLOR_WHITE if flash_timer > 0 else COLOR_DIRTY_SHIRT
    pygame.draw.circle(surface, COLOR_SHIRT_SHADOW, (cx, cy), int(radius * 0.78))
    pygame.draw.circle(surface, torso_color, (cx, cy - 1), int(radius * 0.72))
    
    # Realistic coal dust and grime smudges across the shirt
    if flash_timer <= 0:
        pygame.draw.ellipse(surface, COLOR_SOOT, (cx - 8, cy - 6, 7, 5))
        pygame.draw.ellipse(surface, COLOR_SOOT, (cx + 2, cy - 2, 9, 6))
        pygame.draw.circle(surface, (60, 55, 50), (cx - 2, cy + 1), 4)

    # Suspenders running over shoulders
    pygame.draw.line(surface, COLOR_LEATHER_BELT, (cx - 8, cy - 12), (cx - 8, belt_y), 2)
    pygame.draw.line(surface, COLOR_LEATHER_BELT, (cx + 8, cy - 12), (cx + 8, belt_y), 2)

    # 6. Burly Muscular Arms Gripping Weapon (following weapon_angle)
    arm_color = COLOR_WHITE if flash_timer > 0 else COLOR_STOKER_SKIN
    shadow_arm = COLOR_STOKER_SKIN_SHADOW

    if is_blocking:
        l_shoulder_x = cx + perp_cos * 13.0
        l_shoulder_y = cy + perp_sin * 13.0
        r_shoulder_x = cx - perp_cos * 13.0
        r_shoulder_y = cy - perp_sin * 13.0
        l_hand_x = cx + aim_cos * 12.0 + perp_cos * 10.0
        l_hand_y = cy + aim_sin * 12.0 + perp_sin * 10.0
        r_hand_x = cx + aim_cos * 14.0 - perp_cos * 6.0
        r_hand_y = cy + aim_sin * 14.0 - perp_sin * 6.0
    elif melee_swing_timer > 0:
        l_shoulder_x = cx + perp_cos * 13.0
        l_shoulder_y = cy + perp_sin * 13.0
        r_shoulder_x = cx - perp_cos * 13.0
        r_shoulder_y = cy - perp_sin * 13.0
        l_hand_x = cx + wpn_cos * 14.0 + wpn_perp_cos * 5.0
        l_hand_y = cy + wpn_sin * 14.0 + wpn_perp_sin * 5.0
        r_hand_x = cx + wpn_cos * 17.0 - wpn_perp_cos * 4.0
        r_hand_y = cy + wpn_sin * 17.0 - wpn_perp_sin * 4.0
    else:
        l_shoulder_x = cx + perp_cos * 13.0
        l_shoulder_y = cy + perp_sin * 13.0
        r_shoulder_x = cx - perp_cos * 13.0
        r_shoulder_y = cy - perp_sin * 13.0
        l_hand_x = cx + aim_cos * 16.0 + perp_cos * 6.0 + recoil_x
        l_hand_y = cy + aim_sin * 16.0 + perp_sin * 6.0 + recoil_y
        r_hand_x = cx + aim_cos * 18.0 - perp_cos * 4.0 + recoil_x
        r_hand_y = cy + aim_sin * 18.0 - perp_sin * 4.0 + recoil_y

    pygame.draw.circle(surface, shadow_arm, (int(l_shoulder_x), int(l_shoulder_y)), 6)
    pygame.draw.line(surface, arm_color, (int(l_shoulder_x), int(l_shoulder_y)), (int(l_hand_x), int(l_hand_y)), 7)
    pygame.draw.circle(surface, arm_color, (int(l_hand_x), int(l_hand_y)), 4)

    pygame.draw.circle(surface, shadow_arm, (int(r_shoulder_x), int(r_shoulder_y)), 6)
    pygame.draw.line(surface, arm_color, (int(r_shoulder_x), int(r_shoulder_y)), (int(r_hand_x), int(r_hand_y)), 7)
    pygame.draw.circle(surface, arm_color, (int(r_hand_x), int(r_hand_y)), 4)

    # Fiery Crescent Slash Arc Trail (when swinging melee)
    if melee_swing_timer > 0:
        start_swing_ang = aim_angle - melee_swing_arc * 0.8
        trail_steps = 8
        step_delta = (weapon_angle - start_swing_ang) / max(1, trail_steps)
        poly_trail = []
        for s in range(trail_steps + 1):
            ang = start_swing_ang + s * step_delta
            poly_trail.append((int(cx + math.cos(ang) * 44), int(cy + math.sin(ang) * 44)))
        for s in range(trail_steps, -1, -1):
            ang = start_swing_ang + s * step_delta
            poly_trail.append((int(cx + math.cos(ang) * 78), int(cy + math.sin(ang) * 78)))
        if len(poly_trail) >= 3:
            trail_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            pygame.draw.polygon(trail_surf, (255, 120, 20, 115), poly_trail)
            surface.blit(trail_surf, (0, 0))

    # 7. Held Weapon Sprite (Held firmly in burly hands with dynamic angle)
    wpn_base_x = cx + wpn_cos * 15.0 + recoil_x
    wpn_base_y = cy + wpn_sin * 15.0 + recoil_y
    draw_held_weapon(surface, (wpn_base_x, wpn_base_y), weapon_angle, weapon, recoil_timer)

    # 8. Rugged Stoker Head, Flat Cap & Welding Goggles
    head_y = cy - 6
    head_color = COLOR_WHITE if flash_timer > 0 else COLOR_STOKER_SKIN
    pygame.draw.circle(surface, head_color, (cx, head_y), 9)

    # Facial stubble / 5 o'clock shadow
    if flash_timer <= 0:
        pygame.draw.arc(surface, (80, 60, 50), (cx - 7, head_y - 2, 14, 10), 0, math.pi, 2)
        # Soot scratch on cheek
        pygame.draw.line(surface, COLOR_SOOT, (cx - 5, head_y - 1), (cx - 2, head_y + 2), 1)

    # Stoker Flat Cap (Newsboy Cap)
    cap_rect = pygame.Rect(cx - 10, head_y - 10, 20, 13)
    pygame.draw.ellipse(surface, COLOR_CAP_TWEED, cap_rect)
    # Cap brim projecting forward toward aim
    brim_x = cx + int(aim_cos * 4.0)
    brim_y = head_y - 5 + int(aim_sin * 4.0)
    pygame.draw.arc(surface, (25, 25, 28), (brim_x - 9, brim_y - 4, 18, 9), 0, math.pi, 2)

    # Brass Welding Goggles on Cap
    goggle_lx = cx - 4
    goggle_rx = cx + 4
    goggle_y = head_y - 7
    pygame.draw.circle(surface, COLOR_GOGGLE_BRASS, (goggle_lx, goggle_y), 4)
    pygame.draw.circle(surface, COLOR_GOGGLE_BRASS, (goggle_rx, goggle_y), 4)
    pygame.draw.circle(surface, COLOR_GOGGLE_LENS, (goggle_lx, goggle_y), 2)
    pygame.draw.circle(surface, COLOR_GOGGLE_LENS, (goggle_rx, goggle_y), 2)
    # Goggle strap around cap
    pygame.draw.line(surface, COLOR_LEATHER_BELT, (cx - 9, head_y - 6), (cx + 9, head_y - 6), 2)

    # 9. Overcharge Electric Aura
    if attack_boost_timer > 0:
        pulse = (math.sin(pygame.time.get_ticks() * 0.015) + 1) * 0.5
        aura_r = int(radius + 5 + 3 * pulse)
        pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, (cx, cy), aura_r, 2)
        # Orbiting ion sparks
        t = pygame.time.get_ticks() * 0.006
        for sp_i in range(3):
            ang = t + sp_i * (math.tau / 3)
            spx = cx + int(math.cos(ang) * (aura_r + 2))
            spy = cy + int(math.sin(ang) * (aura_r + 2))
            pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (spx, spy), 2)

    # 10. Invulnerability Strobe
    if invuln_timer > 0 and int(invuln_timer * 30) % 2 == 0:
        pygame.draw.circle(surface, COLOR_WHITE, (cx, cy), int(radius + 2), 2)

    # 11. Defensive Aegis Shield Barrier (Active Block Stance)
    if is_blocking:
        shield_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        shield_dist = 26.0
        barrier_cx = cx + int(aim_cos * shield_dist)
        barrier_cy = cy + int(aim_sin * shield_dist)
        span = math.pi * 0.70
        b_steps = 12
        arc_pts = []
        for s in range(b_steps + 1):
            ang = aim_angle - span * 0.5 + (span * s / b_steps)
            arc_pts.append((barrier_cx + math.cos(ang) * 16.0, barrier_cy + math.sin(ang) * 16.0))

        pulse = (math.sin(pygame.time.get_ticks() * 0.014) + 1) * 0.5
        shield_alpha = 240 if parry_flash_timer > 0 else int(120 + 50 * pulse)
        shield_col = (255, 255, 230, 245) if parry_flash_timer > 0 else (100, 215, 255, shield_alpha)
        
        if len(arc_pts) >= 2:
            pygame.draw.lines(shield_surf, shield_col, False, arc_pts, 5)
            # Edge brass rivets & energy nodes
            for pt in [arc_pts[0], arc_pts[len(arc_pts) // 2], arc_pts[-1]]:
                pygame.draw.circle(shield_surf, (240, 195, 60, 230), (int(pt[0]), int(pt[1])), 4)
                pygame.draw.circle(shield_surf, (255, 255, 255, 230), (int(pt[0]), int(pt[1])), 2)

        surface.blit(shield_surf, (0, 0))


def draw_held_weapon(surface: pygame.Surface, pos: tuple, aim_angle: float, weapon, recoil_timer: float):
    """Draws custom weapon model held in character hands with distinct mechanical details."""
    if not weapon:
        return
    wx, wy = pos
    cos_a = math.cos(aim_angle)
    sin_a = math.sin(aim_angle)
    perp_x = -sin_a
    perp_y = cos_a
    w_name = getattr(weapon, "name", "").lower()

    if "riveter" in w_name or "rivet" in w_name:
        # --- Pneumatic Riveter: Brass cylinder, needle nozzle, air hose ---
        barrel_len = 24
        b_end_x = wx + cos_a * barrel_len
        b_end_y = wy + sin_a * barrel_len
        # Pressure cylinder
        pygame.draw.line(surface, COLOR_STEEL_DARK, (wx, wy), (int(b_end_x), int(b_end_y)), 7)
        pygame.draw.line(surface, COLOR_BRASS, (wx + cos_a * 4, wy + sin_a * 4), (int(wx + cos_a * 16), int(wy + sin_a * 16)), 5)
        # Needle muzzle tip
        tip_x = wx + cos_a * (barrel_len + 4)
        tip_y = wy + sin_a * (barrel_len + 4)
        pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (int(b_end_x), int(b_end_y)), (int(tip_x), int(tip_y)), 3)
        # Pressure gauge dial
        gauge_x = wx + perp_x * 5 + cos_a * 8
        gauge_y = wy + perp_y * 5 + sin_a * 8
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(gauge_x), int(gauge_y)), 3)
        pygame.draw.circle(surface, COLOR_WHITE, (int(gauge_x), int(gauge_y)), 2)

    elif "cleaver" in w_name or "wrench" in w_name:
        # --- Stoker's Cleaver: Heavy forged shovel/cleaver with heated orange cutting edge ---
        blade_len = 32
        tip_x = wx + cos_a * blade_len
        tip_y = wy + sin_a * blade_len
        # Heavy steel shaft
        pygame.draw.line(surface, COLOR_STEEL_DARK, (wx, wy), (int(tip_x), int(tip_y)), 6)
        # Broad cleaver / coal shovel blade
        blade_w = 12
        p1 = (int(tip_x + perp_x * blade_w), int(tip_y + perp_y * blade_w))
        p2 = (int(tip_x - perp_x * blade_w), int(tip_y - perp_y * blade_w))
        p3 = (int(wx + cos_a * 14 - perp_x * (blade_w - 2)), int(wy + sin_a * 14 - perp_y * (blade_w - 2)))
        p4 = (int(wx + cos_a * 14 + perp_x * (blade_w - 2)), int(wy + sin_a * 14 + perp_y * (blade_w - 2)))
        pygame.draw.polygon(surface, (50, 52, 58), [p1, p2, p3, p4])
        # Glowing heated razor edge
        pygame.draw.line(surface, COLOR_EMBER_ORANGE, p1, p2, 3)
        pygame.draw.line(surface, COLOR_CRIT_YELLOW, p1, p2, 1)

    elif "scattergun" in w_name or "shotgun" in w_name:
        # --- Coal Scattergun: Double brass blunderbuss with flared bell muzzle ---
        barrel_len = 22
        b1_x = wx + cos_a * barrel_len + perp_x * 3
        b1_y = wy + sin_a * barrel_len + perp_y * 3
        b2_x = wx + cos_a * barrel_len - perp_x * 3
        b2_y = wy + sin_a * barrel_len - perp_y * 3
        # Wooden stock
        pygame.draw.line(surface, (85, 45, 25), (wx - cos_a * 6, wy - sin_a * 6), (wx, wy), 7)
        # Twin brass barrels
        pygame.draw.line(surface, COLOR_BRASS, (wx + perp_x * 3, wy + perp_y * 3), (int(b1_x), int(b1_y)), 4)
        pygame.draw.line(surface, COLOR_BRASS, (wx - perp_x * 3, wy - perp_y * 3), (int(b2_x), int(b2_y)), 4)
        # Flared blunderbuss muzzle rings
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(b1_x), int(b1_y)), 3)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(b2_x), int(b2_y)), 3)

    elif "tesla" in w_name or "arc" in w_name:
        # --- Tesla Arc Caster: Twin copper induction coils & crackling plasma core ---
        barrel_len = 26
        tip_x = wx + cos_a * barrel_len
        tip_y = wy + sin_a * barrel_len
        # Central vacuum cathode tube
        pygame.draw.line(surface, COLOR_STEEL_DARK, (wx, wy), (int(tip_x), int(tip_y)), 6)
        pygame.draw.line(surface, (200, 240, 255), (wx + cos_a * 4, wy + sin_a * 4), (int(tip_x - cos_a * 2), int(tip_y - sin_a * 2)), 3)
        # Copper induction coil rings
        for c_step in [8, 14, 20]:
            cx_ring = wx + cos_a * c_step
            cy_ring = wy + sin_a * c_step
            pygame.draw.circle(surface, (215, 120, 60), (int(cx_ring), int(cy_ring)), 5, 2)
        # Crackling emitter tip
        pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, (int(tip_x), int(tip_y)), 4)
        pygame.draw.circle(surface, COLOR_WHITE, (int(tip_x), int(tip_y)), 2)

    # Mechanical slide recoil: Sharp starburst muzzle flash & ejected shell casing
    if recoil_timer > 0 and "cleaver" not in w_name and "wrench" not in w_name:
        flash_p = min(1.0, recoil_timer * 12.0)
        flash_barrel_len = 28 if ("tesla" in w_name or "arc" in w_name) else (24 if ("scatter" in w_name or "shotgun" in w_name) else 26)
        flash_x = wx + cos_a * flash_barrel_len
        flash_y = wy + sin_a * flash_barrel_len
        star_r = 11.0 * flash_p
        pts = []
        for s_i in range(8):
            s_ang = aim_angle + (s_i * math.pi / 4.0)
            s_dist = star_r if s_i % 2 == 0 else (star_r * 0.42)
            pts.append((flash_x + math.cos(s_ang) * s_dist, flash_y + math.sin(s_ang) * s_dist))
        if len(pts) >= 3:
            flash_col = COLOR_LIGHTNING_CYAN if ("tesla" in w_name or "arc" in w_name) else COLOR_CRIT_YELLOW
            pygame.draw.polygon(surface, flash_col, pts)
            pygame.draw.circle(surface, COLOR_WHITE, (int(flash_x), int(flash_y)), max(2, int(star_r * 0.4)))
        # Ejected brass shell casing spinning out
        case_dist = 8.0 + (1.0 - flash_p) * 16.0
        case_x = wx - perp_x * case_dist - cos_a * 4
        case_y = wy - perp_y * case_dist - sin_a * 4
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, (int(case_x), int(case_y), 4, 2))

# =========================================================================
# ENEMY CHARACTER ANATOMY & PROCEDURAL SPRITE OVERHAUL
# =========================================================================

def draw_elite_indicator(surface: pygame.Surface, cx: int, cy: int, enemy):
    """Renders elite visual crown, pulse aura, and modifier badge."""
    mod = getattr(enemy, "elite_modifier", "overclocked")
    pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
    r = enemy.radius

    if mod == "overclocked":
        # Electric cyan lightning corona
        ring_col = (50, int(180 + 75 * pulse), 255)
        pygame.draw.circle(surface, ring_col, (cx, cy), int(r + 6), 2)
        # Small crackle sparks
        t = pygame.time.get_ticks() * 0.005
        sp_x = cx + int(math.cos(t) * (r + 7))
        sp_y = cy + int(math.sin(t) * (r + 7))
        pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, (sp_x, sp_y), 2)
    elif mod == "armored":
        # Brass gilded spike crest
        ring_col = (255, int(180 + 60 * pulse), 40)
        pygame.draw.circle(surface, ring_col, (cx, cy), int(r + 6), 2)
        for a_deg in range(0, 360, 60):
            rad = math.radians(a_deg + pygame.time.get_ticks() * 0.02)
            px = cx + int(math.cos(rad) * (r + 7))
            py = cy + int(math.sin(rad) * (r + 7))
            pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (px, py), 2)
    elif mod == "volatile":
        # Scorching fire pulse
        ring_col = (255, int(70 + 80 * pulse), 20)
        pygame.draw.circle(surface, ring_col, (cx, cy), int(r + 6), 2)

    # Overhead elite star badge
    badge_y = cy - int(r + 14)
    pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (cx, badge_y), 4)
    pygame.draw.circle(surface, COLOR_WHITE, (cx, badge_y), 2)


def draw_ticket_inspector_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Ticket Inspector: Full humanoid conductor with walking boots, coat tails, satchel, and truncheon."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = enemy.vel.length() > 10.0
    stride = math.sin(walk_dist * 0.24) * 6.0 if is_moving else 0.0

    # 1. Soft Oval Drop Shadow
    shadow_w = int(r * 2.2)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.4)))

    # 2. Polished Conductor Boots with walking stride
    boot_color = (20, 20, 25)
    for foot_idx, offset in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        bx = cx + int(perp_x * (side_sign * 7.0) - cos_f * (3.0 - offset))
        by = cy + int(perp_y * (side_sign * 7.0) - sin_f * (3.0 - offset) + 7)
        pygame.draw.rect(surface, (10, 10, 12), (bx - 4, by - 1, 9, 6), border_radius=2)
        pygame.draw.rect(surface, boot_color, (bx - 3, by - 4, 7, 7), border_radius=2)

    # 3. Navy Conductor Trousers
    p_surf = pygame.Surface((24, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(p_surf, COLOR_CONDUCTOR_NAVY_DARK, (2, 2, 20, 12))
    surface.blit(p_surf, (cx - 12, cy + 2))

    # 4. Tailored Conductor Greatcoat Tails (split coat tails swaying behind him)
    coat_color = COLOR_WHITE if enemy.flash_timer > 0 else COLOR_CONDUCTOR_NAVY
    coat_dark = COLOR_CONDUCTOR_NAVY_DARK
    tail_offset = -stride * 0.5
    tail_x = cx - cos_f * (r * 0.7)
    tail_y = cy - sin_f * (r * 0.7) + 3
    pygame.draw.polygon(surface, coat_dark, [
        (cx - perp_x * 7, cy),
        (int(tail_x - perp_x * 8 + tail_offset), int(tail_y - perp_y * 8)),
        (int(tail_x - perp_x * 2), int(tail_y - perp_y * 2))
    ])
    pygame.draw.polygon(surface, coat_dark, [
        (cx + perp_x * 7, cy),
        (int(tail_x + perp_x * 8 - tail_offset), int(tail_y + perp_y * 8)),
        (int(tail_x + perp_x * 2), int(tail_y + perp_y * 2))
    ])

    # 5. Conductor Torso with Gold Buttons & Stiff Collar
    pygame.draw.ellipse(surface, coat_dark, (cx - 11, cy - 8, 22, 17))
    pygame.draw.ellipse(surface, coat_color, (cx - 10, cy - 9, 20, 15))

    # Stiff white collar & black tie
    collar_pos = (cx + int(cos_f * 2), cy + int(sin_f * 2) - 4)
    pygame.draw.polygon(surface, (235, 235, 240), [
        (collar_pos[0] - 5, collar_pos[1] - 2),
        (collar_pos[0] + 5, collar_pos[1] - 2),
        (collar_pos[0], collar_pos[1] + 3)
    ])
    pygame.draw.polygon(surface, (20, 20, 25), [
        (collar_pos[0] - 2, collar_pos[1] - 1),
        (collar_pos[0] + 2, collar_pos[1] - 1),
        (collar_pos[0], collar_pos[1] + 4)
    ])

    # Double-breasted gold button rows
    if enemy.flash_timer <= 0:
        for b_i in [-3, 1]:
            bx1 = cx - perp_x * 3 + cos_f * b_i
            by1 = cy - perp_y * 3 + sin_f * b_i
            bx2 = cx + perp_x * 3 + cos_f * b_i
            by2 = cy + perp_y * 3 + sin_f * b_i
            pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(bx1), int(by1)), 2)
            pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(bx2), int(by2)), 2)

    # Leather ticket punch satchel slung on left hip
    satchel_x = cx - perp_x * (r * 0.65)
    satchel_y = cy - perp_y * (r * 0.65)
    pygame.draw.rect(surface, (65, 42, 22), (int(satchel_x - 4), int(satchel_y - 4), 8, 8), border_radius=2)
    pygame.draw.rect(surface, COLOR_BRASS, (int(satchel_x - 2), int(satchel_y - 2), 4, 3), 1)

    # 6. Arms & Dynamic Truncheon Baton Poses
    is_windup = (getattr(enemy, "state", "") == "windup")
    is_attack = (getattr(enemy, "state", "") == "attack")
    arm_color = coat_color
    hand_color = (235, 235, 240)  # White conductor gloves

    # Left Arm (carrying ticket pouch/punch)
    l_sh_x = cx + perp_x * 10
    l_sh_y = cy + perp_y * 10
    l_hd_x = cx + perp_x * 7 + cos_f * 8
    l_hd_y = cy + perp_y * 7 + sin_f * 8
    pygame.draw.line(surface, arm_color, (int(l_sh_x), int(l_sh_y)), (int(l_hd_x), int(l_hd_y)), 5)
    pygame.draw.circle(surface, hand_color, (int(l_hd_x), int(l_hd_y)), 3)
    # Brass ticket punch in left hand
    pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (int(l_hd_x), int(l_hd_y)), (int(l_hd_x + cos_f * 5), int(l_hd_y + sin_f * 5)), 2)

    # Right Arm (wielding heavy baton)
    r_sh_x = cx - perp_x * 10
    r_sh_y = cy - perp_y * 10
    
    if is_windup:
        baton_angle = fa - 1.35
        r_hd_x = cx - perp_x * 4 + math.cos(baton_angle) * 10
        r_hd_y = cy - perp_y * 4 + math.sin(baton_angle) * 10
        b_len = 22
    elif is_attack:
        baton_angle = fa + 0.1
        r_hd_x = cx - perp_x * 2 + cos_f * 14
        r_hd_y = cy - perp_y * 2 + sin_f * 14
        b_len = 24
    else:
        baton_angle = fa + 0.45
        r_hd_x = cx - perp_x * 8 + cos_f * 10
        r_hd_y = cy - perp_y * 8 + sin_f * 10
        b_len = 20

    pygame.draw.line(surface, arm_color, (int(r_sh_x), int(r_sh_y)), (int(r_hd_x), int(r_hd_y)), 5)
    pygame.draw.circle(surface, hand_color, (int(r_hd_x), int(r_hd_y)), 4)

    # The Heavy Baton itself
    b_end_x = r_hd_x + math.cos(baton_angle) * b_len
    b_end_y = r_hd_y + math.sin(baton_angle) * b_len
    pygame.draw.line(surface, (60, 42, 28), (int(r_hd_x), int(r_hd_y)), (int(b_end_x), int(b_end_y)), 5)
    pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(b_end_x), int(b_end_y)), 4)
    if is_windup:
        pygame.draw.circle(surface, (255, 50, 50), (int(b_end_x), int(b_end_y)), 7, 2)

    # 7. Head, Conductor Cap & Mustache
    head_x = cx + cos_f * 3
    head_y = cy + sin_f * 3 - 6
    pygame.draw.circle(surface, (215, 165, 130), (int(head_x), int(head_y)), 6)
    
    # Handlebar mustache
    must_x = head_x + cos_f * 4
    must_y = head_y + sin_f * 4 + 1
    pygame.draw.line(surface, (45, 35, 30), (int(must_x - perp_x * 4), int(must_y - perp_y * 4)), (int(must_x + perp_x * 4), int(must_y + perp_y * 4)), 2)

    # Peaked Conductor Visor Cap
    cap_x = head_x + cos_f * 1
    cap_y = head_y + sin_f * 1 - 2
    pygame.draw.ellipse(surface, (16, 24, 42), (int(cap_x - 8), int(cap_y - 6), 16, 12))
    # Shiny black visor brim
    brim_x = cap_x + cos_f * 5
    brim_y = cap_y + sin_f * 5 + 1
    pygame.draw.arc(surface, (10, 10, 15), (int(brim_x - 7), int(brim_y - 4), 14, 8), 0, math.pi, 3)
    # Gold cap strap & winged wheel badge
    pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (int(cap_x - perp_x * 6), int(cap_y - perp_y * 6)), (int(cap_x + perp_x * 6), int(cap_y + perp_y * 6)), 2)
    pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(cap_x + cos_f * 4), int(cap_y + sin_f * 4)), 2)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


def draw_luggage_steward_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Luggage Steward: Full humanoid bellhop porter with burgundy vest, aiguillette, and steam canister."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = enemy.vel.length() > 10.0
    stride = math.sin(walk_dist * 0.32) * 7.0 if is_moving else 0.0

    # 1. Soft Oval Drop Shadow
    shadow_w = int(r * 2.0)
    shadow_h = int(r * 0.90)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.4)))

    # 2. Scurrying Porter Shoes
    shoe_color = (25, 20, 20)
    for foot_idx, offset in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        sx = cx + int(perp_x * (side_sign * 6.0) - cos_f * (2.0 - offset))
        sy = cy + int(perp_y * (side_sign * 6.0) - sin_f * (2.0 - offset) + 6)
        pygame.draw.rect(surface, shoe_color, (sx - 3, sy - 3, 7, 6), border_radius=2)

    # 3. Charcoal Trousers with Red Seam
    p_surf = pygame.Surface((22, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(p_surf, (40, 42, 46), (2, 2, 18, 10))
    surface.blit(p_surf, (cx - 11, cy + 2))

    # 4. Fitted Burgundy Waistcoat over Cream Shirt
    vest_color = COLOR_WHITE if enemy.flash_timer > 0 else COLOR_PORTER_BURGUNDY
    vest_dark = COLOR_PORTER_BURGUNDY_DARK
    # Cream shirt background
    pygame.draw.ellipse(surface, (230, 226, 214), (cx - 9, cy - 8, 18, 16))
    # Burgundy vest panels
    pygame.draw.ellipse(surface, vest_dark, (cx - 9, cy - 7, 18, 14))
    pygame.draw.ellipse(surface, vest_color, (cx - 8, cy - 8, 16, 13))

    # Gold Aiguillette Braided Rope on right shoulder
    pygame.draw.arc(surface, COLOR_BRASS_HIGHLIGHT, (cx - 8, cy - 7, 14, 10), 0, math.pi, 2)
    # Brass buttons down center
    if enemy.flash_timer <= 0:
        for b_i in [-2, 2]:
            pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (cx, cy + b_i - 2), 1)

    # Crossbody leather courier satchel
    satchel_x = cx - perp_x * (r * 0.6)
    satchel_y = cy - perp_y * (r * 0.6)
    pygame.draw.rect(surface, (75, 45, 25), (int(satchel_x - 3), int(satchel_y - 3), 7, 7), border_radius=2)
    pygame.draw.line(surface, (50, 30, 18), (cx + perp_x * 6, cy - 4), (satchel_x, satchel_y), 2)

    # 5. Arms & Pressure Canister
    is_windup = (getattr(enemy, "state", "") == "windup")
    arm_shirt = (230, 226, 214)

    # Left Arm (clutching satchel)
    l_sh_x = cx + perp_x * 8
    l_sh_y = cy + perp_y * 8
    l_hd_x = cx + perp_x * 6 + cos_f * 5
    l_hd_y = cy + perp_y * 6 + sin_f * 5
    pygame.draw.line(surface, arm_shirt, (int(l_sh_x), int(l_sh_y)), (int(l_hd_x), int(l_hd_y)), 4)
    pygame.draw.circle(surface, (215, 165, 130), (int(l_hd_x), int(l_hd_y)), 3)

    # Right Arm (aiming & cocking brass steam canister)
    r_sh_x = cx - perp_x * 8
    r_sh_y = cy - perp_y * 8
    if is_windup:
        c_ang = fa - 1.1
        c_reach = 14
    else:
        c_ang = fa + 0.35
        c_reach = 12

    c_hd_x = r_sh_x + math.cos(c_ang) * c_reach
    c_hd_y = r_sh_y + math.sin(c_ang) * c_reach
    pygame.draw.line(surface, arm_shirt, (int(r_sh_x), int(r_sh_y)), (int(c_hd_x), int(c_hd_y)), 4)
    pygame.draw.circle(surface, (215, 165, 130), (int(c_hd_x), int(c_hd_y)), 3)

    # Heavy Brass Steam Canister
    can_x = c_hd_x + math.cos(c_ang) * 6
    can_y = c_hd_y + math.sin(c_ang) * 6
    pygame.draw.rect(surface, (45, 50, 55), (int(can_x - 4), int(can_y - 4), 8, 9), border_radius=2)
    pygame.draw.rect(surface, COLOR_BRASS, (int(can_x - 3), int(can_y - 3), 6, 7), border_radius=1)
    pygame.draw.circle(surface, COLOR_EMBER_ORANGE, (int(can_x), int(can_y - 4)), 2)

    # Windup steam hiss effect
    if is_windup:
        pulse = (math.sin(pygame.time.get_ticks() * 0.04) + 1) * 0.5
        pygame.draw.circle(surface, COLOR_WHITE, (int(can_x), int(can_y - 5)), int(3 + 3 * pulse), 1)

    # 6. Head & Pillbox Bellhop Hat
    head_x = cx + cos_f * 2
    head_y = cy + sin_f * 2 - 5
    pygame.draw.circle(surface, (215, 165, 130), (int(head_x), int(head_y)), 5)
    # Expressive porter eyes
    eye_x = head_x + cos_f * 3
    eye_y = head_y + sin_f * 3
    pygame.draw.circle(surface, (20, 20, 25), (int(eye_x), int(eye_y)), 1)

    # Tilted pillbox bellhop hat
    hat_x = head_x - perp_x * 2 - cos_f * 1
    hat_y = head_y - perp_y * 2 - sin_f * 1 - 3
    pygame.draw.ellipse(surface, (70, 18, 25), (int(hat_x - 6), int(hat_y - 4), 12, 8))
    pygame.draw.ellipse(surface, vest_color, (int(hat_x - 5), int(hat_y - 4), 10, 7))
    pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (int(hat_x - 5), int(hat_y)), (int(hat_x + 5), int(hat_y)), 2)
    # Gold chinstrap
    pygame.draw.line(surface, COLOR_BRASS, (int(hat_x - 4), int(hat_y + 1)), (int(head_x), int(head_y + 3)), 1)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


def draw_boiler_imp_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Scrap Boiler Imp: Hunched bipedal mechanical scrap gremlin with 2 articulated runner legs, stomping talons, and blazing furnace core."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_windup = (getattr(enemy, "state", "") == "windup")

    # 1. Bipedal Ground Drop Shadow
    shadow_w = int(r * 2.1)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 95), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.35)))

    # 2. Two Articulated Bipedal Runner Legs (Digitigrade scrap legs with stomping talons!)
    leg_color = (45, 30, 20)
    stride = math.sin(walk_dist * 0.35) * 6.0 if not is_windup else 0.0
    for leg_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if leg_idx == 0 else 1
        # Pelvic hip joint
        hx = cx + int(perp_x * (side_sign * 6.0) - cos_f * 2.0)
        hy = cy + int(perp_y * (side_sign * 6.0) - sin_f * 2.0 + 3)
        # High-raised knee joint swinging with stride
        kx = hx + int(cos_f * (5.0 + step_off * 0.4) + perp_x * (side_sign * 3.0))
        ky = hy + int(sin_f * (5.0 + step_off * 0.4) + perp_y * (side_sign * 3.0) + 4)
        # Digitigrade foot / talon planted on deck
        fx = hx + int(cos_f * (2.0 + step_off) + perp_x * (side_sign * 4.0))
        fy = hy + int(sin_f * (2.0 + step_off) + perp_y * (side_sign * 4.0) + 9)

        # Upper thigh segment
        pygame.draw.line(surface, leg_color, (hx, hy), (kx, ky), 4)
        # Lower shin segment
        pygame.draw.line(surface, (30, 20, 15), (kx, ky), (fx, fy), 3)
        # Brass knee joint rivet
        pygame.draw.circle(surface, COLOR_BRASS, (kx, ky), 2)
        # Three-pronged scrap metal foot talons
        pygame.draw.line(surface, (20, 15, 12), (fx, fy), (int(fx + cos_f * 6), int(fy + sin_f * 6)), 2)
        pygame.draw.line(surface, (20, 15, 12), (fx, fy), (int(fx + cos_f * 4 + perp_x * 4), int(fy + sin_f * 4 + perp_y * 4)), 2)
        pygame.draw.line(surface, (20, 15, 12), (fx, fy), (int(fx + cos_f * 4 - perp_x * 4), int(fy + sin_f * 4 - perp_y * 4)), 2)
        pygame.draw.circle(surface, (65, 45, 30), (fx, fy), 2)

    # 3. Hunched Patchworked Boiler Abdomen Carapace
    chassis_color = COLOR_WHITE if enemy.flash_timer > 0 else COLOR_IMP_SCRAP
    body_surf = pygame.Surface((int(r * 2), int(r * 1.7)), pygame.SRCALPHA)
    pygame.draw.ellipse(body_surf, (35, 22, 14), (1, 1, int(r * 1.9), int(r * 1.6)))
    pygame.draw.ellipse(body_surf, chassis_color, (2, 2, int(r * 1.8), int(r * 1.5)))
    surface.blit(body_surf, (cx - int(r), cy - int(r * 0.85)))

    # Rivet plates on carapace
    if enemy.flash_timer <= 0:
        pygame.draw.circle(surface, COLOR_BRASS, (cx - 4, cy - 3), 2)
        pygame.draw.circle(surface, COLOR_BRASS, (cx + 4, cy - 3), 2)

    # 4. Twin Steaming Copper Exhaust Chimneys on upper back
    pipe1_x = cx - cos_f * 8 + perp_x * 5
    pipe1_y = cy - sin_f * 8 + perp_y * 5 - 4
    pipe2_x = cx - cos_f * 8 - perp_x * 5
    pipe2_y = cy - sin_f * 8 - perp_y * 5 - 4
    for px, py in [(pipe1_x, pipe1_y), (pipe2_x, pipe2_y)]:
        pygame.draw.circle(surface, (55, 35, 22), (int(px), int(py)), 4)
        pygame.draw.circle(surface, COLOR_BRASS, (int(px), int(py)), 4, 1)
        pygame.draw.circle(surface, (15, 12, 10), (int(px), int(py)), 2)
        # Smoke puff on exhaust
        pygame.draw.circle(surface, (70, 65, 60), (int(px), int(py - 3)), 2)

    # 5. Glowing Roaring Firebox Ribcage / Furnace Core
    fire_pulse = (math.sin(pygame.time.get_ticks() * (0.04 if is_windup else 0.01)) + 1) * 0.5
    fire_col = (255, 240, 180) if is_windup and int(enemy.state_timer * 20) % 2 == 0 else (
        int(220 + 35 * fire_pulse), int(80 + 50 * fire_pulse), 15
    )
    pygame.draw.circle(surface, fire_col, (cx, cy + 1), int(r * 0.45))
    # Iron grate bars over furnace
    pygame.draw.line(surface, (25, 18, 14), (cx - 3, cy - 4), (cx - 3, cy + 6), 2)
    pygame.draw.line(surface, (25, 18, 14), (cx + 3, cy - 4), (cx + 3, cy + 6), 2)

    # 6. Front Grasping Scrap Iron Pincer Claws
    c_left_x = cx + cos_f * (r * 0.7) + perp_x * 6
    c_left_y = cy + sin_f * (r * 0.7) + perp_y * 6
    c_right_x = cx + cos_f * (r * 0.7) - perp_x * 6
    c_right_y = cy + sin_f * (r * 0.7) - perp_y * 6
    pygame.draw.line(surface, (60, 45, 35), (cx + perp_x * 4, cy), (int(c_left_x), int(c_left_y)), 3)
    pygame.draw.line(surface, (60, 45, 35), (cx - perp_x * 4, cy), (int(c_right_x), int(c_right_y)), 3)
    # Claw pincer tips
    pygame.draw.circle(surface, COLOR_STEEL_MID, (int(c_left_x), int(c_left_y)), 2)
    pygame.draw.circle(surface, COLOR_STEEL_MID, (int(c_right_x), int(c_right_y)), 2)

    # 7. Cyclopean Shutter Eye (dilates and blazes bright white in windup!)
    eye_x = cx + cos_f * (r * 0.55)
    eye_y = cy + sin_f * (r * 0.55) - 1
    eye_size = 4 if is_windup else 3
    pygame.draw.circle(surface, (20, 15, 15), (int(eye_x), int(eye_y)), eye_size + 1)
    pygame.draw.circle(surface, COLOR_WHITE if is_windup else COLOR_CRIT_YELLOW, (int(eye_x), int(eye_y)), eye_size)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


def draw_freight_warden_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Freight Warden: Gunmetal riot automaton with stomping greaves, hazard cuirass, stun truncheon, and ballistic shield."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = enemy.vel.length() > 10.0
    stride = math.sin(walk_dist * 0.20) * 5.0 if is_moving else 0.0

    # 1. Heavy Mechanical Drop Shadow
    shadow_w = int(r * 2.3)
    shadow_h = int(r * 1.0)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.4)))

    # 2. Chunky Hydraulic Stomping Greaves
    greave_color = COLOR_STEEL_DARK
    for foot_idx, offset in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        gx = cx + int(perp_x * (side_sign * 9.0) - cos_f * (4.0 - offset))
        gy = cy + int(perp_y * (side_sign * 9.0) - sin_f * (4.0 - offset) + 7)
        pygame.draw.rect(surface, (20, 22, 26), (gx - 5, gy - 2, 11, 7), border_radius=2)
        pygame.draw.rect(surface, greave_color, (gx - 4, gy - 5, 9, 8), border_radius=2)
        pygame.draw.circle(surface, COLOR_BRASS, (gx + 1, gy), 2)

    # 3. Trapezoidal Armored Cuirass with Hazard Stripes
    body_color = COLOR_WHITE if enemy.flash_timer > 0 else COLOR_AUTOMATON_IRON
    pygame.draw.rect(surface, COLOR_AUTOMATON_DARK, (cx - 12, cy - 10, 24, 20), border_radius=3)
    pygame.draw.rect(surface, body_color, (cx - 11, cy - 9, 22, 18), border_radius=3)

    # Yellow-and-black hazard chevron stripes across chest plate
    if enemy.flash_timer <= 0:
        for hz in [-6, 0, 6]:
            pygame.draw.line(surface, COLOR_CRIT_YELLOW, (cx + hz - 3, cy - 6), (cx + hz + 3, cy + 4), 2)

    # 4. Massive Hydraulic Pauldron Shoulder Blocks
    p_left = (cx + perp_x * (r * 0.85), cy + perp_y * (r * 0.85))
    p_right = (cx - perp_x * (r * 0.85), cy - perp_y * (r * 0.85))
    for px, py in [p_left, p_right]:
        pygame.draw.circle(surface, COLOR_STEEL_DARK, (int(px), int(py)), 8)
        pygame.draw.circle(surface, COLOR_STEEL_MID, (int(px), int(py)), 6)
        pygame.draw.circle(surface, COLOR_BRASS, (int(px), int(py)), 3)

    # 5. Right Arm & Pneumatic Stun Truncheon
    r_arm_x = cx - perp_x * 12
    r_arm_y = cy - perp_y * 12
    t_end_x = r_arm_x + cos_f * 18
    t_end_y = r_arm_y + sin_f * 18
    pygame.draw.line(surface, COLOR_STEEL_DARK, (int(r_arm_x), int(r_arm_y)), (int(t_end_x), int(t_end_y)), 4)
    # Electric cyan spark coils on truncheon tip
    pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, (int(t_end_x), int(t_end_y)), 3)

    # 6. Sentry Dome Helmet with Sweeping Red Scanner Eye
    helm_x = cx + cos_f * 3
    helm_y = cy + sin_f * 3 - 6
    pygame.draw.circle(surface, COLOR_STEEL_DARK, (int(helm_x), int(helm_y)), 7)
    pygame.draw.circle(surface, (25, 28, 32), (int(helm_x), int(helm_y)), 5)
    # Horizontal visor slit
    v_left = (helm_x - perp_x * 4 + cos_f * 2, helm_y - perp_y * 4 + sin_f * 2)
    v_right = (helm_x + perp_x * 4 + cos_f * 2, helm_y + perp_y * 4 + sin_f * 2)
    pygame.draw.line(surface, (10, 10, 15), (int(v_left[0]), int(v_left[1])), (int(v_right[0]), int(v_right[1])), 3)
    # Sweeping red eye
    sweep = math.sin(pygame.time.get_ticks() * 0.008)
    eye_px = helm_x + perp_x * (sweep * 3.5) + cos_f * 2
    eye_py = helm_y + perp_y * (sweep * 3.5) + sin_f * 2
    pygame.draw.circle(surface, (255, 30, 30), (int(eye_px), int(eye_py)), 2)

    # 7. Massive Curved Rectangular Ballistic Tower Riot Shield
    shield_span = getattr(enemy, "shield_angle_span", math.pi * 0.55)
    shield_r = r + 9
    num_pts = 8
    shield_pts = []
    for i in range(num_pts):
        t = -shield_span / 2 + (shield_span * i / (num_pts - 1))
        ang = fa + t
        sx = cx + math.cos(ang) * shield_r
        sy = cy + math.sin(ang) * shield_r
        shield_pts.append((sx, sy))

    if len(shield_pts) >= 2:
        # Base thick shield plate
        pygame.draw.lines(surface, (20, 24, 30), False, shield_pts, 9)
        pygame.draw.lines(surface, COLOR_STEEL_MID, False, shield_pts, 6)
        pygame.draw.lines(surface, COLOR_BRASS_HIGHLIGHT, False, shield_pts, 2)
        # Hazard chevron markers along shield face
        for i in range(1, len(shield_pts) - 1, 2):
            px, py = shield_pts[i]
            pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(px), int(py)), 3)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


def draw_boiler_brute_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Boiler Brute: Colossal ironclad juggernaut with articulated bipedal sabatons, flexing pistons, burning coal firebox, and steam sledgehammer."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(enemy, "radius", 34)
    fa = getattr(enemy, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = getattr(enemy, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.20) * 8.0 if is_moving else 0.0
    is_windup = (getattr(enemy, "state", "") == "windup")
    flash = getattr(enemy, "flash_timer", 0.0) > 0.0

    # 1. Massive Ground Drop Shadow
    shadow_w = int(r * 2.5)
    shadow_h = int(r * 1.15)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 115), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.42)))

    # 2. Articulated Bipedal Iron Sabatons & Hydraulic Calves
    boot_color = (35, 26, 22)
    for foot_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 15.0) - cos_f * 5.0)
        hy = cy + int(perp_y * (side_sign * 15.0) - sin_f * 5.0 + 10)
        kx = hx + int(cos_f * (7.0 + step_off * 0.4) + perp_x * (side_sign * 4.0))
        ky = hy + int(sin_f * (7.0 + step_off * 0.4) + perp_y * (side_sign * 4.0) + 12)
        bx = hx + int(cos_f * (4.0 + step_off) + perp_x * (side_sign * 6.0))
        by = hy + int(sin_f * (4.0 + step_off) + perp_y * (side_sign * 6.0) + 20)

        # Thigh & Shin Iron Plates
        pygame.draw.line(surface, (25, 20, 18), (hx, hy), (kx, ky), 7)
        pygame.draw.line(surface, boot_color, (kx, ky), (bx, by), 6)
        # Hydraulic piston rod on calf
        pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (hx - 2, hy), (kx - 2, ky), 2)
        # Heavy cast-iron sabaton foot
        pygame.draw.rect(surface, (16, 12, 10), (bx - 8, by - 4, 16, 10), border_radius=3)
        pygame.draw.rect(surface, boot_color, (bx - 7, by - 6, 14, 9), border_radius=3)
        pygame.draw.circle(surface, COLOR_BRASS, (bx, by), 3)

    # 3. Heavy Barrel-Chested Iron Boiler Torso
    armor_color = COLOR_WHITE if flash else COLOR_BRUTE_IRON
    pygame.draw.ellipse(surface, (28, 18, 16), (cx - 24, cy - 18, 48, 36))
    pygame.draw.ellipse(surface, armor_color, (cx - 22, cy - 16, 44, 32))
    pygame.draw.ellipse(surface, (45, 30, 26), (cx - 22, cy - 16, 44, 32), 2)

    # Dual rear steam exhaust smokestacks
    for side in [-1, 1]:
        pipe_x = cx - cos_f * 18 + perp_x * (side * 12)
        pipe_y = cy - sin_f * 18 + perp_y * (side * 12)
        pygame.draw.circle(surface, (25, 18, 14), (int(pipe_x), int(pipe_y)), 7)
        pygame.draw.circle(surface, COLOR_BRASS, (int(pipe_x), int(pipe_y)), 7, 2)
        pygame.draw.circle(surface, (12, 10, 8), (int(pipe_x), int(pipe_y)), 4)
        # Steam soot puffs
        smk = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(smk, (60, 55, 52, 120), (8, 8), 6)
        surface.blit(smk, (int(pipe_x - 8), int(pipe_y - 14)))

    # 4. Exposed Blazing Coal Firebox Ribcage
    fire_pulse = (math.sin(pygame.time.get_ticks() * (0.025 if is_windup else 0.009)) + 1) * 0.5
    fire_col = (255, int(130 + 80 * fire_pulse), 20) if is_windup else (
        int(215 + 40 * fire_pulse), int(75 + 40 * fire_pulse), 20
    )
    pygame.draw.ellipse(surface, (22, 12, 8), (cx - 14, cy - 6, 28, 22))
    pygame.draw.ellipse(surface, fire_col, (cx - 11, cy - 4, 22, 18))
    # Cast-iron grate bars over firebox
    for gx in [-6, 0, 6]:
        pygame.draw.line(surface, (22, 18, 16), (cx + gx, cy - 4), (cx + gx, cy + 14), 2)

    # Brass pressure gauge dial on breastplate
    pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (cx + 12, cy - 10), 5)
    pygame.draw.circle(surface, COLOR_WHITE, (cx + 12, cy - 10), 3)
    pygame.draw.line(surface, (180, 30, 20), (cx + 12, cy - 10), (cx + 14, cy - 12), 1)

    # 5. Spiked Heavy Pauldron Shoulders
    p_l = (cx + perp_x * 22, cy + perp_y * 22)
    p_r = (cx - perp_x * 22, cy - perp_y * 22)
    for px, py in [p_l, p_r]:
        pygame.draw.circle(surface, (38, 24, 20), (int(px), int(py)), 12)
        pygame.draw.circle(surface, COLOR_BRASS, (int(px), int(py)), 12, 2)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(px), int(py)), 5)

    # 6. Colossal Steam Piston Sledgehammer
    hammer_angle = (fa - 1.55) if is_windup else (fa + 0.35)
    reach = 26 if is_windup else 46
    h_end_x = cx + math.cos(hammer_angle) * reach
    h_end_y = cy + math.sin(hammer_angle) * reach

    # Arm linkages
    pygame.draw.line(surface, armor_color, (int(p_l[0]), int(p_l[1])), (int(h_end_x - math.cos(hammer_angle) * 10), int(h_end_y - math.sin(hammer_angle) * 10)), 7)
    pygame.draw.line(surface, armor_color, (int(p_r[0]), int(p_r[1])), (int(h_end_x - math.cos(hammer_angle) * 10), int(h_end_y - math.sin(hammer_angle) * 10)), 7)

    # Heavy steel hammer shaft & head
    pygame.draw.line(surface, (40, 42, 48), (cx, cy), (int(h_end_x), int(h_end_y)), 8)
    pygame.draw.line(surface, COLOR_STEEL_MID, (cx, cy), (int(h_end_x), int(h_end_y)), 4)
    # Huge steel piston hammer head
    pygame.draw.circle(surface, COLOR_STEEL_DARK, (int(h_end_x), int(h_end_y)), 16)
    pygame.draw.circle(surface, COLOR_STEEL_LIGHT, (int(h_end_x), int(h_end_y)), 14)
    pygame.draw.circle(surface, (255, 110, 20) if is_windup else COLOR_BRASS, (int(h_end_x), int(h_end_y)), 9)
    if is_windup:
        pygame.draw.circle(surface, COLOR_WHITE, (int(h_end_x), int(h_end_y)), 18, 2)

    # 7. Heavy Diving Helmet with 3-Bar Protective Face Cage
    helm_x = cx + cos_f * 6
    helm_y = cy + sin_f * 6 - 12
    pygame.draw.circle(surface, (32, 20, 16), (int(helm_x), int(helm_y)), 11)
    pygame.draw.circle(surface, COLOR_BRASS, (int(helm_x), int(helm_y)), 11, 2)
    pygame.draw.circle(surface, fire_col, (int(helm_x), int(helm_y)), 6)
    for bx in (-3, 0, 3):
        pygame.draw.line(surface, (22, 16, 12), (int(helm_x + bx), int(helm_y - 5)), (int(helm_x + bx), int(helm_y + 5)), 2)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


def draw_furnace_golem_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Furnace Golem: Colossal bipedal volcanic basalt titan with stomping pillar legs, glowing magma fissures, and heavy swinging fists."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(enemy, "radius", 36)
    fa = getattr(enemy, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = getattr(enemy, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.18) * 8.0 if is_moving else 0.0
    flash = getattr(enemy, "flash_timer", 0.0) > 0.0
    ticks = pygame.time.get_ticks()
    t = ticks * 0.003

    # 1. Scorched Molten Drop Shadow
    shadow_w = int(r * 2.4)
    shadow_h = int(r * 1.05)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (255, 80, 20, 35), (2, 2, shadow_w - 4, shadow_h - 4))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.40)))

    # 2. Stomping Basalt Pillar Legs with Glowing Magma Knee Joints
    rock_dark = (28, 22, 20)
    rock_color = COLOR_WHITE if flash else COLOR_GOLEM_BASALT
    pulse = (math.sin(ticks * 0.012) + 1) * 0.5
    lava_col = (255, int(115 + 75 * pulse), 20)

    for leg_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if leg_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 14.0) - cos_f * 4.0)
        hy = cy + int(perp_y * (side_sign * 14.0) - sin_f * 4.0 + 8)
        kx = hx + int(cos_f * (6.0 + step_off * 0.3) + perp_x * (side_sign * 4.0))
        ky = hy + int(sin_f * (6.0 + step_off * 0.3) + perp_y * (side_sign * 4.0) + 12)
        fx = hx + int(cos_f * (3.0 + step_off) + perp_x * (side_sign * 6.0))
        fy = hy + int(sin_f * (3.0 + step_off) + perp_y * (side_sign * 6.0) + 20)

        # Upper and lower basalt leg segments
        pygame.draw.line(surface, rock_dark, (hx, hy), (kx, ky), 8)
        pygame.draw.line(surface, rock_color, (hx, hy), (kx, ky), 5)
        pygame.draw.line(surface, rock_dark, (kx, ky), (fx, fy), 7)
        pygame.draw.line(surface, rock_color, (kx, ky), (fx, fy), 4)

        # Glowing molten knee joint
        pygame.draw.circle(surface, lava_col, (int(kx), int(ky)), 4)
        # Heavy stone stomper foot
        pygame.draw.rect(surface, rock_dark, (fx - 7, fy - 4, 15, 9), border_radius=3)
        pygame.draw.rect(surface, rock_color, (fx - 6, fy - 5, 13, 8), border_radius=2)
        pygame.draw.line(surface, lava_col, (fx - 4, fy), (fx + 4, fy), 2)

    # 3. Jagged Basalt Torso & Molten Lava Core
    pygame.draw.circle(surface, rock_dark, (cx, cy), int(r * 0.88))
    pygame.draw.circle(surface, rock_color, (cx, cy), int(r * 0.80))

    # Internal white-hot magma firebox
    pygame.draw.circle(surface, lava_col, (cx, cy), int(r * 0.52))
    pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (cx, cy), int(r * 0.32))
    pygame.draw.circle(surface, COLOR_WHITE, (cx, cy), int(r * 0.16))

    # Jagged rock fissure cracks across chest
    pygame.draw.line(surface, rock_dark, (cx - 16, cy - 8), (cx - 4, cy + 4), 3)
    pygame.draw.line(surface, rock_dark, (cx + 16, cy - 8), (cx + 4, cy + 4), 3)
    pygame.draw.line(surface, lava_col, (cx - 12, cy - 4), (cx - 2, cy + 2), 2)
    pygame.draw.line(surface, lava_col, (cx + 12, cy - 4), (cx + 2, cy + 2), 2)

    # 4. Floating Stony Boulder Fists with Lava Knuckles
    for side in [-1, 1]:
        fist_dist = r * 0.98
        fist_x = cx + perp_x * (side * fist_dist) + cos_f * (6.0 if is_moving else 2.0)
        fist_y = cy + perp_y * (side * fist_dist) + sin_f * (6.0 if is_moving else 2.0)
        pygame.draw.circle(surface, rock_dark, (int(fist_x), int(fist_y)), 10)
        pygame.draw.circle(surface, rock_color, (int(fist_x), int(fist_y)), 8)
        pygame.draw.circle(surface, lava_col, (int(fist_x), int(fist_y)), 4)

    # 5. Orbiting Molten Slag Boulders
    for e_idx in range(4):
        e_ang = t * 1.3 + e_idx * 1.57
        ex = cx + math.cos(e_ang) * (r * 1.15)
        ey = cy + math.sin(e_ang) * (r * 1.15)
        pygame.draw.circle(surface, rock_dark, (int(ex), int(ey)), 4)
        pygame.draw.circle(surface, COLOR_EMBER_ORANGE, (int(ex), int(ey)), 3)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


# =========================================================================
# ALL 10 STAGE BOSS & MINI-BOSS HIGH-DETAIL PROCEDURAL SPRITE RENDERERS
# =========================================================================

def draw_chief_inspector_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Chief Ticket Inspector: Tyrannical bipedal enforcer in high-gloss officer boots, navy greatcoat, gold epaulets, peaked cap, ruby monocle, and electrified truncheon."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(enemy, "radius", 38)
    fa = getattr(enemy, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = getattr(enemy, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.24) * 7.5 if is_moving else 0.0
    phase = getattr(enemy, "phase", 1)
    is_enraged = (phase == 2)
    flash = getattr(enemy, "flash_timer", 0.0) > 0.0
    ticks = pygame.time.get_ticks()

    # 1. Base Drop Shadow
    shadow_w = int(r * 2.3)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), (0, 0, shadow_w, shadow_h))
    if is_enraged:
        pygame.draw.ellipse(shadow_surf, (220, 40, 20, 40), (2, 2, shadow_w - 4, shadow_h - 4))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.40)))

    # 2. Polished High-Gloss Jackboots (Articulated Bipedal Stride)
    boot_leather = (20, 22, 28)
    for leg_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if leg_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 11.0) - cos_f * 3.0)
        hy = cy + int(perp_y * (side_sign * 11.0) - sin_f * 3.0 + 8)
        bx = hx + int(cos_f * (4.0 + step_off) + perp_x * (side_sign * 4.0))
        by = hy + int(sin_f * (4.0 + step_off) + perp_y * (side_sign * 4.0) + 12)

        # Calf & boot shaft
        pygame.draw.line(surface, boot_leather, (hx, hy), (bx, by), 6)
        # Boot heel & sole
        pygame.draw.rect(surface, (12, 14, 18), (bx - 5, by - 3, 11, 8), border_radius=2)
        pygame.draw.rect(surface, (45, 50, 60), (bx - 4, by - 5, 9, 7), border_radius=2)
        # Polished toe cap shine
        pygame.draw.circle(surface, (140, 150, 175), (bx + int(cos_f * 3), by + int(sin_f * 3)), 2)
        # Brass spur
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (bx - int(cos_f * 3), by - int(sin_f * 3)), 2)

    # 3. Billowing Conductor Greatcoat Coattails
    coat_tail_sway = math.sin(walk_dist * 0.24) * 4.0 if is_moving else math.sin(ticks * 0.003) * 2.0
    rear_x = cx - cos_f * 16 + perp_x * coat_tail_sway
    rear_y = cy - sin_f * 16 + perp_y * coat_tail_sway
    t1 = (cx + perp_x * 14, cy + perp_y * 14)
    t2 = (cx - perp_x * 14, cy - perp_y * 14)
    t3 = (int(rear_x), int(rear_y))
    pygame.draw.polygon(surface, (18, 28, 48), [t1, t2, t3])
    pygame.draw.polygon(surface, COLOR_BRASS, [t1, t2, t3], 1)

    # 4. Double-Breasted Conductor Navy Greatcoat
    pulse = (math.sin(ticks * 0.01) + 1) * 0.5
    coat_col = COLOR_WHITE if flash else (
        (int(150 + 60 * pulse), 30, 30) if is_enraged else COLOR_CONDUCTOR_NAVY
    )
    pygame.draw.circle(surface, (12, 20, 36), (cx, cy), int(r * 0.88))
    pygame.draw.circle(surface, coat_col, (cx, cy), int(r * 0.82))

    # Crimson velvet lapels & brass buttons
    pygame.draw.line(surface, (140, 25, 30), (cx - 8, cy - 14), (cx, cy + 6), 3)
    pygame.draw.line(surface, (140, 25, 30), (cx + 8, cy - 14), (cx, cy + 6), 3)
    for b_row in (-6, 0, 6):
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (cx - 5, cy + b_row), 2)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (cx + 5, cy + b_row), 2)

    # Heavy leather officer belt with gleaming brass buckle
    pygame.draw.rect(surface, (40, 28, 20), (cx - 14, cy + 8, 28, 5), border_radius=2)
    pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, (cx - 5, cy + 7, 10, 7), 2, border_radius=1)

    # 5. Golden Tasseled Shoulder Epaulets
    for s in (-1, 1):
        ep_x = cx + perp_x * (s * 18) - cos_f * 2
        ep_y = cy + perp_y * (s * 18) - sin_f * 2
        pygame.draw.circle(surface, COLOR_BRASS, (int(ep_x), int(ep_y)), 7)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(ep_x), int(ep_y)), 5)
        # Hanging gold fringe tassels
        tass_x = ep_x + perp_x * (s * 4) + cos_f * 2
        tass_y = ep_y + perp_y * (s * 4) + sin_f * 2
        pygame.draw.line(surface, COLOR_CRIT_YELLOW, (int(ep_x), int(ep_y)), (int(tass_x), int(tass_y)), 3)

    # 6. Electrified Golden Conductor's Truncheon
    baton_ang = fa + (0.55 if not is_enraged else 0.85 + math.sin(ticks * 0.02) * 0.2)
    b_cos = math.cos(baton_ang)
    b_sin = math.sin(baton_ang)
    h_x = cx + cos_f * 14 + perp_x * 12
    h_y = cy + sin_f * 14 + perp_y * 12
    t_len = 34
    tip_x = h_x + b_cos * t_len
    tip_y = h_y + b_sin * t_len

    # Arm reaching forward
    pygame.draw.line(surface, coat_col, (cx + perp_x * 14, cy + perp_y * 14), (int(h_x), int(h_y)), 6)
    pygame.draw.circle(surface, (230, 230, 235), (int(h_x), int(h_y)), 4)
    # Heavy gold baton shaft
    pygame.draw.line(surface, COLOR_BRASS, (int(h_x), int(h_y)), (int(tip_x), int(tip_y)), 5)
    pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (int(h_x), int(h_y)), (int(tip_x), int(tip_y)), 3)
    # Fluted shock head
    pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(tip_x), int(tip_y)), 5)
    # Branching electric arcs crackling around baton
    if is_enraged or (ticks // 180) % 2 == 0:
        spk_x = tip_x + math.sin(ticks * 0.04) * 8
        spk_y = tip_y + math.cos(ticks * 0.04) * 8
        pygame.draw.line(surface, COLOR_LIGHTNING_CYAN, (int(tip_x), int(tip_y)), (int(spk_x), int(spk_y)), 2)

    # 7. Peaked Conductor's Officer Cap & Crest
    cap_x = cx + cos_f * 8
    cap_y = cy + sin_f * 8 - 10
    pygame.draw.circle(surface, (16, 24, 40), (int(cap_x), int(cap_y)), 12)
    # Patent leather visor
    v_end_x = cap_x + cos_f * 8
    v_end_y = cap_y + sin_f * 8
    pygame.draw.line(surface, (10, 10, 12), (int(cap_x - perp_x * 9), int(cap_y - perp_y * 9)), (int(v_end_x), int(v_end_y)), 3)
    pygame.draw.line(surface, (10, 10, 12), (int(cap_x + perp_x * 9), int(cap_y + perp_y * 9)), (int(v_end_x), int(v_end_y)), 3)
    # Gold braided cap band
    pygame.draw.arc(surface, COLOR_BRASS_HIGHLIGHT, (int(cap_x - 10), int(cap_y - 10), 20, 20), 0, math.pi, 2)
    # Imperial eagle crest badge
    pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(cap_x + cos_f * 3), int(cap_y + sin_f * 3 - 3)), 3)

    # 8. Cybernetic Ruby Monocle / Optic Eye
    eye_col = (255, 30, 30) if is_enraged else (255, 160, 40)
    eye_x = cap_x + cos_f * 5 + perp_x * 3
    eye_y = cap_y + sin_f * 5 + perp_y * 3
    pygame.draw.circle(surface, (15, 10, 10), (int(eye_x), int(eye_y)), 5)
    pygame.draw.circle(surface, eye_col, (int(eye_x), int(eye_y)), 3)
    pygame.draw.circle(surface, COLOR_WHITE, (int(eye_x), int(eye_y)), 1)


def draw_conductor_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws The Conductor (Final Boss of Track 1): Monumental Steam Locomotive Mecha-Conductor with giant hydraulic walker legs, spinning knee cogs, royal crimson velvet greatcoat, roaring firebox chest, Conductor's Scepter, and dual searchlight eyes."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(enemy, "radius", 58)
    fa = getattr(enemy, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = getattr(enemy, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.16) * 11.0 if is_moving else 0.0
    phase = getattr(enemy, "phase", 1)
    is_enraged = (phase == 2)
    flash = getattr(enemy, "flash_timer", 0.0) > 0.0
    ticks = pygame.time.get_ticks()

    # 1. Monumental Ground Drop Shadow
    shadow_w = int(r * 2.6)
    shadow_h = int(r * 1.15)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 130), (0, 0, shadow_w, shadow_h))
    if is_enraged:
        pygame.draw.ellipse(shadow_surf, (220, 60, 20, 50), (4, 4, shadow_w - 8, shadow_h - 8))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.42)))

    # 2. Giant Hydraulic Locomotive Walker Legs & Rotating Knee Cogs
    leg_iron = (30, 32, 38)
    cog_rot = ticks * 0.005
    for leg_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if leg_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 22.0) - cos_f * 6.0)
        hy = cy + int(perp_y * (side_sign * 22.0) - sin_f * 6.0 + 12)
        kx = hx + int(cos_f * (12.0 + step_off * 0.4) + perp_x * (side_sign * 8.0))
        ky = hy + int(sin_f * (12.0 + step_off * 0.4) + perp_y * (side_sign * 8.0) + 16)
        fx = hx + int(cos_f * (6.0 + step_off) + perp_x * (side_sign * 10.0))
        fy = hy + int(sin_f * (6.0 + step_off) + perp_y * (side_sign * 10.0) + 26)

        # Thick armored thigh and shin struts
        pygame.draw.line(surface, leg_iron, (hx, hy), (kx, ky), 10)
        pygame.draw.line(surface, COLOR_STEEL_MID, (hx, hy), (kx, ky), 6)
        pygame.draw.line(surface, leg_iron, (kx, ky), (fx, fy), 9)
        pygame.draw.line(surface, COLOR_STEEL_LIGHT, (kx, ky), (fx, fy), 5)
        # Hydraulic piston rod on calf
        pygame.draw.line(surface, COLOR_BRASS_HIGHLIGHT, (hx + side_sign * 3, hy), (kx + side_sign * 3, ky), 3)

        # Rotating brass knee cog
        pygame.draw.circle(surface, (20, 20, 25), (int(kx), int(ky)), 9)
        pygame.draw.circle(surface, COLOR_BRASS, (int(kx), int(ky)), 8)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(kx), int(ky)), 8, 2)
        for cog_i in range(4):
            c_ang = cog_rot + cog_i * (math.pi / 2)
            cx_c = kx + math.cos(c_ang) * 9
            cy_c = ky + math.sin(c_ang) * 9
            pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(cx_c), int(cy_c)), 2)

        # Massive locomotive sabaton foot
        pygame.draw.rect(surface, (18, 16, 16), (fx - 10, fy - 5, 20, 14), border_radius=4)
        pygame.draw.rect(surface, COLOR_STEEL_DARK, (fx - 9, fy - 8, 18, 12), border_radius=4)
        pygame.draw.circle(surface, COLOR_BRASS, (fx, fy), 4)

    # 3. Opulent Royal Crimson Admiral Greatcoat & Billowing Coattails
    coat_sway = math.sin(walk_dist * 0.16) * 6.0 if is_moving else math.sin(ticks * 0.002) * 3.0
    c_tail_x = cx - cos_f * 26 + perp_x * coat_sway
    c_tail_y = cy - sin_f * 26 + perp_y * coat_sway
    ct_p1 = (cx + perp_x * 24, cy + perp_y * 24)
    ct_p2 = (cx - perp_x * 24, cy - perp_y * 24)
    ct_p3 = (int(c_tail_x), int(c_tail_y))
    pygame.draw.polygon(surface, (90, 18, 25), [ct_p1, ct_p2, ct_p3])
    pygame.draw.polygon(surface, COLOR_BRASS_HIGHLIGHT, [ct_p1, ct_p2, ct_p3], 2)

    # Outer boiler armor shell
    pulse = (math.sin(ticks * 0.008) + 1) * 0.5
    body_color = COLOR_WHITE if flash else (
        (int(210 + 45 * pulse), 40, 20) if is_enraged else COLOR_CARPET_RED
    )
    pygame.draw.circle(surface, (20, 20, 25), (cx, cy), int(r * 0.95))
    pygame.draw.circle(surface, COLOR_STEEL_DARK, (cx, cy), int(r * 0.90))
    pygame.draw.circle(surface, body_color, (cx, cy), int(r * 0.82))
    for rv in range(0, 360, 30):
        rv_rad = math.radians(rv)
        rx = cx + math.cos(rv_rad) * (r * 0.84)
        ry = cy + math.sin(rv_rad) * (r * 0.84)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(rx), int(ry)), 2)

    # 4. Central Roaring Locomotive Firebox Heart
    fire_pulse = (math.sin(ticks * (0.02 if is_enraged else 0.01)) + 1) * 0.5
    fire_col = (255, int(120 + 90 * fire_pulse), 20)
    fb_r = int(r * 0.38)
    pygame.draw.circle(surface, (25, 18, 14), (cx, cy), fb_r + 4)
    pygame.draw.circle(surface, fire_col, (cx, cy), fb_r)
    pygame.draw.circle(surface, (255, 240, 160), (cx, cy), int(fb_r * 0.55))
    for gx in (-7, 0, 7):
        pygame.draw.line(surface, (28, 22, 20), (cx + gx, cy - fb_r), (cx + gx, cy + fb_r), 3)
    pygame.draw.line(surface, (28, 22, 20), (cx - fb_r, cy), (cx + fb_r, cy), 3)

    # 5. Dual Towering Brass Exhaust Smokestacks
    rear_angle = fa + math.pi
    for side in (-1, 1):
        stack_pos = pygame.math.Vector2(cx, cy) + pygame.math.Vector2(math.cos(rear_angle), math.sin(rear_angle)) * (r * 0.65) + pygame.math.Vector2(perp_x, perp_y) * (side * 24)
        sx, sy = int(stack_pos.x), int(stack_pos.y)
        pygame.draw.rect(surface, (22, 22, 28), (sx - 9, sy - 14, 18, 24), border_radius=4)
        pygame.draw.rect(surface, COLOR_BRASS, (sx - 10, sy - 16, 20, 6), border_radius=2)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (sx, sy - 14), 6)
        smk_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        smk_col = (255, 120, 60, 140) if is_enraged else (210, 215, 225, 110)
        pygame.draw.circle(smk_surf, smk_col, (14, 14), 10 + int(math.sin(ticks * 0.01 + side) * 3))
        surface.blit(smk_surf, (sx - 14, sy - 30 + int(math.cos(ticks * 0.008 + side) * 4)))

    # 6. Right Hand: The Conductor's Scepter (Turbine Engine Staff)
    s_ang = fa + (0.45 if not is_enraged else 0.70)
    s_cos = math.cos(s_ang)
    s_sin = math.sin(s_ang)
    s_base_x = cx + cos_f * 18 + perp_x * 20
    s_base_y = cy + sin_f * 18 + perp_y * 20
    s_len = 54
    s_head_x = s_base_x + s_cos * s_len
    s_head_y = s_base_y + s_sin * s_len

    pygame.draw.line(surface, body_color, (cx + perp_x * 22, cy + perp_y * 22), (int(s_base_x), int(s_base_y)), 9)
    pygame.draw.circle(surface, (240, 240, 245), (int(s_base_x), int(s_base_y)), 6)
    pygame.draw.line(surface, (35, 30, 25), (int(s_base_x), int(s_base_y)), (int(s_head_x), int(s_head_y)), 8)
    pygame.draw.line(surface, COLOR_BRASS, (int(s_base_x), int(s_base_y)), (int(s_head_x), int(s_head_y)), 5)
    pygame.draw.circle(surface, (20, 20, 25), (int(s_head_x), int(s_head_y)), 12)
    pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(s_head_x), int(s_head_y)), 10)
    pygame.draw.circle(surface, fire_col, (int(s_head_x), int(s_head_y)), 6)
    pygame.draw.circle(surface, COLOR_WHITE, (int(s_head_x), int(s_head_y)), 3)

    # 7. Left Hand: Locomotive Cowcatcher Shield Claw
    c_base_x = cx + cos_f * 18 - perp_x * 20
    c_base_y = cy + sin_f * 18 - perp_y * 20
    c_tip_x = c_base_x + cos_f * 26
    c_tip_y = c_base_y + sin_f * 26
    pygame.draw.line(surface, body_color, (cx - perp_x * 22, cy - perp_y * 22), (int(c_base_x), int(c_base_y)), 9)
    wedge_tip = (int(c_tip_x + cos_f * 16), int(c_tip_y + sin_f * 16))
    wedge_l = (int(c_tip_x + perp_x * 16), int(c_tip_y + perp_y * 16))
    wedge_r = (int(c_tip_x - perp_x * 16), int(c_tip_y - perp_y * 16))
    pygame.draw.polygon(surface, COLOR_STEEL_DARK, [wedge_tip, wedge_l, wedge_r])
    pygame.draw.polygon(surface, COLOR_BRASS_HIGHLIGHT, [wedge_tip, wedge_l, wedge_r], 2)

    # 8. Iron Conductor Helm & Peaked Hat
    helm_x = cx + cos_f * 10
    helm_y = cy + sin_f * 10 - 14
    pygame.draw.circle(surface, (18, 22, 32), (int(helm_x), int(helm_y)), 16)
    pygame.draw.circle(surface, COLOR_BRASS, (int(helm_x), int(helm_y)), 16, 2)
    pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(helm_x + cos_f * 4), int(helm_y + sin_f * 4 - 4)), 5)

    # 9. Dual Searchlight Optic Eyes (Bright Gold & Red)
    eye_col = (255, 40, 20) if is_enraged else COLOR_CRIT_YELLOW
    for s in (-1, 1):
        ex = helm_x + cos_f * 7 + perp_x * (s * 6)
        ey = helm_y + sin_f * 7 + perp_y * (s * 6)
        pygame.draw.circle(surface, (15, 12, 10), (int(ex), int(ey)), 6)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(ex), int(ey)), 6, 1)
        pygame.draw.circle(surface, eye_col, (int(ex), int(ey)), 4)
        pygame.draw.circle(surface, COLOR_WHITE, (int(ex), int(ey)), 2)


def draw_scrapper_foreman_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Scrapper Foreman (Stage 2 Mini-Boss): Towering bipedal junkyard warlord in leather apron with giant toothed pipe wrench."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 40)
    fa = getattr(boss, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f
    ticks = pygame.time.get_ticks()

    walk_dist = getattr(boss, "walk_distance", 0.0)
    is_moving = getattr(boss, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.22) * 8.0 if is_moving else 0.0

    # 1. Drop shadow
    shadow_w = int(r * 2.3)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.42)))

    # Whirlwind attack visual blur
    is_whirlwind = getattr(boss, "current_attack", None) == "whirlwind"
    if is_whirlwind:
        blur_surf = pygame.Surface((int(r * 3.2), int(r * 3.2)), pygame.SRCALPHA)
        pygame.draw.circle(blur_surf, (230, 130, 40, 85), (int(r * 1.6), int(r * 1.6)), int(r * 1.5), 10)
        surface.blit(blur_surf, (cx - int(r * 1.6), cy - int(r * 1.6)))

    # 2. Heavy Articulated Steel-Toed Work Boots
    for foot_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 12.0) - cos_f * 4.0)
        hy = cy + int(perp_y * (side_sign * 12.0) - sin_f * 4.0 + 10)
        bx = hx + int(cos_f * (4.0 + step_off) + perp_x * (side_sign * 4.0))
        by = hy + int(sin_f * (4.0 + step_off) + perp_y * (side_sign * 4.0) + 16)
        pygame.draw.line(surface, (35, 25, 20), (hx, hy), (bx, by), 7)
        pygame.draw.rect(surface, (20, 15, 12), (bx - 6, by - 4, 12, 9), border_radius=2)
        pygame.draw.rect(surface, (80, 50, 32), (bx - 5, by - 6, 10, 8), border_radius=2)
        pygame.draw.circle(surface, (150, 140, 130), (bx + int(cos_f * 3), by + int(sin_f * 3)), 3)

    # 3. Leather Welder's Apron & Torso
    flash = getattr(boss, "flash_timer", 0) > 0
    body_col = COLOR_WHITE if flash else (145, 85, 45)
    pygame.draw.circle(surface, (45, 30, 22), (cx, cy), int(r * 0.88))
    pygame.draw.circle(surface, body_col, (cx, cy), int(r * 0.82))
    # Soot and grease stains on apron
    pygame.draw.ellipse(surface, (35, 25, 20), (cx - 10, cy - 8, 14, 18))

    # Toolbelt with dangling chains
    pygame.draw.rect(surface, (40, 28, 20), (cx - 18, cy + 6, 36, 8), border_radius=2)
    pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, (cx - 7, cy + 5, 14, 10), 2, border_radius=1)
    pygame.draw.line(surface, (140, 130, 120), (cx - 14, cy + 13), (cx - 10, cy + 22), 2)
    pygame.draw.line(surface, (140, 130, 120), (cx + 12, cy + 13), (cx + 16, cy + 23), 2)

    # 4. Spiked Scrap Iron Shoulder Pauldrons
    for s in (-1, 1):
        px = cx + perp_x * (s * 20)
        py = cy + perp_y * (s * 20)
        pygame.draw.circle(surface, (70, 65, 60), (int(px), int(py)), 10)
        pygame.draw.circle(surface, (140, 130, 120), (int(px), int(py)), 8)
        spk_x = px + perp_x * (s * 8) - cos_f * 4
        spk_y = py + perp_y * (s * 8) - sin_f * 4
        pygame.draw.line(surface, (210, 200, 190), (int(px), int(py)), (int(spk_x), int(spk_y)), 3)

    # 5. Massive Industrial Pipe Wrench
    w_ang = fa + (ticks * 0.024 if is_whirlwind else 0.5)
    w_cos = math.cos(w_ang)
    w_sin = math.sin(w_ang)
    w_perp_x = -w_sin
    w_perp_y = w_cos

    w_base_x = cx + cos_f * 14 + perp_x * 10
    w_base_y = cy + sin_f * 14 + perp_y * 10
    w_len = 46
    w_head_x = w_base_x + w_cos * w_len
    w_head_y = w_base_y + w_sin * w_len

    # Steel shaft
    pygame.draw.line(surface, (55, 52, 50), (int(w_base_x), int(w_base_y)), (int(w_head_x), int(w_head_y)), 9)
    pygame.draw.line(surface, (170, 165, 155), (int(w_base_x), int(w_base_y)), (int(w_head_x), int(w_head_y)), 5)
    # Heavy toothed wrench jaw
    jaw_p1 = (int(w_head_x + w_perp_x * 12), int(w_head_y + w_perp_y * 12))
    jaw_p2 = (int(w_head_x - w_perp_x * 8), int(w_head_y - w_perp_y * 8))
    jaw_p3 = (int(w_head_x + w_cos * 12 + w_perp_x * 14), int(w_head_y + w_sin * 12 + w_perp_y * 14))
    jaw_p4 = (int(w_head_x + w_cos * 12 - w_perp_x * 6), int(w_head_y + w_sin * 12 - w_perp_y * 6))
    pygame.draw.polygon(surface, (100, 95, 90), [jaw_p1, jaw_p2, jaw_p4, jaw_p3])
    pygame.draw.polygon(surface, (180, 170, 160), [jaw_p1, jaw_p2, jaw_p4, jaw_p3], 2)
    pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(w_base_x + w_cos * 18), int(w_base_y + w_sin * 18)), 5)

    # 6. Welder's Heavy Helmet & Glowing Visor
    head_x = cx + cos_f * 8
    head_y = cy + sin_f * 8 - 10
    pygame.draw.circle(surface, (45, 40, 38), (int(head_x), int(head_y)), 13)
    pygame.draw.rect(surface, (75, 70, 68), (int(head_x - 10), int(head_y - 10), 20, 20), border_radius=4)
    # Glowing amber welding visor slit
    vx = head_x + cos_f * 5 - 7
    vy = head_y + sin_f * 5 - 3
    glow_pulse = (math.sin(ticks * 0.01) + 1) * 0.5
    visor_col = (255, int(150 + 80 * glow_pulse), 30)
    pygame.draw.rect(surface, visor_col, (int(vx), int(vy), 14, 5), border_radius=1)
    pygame.draw.line(surface, COLOR_WHITE, (int(vx + 2), int(vy + 1)), (int(vx + 12), int(vy + 1)), 1)


def draw_vermin_brood_engine_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Vermin Brood Engine (Stage 2 Final Boss): Colossal Bio-Mechanical Incinerator Behemoth with multi-jointed hydraulic walker legs, weeping toxic slime, and gaping furnace maw."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 60)
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0
    phase = getattr(boss, "phase", 1)

    # 1. Monumental Toxic Shadow
    shadow_w = int(r * 2.5)
    shadow_h = int(r * 1.15)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (15, 20, 10, 130), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.42)))

    # 2. 6 Reinforced Hydraulic Bio-Mechanical Walker Legs
    for side in (-1, 1):
        for leg_i in range(3):
            leg_ang = (leg_i - 1) * 0.55 + (0 if side == 1 else math.pi)
            stride = math.sin(ticks * 0.007 + leg_i * 1.2) * 8.0
            knee_x = cx + math.cos(leg_ang) * (r * 0.95)
            knee_y = cy + math.sin(leg_ang) * (r * 0.75) - 6
            foot_x = cx + math.cos(leg_ang) * (r * 1.45 + stride)
            foot_y = cy + math.sin(leg_ang) * (r * 1.15 + stride) + 16
            pygame.draw.line(surface, (38, 30, 24), (cx, cy), (int(knee_x), int(knee_y)), 8)
            pygame.draw.line(surface, (75, 58, 40), (int(knee_x), int(knee_y)), (int(foot_x), int(foot_y)), 7)
            # Hydraulic joint pistons
            pygame.draw.circle(surface, (150, 120, 80), (int(knee_x), int(knee_y)), 6)
            # Talons
            pygame.draw.circle(surface, (30, 25, 20), (int(foot_x), int(foot_y)), 6)
            pygame.draw.line(surface, (180, 150, 90), (int(foot_x), int(foot_y)), (int(foot_x + side * 8), int(foot_y + 6)), 3)

    # 3. Giant Cylindrical Boiler Hull
    hull_col = COLOR_WHITE if flash else ((185, 75, 45) if phase == 2 else (115, 65, 42))
    hull_dark = (45, 28, 20)
    pygame.draw.circle(surface, hull_dark, (cx, cy), int(r))
    pygame.draw.circle(surface, hull_col, (cx, cy), int(r - 5))
    
    # Weeping acidic slime streaks
    pygame.draw.arc(surface, (90, 220, 40), (cx - 30, cy - 18, 60, 36), 0, math.pi, 4)
    for rv in range(-int(r * 0.7), int(r * 0.7), 18):
        pygame.draw.circle(surface, (190, 150, 90), (cx + rv, cy - 12), 3)
        pygame.draw.circle(surface, (190, 150, 90), (cx + rv, cy + 12), 3)

    # 4. Gaping Toxic Incinerator Maw with Iron Teeth
    pulse = (math.sin(ticks * 0.012) + 1) * 0.5
    fire_col = (int(160 + 95 * pulse), 40, 25) if phase == 2 else (int(70 + 60 * pulse), int(220 + 35 * pulse), 40)
    core_r = int(r * 0.45)
    pygame.draw.circle(surface, (20, 16, 14), (cx, cy), core_r + 5)
    pygame.draw.circle(surface, fire_col, (cx, cy), core_r)
    pygame.draw.circle(surface, (245, 255, 190), (cx, cy), int(core_r * 0.55))
    # Serrated teeth
    for g_off in (-10, 0, 10):
        pygame.draw.line(surface, (30, 22, 18), (cx + g_off, cy - core_r), (cx + g_off, cy + core_r), 4)

    # 5. Twin Industrial Smokestacks Spewing Smog
    for side in (-1, 1):
        stack_x = cx + side * 28
        stack_y = cy - int(r * 0.75)
        pygame.draw.rect(surface, (35, 28, 24), (stack_x - 10, stack_y - 16, 20, 24), border_radius=4)
        pygame.draw.rect(surface, (140, 100, 65), (stack_x - 11, stack_y - 18, 22, 6), border_radius=2)
        smoke_col = (100, 190, 50, 140) if phase == 1 else (240, 80, 40, 160)
        smk_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(smk_surf, smoke_col, (15, 15), 11)
        surface.blit(smk_surf, (stack_x - 15, stack_y - 32 + int(math.sin(ticks * 0.01 + side) * 4)))


def draw_cyber_dispatcher_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Cyber Dispatcher (Stage 3 Mini-Boss): Sleek bipedal cybernetic officer in matte carbon armor with maglev thrusters and dual crackling arc-batons."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 38)
    fa = getattr(boss, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0

    walk_dist = getattr(boss, "walk_distance", 0.0)
    is_moving = getattr(boss, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.24) * 7.5 if is_moving else 0.0

    # 1. Drop shadow with cyan ambient under-glow
    shadow_w = int(r * 2.2)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (0, 220, 255, 45), (2, 2, shadow_w - 4, shadow_h - 4))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.40)))

    # 2. Articulated Bipedal Maglev Thruster Boots
    for leg_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if leg_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 11.0) - cos_f * 4.0)
        hy = cy + int(perp_y * (side_sign * 11.0) - sin_f * 4.0 + 8)
        bx = hx + int(cos_f * (4.0 + step_off) + perp_x * (side_sign * 4.0))
        by = hy + int(sin_f * (4.0 + step_off) + perp_y * (side_sign * 4.0) + 14)

        pygame.draw.line(surface, (20, 26, 38), (hx, hy), (bx, by), 6)
        pygame.draw.rect(surface, (16, 22, 34), (bx - 5, by - 4, 11, 8), border_radius=2)
        # Maglev cyan jet sole
        pygame.draw.rect(surface, COLOR_LIGHTNING_CYAN, (bx - 4, by + 4, 9, 3))

    # 3. Matte Carbon-Fiber Plate Armor & Neon Conduits
    suit_col = COLOR_WHITE if flash else (22, 32, 50)
    pygame.draw.circle(surface, (10, 14, 24), (cx, cy), int(r * 0.88))
    pygame.draw.circle(surface, suit_col, (cx, cy), int(r * 0.82))

    neon_pulse = (math.sin(ticks * 0.01) + 1) * 0.5
    cyan_col = (int(30 + 30 * neon_pulse), int(220 + 35 * neon_pulse), 255)
    pygame.draw.circle(surface, cyan_col, (cx, cy), int(r * 0.82), 2)
    pygame.draw.line(surface, cyan_col, (cx - 10, cy - 10), (cx, cy + 6), 2)
    pygame.draw.line(surface, cyan_col, (cx + 10, cy - 10), (cx, cy + 6), 2)

    # 4. Angular Riot Pauldrons
    for s in (-1, 1):
        px = cx + perp_x * (s * 18)
        py = cy + perp_y * (s * 18)
        pygame.draw.circle(surface, (16, 22, 36), (int(px), int(py)), 8)
        pygame.draw.circle(surface, cyan_col, (int(px), int(py)), 8, 1)

    # 5. Dual Arc-Batons Crackling with Branching Lightning
    for s in (-1, 1):
        hand_x = cx + cos_f * 15 + perp_x * (s * 15)
        hand_y = cy + sin_f * 15 + perp_y * (s * 15)
        b_ang = fa + s * 0.4
        tip_x = hand_x + math.cos(b_ang) * 28
        tip_y = hand_y + math.sin(b_ang) * 28

        pygame.draw.line(surface, (38, 45, 58), (int(hand_x), int(hand_y)), (int(tip_x), int(tip_y)), 6)
        pygame.draw.line(surface, COLOR_LIGHTNING_CYAN, (int(hand_x), int(hand_y)), (int(tip_x), int(tip_y)), 3)
        pygame.draw.circle(surface, (200, 250, 255), (int(tip_x), int(tip_y)), 5)
        # Lightning sparks
        spark_ang = ticks * 0.03 * s
        spk_x = tip_x + math.cos(spark_ang) * 8
        spk_y = tip_y + math.sin(spark_ang) * 8
        pygame.draw.line(surface, (140, 255, 255), (int(tip_x), int(tip_y)), (int(spk_x), int(spk_y)), 2)

    # 6. Tactical Helmet & Holographic Visor
    head_x = cx + cos_f * 8
    head_y = cy + sin_f * 8 - 8
    pygame.draw.circle(surface, (12, 18, 30), (int(head_x), int(head_y)), 11)
    v_col = (255, 40, 180) if (ticks // 220) % 2 == 0 else cyan_col
    pygame.draw.rect(surface, v_col, (int(head_x - 7), int(head_y - 5), 14, 6), border_radius=1)
    pygame.draw.line(surface, COLOR_WHITE, (int(head_x - 5), int(head_y - 2)), (int(head_x + 5), int(head_y - 2)), 1)


def draw_traction_ai_core_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Traction AI Core (Stage 3 Final Boss): Towering Cybernetic Walker Mainframe & Floating Gyro-Core with hydraulic stabilization struts, rotating rings, and aperture eye."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 58)
    fa = getattr(boss, "facing_angle", 0.0)
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0
    phase = getattr(boss, "phase", 1)

    # 1. Pulsing Maglev Shadow
    shadow_w = int(r * 2.5)
    shadow_h = int(r * 1.1)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (40, 220, 255, 50), (4, 4, shadow_w - 8, shadow_h - 8))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.42)))

    # 2. Articulated Bipedal Hydraulic Stabilization Struts
    for side in (-1, 1):
        hx = cx + side * int(r * 0.65)
        hy = cy + 12
        fx = cx + side * int(r * 0.95)
        fy = cy + int(r * 0.55)
        pygame.draw.line(surface, (20, 28, 44), (hx, hy), (fx, fy), 8)
        pygame.draw.line(surface, (50, 180, 240), (hx, hy), (fx, fy), 3)
        pygame.draw.circle(surface, (12, 16, 26), (int(fx), int(fy)), 8)
        pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, (int(fx), int(fy)), 5)

    # 3. 4 Orbiting Magnetic Capacitor Pylons
    pylon_count = 4
    orbit_speed = 0.0025 if phase == 1 else 0.005
    for p_idx in range(pylon_count):
        p_ang = ticks * orbit_speed + (math.tau / pylon_count) * p_idx
        px = cx + math.cos(p_ang) * (r * 1.30)
        py = cy + math.sin(p_ang) * (r * 1.30)
        pygame.draw.circle(surface, (16, 24, 38), (int(px), int(py)), 9)
        pylon_glow = (255, 50, 180) if phase == 2 else (40, 240, 255)
        pygame.draw.circle(surface, pylon_glow, (int(px), int(py)), 7, 2)
        pygame.draw.circle(surface, COLOR_WHITE, (int(px), int(py)), 3)
        pygame.draw.line(surface, pylon_glow, (int(px), int(py)), (cx, cy), 1)

    # 4. Octagonal Mainframe Chassis
    oct_pts = []
    base_col = COLOR_WHITE if flash else (20, 30, 48)
    for i in range(8):
        ang = (math.tau / 8) * i + math.pi / 8
        oct_pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    pygame.draw.polygon(surface, (10, 14, 24), oct_pts)
    pygame.draw.polygon(surface, base_col, oct_pts, 0)
    pygame.draw.polygon(surface, (50, 180, 240), oct_pts, 3)

    # 5. Triple Concentric Gyroscopic Magnetic Rings
    ring_rot = ticks * 0.003
    for ring_i in range(3):
        rr = int(r * (0.80 - ring_i * 0.16))
        pygame.draw.circle(surface, (30, 140, 200), (cx, cy), rr, 2)
        # Ring node indicator
        n_ang = ring_rot * (1 if ring_i % 2 == 0 else -1) + ring_i * 1.2
        nx = cx + math.cos(n_ang) * rr
        ny = cy + math.sin(n_ang) * rr
        pygame.draw.circle(surface, COLOR_LIGHTNING_CYAN, (int(nx), int(ny)), 4)

    # 6. Central Aperture Optic Camera Eye (Tracking Player)
    eye_r = int(r * 0.44)
    pygame.draw.circle(surface, (10, 14, 24), (cx, cy), eye_r)
    pygame.draw.circle(surface, (40, 220, 255), (cx, cy), eye_r, 2)

    pupil_offset = pygame.math.Vector2(math.cos(fa), math.sin(fa)) * 8.0
    pupil_x = cx + pupil_offset.x
    pupil_y = cy + pupil_offset.y
    core_glow = (255, 40, 180) if phase == 2 else (0, 255, 240)
    pygame.draw.circle(surface, core_glow, (int(pupil_x), int(pupil_y)), 11)
    pygame.draw.circle(surface, COLOR_WHITE, (int(pupil_x), int(pupil_y)), 5)


def draw_sub_zero_warden_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Sub-Zero Warden (Stage 4 Mini-Boss): Glacial bipedal cryogenic dreadnought with frosted sabatons, crampons, liquid nitrogen canisters, and frost-breaker hammer."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 40)
    fa = getattr(boss, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0

    walk_dist = getattr(boss, "walk_distance", 0.0)
    is_moving = getattr(boss, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.22) * 8.0 if is_moving else 0.0

    # 1. Frosted Glacial Shadow
    shadow_w = int(r * 2.3)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (160, 230, 255, 45), (2, 2, shadow_w - 4, shadow_h - 4))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.40)))

    # 2. Heavy Frosted Bipedal Sabatons with Ice Crampons
    for foot_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 13.0) - cos_f * 4.0)
        hy = cy + int(perp_y * (side_sign * 13.0) - sin_f * 4.0 + 8)
        bx = hx + int(cos_f * (4.0 + step_off) + perp_x * (side_sign * 4.0))
        by = hy + int(sin_f * (4.0 + step_off) + perp_y * (side_sign * 4.0) + 16)
        pygame.draw.line(surface, (25, 45, 70), (hx, hy), (bx, by), 7)
        pygame.draw.rect(surface, (18, 32, 52), (bx - 6, by - 4, 12, 9), border_radius=2)
        pygame.draw.rect(surface, (140, 220, 255), (bx - 5, by - 6, 10, 8), border_radius=2)
        # Ice crampon teeth
        pygame.draw.line(surface, (210, 245, 255), (bx - 5, by + 4), (bx - 3, by + 7), 2)
        pygame.draw.line(surface, (210, 245, 255), (bx + 3, by + 4), (bx + 5, by + 7), 2)

    # 3. Back-Mounted Liquid Nitrogen Canisters Venting Vapor
    for s in (-1, 1):
        cx_tank = cx - cos_f * 16 + perp_x * (s * 15)
        cy_tank = cy - sin_f * 16 + perp_y * (s * 15)
        pygame.draw.rect(surface, (28, 45, 68), (int(cx_tank - 6), int(cy_tank - 10), 12, 20), border_radius=3)
        pygame.draw.rect(surface, (140, 230, 255), (int(cx_tank - 4), int(cy_tank - 7), 8, 14), border_radius=1)
        # Cold vapor puff
        vp_surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(vp_surf, (190, 240, 255, 120), (9, 9), 7)
        surface.blit(vp_surf, (int(cx_tank - 9), int(cy_tank - 22 + math.sin(ticks * 0.01 + s) * 3)))

    # 4. Frosted Cobalt Power Armor Torso
    suit_col = COLOR_WHITE if flash else (45, 80, 125)
    pygame.draw.circle(surface, (18, 36, 58), (cx, cy), int(r * 0.88))
    pygame.draw.circle(surface, suit_col, (cx, cy), int(r * 0.80))
    pygame.draw.circle(surface, (180, 240, 255), (cx, cy), int(r * 0.80), 2)

    # 5. Jagged Icicle Pauldrons
    for s in (-1, 1):
        px = cx + perp_x * (s * 20)
        py = cy + perp_y * (s * 20)
        pygame.draw.circle(surface, (55, 100, 150), (int(px), int(py)), 9)
        for ic in range(3):
            ic_len = 8 + ic * 3
            ic_ang = fa + math.pi + (s * 0.5) + (ic - 1) * 0.3
            ix = px + math.cos(ic_ang) * ic_len
            iy = py + math.sin(ic_ang) * ic_len
            pygame.draw.line(surface, (210, 245, 255), (int(px), int(py)), (int(ix), int(iy)), 3)

    # 6. Colossal Pneumatic Frost-Breaker Warhammer
    h_ang = fa + 0.45
    h_cos = math.cos(h_ang)
    h_sin = math.sin(h_ang)
    h_perp_x = -h_sin
    h_perp_y = h_cos
    h_base_x = cx + cos_f * 14 + perp_x * 10
    h_base_y = cy + sin_f * 14 + perp_y * 10
    h_tip_x = h_base_x + h_cos * 42
    h_tip_y = h_base_y + h_sin * 42

    pygame.draw.line(surface, (35, 45, 60), (int(h_base_x), int(h_base_y)), (int(h_tip_x), int(h_tip_y)), 8)
    m_w = 16
    m_h = 24
    m_p1 = (int(h_tip_x + h_perp_x * m_w), int(h_tip_y + h_perp_y * m_w))
    m_p2 = (int(h_tip_x - h_perp_x * m_w), int(h_tip_y - h_perp_y * m_w))
    m_p3 = (int(h_tip_x - h_cos * m_h - h_perp_x * m_w), int(h_tip_y - h_sin * m_h - h_perp_y * m_w))
    m_p4 = (int(h_tip_x - h_cos * m_h + h_perp_x * m_w), int(h_tip_y - h_sin * m_h + h_perp_y * m_w))
    pygame.draw.polygon(surface, (22, 42, 70), [m_p1, m_p2, m_p3, m_p4])
    pygame.draw.polygon(surface, (170, 235, 255), [m_p1, m_p2, m_p3, m_p4], 2)
    pygame.draw.circle(surface, (200, 245, 255), (int(h_tip_x), int(h_tip_y)), 7)

    # 7. Horned Helm & Glacial Slit Visor
    head_x = cx + cos_f * 8
    head_y = cy + sin_f * 8 - 8
    pygame.draw.circle(surface, (22, 40, 65), (int(head_x), int(head_y)), 12)
    pygame.draw.circle(surface, (160, 230, 255), (int(head_x), int(head_y)), 12, 2)
    pygame.draw.circle(surface, (120, 240, 255), (int(head_x + cos_f * 4), int(head_y + sin_f * 4)), 4)


def draw_ash_pyromancer_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Ash Pyromancer (Stage 5 Mini-Boss): Sinister bipedal incinerator zealot with charred iron greaves, flowing burnt robes, magma core, and twin flamethrowers."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 39)
    fa = getattr(boss, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0

    walk_dist = getattr(boss, "walk_distance", 0.0)
    is_moving = getattr(boss, "vel", pygame.math.Vector2(0, 0)).length() > 8.0
    stride = math.sin(walk_dist * 0.22) * 8.0 if is_moving else 0.0

    # 1. Fiery Ember Drop Shadow
    shadow_w = int(r * 2.3)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (255, 90, 20, 45), (2, 2, shadow_w - 4, shadow_h - 4))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.40)))

    # 2. Charred Iron Greaves & Bipedal Stride
    for foot_idx, step_off in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        hx = cx + int(perp_x * (side_sign * 12.0) - cos_f * 4.0)
        hy = cy + int(perp_y * (side_sign * 12.0) - sin_f * 4.0 + 8)
        bx = hx + int(cos_f * (4.0 + step_off) + perp_x * (side_sign * 4.0))
        by = hy + int(sin_f * (4.0 + step_off) + perp_y * (side_sign * 4.0) + 16)
        pygame.draw.line(surface, (25, 18, 16), (hx, hy), (bx, by), 7)
        pygame.draw.rect(surface, (18, 12, 10), (bx - 5, by - 4, 11, 8), border_radius=2)
        pygame.draw.rect(surface, (160, 40, 25), (bx - 4, by - 6, 9, 7), border_radius=2)

    # 3. Charred Robes & Obsidian Breastplate
    body_col = COLOR_WHITE if flash else (30, 20, 20)
    robe_col = (140, 32, 22)
    pygame.draw.circle(surface, robe_col, (cx, cy), int(r * 0.88))
    pygame.draw.circle(surface, body_col, (cx, cy), int(r * 0.78))

    pulse = (math.sin(ticks * 0.015) + 1) * 0.5
    magma_col = (255, int(130 + 80 * pulse), 30)
    pygame.draw.line(surface, magma_col, (cx - 8, cy - 8), (cx + 3, cy + 6), 3)
    pygame.draw.line(surface, magma_col, (cx + 8, cy - 10), (cx + 2, cy + 3), 2)
    pygame.draw.circle(surface, (255, 230, 100), (cx + 2, cy), 4)

    # 4. Twin Forearm-Mounted Industrial Flamethrowers
    for s in (-1, 1):
        hand_x = cx + cos_f * 16 + perp_x * (s * 16)
        hand_y = cy + sin_f * 16 + perp_y * (s * 16)
        tip_x = hand_x + cos_f * 22
        tip_y = hand_y + sin_f * 22

        pygame.draw.line(surface, (45, 40, 38), (int(hand_x), int(hand_y)), (int(tip_x), int(tip_y)), 7)
        pygame.draw.line(surface, COLOR_BRASS, (int(hand_x + cos_f * 4), int(hand_y + sin_f * 4)), (int(tip_x), int(tip_y)), 4)
        pilot_r = 5 + int(3 * pulse)
        pygame.draw.circle(surface, (255, 90, 20), (int(tip_x + cos_f * 4), int(tip_y + sin_f * 4)), pilot_r)
        pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(tip_x + cos_f * 2), int(tip_y + sin_f * 2)), max(2, pilot_r - 2))

    # 5. Horned Furnace Helm
    head_x = cx + cos_f * 8
    head_y = cy + sin_f * 8 - 8
    pygame.draw.circle(surface, (20, 16, 14), (int(head_x), int(head_y)), 12)
    pygame.draw.circle(surface, (255, 140, 40), (int(head_x), int(head_y)), 12, 2)
    for s in (-1, 1):
        horn_x = head_x - cos_f * 5 + perp_x * (s * 10)
        horn_y = head_y - sin_f * 5 + perp_y * (s * 10) - 7
        pygame.draw.line(surface, (40, 30, 25), (int(head_x), int(head_y)), (int(horn_x), int(horn_y)), 3)
        pygame.draw.circle(surface, magma_col, (int(horn_x), int(horn_y)), 2)
    pygame.draw.circle(surface, (255, 210, 60), (int(head_x + cos_f * 4), int(head_y + sin_f * 4)), 4)


def draw_cryo_turbine_engine_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws Cryo-Turbine Engine (Stage 4 Final Boss): Monumental Bipedal Glacial Jet-Turbine Dreadnought with hydraulic walker struts, 12 spinning blades, and freezing cryo vortex core."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 62)
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0
    phase = getattr(boss, "phase", 1)

    # 1. Monumental Frost Shadow
    shadow_w = int(r * 2.6)
    shadow_h = int(r * 1.15)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (140, 220, 255, 55), (4, 4, shadow_w - 8, shadow_h - 8))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.42)))

    # 2. Articulated Bipedal Hydraulic Walker Struts
    for side in (-1, 1):
        hx = cx + side * int(r * 0.65)
        hy = cy + 14
        kx = cx + side * int(r * 0.90)
        ky = cy + int(r * 0.45)
        fx = cx + side * int(r * 1.05)
        fy = cy + int(r * 0.60)
        pygame.draw.line(surface, (20, 35, 55), (hx, hy), (kx, ky), 9)
        pygame.draw.line(surface, (140, 220, 255), (hx, hy), (kx, ky), 4)
        pygame.draw.line(surface, (20, 35, 55), (kx, ky), (fx, fy), 8)
        pygame.draw.circle(surface, (180, 240, 255), (int(fx), int(fy)), 8)

    # 3. Dual Exhaust Cryo-Ports Blasting Freezing Vapor
    for side in (-1, 1):
        ex_x = cx + side * int(r * 0.75)
        ex_y = cy - int(r * 0.50)
        pygame.draw.circle(surface, (22, 38, 60), (ex_x, ex_y), 18)
        pygame.draw.circle(surface, (140, 225, 255), (ex_x, ex_y), 16, 3)
        pygame.draw.circle(surface, (200, 245, 255), (ex_x, ex_y), 8)

    # 4. Heavy Titanium Cowling Chassis
    hull_col = COLOR_WHITE if flash else ((50, 120, 190) if phase == 1 else (30, 160, 240))
    pygame.draw.circle(surface, (16, 26, 42), (cx, cy), r)
    pygame.draw.circle(surface, hull_col, (cx, cy), r - 5)
    pygame.draw.circle(surface, (210, 248, 255), (cx, cy), r - 5, 3)

    # 5. 12 Spinning Turbine Intake Fan Blades (Animated)
    blade_count = 12
    blade_speed = 0.015 if phase == 1 else 0.03
    rot_ang = ticks * blade_speed
    hub_r = int(r * 0.36)
    intake_r = int(r * 0.80)

    pygame.draw.circle(surface, (12, 18, 30), (cx, cy), intake_r)

    for b in range(blade_count):
        b_ang = rot_ang + (math.tau / blade_count) * b
        b_cos = math.cos(b_ang)
        b_sin = math.sin(b_ang)
        b_perp_x = -b_sin
        b_perp_y = b_cos
        
        p1 = (cx + b_cos * hub_r, cy + b_sin * hub_r)
        p2 = (cx + b_cos * intake_r + b_perp_x * 9, cy + b_sin * intake_r + b_perp_y * 9)
        p3 = (cx + b_cos * intake_r, cy + b_sin * intake_r)
        pygame.draw.polygon(surface, (100, 160, 215), [p1, p2, p3])
        pygame.draw.polygon(surface, (190, 235, 255), [p1, p2, p3], 1)

    # 6. Supercooled Azure Vortex Core
    pulse = (math.sin(ticks * 0.012) + 1) * 0.5
    core_col = (int(30 + 30 * pulse), int(210 + 45 * pulse), 255)
    pygame.draw.circle(surface, (8, 14, 25), (cx, cy), hub_r + 3)
    pygame.draw.circle(surface, core_col, (cx, cy), hub_r)
    pygame.draw.circle(surface, COLOR_WHITE, (cx, cy), int(hub_r * 0.45))


def draw_iron_leviathan_sprite(surface: pygame.Surface, screen_pos: tuple, boss):
    """Draws The Iron Leviathan (Track 5 Climax Final Boss): The ultimate monumental apocalypse locomotive juggernaut with tungsten walker legs, fortress armor, roaring magma heart, and triple revolving artillery."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = getattr(boss, "radius", 70)
    fa = getattr(boss, "facing_angle", 0.0)
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f
    ticks = pygame.time.get_ticks()
    flash = getattr(boss, "flash_timer", 0) > 0
    phase = getattr(boss, "phase", 1)

    # 1. Monumental Volcanic Drop Shadow
    shadow_w = int(r * 2.7)
    shadow_h = int(r * 1.20)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 140), (0, 0, shadow_w, shadow_h))
    pygame.draw.ellipse(shadow_surf, (255, 60, 10, 55), (4, 4, shadow_w - 8, shadow_h - 8))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.44)))

    # 2. Giant Tungsten-Plated Hydraulic Walker Legs
    stride = math.sin(ticks * 0.006) * 12.0
    for side in (-1, 1):
        hx = cx + int(perp_x * (side * 28.0) - cos_f * 8.0)
        hy = cy + int(perp_y * (side * 28.0) - sin_f * 8.0 + 16)
        kx = hx + int(cos_f * (14.0 + stride * 0.3) + perp_x * (side * 10.0))
        ky = hy + int(sin_f * (14.0 + stride * 0.3) + perp_y * (side * 10.0) + 20)
        fx = hx + int(cos_f * (8.0 + stride) + perp_x * (side * 12.0))
        fy = hy + int(sin_f * (8.0 + stride) + perp_y * (side * 12.0) + 32)

        # Huge tungsten legs
        pygame.draw.line(surface, (18, 16, 16), (hx, hy), (kx, ky), 12)
        pygame.draw.line(surface, (55, 50, 48), (hx, hy), (kx, ky), 8)
        pygame.draw.line(surface, (18, 16, 16), (kx, ky), (fx, fy), 11)
        pygame.draw.line(surface, (75, 68, 65), (kx, ky), (fx, fy), 7)
        # Giant floor-crushing foot
        pygame.draw.rect(surface, (14, 12, 12), (fx - 14, fy - 6, 28, 18), border_radius=5)
        pygame.draw.rect(surface, COLOR_BRASS_HIGHLIGHT, (fx - 12, fy - 8, 24, 14), 2, border_radius=4)

    # 3. Dreadnought Cowcatcher Prow (Grinding Steel Teeth)
    prow_tip = (int(cx + cos_f * (r + 18)), int(cy + sin_f * (r + 18)))
    prow_l = (int(cx + cos_f * (r - 10) + perp_x * 40), int(cy + sin_f * (r - 10) + perp_y * 40))
    prow_r = (int(cx + cos_f * (r - 10) - perp_x * 40), int(cy + sin_f * (r - 10) - perp_y * 40))
    pygame.draw.polygon(surface, (20, 16, 16), [prow_tip, prow_l, prow_r])
    pygame.draw.polygon(surface, COLOR_BRASS_HIGHLIGHT, [prow_tip, prow_l, prow_r], 4)
    for t_idx in (-26, 0, 26):
        t_x = cx + cos_f * (r + 6) + perp_x * t_idx
        t_y = cy + sin_f * (r + 6) + perp_y * t_idx
        pygame.draw.circle(surface, (210, 200, 190), (int(t_x), int(t_y)), 4)

    # 4. Fortress Armored Hull with Brass Rivet Bands
    hull_col = COLOR_WHITE if flash else (26, 22, 22)
    pygame.draw.circle(surface, (12, 10, 10), (cx, cy), r)
    pygame.draw.circle(surface, hull_col, (cx, cy), r - 6)
    pygame.draw.circle(surface, COLOR_BRASS, (cx, cy), r - 6, 5)
    for rv_ang in range(0, 360, 24):
        rad = math.radians(rv_ang)
        rx = cx + math.cos(rad) * (r - 11)
        ry = cy + math.sin(rad) * (r - 11)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(rx), int(ry)), 2)

    # 5. Roaring White-Hot Magma Furnace Heart
    fire_pulse = (math.sin(ticks * 0.016) + 1) * 0.5
    magma_r = int(r * 0.44)
    pygame.draw.circle(surface, (18, 10, 8), (cx, cy), magma_r + 5)
    magma_col = (255, int(100 + 90 * fire_pulse), 20)
    pygame.draw.circle(surface, magma_col, (cx, cy), magma_r)
    pygame.draw.circle(surface, (255, 235, 100), (cx, cy), int(magma_r * 0.65))
    pygame.draw.circle(surface, COLOR_WHITE, (cx, cy), int(magma_r * 0.35))
    pygame.draw.line(surface, (28, 18, 14), (cx - magma_r, cy), (cx + magma_r, cy), 4)
    pygame.draw.line(surface, (28, 18, 14), (cx, cy - magma_r), (cx, cy + magma_r), 4)

    # 6. Dorsal Triple Artillery Cannon Turret Array
    cannon_offsets = [(-22, 0.95), (0, 1.20), (22, 0.95)]
    for c_perp, c_mult in cannon_offsets:
        c_base_x = cx - cos_f * 14 + perp_x * c_perp
        c_base_y = cy - sin_f * 14 + perp_y * c_perp
        c_end_x = c_base_x + cos_f * (38 * c_mult)
        c_end_y = c_base_y + sin_f * (38 * c_mult)
        pygame.draw.line(surface, (16, 14, 14), (int(c_base_x), int(c_base_y)), (int(c_end_x), int(c_end_y)), 9)
        pygame.draw.line(surface, COLOR_STEEL_LIGHT, (int(c_base_x), int(c_base_y)), (int(c_end_x), int(c_end_y)), 4)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(c_end_x), int(c_end_y)), 6, 2)
        pygame.draw.circle(surface, (8, 6, 6), (int(c_end_x), int(c_end_y)), 4)

    # 7. Twin High-Intensity Searchlights
    for s in (-1, 1):
        light_x = cx + cos_f * (r - 6) + perp_x * (s * 28)
        light_y = cy + sin_f * (r - 6) + perp_y * (s * 28)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(light_x), int(light_y)), 9)
        pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(light_x), int(light_y)), 6)
        pygame.draw.circle(surface, COLOR_WHITE, (int(light_x), int(light_y)), 3)



