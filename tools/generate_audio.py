"""Genera una banda sonora original y efectos de audio en formato WAV."""

import math
import wave
from array import array
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "audio"
RATE = 22050


def midi(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def write_wav(name, samples):
    OUT.mkdir(parents=True, exist_ok=True)
    data = array("h")
    peak = max(1, max(abs(v) for v in samples))
    for value in samples:
        data.append(max(-32767, min(32767, int(value * 30000 / peak))))
    with wave.open(str(OUT / name), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(data.tobytes())


def soft_sine(t, frequency, attack=0.015, release=0.18):
    env = min(1.0, t / attack, (0.22 - t) / release) if t < 0.22 else 1.0
    env = max(0.0, env)
    return env * math.sin(2 * math.pi * frequency * t)


def effect(name, kind):
    duration = 0.7 if kind in ("victory", "gameover") else 0.25
    samples = []
    for i in range(int(RATE * duration)):
        t = i / RATE
        if kind == "shot":
            f = 520 - t * 1800
            value = math.sin(2 * math.pi * f * t) * math.exp(-t * 18)
        elif kind == "swing":
            value = (math.sin(2 * math.pi * (280 + t * 300) * t) +
                     0.3 * math.sin(2 * math.pi * 980 * t)) * math.exp(-t * 13)
        elif kind == "hurt":
            value = (math.sin(2 * math.pi * (95 - t * 40) * t) +
                     0.5 * math.sin(2 * math.pi * 47 * t)) * math.exp(-t * 9)
        elif kind == "enemy_dead":
            value = math.sin(2 * math.pi * (190 - t * 550) * t) * math.exp(-t * 12)
        elif kind == "pickup":
            f = 640 + t * 500
            value = (math.sin(2 * math.pi * f * t) +
                     0.45 * math.sin(2 * math.pi * f * 2 * t)) * math.exp(-t * 8)
        elif kind == "door":
            value = sum(math.sin(2 * math.pi * f * t) * math.exp(-t * 4) for f in (98, 147, 196)) * 0.25
        elif kind == "switch":
            value = (math.sin(2 * math.pi * 420 * t) * math.exp(-t * 13) +
                     math.sin(2 * math.pi * 630 * t) * math.exp(-t * 17) * 0.5)
        elif kind == "victory":
            note = [midi(n) for n in (72, 76, 79, 84)][min(3, int(t / 0.14))]
            value = math.sin(2 * math.pi * note * t) * math.exp(-((t % 0.14) * 9))
        else:
            f = 150 - t * 160
            value = (math.sin(2 * math.pi * f * t) + 0.25 * math.sin(2 * math.pi * f * 0.5 * t)) * math.exp(-t * 2)
        samples.append(value)
    write_wav("%s.wav" % kind, samples)


def track(level, name):
    bpm = (82, 74, 96, 88, 68)[level]
    beat = 60.0 / bpm
    bars = 8
    duration = bars * beat * 4
    samples = []
    scales = (
        (45, 48, 51, 53, 48, 51, 55, 58),
        (40, 43, 46, 48, 40, 43, 46, 51),
        (43, 46, 48, 50, 43, 46, 51, 55),
        (38, 41, 43, 46, 38, 41, 48, 50),
        (36, 39, 43, 46, 48, 43, 39, 34),
    )
    scale = scales[level]
    for i in range(int(RATE * duration)):
        t = i / RATE
        beat_index = int(t / beat)
        step = beat_index % len(scale)
        local = t % beat
        bar = beat_index // 4 % 2
        root = midi(scale[step])
        bass_root = midi(scale[(beat_index // 4) % len(scale)] - 12)

        pad_env = 0.8 + 0.2 * math.sin(2 * math.pi * t / (beat * 8))
        pad = (
            math.sin(2 * math.pi * root * t) +
            0.5 * math.sin(2 * math.pi * root * 1.5 * t) +
            0.25 * math.sin(2 * math.pi * root * 2.01 * t)
        ) * pad_env * 0.075

        melody_on = 1.0 - level * 0.08
        attack = min(1.0, local / 0.018)
        release = min(1.0, (beat - local) / 0.08)
        melody = math.sin(2 * math.pi * midi(scale[step] + 12) * t)
        melody += 0.28 * math.sin(2 * math.pi * midi(scale[step] + 19) * t)
        melody *= attack * release * melody_on * 0.09

        bass = math.sin(2 * math.pi * bass_root * t)
        bass += 0.22 * math.sin(2 * math.pi * bass_root * 2 * t)
        bass *= 0.12

        pulse = math.exp(-((t % (beat / 2)) * 16))
        kick = math.sin(2 * math.pi * (70 - 35 * pulse) * t) * pulse * 0.10

        hat_t = t % (beat / 2)
        noise = math.sin(1271 * t * math.pi) * math.sin(311 * t * math.pi)
        hat = noise * math.exp(-hat_t * 55) * (0.025 if level > 1 else 0.015)

        ambience = 0.008 * math.sin(2 * math.pi * (55 + bar) * t)
        value = pad + melody + bass + kick + hat + ambience
        samples.append(value)
    write_wav(name, samples)


def main():
    for kind in ("shot", "swing", "hurt", "enemy_dead", "pickup", "door", "switch", "victory", "gameover"):
        effect("%s.wav" % kind, kind)
    for level, name in enumerate(("musica_bosque.wav", "musica_catacumbas.wav",
                                  "musica_forja.wav", "musica_ceniza.wav", "musica_umbral.wav")):
        track(level, name)
    print("Generada banda sonora original de 5 temas y 9 efectos WAV.")


if __name__ == "__main__":
    main()
