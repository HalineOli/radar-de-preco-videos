import numpy as np, sys
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 44100; DUR = float(sys.argv[1]); OUT = sys.argv[2]
BPM = 118; beat = 60 / BPM; n = int(SR * DUR); t = np.arange(n) / SR
mix = np.zeros(n)
def note(f): return 440 * 2 ** ((f - 69) / 12)
def env(length, a=0.005, d=0.3):
    x = np.arange(int(SR * length)) / SR
    return np.minimum(x / a, 1) * np.exp(-x / d)
def add(sig, start, gain=1.0):
    i = int(start * SR); j = min(n, i + len(sig))
    if i < n: mix[i:j] += gain * sig[: j - i]
lp = lambda x, f: sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
hp = lambda x, f: sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)
# progressao alegre: C - G - Am - F (1 compasso cada)
prog = [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]]
bar = 4 * beat
nbars = int(DUR / bar) + 2
for b in range(nbars):
    ch = prog[b % 4]; s = b * bar
    # pad suave
    L = int(SR * bar); x = np.arange(L) / SR
    pad = sum(np.sin(2 * np.pi * note(m) * x) + 0.3 * np.sin(4 * np.pi * note(m) * x) for m in ch)
    pad *= np.minimum(x / 0.3, 1) * np.minimum((bar - x) / 0.2, 1)
    add(lp(pad, 1800), s, 0.035)
    # baixo
    for k in range(4):
        x = np.arange(int(SR * beat)) / SR
        bs = np.sin(2 * np.pi * note(ch[0] - 24) * x) * env(beat, 0.01, 0.25)
        add(bs, s + k * beat, 0.32)
    # arpejo pluck em colcheias
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for k, p in enumerate(pat):
        f = note(ch[p] + 12); x = np.arange(int(SR * beat)) / SR
        pl = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x) + 0.15 * np.sin(6 * np.pi * f * x)) * env(beat, 0.003, 0.12)
        add(pl, s + k * beat / 2, 0.09)
    for k in range(4):
        x = np.arange(int(SR * 0.35)) / SR
        kick = np.sin(2 * np.pi * (50 * x + 110 * (1 - np.exp(-x * 30)) / 30)) * np.exp(-x * 9)
        add(kick, s + k * beat, 0.55)
        if k in (1, 3):
            cl = hp(np.random.randn(int(SR * 0.2)), 1200) * env(0.2, 0.002, 0.06)
            add(cl, s + k * beat, 0.16)
        hat = hp(np.random.randn(int(SR * 0.06)), 7000) * env(0.06, 0.001, 0.02)
        add(hat, s + k * beat + beat / 2, 0.12)
mix = np.tanh(mix * 1.4) * 0.6
fade = np.ones(n); fl = int(SR * 1.2); fade[-fl:] = np.linspace(1, 0, fl); mix *= fade
wavfile.write(OUT, SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))

# efeitos: whoosh nas trocas e "pop" nos destaques
fx = np.zeros(n)
def addfx(sig, start, g):
    i = int(start * SR); j = min(n, i + len(sig)); fx[i:j] += g * sig[: j - i]
for c in [3.2, 5.2, 9.2, 11.4]:
    L = int(SR * 0.4); x = np.arange(L) / SR
    w = np.random.randn(L) * np.sin(np.pi * x / 0.4) ** 2
    w = sosfilt(butter(2, [600, 5000], "band", fs=SR, output="sos"), w)
    addfx(w, c - 0.25, 0.5)
for p in [0.15, 3.55, 3.85, 4.15, 6.35, 6.7, 7.3, 11.55, 14.1, 14.6]:
    x = np.arange(int(SR * 0.12)) / SR
    f = 600 + 900 * x / 0.12
    addfx(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 30), p, 0.35)
x = np.arange(int(SR * 0.6)) / SR   # "ding" de caixa no preco
ding = (np.sin(2 * np.pi * 1318 * x) + 0.6 * np.sin(2 * np.pi * 1976 * x)) * np.exp(-x * 6)
addfx(ding, 6.35, 0.35)
wavfile.write(OUT.replace(".wav", "_fx.wav"), SR, (np.stack([fx, fx], 1).clip(-1, 1) * 32767).astype(np.int16))
