"""Specialized high-detail sprite rendering module for Next Stop (2026).
Provides layered, animated procedural character and enemy models.
"""
import pygame
import math
import random
from src.config import (
    COLOR_WHITE, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_EMBER_ORANGE,
    COLOR_LIGHTNING_CYAN, COLOR_CRIT_YELLOW, COLOR_CARPET_RED
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
                       radius: float = 22.0):
    """Renders the rugged train stoker hero with dirty shirt, burly arms, pants, boots, and held weapon."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    
    # 1. Soft Oval Drop Shadow
    shadow_w = int(radius * 2.1)
    shadow_h = int(radius * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 95), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(radius * 0.45)))

    # Direction vectors
    aim_cos = math.cos(aim_angle)
    aim_sin = math.sin(aim_angle)
    perp_cos = -aim_sin
    perp_sin = aim_cos

    # Recoil offset on arms & weapon
    recoil = max(0.0, recoil_timer * 18.0)
    recoil_x = -aim_cos * recoil
    recoil_y = -aim_sin * recoil

    # 2. Work Boots & Animated Walk Cycle
    stride = math.sin(walk_dist * 0.22) * 8.0 if is_moving else 0.0
    left_boot_offset = stride
    right_boot_offset = -stride

    for foot_idx, offset in enumerate([left_boot_offset, right_boot_offset]):
        side_sign = -1 if foot_idx == 0 else 1
        # Position boots behind torso relative to view
        bx = cx + int(perp_cos * (side_sign * 9.0) - aim_cos * (4.0 - offset))
        by = cy + int(perp_sin * (side_sign * 9.0) - aim_sin * (4.0 - offset) + 10)
        
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

    # 6. Burly Muscular Arms Gripping Weapon
    arm_color = COLOR_WHITE if flash_timer > 0 else COLOR_STOKER_SKIN
    shadow_arm = COLOR_STOKER_SKIN_SHADOW

    # Left Shoulder & Forearm (support hand)
    l_shoulder_x = cx + perp_cos * 13.0
    l_shoulder_y = cy + perp_sin * 13.0
    l_hand_x = cx + aim_cos * 16.0 + perp_cos * 6.0 + recoil_x
    l_hand_y = cy + aim_sin * 16.0 + perp_sin * 6.0 + recoil_y

    pygame.draw.circle(surface, shadow_arm, (int(l_shoulder_x), int(l_shoulder_y)), 6)
    pygame.draw.line(surface, arm_color, (int(l_shoulder_x), int(l_shoulder_y)), (int(l_hand_x), int(l_hand_y)), 7)
    pygame.draw.circle(surface, arm_color, (int(l_hand_x), int(l_hand_y)), 4)
    # Soot smudge on left bicep
    pygame.draw.circle(surface, COLOR_SOOT, (int((l_shoulder_x + l_hand_x) / 2), int((l_shoulder_y + l_hand_y) / 2)), 2)

    # Right Shoulder & Forearm (trigger / swing hand)
    r_shoulder_x = cx - perp_cos * 13.0
    r_shoulder_y = cy - perp_sin * 13.0
    r_hand_x = cx + aim_cos * 18.0 - perp_cos * 4.0 + recoil_x
    r_hand_y = cy + aim_sin * 18.0 - perp_sin * 4.0 + recoil_y

    pygame.draw.circle(surface, shadow_arm, (int(r_shoulder_x), int(r_shoulder_y)), 6)
    pygame.draw.line(surface, arm_color, (int(r_shoulder_x), int(r_shoulder_y)), (int(r_hand_x), int(r_hand_y)), 7)
    pygame.draw.circle(surface, arm_color, (int(r_hand_x), int(r_hand_y)), 4)
    # Soot smudge on right arm
    pygame.draw.circle(surface, COLOR_SOOT, (int((r_shoulder_x + r_hand_x) / 2), int((r_shoulder_y + r_hand_y) / 2)), 2)

    # 7. Held Weapon Sprite (Held firmly in burly hands with recoil)
    wpn_base_x = cx + aim_cos * 15.0 + recoil_x
    wpn_base_y = cy + aim_sin * 15.0 + recoil_y
    draw_held_weapon(surface, (wpn_base_x, wpn_base_y), aim_angle, weapon, recoil_timer)

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
    """Draws the Scrap Boiler Imp: Spindly quadruped mechanical scrap gremlin with 4 animated legs and twin exhaust chimneys."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_windup = (getattr(enemy, "state", "") == "windup")

    # 1. Sprawled Spider-like Drop Shadow
    shadow_w = int(r * 2.4)
    shadow_h = int(r * 1.1)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 95), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.35)))

    # 2. 4 Articulated Scrap Iron Spider Legs (Scuttling crawl cycle!)
    leg_angles = [-2.1, -0.9, 0.9, 2.1]
    for leg_idx, base_ang in enumerate(leg_angles):
        step_phase = math.sin(walk_dist * 0.35 + leg_idx * 1.57) * 4.0 if not is_windup else 0.0
        ang = fa + base_ang
        # Leg root at body chassis
        lx1 = cx + math.cos(ang) * (r * 0.45)
        ly1 = cy + math.sin(ang) * (r * 0.45)
        # Knee joint raised high
        lx2 = cx + math.cos(ang) * (r * 0.85) + perp_x * (step_phase * 0.4)
        ly2 = cy + math.sin(ang) * (r * 0.85) + perp_y * (step_phase * 0.4) - 4
        # Pointed claw tip planted on deck
        lx3 = cx + math.cos(ang) * (r * 1.25) + cos_f * step_phase
        ly3 = cy + math.sin(ang) * (r * 1.25) + sin_f * step_phase + 3

        # Bent segmented iron leg
        pygame.draw.line(surface, (45, 30, 20), (int(lx1), int(ly1)), (int(lx2), int(ly2)), 3)
        pygame.draw.line(surface, (30, 20, 15), (int(lx2), int(ly2)), (int(lx3), int(ly3)), 2)
        # Iron spike foot
        pygame.draw.circle(surface, (60, 40, 28), (int(lx3), int(ly3)), 2)

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
    """Draws the Boiler Brute: Colossal ironclad juggernaut with stomping sabatons, burning coal firebox, and steam sledgehammer."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    walk_dist = getattr(enemy, "walk_distance", 0.0)
    is_moving = enemy.vel.length() > 10.0
    stride = math.sin(walk_dist * 0.16) * 6.0 if is_moving else 0.0
    is_windup = (getattr(enemy, "state", "") == "windup")

    # 1. Massive Oval Drop Shadow
    shadow_w = int(r * 2.5)
    shadow_h = int(r * 1.1)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 115), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.45)))

    # 2. Colossal Stomping Sabatons & Piston Rods
    boot_color = (35, 26, 22)
    for foot_idx, offset in enumerate([stride, -stride]):
        side_sign = -1 if foot_idx == 0 else 1
        bx = cx + int(perp_x * (side_sign * 13.0) - cos_f * (5.0 - offset))
        by = cy + int(perp_y * (side_sign * 13.0) - sin_f * (5.0 - offset) + 12)
        pygame.draw.rect(surface, (15, 12, 10), (bx - 7, by - 3, 15, 9), border_radius=3)
        pygame.draw.rect(surface, boot_color, (bx - 6, by - 6, 13, 10), border_radius=3)
        # Hydraulic piston on calf
        pygame.draw.line(surface, COLOR_BRASS, (bx - 2, by - 8), (bx - 2, by - 2), 2)

    # 3. Heavy Barrel-Chested Iron Boiler Torso
    armor_color = COLOR_WHITE if enemy.flash_timer > 0 else COLOR_BRUTE_IRON
    pygame.draw.ellipse(surface, (35, 20, 18), (cx - 18, cy - 14, 36, 28))
    pygame.draw.ellipse(surface, armor_color, (cx - 16, cy - 13, 32, 26))

    # Dual rear steam exhaust stacks
    for side in [-1, 1]:
        pipe_x = cx - cos_f * 14 + perp_x * (side * 9)
        pipe_y = cy - sin_f * 14 + perp_y * (side * 9)
        pygame.draw.circle(surface, (30, 20, 15), (int(pipe_x), int(pipe_y)), 5)
        pygame.draw.circle(surface, COLOR_BRASS, (int(pipe_x), int(pipe_y)), 5, 2)
        pygame.draw.circle(surface, (15, 12, 10), (int(pipe_x), int(pipe_y)), 3)

    # 4. Exposed Blazing Coal Firebox Ribcage
    fire_pulse = (math.sin(pygame.time.get_ticks() * (0.02 if is_windup else 0.008)) + 1) * 0.5
    fire_col = (255, int(120 + 80 * fire_pulse), 20) if is_windup else (
        int(210 + 45 * fire_pulse), int(75 + 40 * fire_pulse), 20
    )
    pygame.draw.ellipse(surface, (25, 15, 10), (cx - 10, cy - 4, 20, 16))
    pygame.draw.ellipse(surface, fire_col, (cx - 8, cy - 3, 16, 14))
    # Cast-iron grate bars over firebox
    for gx in [-4, 0, 4]:
        pygame.draw.line(surface, (25, 20, 18), (cx + gx, cy - 3), (cx + gx, cy + 10), 2)

    # Brass pressure gauge dial on chest
    pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (cx + 8, cy - 8), 4)
    pygame.draw.line(surface, (180, 40, 20), (cx + 8, cy - 8), (cx + 10, cy - 10), 1)

    # 5. Heavy Spiked Pauldron Shoulders
    p_l = (cx + perp_x * 16, cy + perp_y * 16)
    p_r = (cx - perp_x * 16, cy - perp_y * 16)
    for px, py in [p_l, p_r]:
        pygame.draw.circle(surface, (45, 28, 22), (int(px), int(py)), 10)
        pygame.draw.circle(surface, COLOR_BRASS, (int(px), int(py)), 10, 2)
        pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(px), int(py)), 4)

    # 6. Colossal Steam Piston Sledgehammer
    hammer_angle = (fa - 1.45) if is_windup else (fa + 0.35)
    reach = 22 if is_windup else 38
    h_end_x = cx + math.cos(hammer_angle) * reach
    h_end_y = cy + math.sin(hammer_angle) * reach

    # Two-handed mechanical arms gripping haft
    pygame.draw.line(surface, armor_color, (int(p_l[0]), int(p_l[1])), (int(h_end_x - math.cos(hammer_angle) * 8), int(h_end_y - math.sin(hammer_angle) * 8)), 6)
    pygame.draw.line(surface, armor_color, (int(p_r[0]), int(p_r[1])), (int(h_end_x - math.cos(hammer_angle) * 8), int(h_end_y - math.sin(hammer_angle) * 8)), 6)

    # Heavy steel hammer shaft
    pygame.draw.line(surface, (45, 48, 55), (cx, cy), (int(h_end_x), int(h_end_y)), 7)
    # Huge steel piston hammer head
    pygame.draw.circle(surface, COLOR_STEEL_MID, (int(h_end_x), int(h_end_y)), 13)
    pygame.draw.circle(surface, (255, 110, 20) if is_windup else COLOR_BRASS, (int(h_end_x), int(h_end_y)), 8)
    if is_windup:
        pygame.draw.circle(surface, COLOR_WHITE, (int(h_end_x), int(h_end_y)), 16, 2)

    # 7. Heavy Diving Helmet with 3-Bar Protective Face Cage
    helm_x = cx + cos_f * 5
    helm_y = cy + sin_f * 5 - 10
    pygame.draw.circle(surface, (40, 25, 20), (int(helm_x), int(helm_y)), 9)
    pygame.draw.circle(surface, COLOR_BRASS, (int(helm_x), int(helm_y)), 9, 2)
    # Glowing interior furnace slit
    pygame.draw.circle(surface, fire_col, (int(helm_x), int(helm_y)), 5)
    # 3-bar cage grill
    pygame.draw.line(surface, (30, 20, 15), (int(helm_x - 3), int(helm_y - 4)), (int(helm_x - 3), int(helm_y + 4)), 2)
    pygame.draw.line(surface, (30, 20, 15), (int(helm_x), int(helm_y - 4)), (int(helm_x), int(helm_y + 4)), 2)
    pygame.draw.line(surface, (30, 20, 15), (int(helm_x + 3), int(helm_y - 4)), (int(helm_x + 3), int(helm_y + 4)), 2)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)


def draw_furnace_golem_sprite(surface: pygame.Surface, screen_pos: tuple, enemy):
    """Draws the Furnace Golem: Floating volcanic basalt elemental with jagged orbiting obsidian plates and lava fissures."""
    cx, cy = int(screen_pos[0]), int(screen_pos[1])
    r = enemy.radius
    fa = enemy.facing_angle
    cos_f = math.cos(fa)
    sin_f = math.sin(fa)
    perp_x = -sin_f
    perp_y = cos_f

    # Levitation hover bobbing
    t = pygame.time.get_ticks() * 0.003
    bob_y = math.sin(t) * 3.0
    cy += int(bob_y)

    # 1. Flickering Fiery Drop Shadow
    shadow_w = int(r * 2.2)
    shadow_h = int(r * 0.95)
    shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), (0, 0, shadow_w, shadow_h))
    surface.blit(shadow_surf, (cx - shadow_w // 2, cy + int(r * 0.45) - int(bob_y)))

    # 2. Central Incandescent Molten Magma Core
    pulse = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
    lava_col = (255, int(110 + 70 * pulse), 20)
    pygame.draw.circle(surface, lava_col, (cx, cy), int(r * 0.55))
    pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (cx, cy), int(r * 0.35))

    # 3. Floating Jagged Basalt Rock Plates (asymmetrical polygonal stones)
    rock_color = COLOR_WHITE if enemy.flash_timer > 0 else COLOR_GOLEM_BASALT
    rock_dark = (30, 24, 22)

    plate_angles = [0.2, 1.3, 2.5, 3.8, 5.0]
    for p_idx, p_ang in enumerate(plate_angles):
        orbit_ang = p_ang + t * 0.4
        dist = r * 0.65 + math.sin(t + p_idx) * 2.0
        px = cx + math.cos(orbit_ang) * dist
        py = cy + math.sin(orbit_ang) * dist
        
        # Jagged triangular/diamond rock plate
        d1 = pygame.math.Vector2(math.cos(orbit_ang), math.sin(orbit_ang)) * 8
        d2 = pygame.math.Vector2(-math.sin(orbit_ang), math.cos(orbit_ang)) * 6
        pts = [
            (int(px + d1.x), int(py + d1.y)),
            (int(px + d2.x), int(py + d2.y)),
            (int(px - d1.x * 0.6), int(py - d1.y * 0.6)),
            (int(px - d2.x), int(py - d2.y))
        ]
        pygame.draw.polygon(surface, rock_dark, pts)
        pygame.draw.polygon(surface, rock_color, pts, 0)
        # Molten vein fissure on rock
        pygame.draw.line(surface, lava_col, (int(px), int(py)), (int(px + d1.x * 0.6), int(py + d1.y * 0.6)), 2)

    # 4. Floating Stony Boulder Fists
    for side in [-1, 1]:
        fist_dist = r * 0.95
        fist_x = cx + perp_x * (side * fist_dist) + cos_f * (4.0 if side == 1 else 0.0)
        fist_y = cy + perp_y * (side * fist_dist) + sin_f * (4.0 if side == 1 else 0.0)
        
        # Heavy floating stone fist
        pygame.draw.circle(surface, rock_dark, (int(fist_x), int(fist_y)), 8)
        pygame.draw.circle(surface, rock_color, (int(fist_x), int(fist_y)), 7)
        pygame.draw.circle(surface, lava_col, (int(fist_x), int(fist_y)), 3)

    # 5. Orbiting Magma Ember Droplets
    for e_idx in range(3):
        e_ang = t * 1.2 + e_idx * 2.09
        ex = cx + math.cos(e_ang) * (r * 1.1)
        ey = cy + math.sin(e_ang) * (r * 1.1)
        pygame.draw.circle(surface, COLOR_EMBER_ORANGE, (int(ex), int(ey)), 2)

    if getattr(enemy, "is_elite", False):
        draw_elite_indicator(surface, cx, cy, enemy)

