"""Procedural audio synthesizer and sound manager with safe fallbacks."""
import math
import struct
import random
import pygame

class SoundManager:
    """Generates and plays retro arcade sound effects safely."""
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        
        try:
            # Initialize mixer with 16-bit mono
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.enabled = True
            self._generate_sfx()
        except Exception as e:
            # Audio device might not be available (e.g. headless or permission restricted)
            print(f"[SoundManager] Audio initialization skipped ({e}). Running in silent mode.")
            self.enabled = False

    def _create_tone(self, freq_start: float, freq_end: float, duration: float, volume: float = 0.5, wave_type: str = "square") -> pygame.mixer.Sound:
        """Synthesize a frequency slide sound effect."""
        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        raw_bytes = bytearray()
        
        for i in range(num_samples):
            t = i / float(sample_rate)
            progress = t / duration
            # Exponential or linear frequency ramp
            current_freq = freq_start + (freq_end - freq_start) * progress
            phase = 2.0 * math.pi * current_freq * t
            
            # Waveform generation
            if wave_type == "sine":
                sample = math.sin(phase)
            elif wave_type == "square":
                sample = 1.0 if math.sin(phase) >= 0 else -1.0
            elif wave_type == "saw":
                sample = 2.0 * (t * current_freq - math.floor(t * current_freq + 0.5))
            elif wave_type == "noise":
                sample = random.uniform(-1.0, 1.0)
            else:
                sample = math.sin(phase)

            # Apply linear decay envelope to eliminate clicks
            envelope = max(0.0, 1.0 - progress)
            val = int(sample * envelope * volume * 32767)
            val = max(-32768, min(32767, val))
            raw_bytes.extend(struct.pack('<h', val))
            
        return pygame.mixer.Sound(buffer=bytes(raw_bytes))

    def _generate_sfx(self):
        """Pre-generate procedural sound effects."""
        try:
            # Laser / Rivet shoot: high pitch quick drop
            self.sounds['shoot'] = self._create_tone(880, 220, 0.08, volume=0.35, wave_type="square")
            # Shotgun blast: noisy drop
            self.sounds['shotgun'] = self._create_tone(350, 80, 0.18, volume=0.5, wave_type="noise")
            # Melee wrench swing: swoosh
            self.sounds['swing'] = self._create_tone(240, 120, 0.12, volume=0.4, wave_type="sine")
            # Impact / Hit: quick crunch
            self.sounds['hit'] = self._create_tone(180, 60, 0.09, volume=0.5, wave_type="noise")
            # Dash: airy whoosh
            self.sounds['dash'] = self._create_tone(400, 160, 0.14, volume=0.4, wave_type="saw")
            # Explosion: rumbling blast
            self.sounds['explosion'] = self._create_tone(150, 40, 0.35, volume=0.6, wave_type="noise")
            # Boon picked: bright triumphant arpeggio-like chirp
            self.sounds['boon'] = self._create_tone(523, 1046, 0.25, volume=0.45, wave_type="sine")
            # Door unlocked: metal clack
            self.sounds['door'] = self._create_tone(300, 500, 0.2, volume=0.4, wave_type="square")
            # Electric arc / Tesla: buzzy crackle
            self.sounds['zap'] = self._create_tone(700, 1200, 0.12, volume=0.4, wave_type="saw")
            # Boss telegraph alarm: sharp double beep
            self.sounds['alarm'] = self._create_tone(900, 950, 0.15, volume=0.5, wave_type="square")
        except Exception as e:
            print(f"[SoundManager] SFX generation error: {e}")

    def play(self, sound_name: str):
        """Play a cached sound effect if enabled."""
        if not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

# Global audio singleton
audio = SoundManager()
