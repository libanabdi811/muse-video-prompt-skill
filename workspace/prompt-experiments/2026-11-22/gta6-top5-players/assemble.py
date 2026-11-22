"""Build the 60 s '5 Types of GTA 6 Players' Short from 7 Muse clips + British VO + captions + cards + music.

usage: python assemble.py [clip_dir] [out.mp4]
Looks for clip1.mp4 ... clip7.mp4 in clip_dir. Any missing clip is replaced by a labelled placeholder, so the
same command makes a timing preview before the Muse clips exist.
Needs build/mix.wav and build/timing.json (run tts.py then music.py first).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.join(HERE, "build")
CLIPS = sys.argv[1] if len(sys.argv) > 1 else HERE
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BUILD, "gta6-top5-players.mp4")
W, H, FPS, DUR = 1080, 1920, 30, 60.0
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
WARM = (255, 226, 160); WHITE = (255, 255, 255)

script = json.load(open(os.path.join(HERE, "script.json")))
timing = json.load(open(os.path.join(BUILD, "timing.json")))
start = {}
for x in timing: start.setdefault(x["scene"], x["start"])
cuts = [0.0] + [start[s["scene"]] - 0.3 for s in script[1:]] + [DUR]
segs = [(cuts[i], cuts[i + 1]) for i in range(len(script))]

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

_c = {}
def font(f, s):
    if (f, s) not in _c: _c[(f, s)] = ImageFont.truetype(f, s)
    return _c[(f, s)]

def txt(s, f, size, fill=WHITE, stroke=0, shadow=True, track=0):
    k = ("t", s, f, size, fill, stroke, shadow, track)
    if k in _c: return _c[k]
    fo = font(f, size); l, t, r, b = fo.getbbox(s, stroke_width=stroke); pad = 40
    im = Image.new("RGBA", (int(r - l + 2 * pad + track * len(s)), b - t + 2 * pad)); d = ImageDraw.Draw(im)
    if track:
        x = pad - l
        for ch in s: d.text((x, pad - t), ch, font=fo, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0)); x += fo.getlength(ch) + track
    else:
        d.text((pad - l, pad - t), s, font=fo, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * .75)))
        sh.alpha_composite(im); im = sh
    _c[k] = im; return im

def put(fr, im, cx, cy, a=1.0, s=1.0):
    if a <= 0.01: return
    if s != 1.0: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if x >= W or y >= H or x + im.width <= 0 or y + im.height <= 0: return
    fr.alpha_composite(im, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0), min(im.width, W - x), min(im.height, H - y)))

# ---------- 1. placeholders for missing clips, then fit + concat
def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

def has_audio(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", p], capture_output=True, text=True)
    return bool(r.stdout.strip())

paths, missing = [], []
for i, sc in enumerate(script):
    p = os.path.join(CLIPS, f"clip{i + 1}.mp4")
    if not os.path.exists(p):
        missing.append(i + 1); p = os.path.join(BUILD, f"_ph{i + 1}.mp4")
        im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
        for y in range(H): d.line([(0, y), (W, y)], fill=(18 + y // 90, 20 + y // 110, 28 + y // 70))
        im = im.convert("RGBA")
        put(im, txt(f"MUSE CLIP {i + 1}", F_BLACK, 90, (90, 96, 110), shadow=False), W / 2, 1180)
        put(im, txt("placeholder: footage goes here", F_MED, 38, (90, 96, 110), shadow=False), W / 2, 1270)
        png = os.path.join(BUILD, f"_ph{i + 1}.png"); im.convert("RGB").save(png)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-t", "10", "-r", str(FPS),
                        "-pix_fmt", "yuv420p", "-c:v", "libx264", p], check=True)
    paths.append(p)

inputs, filt = [], []
for i, p in enumerate(paths):
    need = segs[i][1] - segs[i][0]; have = probe(p) or need
    slow = min(max(need / have, 1.0), 1.15)          # stretch short clips up to 15 %, then hold the last frame
    inputs += ["-i", p]
    filt.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts={slow:.4f}*(PTS-STARTPTS),"
                f"fps={FPS},setsar=1,tpad=stop_mode=clone:stop_duration={need:.3f},trim=duration={need:.3f},setpts=PTS-STARTPTS[v{i}]")
    if has_audio(p):
        filt.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=duration={need:.3f},asetpts=PTS-STARTPTS[a{i}]")
    else:
        filt.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={need:.3f}[a{i}]")
n = len(paths)
filt.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
norm = os.path.join(BUILD, "_norm.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", norm], check=True)

# ---------- 2. overlay design (clean cinematic, no neon)
grad = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(grad)
for y in range(H):
    a = int(150 * ((y - H * .55) / (H * .45)) ** 1.4) if y > H * .55 else 0
    if y < 420: a = max(a, int(120 * (1 - y / 420)))
    gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))

words = []
for ln in timing:
    ws = ln["text"].split(); tot = sum(len(w) + 2 for w in ws); t = ln["start"]
    for w in ws:
        d = (ln["end"] - ln["start"]) * (len(w) + 2) / tot; words.append((w, t, t + d)); t += d
groups, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) >= 4 or w[0][-1] in ",.?!" or len(" ".join(x[0] for x in cur)) > 20: groups.append(cur); cur = []
if cur: groups.append(cur)

def captions(fr, t):
    for g in groups:
        if g[0][1] - .02 <= t < g[-1][2] + .1:
            parts = [txt(w, F_BOLD, 64, WARM if s <= t < e + .04 else (WHITE if s <= t else (200, 200, 200)), 3) for w, s, e in g]
            gap = -62; tw = sum(p.width for p in parts) + gap * (len(parts) - 1); sc = min(1, 900 / tw); x = W / 2 - tw * sc / 2
            for p in parts: put(fr, p, x + p.width * sc / 2, 1470, 1, sc); x += (p.width + gap) * sc
            return

def overlay(fr, t):
    fr.alpha_composite(grad)
    lab = txt("AI-GENERATED FOOTAGE · NOT GAMEPLAY", F_MED, 26, (230, 230, 230), track=2)
    put(fr, lab, 60 + lab.width / 2, 215, .85)
    for i, sc in enumerate(script):
        s0, s1 = segs[i]
        if not (s0 <= t < s1): continue
        top, sub = sc["card"]; lt = t - s0; out = min(1, ease((s1 - t) / .3)) if i < len(script) - 1 else 1
        if sc["scene"] in ("hook", "cta"):
            k1, k2 = ease(lt / .45), ease((lt - .15) / .45)
            put(fr, txt(top, F_BOLD, 96, WHITE), W / 2, 640 + 30 * (1 - k1), k1 * out)
            put(fr, txt(sub, F_BLACK, 132 if sc["scene"] == "hook" else 150, WARM), W / 2, 780 + 30 * (1 - k2), k2 * out)
            if sc["scene"] == "cta" and lt > .6:
                k3 = ease((lt - .6) / .45); put(fr, txt("COMMENT YOUR NUMBER", F_BOLD, 52, WHITE), W / 2, 930 + 20 * (1 - k3), k3)
        else:
            big = 1 - ease((lt - 2.4) / .5)          # big card for ~2.6 s, then a small badge stays top-left
            if big > 0.01:
                pop = 1 + .25 * (1 - ease(lt / .35))
                put(fr, txt(top, F_BLACK, 300, WARM), W / 2, 700, big * min(1, lt / .15) , pop)
                k = ease((lt - .15) / .4); put(fr, txt(sub, F_BLACK, 96, WHITE), W / 2, 900 + 25 * (1 - k), k * big)
            if lt > 2.4:
                b = ease((lt - 2.4) / .5) * out
                badge = txt(f"{top}  {sub}", F_BOLD, 40, WARM, track=1); put(fr, badge, 60 + badge.width / 2 - 40, 290, b)
    captions(fr, t)

# ---------- 3. render
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", norm, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", os.path.join(BUILD, "mix.wav"), "-i", norm,
                        "-filter_complex", "[2:a]volume=0.22[amb];[1:a][amb]amix=inputs=2:duration=first:normalize=0[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(DUR), OUT], stdin=subprocess.PIPE)
f = 0
while True:
    buf = dec.stdout.read(W * H * 4)
    if len(buf) < W * H * 4: break
    fr = Image.frombuffer("RGBA", (W, H), buf, "raw", "RGBA", 0, 1).copy()
    overlay(fr, f / FPS); enc.stdin.write(fr.tobytes()); f += 1
    if f % 300 == 0: print(f"{f}/{int(DUR * FPS)}", flush=True)
enc.stdin.close(); enc.wait(); os.remove(norm)
print("wrote", OUT, "| placeholders for clips:", missing or "none")
