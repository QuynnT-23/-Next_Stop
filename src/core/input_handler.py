"""Input handling system supporting Spacebar attacks, double-tap directional dashes, and mouse precision."""
import pygame
import time

class InputHandler:
    """Aggregates and normalizes keyboard and mouse events with double-tap dash support."""
    DOUBLE_TAP_THRESHOLD = 0.28  # Max seconds between taps to trigger a dash

    def __init__(self):
        self.move_dir = pygame.math.Vector2(0, 0)
        self.mouse_pos = (0, 0)
        self.mouse_world_pos = pygame.math.Vector2(0, 0)
        
        # State flags
        self.attack_held = False
        self.attack_pressed = False
        self.dash_pressed = False
        self.dash_dir_override = None  # Vector2 if triggered by double-tap
        self.interact_pressed = False
        self.pause_pressed = False
        
        # Double-tap tracking: key -> last_press_timestamp
        self.last_key_press_time = {}
        
        # Directional mapping for double-tap dashing
        self.dir_key_vectors = {
            pygame.K_w: pygame.math.Vector2(0, -1),
            pygame.K_UP: pygame.math.Vector2(0, -1),
            pygame.K_s: pygame.math.Vector2(0, 1),
            pygame.K_DOWN: pygame.math.Vector2(0, 1),
            pygame.K_a: pygame.math.Vector2(-1, 0),
            pygame.K_LEFT: pygame.math.Vector2(-1, 0),
            pygame.K_d: pygame.math.Vector2(1, 0),
            pygame.K_RIGHT: pygame.math.Vector2(1, 0),
        }

        # Numeric keys for boon selection (1, 2, 3)
        self.num_keys_pressed = []

    def reset_frame_triggers(self):
        """Clear triggers that should only fire once per press."""
        self.attack_pressed = False
        self.dash_pressed = False
        self.dash_dir_override = None
        self.interact_pressed = False
        self.pause_pressed = False
        self.num_keys_pressed.clear()

    def process_events(self, events: list[pygame.event.Event], camera=None):
        """Process pygame events and update input states."""
        self.reset_frame_triggers()
        self.mouse_pos = pygame.mouse.get_pos()
        if camera:
            self.mouse_world_pos = camera.screen_to_world(self.mouse_pos)

        now = time.time()

        for event in events:
            if event.type == pygame.KEYDOWN:
                # 1. Spacebar = Attack!
                if event.key == pygame.K_SPACE:
                    self.attack_pressed = True
                    self.attack_held = True

                # 2. Shift = Dash fallback
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.dash_pressed = True

                # 3. Double-tap directional keys (WASD / Arrows) to Dash!
                elif event.key in self.dir_key_vectors:
                    last_time = self.last_key_press_time.get(event.key, 0)
                    if (now - last_time) <= self.DOUBLE_TAP_THRESHOLD:
                        # Double tap detected!
                        self.dash_pressed = True
                        self.dash_dir_override = self.dir_key_vectors[event.key]
                        # Reset so triple tap doesn't instantly dash again
                        self.last_key_press_time[event.key] = 0
                    else:
                        self.last_key_press_time[event.key] = now

                # 4. Interact & Pause
                elif event.key == pygame.K_e:
                    self.interact_pressed = True
                elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.pause_pressed = True

                # 5. Number keys
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self.num_keys_pressed.append(1)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.num_keys_pressed.append(2)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.num_keys_pressed.append(3)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.attack_held = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click also attacks
                    self.attack_pressed = True
                    self.attack_held = True
                elif event.button == 3:  # Right click also dashes
                    self.dash_pressed = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # Only release attack_held if space isn't still pressed
                    keys = pygame.key.get_pressed()
                    if not keys[pygame.K_SPACE]:
                        self.attack_held = False

        # Continuous keys for movement (WASD + Arrow keys)
        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        self.move_dir = pygame.math.Vector2(dx, dy)
        if self.move_dir.length_squared() > 0:
            self.move_dir = self.move_dir.normalize()
