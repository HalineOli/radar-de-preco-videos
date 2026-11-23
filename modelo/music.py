"""Gera musica de fundo + efeitos a partir do timeline.json do render.
Uso: python3 music.py <timeline.json> <saida_musica.wav>   (gera tambem <saida>_fx.wav)"""
import numpy as np, sys, json
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
TL = json.load(open(sys.argv[1])); OUT = sys.argv[2]
SR = 44100; DUR = TL["dur"]; BPM = TL["bpm"]; TOM = TL["tom"]
rng = np.random.default_rng(BPM * 7 + TOM)
beat = 60 / BPM; n = int(SR * DUR)
mix = np.zeros(n)
def note(m): return 440 * 2 ** ((m + TOM - 69) / 12)
def env(length, a=0.005, d=0.3):
    x = np.arange(int(SR * length)) / SR
    return np.minimum(x / a, 1) * np.exp(-x / d)
def add(buf, sig, start, gain=1.0):
    i = int(start * SR); j = min(n, i + len(sig))
    if 0 <= i < n: buf[i:j] += gain * sig[: j - i]
hp = lambda x, f: sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)
lp = lambda x, f: sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
PROGS = {"A": [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]],   # I V vi IV
         "B": [[57, 60, 64, 69], [53, 57, 60, 65], [60, 64, 67, 72], [55, 59, 62, 67]],   # vi IV I V
         "C": [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]],   # I vi IV V
         "D": [[57, 60, 64, 69], [55, 59, 62, 67], [53, 57, 60, 65], [55, 59, 62, 67]],   # vi V IV V
         "E": [[53, 57, 60, 65], [60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69]]}   # IV I V vi
prog = PROGS.get(TL["estilo"], PROGS["A"])
ARPS = [[0, 1, 2, 3, 2, 1, 2, 3], [0, 2, 1, 3, 0, 2, 1, 3], [3, 2, 1, 0, 1, 2, 3, 2], [0, 1, 2, 1, 3, 2, 1, 2]]
arp = ARPS["ABCDE".index(TL["estilo"]) % len(ARPS)]
bar = 4 * beat
for b in range(int(DUR / bar) + 2):
    ch = prog[b % 4]; s = b * bar
    L = int(SR * bar); x = np.arange(L) / SR
    pad = sum(np.sin(2 * np.pi * note(m) * x) + 0.3 * np.sin(4 * np.pi * note(m) * x) for m in ch)
    pad *= np.minimum(x / 0.3, 1) * np.minimum((bar - x) / 0.2, 1)
    add(mix, lp(pad, 1800), s, 0.035)
    for k in range(4):
        x = np.arange(int(SR * beat)) / SR
        add(mix, np.sin(2 * np.pi * note(ch[0] - 24) * x) * env(beat, 0.01, 0.25), s + k * beat, 0.32)
    for k, p in enumerate(arp):
        f = note(ch[p] + 12); x = np.arange(int(SR * beat)) / SR
        pl = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x) + 0.15 * np.sin(6 * np.pi * f * x)) * env(beat, 0.003, 0.12)
        add(mix, pl, s + k * beat / 2, 0.09)
    for k in range(4):
        x = np.arange(int(SR * 0.35)) / SR
        add(mix, np.sin(2 * np.pi * (50 * x + 110 * (1 - np.exp(-x * 30)) / 30)) * np.exp(-x * 9), s + k * beat, 0.55)
        if k in (1, 3): add(mix, hp(rng.standard_normal(int(SR * 0.2)), 1200) * env(0.2, 0.002, 0.06), s + k * beat, 0.16)
        add(mix, hp(rng.standard_normal(int(SR * 0.06)), 7000) * env(0.06, 0.001, 0.02), s + k * beat + beat / 2, 0.12)
mix = np.tanh(mix * 1.4) * 0.6
fl = int(SR * 1.2); mix[-fl:] *= np.linspace(1, 0, fl)
wavfile.write(OUT, SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))

fx = np.zeros(n)
for c in TL["cortes"]:
    L = int(SR * 0.4); x = np.arange(L) / SR
    w = sosfilt(butter(2, [600, 5000], "band", fs=SR, output="sos"), rng.standard_normal(L) * np.sin(np.pi * x / 0.4) ** 2)
    add(fx, w, c - 0.25, 0.5)
for p in TL["pops"]:
    x = np.arange(int(SR * 0.12)) / SR; f = 600 + 900 * x / 0.12
    add(fx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 30), p, 0.3)
for d in TL["ding"]:
    x = np.arange(int(SR * 0.6)) / SR
    add(fx, (np.sin(2 * np.pi * 1318 * x) + 0.6 * np.sin(2 * np.pi * 1976 * x)) * np.exp(-x * 6), d, 0.35)
wavfile.write(OUT.replace(".wav", "_fx.wav"), SR, (np.stack([fx, fx], 1).clip(-1, 1) * 32767).astype(np.int16))
