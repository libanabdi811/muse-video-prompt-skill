"""Original procedural music + SFX (no samples, royalty-free), cut to the voiceover. -> build/mix.wav"""
import json, os, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build")
SR = 44100; DUR = 60.0; N = int(SR * DUR); rng = np.random.default_rng(11)
mus = np.zeros((N, 2)); sfx = np.zeros((N, 2))
timing = json.load(open(os.path.join(B, "timing.json")))
starts = {}
for x in timing: starts.setdefault(x["scene"], x["start"])
order = ["hook", "n5", "n4", "n3", "n2", "n1", "cta"]
st = [starts[s] for s in order]
def scene_at(t):
    i = 0
    for k, s in enumerate(st):
        if t >= s - 0.3: i = k
    return i
def add(buf, t, sig, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    s = sig[:N - i] * g
    buf[i:i + len(s), 0] += s * np.sqrt(.5 * (1 - pan)); buf[i:i + len(s), 1] += s * np.sqrt(.5 * (1 + pan))
def env(n, a=.005, d=.2): t = np.arange(n) / SR; return np.minimum(t / a, 1) * np.exp(-t / d)
def kick():
    n = int(.45 * SR); t = np.arange(n) / SR; f = 48 + 100 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
def clap():
    n = int(.22 * SR); t = np.arange(n) / SR; x = rng.standard_normal(n)
    return x * (np.exp(-t * 22) + .5 * np.exp(-np.maximum(t - .012, 0) * 30) * (t > .012))
def hat(o=False):
    n = int((.16 if o else .045) * SR); x = np.diff(np.concatenate([[0], rng.standard_normal(n)]))
    return x * np.exp(-np.arange(n) / SR * (16 if o else 75)) * .3
def tone(f, n, h=6): t = np.arange(n) / SR; return sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 for k in range(1, h))
def note(m): return 440 * 2 ** ((m - 69) / 12)
BPM = 100; Bt = 60 / BPM
prog = [(50, [62, 65, 69]), (46, [58, 62, 65]), (53, [60, 65, 69]), (48, [60, 64, 67])]  # Dm Bb F C (laid-back Florida evening)
for b in range(int(DUR / Bt) + 1):
    t = b * Bt; s = scene_at(t); root, ch = prog[(b // 4) % 4]
    lvl = [0, 1, 1, 2, 2, 3, 2][s]          # intensity grows toward #1
    if t > 59.2: continue
    if lvl >= 1 or b % 2 == 0: add(mus, t, kick(), .85 if lvl else .5)
    if lvl >= 1 and b % 4 in (1, 3): add(mus, t, clap(), .32, .1)
    for h in range(2 if lvl < 2 else 4):
        add(mus, t + h * Bt / (2 if lvl < 2 else 4), hat(h % 2 == 1 and lvl >= 2), .45, .3)
    for e in range(2):
        n = int(Bt / 2 * SR * .85); tt = np.arange(n) / SR
        add(mus, t + e * Bt / 2, np.tanh(2.2 * np.sin(2 * np.pi * note(root - 12) * tt)) * env(n, .005, .22), .33)
    if b % 4 == 0:
        n = int(4 * Bt * SR); tt = np.arange(n) / SR
        pad = sum(tone(note(m), n) for m in ch) / 3; pad = np.convolve(pad, np.ones(60) / 60, 'same')
        add(mus, t, pad * np.minimum(tt / .5, 1) * np.minimum((4 * Bt - tt) / .3, 1), .11, -.2)
    if lvl >= 2:  # plucky arp
        for a in range(4):
            n = int(Bt / 4 * SR)
            add(mus, t + a * Bt / 4, tone(note(ch[(a + b) % 3] + 12), n, 4) * env(n, .002, .07), .05 if lvl == 2 else .07, .4 if a % 2 else -.4)
def boom():
    n = int(1.4 * SR); t = np.arange(n) / SR; f = 32 + 80 * np.exp(-t * 9)
    return np.tanh(2.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)) + rng.standard_normal(n) * np.exp(-t * 25) * .5
def whoosh(L=.5):
    n = int(L * SR); t = np.arange(n) / SR; x = np.convolve(rng.standard_normal(n), np.ones(8) / 8, 'same'); return x * np.sin(np.pi * t / L) ** 2 * .6
def riser(L=1.6):
    n = int(L * SR); tt = np.arange(n) / SR; f = 250 + 1600 * (tt / L) ** 2
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .3 + rng.standard_normal(n) * .25 * (tt / L)) * (tt / L) ** 1.5
add(sfx, 0.0, boom(), .9)
for s in st[1:]:
    add(sfx, s - .55, whoosh(), .6); add(sfx, s - .05, boom(), .75)
add(sfx, st[5] - 1.7, riser(), .4)  # build into #1
# mix + duck under the voice
v, vsr = sf.read(os.path.join(B, "voice.wav")); idx = (np.arange(int(len(v) * SR / vsr)) * vsr / SR).astype(int); v = v[idx]
voice = np.zeros(N); voice[:min(N, len(v))] = v[:N]
ev = np.convolve(np.abs(voice), np.ones(4410) / 4410, 'same'); duck = 1 - .45 * np.clip(ev / .03, 0, 1)
mix = mus * duck[:, None] * .55 + sfx * .55 + voice[:, None] * 1.25
mix[-int(.8 * SR):] *= np.linspace(1, 0, int(.8 * SR))[:, None]
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix /= np.max(np.abs(mix)) / .95
sf.write(os.path.join(B, "mix.wav"), mix, SR); print("ok")
