"""Original dreamy 'slowed' ambient track, 60 s, generated in code (no samples, royalty-free) -> build/music.wav"""
import os, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build"); os.makedirs(B, exist_ok=True)
SR = 44100; DUR = 60.0; N = int(SR * DUR); rng = np.random.default_rng(21)
BPM = 72; BT = 60 / BPM; BAR = 4 * BT
def note(m): return 440 * 2 ** ((m - 69) / 12)
def add(buf, t, sig, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    s = sig[:N - i] * g; buf[i:i + len(s), 0] += s * np.sqrt(.5 * (1 - pan)); buf[i:i + len(s), 1] += s * np.sqrt(.5 * (1 + pan))
def adsr(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR); e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
# Fmaj7 - Am7 - Dm9 - Bbmaj7 (warm, wistful)
prog = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 57, 60, 64, 65], [46, 53, 57, 62]]
dry = np.zeros((N, 2)); verb_in = np.zeros((N, 2))
nb = int(DUR / BAR) + 1
def sec(t): return 0 if t < 8 else 1 if t < 24 else 2 if t < 44 else 3 if t < 54 else 4
for b in range(nb):
    t = b * BAR; ch = prog[b % 4]; s = sec(t)
    n = int(BAR * SR * 1.15); tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * note(m) * tt * (1 + d)) for m in ch for d in (-.003, .003)) / (2 * len(ch))
    pad *= adsr(n, 1.2, 1.0) * (1 + .15 * np.sin(2 * np.pi * .25 * tt))
    add(verb_in, t, pad, .22); add(dry, t, pad, .10)
    if s >= 1:   # sub bass
        n2 = int(BAR * SR); tt2 = np.arange(n2) / SR
        add(dry, t, np.sin(2 * np.pi * note(ch[0] - 12) * tt2) * adsr(n2, .05, .6), .28)
    if s in (1, 2, 3):  # soft kick + snap, half-time
        for k in range(4):
            tk = t + k * BT
            if k in (0, 2) or (s >= 2 and k == 3 and b % 2):
                nk = int(.5 * SR); tk_ = np.arange(nk) / SR; f = 45 + 70 * np.exp(-tk_ * 25)
                add(dry, tk, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk_ * 6), .45)
            if k == 2 and s >= 2:
                ns = int(.25 * SR); x = rng.standard_normal(ns) * np.exp(-np.arange(ns) / SR * 25)
                add(dry, tk, x, .08, .1); add(verb_in, tk, x, .10)
        for h in range(8):
            nh = int(.04 * SR); x = np.diff(np.concatenate([[0], rng.standard_normal(nh)])) * np.exp(-np.arange(nh) / SR * 90)
            add(dry, t + h * BT / 2, x, .05 if h % 2 else .03, .35)
# soft bell-piano melody (pentatonic around F), sparse, in sections 1-3
mel = [72, 69, 67, 69, 72, 74, 72, 69, 65, 67, 69, 67, 64, 65, 67, 72]
i = 0; t = 8.0
while t < 54:
    if sec(t) in (1, 2, 3) and rng.random() < .75:
        m = mel[i % len(mel)]; n = int(2.2 * SR); tt = np.arange(n) / SR
        tone = (np.sin(2 * np.pi * note(m) * tt) + .35 * np.sin(2 * np.pi * note(m) * 2 * tt) + .12 * np.sin(2 * np.pi * note(m) * 3.01 * tt)) * np.exp(-tt * 2.2) * np.minimum(tt / .005, 1)
        p = rng.uniform(-.4, .4); add(dry, t, tone, .10, p); add(verb_in, t, tone, .16, p)
        i += 1
    t += BT * (1 if rng.random() < .7 else 2)
# airy noise swell into the ending, then vinyl-style crackle throughout
n = int(6 * SR); tt = np.arange(n) / SR
sw = np.convolve(rng.standard_normal(n), np.ones(30) / 30, 'same') * (tt / 6) ** 2
add(verb_in, 48, sw, .15)
crackle = np.zeros(N); idx = rng.integers(0, N, 900); crackle[idx] = rng.uniform(-.25, .25, 900)
dry[:, 0] += crackle * .25; dry[:, 1] += np.roll(crackle, 300) * .25
# big soft reverb (convolution with decaying noise)
L = int(4.5 * SR); ir_t = np.arange(L) / SR
def ir(seed): r = np.random.default_rng(seed).standard_normal(L) * np.exp(-ir_t * 1.4); return np.convolve(r, np.ones(12) / 12, 'same') / 60
wet = np.stack([np.fft.irfft(np.fft.rfft(verb_in[:, c], 2 * N) * np.fft.rfft(ir(c + 3), 2 * N))[:N] for c in range(2)], 1)
mix = dry + wet
# warm 'slowed' tone: gentle low-pass via moving average
mix = np.stack([np.convolve(mix[:, c], np.ones(6) / 6, 'same') for c in range(2)], 1)
fi, fo = int(2.5 * SR), int(5 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = np.tanh(mix * 1.4) / np.tanh(1.4); mix /= np.max(np.abs(mix)) / .9
sf.write(os.path.join(B, "music.wav"), mix, SR); print("ok")
