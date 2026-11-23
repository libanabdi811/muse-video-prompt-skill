"""Original score + sound effects for Drawbridge Getaway, synced to build/events.json -> build/audio.wav"""
import json, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.join(HERE, "build")
ev = json.load(open(os.path.join(BUILD, "events.json")))
SR = 44100; DUR = ev["dur"]; N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(5)
L_, R_ = np.zeros(N), np.zeros(N)

def lp(x, fc):                      # FFT low-pass (fc may be scalar)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))
def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 - 1 / (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))
def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR); sig = sig[: max(0, N - i)]
    L_[i:i + len(sig)] += sig * gain * (1 - pan) ** .5; R_[i:i + len(sig)] += sig * gain * (1 + pan) ** .5
def env(n, a, d): e = np.exp(-np.arange(n) / SR / d); e[: int(a * SR)] *= np.linspace(0, 1, int(a * SR)); return e
def saw(f, n, ph=0): x = np.cumsum(np.full(n, f) if np.isscalar(f) else f) / SR + ph; return 2 * (x % 1) - 1

LAUNCH, LAND, GATE, BELLS, BRAKE = ev["launch"], ev["land"], ev["gate"], ev["bells"], ev["brake"]
SLOW0, SLOW1 = LAUNCH, LAND
# ---------------- music: 120 bpm A-minor synth drive (A F C G)
BPM = 120; beat = 60 / BPM
roots = [55.0, 43.65, 65.41, 49.0]; chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
def bar_of(x): return int(x / (4 * beat)) % 4
music = np.zeros(N)
# bass: driving eighths (from 0, muted during slow-mo)
for k in range(int(DUR / (beat / 2))):
    st = k * beat / 2
    if SLOW0 - .05 < st < SLOW1 or st > 15.6: continue
    n = int(beat / 2 * SR); f = roots[bar_of(st)] * (2 if k % 4 == 3 else 1)
    s = lp(saw(f, n) + .5 * saw(f * 1.005, n), 900) * env(n, .003, .12)
    add(s, st, .30 if st > 3 else .18)
# kick + clap + hats from the cut to the exterior
for k in range(int(DUR / beat)):
    st = k * beat
    if st < 3.0 - 1e-6 or SLOW0 - .05 < st < SLOW1 or st > 15.6: continue
    n = int(.35 * SR); tt = np.arange(n) / SR; kick = np.sin(2 * np.pi * (45 * tt + 90 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 9)
    add(kick, st, .75)
    if k % 2 == 1: add(hp(rng.normal(0, 1, int(.18 * SR)), 1200) * env(int(.18 * SR), .001, .05), st, .22)
for k in range(int(DUR / (beat / 2))):
    st = k * beat / 2
    if st < 1.0 or SLOW0 - .05 < st < SLOW1 or st > 15.6: continue
    add(hp(rng.normal(0, 1, int(.05 * SR)), 7000) * env(int(.05 * SR), .001, .015), st, .10, .3 if k % 2 else -.3)
# pad: whole piece, swells during slow-mo, big final chord
pad = np.zeros(N)
for b in range(int(DUR / (4 * beat)) + 1):
    st = b * 4 * beat; n = int(4 * beat * SR) + SR
    s = sum(saw(f, n, .1 * j) + saw(f * 1.004, n, .3 * j) for j, f in enumerate(chords[b % 4]))
    s = lp(s, 1400) * np.minimum(1, np.arange(n) / SR / .3) * np.minimum(1, (n - np.arange(n)) / SR / .5)
    i = int(st * SR); pad[i:i + n] += s[: max(0, N - i)][: n]
pg = np.full(N, .035); m = (t > SLOW0) & (t < SLOW1); pg[m] = .035 + .05 * np.sin(np.pi * (t[m] - SLOW0) / (SLOW1 - SLOW0))
pg[t > 15.6] = .07 * np.exp(-(t[t > 15.6] - 15.6) / 1.6)
music += pad * pg
L_ += music; R_ += music
# end sting chord at the title card
n = int(2.4 * SR); add(lp(sum(saw(f, n) for f in [110, 220, 261.6, 329.6, 440]), 2000) * env(n, .01, .9), 15.6, .12)

# ---------------- SFX
# engine: rpm follows the story (idle rumble inside, roar outside, screaming free-wheel in the air)
rpm = np.interp(t, [0, 3, 6.7, 8.4, SLOW0, SLOW0 + .3, SLOW1, SLOW1 + .2, 14, 15.6, DUR], [70, 95, 105, 120, 120, 150, 150, 80, 100, 90, 60])
eng = (saw(rpm, N) + .6 * saw(rpm * 2.01, N) + .3 * np.sin(2 * np.pi * np.cumsum(rpm * .5) / SR)) * (1 + .3 * np.sin(2 * np.pi * np.cumsum(rpm / 4) / SR))
eng = lp(eng, 700) + .15 * lp(rng.normal(0, 1, N), 300)
eg = np.interp(t, [0, 2.9, 3.0, SLOW0, SLOW0 + .2, SLOW1 - .1, SLOW1, 14.5, 15.8, DUR], [.10, .10, .22, .22, .06, .06, .20, .16, .03, 0])
L_ += eng * eg; R_ += eng * eg
# sirens: two-tone wail, behind (left), stop after the cops brake
sir = np.sin(2 * np.pi * np.cumsum(950 + 300 * np.sin(2 * np.pi * t / 1.3)) / SR)
sg = np.interp(t, [0, .5, 3, BRAKE, BRAKE + 1.5, SLOW0, SLOW1, DUR], [0, .05, .07, .08, .05, .01, .015, 0])
L_ += sir * sg * 1.2; R_ += sir * sg * .5
# bridge bells
for k in range(int((LAUNCH + .2 - BELLS) / .45) + 1):
    st = BELLS + k * .45; n = int(.9 * SR); tt = np.arange(n) / SR
    bell = (np.sin(2 * np.pi * 1180 * tt) + .5 * np.sin(2 * np.pi * 2950 * tt) + .3 * np.sin(2 * np.pi * 4100 * tt)) * np.exp(-tt * 5)
    add(bell, st, .07, .3)
# gate smash: crack + splinters
n = int(.6 * SR); add(hp(rng.normal(0, 1, n), 900) * env(n, .001, .06) + .8 * np.sin(2 * np.pi * 90 * np.arange(n) / SR) * env(n, .001, .1), GATE, .5)
# police tyre screech
n = int(1.2 * SR); tt = np.arange(n) / SR; scr = np.sin(2 * np.pi * (2300 + 200 * np.sin(2 * np.pi * 13 * tt)) * tt) * (1 + .5 * rng.normal(0, 1, n)) * env(n, .05, .5)
add(lp(scr, 4000), BRAKE, .07, -.6)
# slow-mo: wind rush + deep whoosh + heartbeat
n = int((SLOW1 - SLOW0 + .4) * SR); w = lp(rng.normal(0, 1, n), 500) * np.sin(np.pi * np.arange(n) / n) ** .7
add(w, SLOW0 - .1, .35)
for k in range(int((SLOW1 - SLOW0) / .75)):
    m_ = int(.25 * SR); tt = np.arange(m_) / SR; hb = np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 14)
    add(hb, SLOW0 + .3 + k * .75, .55); add(hb, SLOW0 + .48 + k * .75, .35)
# landing: huge impact + metal + sparks crackle
n = int(1.6 * SR); tt = np.arange(n) / SR
boom = np.sin(2 * np.pi * (38 * tt + 60 * (1 - np.exp(-tt * 12)) / 12)) * np.exp(-tt * 3.2)
crash = hp(rng.normal(0, 1, n), 300) * np.exp(-tt * 4)
clang = (np.sin(2 * np.pi * 410 * tt) + .6 * np.sin(2 * np.pi * 1130 * tt)) * np.exp(-tt * 6)
add(boom * 1.0 + crash * .35 + clang * .15, LAND, .9)
cr = np.zeros(int(1.2 * SR)); idx = rng.integers(0, len(cr) - 300, 260)
for i in idx: cr[i:i + 200] += rng.normal(0, 1, 200) * np.exp(-np.arange(200) / 30)
add(hp(cr, 2500) * np.linspace(1, 0, len(cr)), LAND + .02, .25)

mix = np.stack([L_, R_], 1); mix[: int(.02 * SR)] *= np.linspace(0, 1, int(.02 * SR))[:, None]
mix[-int(.6 * SR):] *= np.linspace(1, 0, int(.6 * SR))[:, None]
mix /= np.abs(mix).max() * 1.05
with wave.open(os.path.join(BUILD, "audio.wav"), "wb") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio ok", DUR)
