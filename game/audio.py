import sys
from pathlib import Path

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
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
                pygame.mixer.init()
            audio_dir = Path(__file__).resolve().parents[1] / "assets" / "audio"
            if not (audio_dir / "musica_bosque.wav").exists():
                from tools.generate_audio import main as generate_audio
                generate_audio()
            for name in ("shot", "swing", "hurt", "enemy_dead", "pickup", "door", "switch", "victory", "gameover"):
                path = audio_dir / ("%s.wav" % name)
                self.sounds[name] = pygame.mixer.Sound(str(path))
            for name in ("musica_bosque.wav", "musica_catacumbas.wav", "musica_forja.wav",
                         "musica_ceniza.wav", "musica_umbral.wav"):
                self.music.append(pygame.mixer.Sound(str(audio_dir / name)))
        except pygame.error as exc:
            self.available = False
            print("Audio no disponible: %s" % exc, file=sys.stderr)


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
