import array
import math
import sys

import pygame


class AudioManager:
    def __init__(self, volume=0.45):
        self.volume = max(0.0, min(1.0, volume))
        self.available = True
        self.sounds = {}
        self.music = []
        self.music_channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.sounds = {name: self._tone(freq, 0.12 if name not in ("victory", "gameover") else 0.45)
                           for name, freq in {
                               "shot": 740, "swing": 310, "hurt": 165, "enemy_dead": 480,
                               "pickup": 920, "door": 620, "switch": 540, "victory": 880, "gameover": 120,
                           }.items()}
            for level in range(5):
                self.music.append(self._melody(level))
        except pygame.error as exc:
            self.available = False
            print("Audio no disponible: %s" % exc, file=sys.stderr)

    def _tone(self, frequency, duration):
        sample_rate = 22050
        samples = array.array("h")
        for i in range(round(sample_rate * duration)):
            envelope = max(0.0, 1.0 - i / (sample_rate * duration))
            samples.append(int(8000 * envelope * math.sin(2 * math.pi * frequency * i / sample_rate)))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _melody(self, level):
        sample_rate = 22050
        notes = (110, 130, 146, 98, 123)[level]
        samples = array.array("h")
        duration = 1.8
        for i in range(round(sample_rate * duration)):
            t = i / sample_rate
            envelope = min(1.0, t * 5, (duration - t) * 5)
            wave = math.sin(2 * math.pi * notes * t) + 0.35 * math.sin(2 * math.pi * notes * 1.5 * t)
            samples.append(int(1500 * max(0.0, envelope) * wave))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def set_volume(self, value):
        self.volume = max(0.0, min(1.0, value))
        if self.available:
            pygame.mixer.music.set_volume(self.volume * 0.35)
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
            for sound in self.music:
                sound.set_volume(self.volume * 0.35)

    def play(self, name):
        if self.available and name in self.sounds:
            self.sounds[name].play()

    def play_level(self, number):
        if self.available:
            if self.music_channel:
                self.music_channel.stop()
            self.music[number - 1].set_volume(self.volume * 0.35)
            self.music_channel = self.music[number - 1].play(loops=-1)
