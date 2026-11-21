"""Assemble 6 Muse Video segments into the 60 s GTA 6 Short, with voiceover, word-synced captions, stat cards and music.

usage: python assemble.py [clip_dir] [out.mp4]
Expects gta6-seg1.mp4 ... gta6-seg6.mp4 in clip_dir. Each clip is scaled and cropped to 1080x1920 and fitted to 10 s
(trimmed, or the last frame is held if a clip is short). The clips' own audio is mixed in quietly underneath.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = sys.argv[1] if len(sys.argv) > 1 else HERE
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "gta6-full.mp4")
VO_MIX = "/home/user/gta6/mix.wav"            # British VO + original music + SFX
TIMING = "/home/user/gta6/timing.json"
W, H, FPS, DUR, SEG = 1080, 1920, 30, 60.0, 10.0
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
WARM = (255, 226, 160)

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

# ---------- 1. normalise + concat the clips (video only), keep their audio separately
norm = os.path.join(HERE, "_norm.mp4")
inputs, filt = [], []
for i in range(6):
    p = os.path.join(CLIPS, f"gta6-seg{i+1}.mp4")
    if not os.path.exists(p): sys.exit(f"missing {p}")
    inputs += ["-i", p]
    filt.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
                f"tpad=stop_mode=clone:stop_duration={SEG},trim=duration={SEG},setpts=PTS-STARTPTS[v{i}]")
has_audio = []
for i in range(6):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                        os.path.join(CLIPS, f"gta6-seg{i+1}.mp4")], capture_output=True, text=True)
    has_audio.append(bool(r.stdout.strip()))
for i in range(6):
    if has_audio[i]:
        filt.append(f"[{i}:a]aresample=44100,apad,atrim=duration={SEG},asetpts=PTS-STARTPTS[a{i}]")
    else:
        filt.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={SEG}[a{i}]")
filt.append("".join(f"[v{i}][a{i}]" for i in range(6)) + "concat=n=6:v=1:a=1[v][a]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", norm], check=True)

# ---------- 2. overlay design (clean cinematic, no neon)
_c = {}
def font(f, s):
    k = (f, s)
    if k not in _c: _c[k] = ImageFont.truetype(f, s)
    return _c[k]

def txt(s, f, size, fill=(255, 255, 255), stroke=0, shadow=True, track=0):
    k = ("t", s, f, size, fill, stroke, shadow, track)
    if k in _c: return _c[k]
    fo = font(f, size); l, t, r, b = fo.getbbox(s, stroke_width=stroke)
    pad = 40
    im = Image.new("RGBA", (r - l + 2 * pad + track * len(s), b - t + 2 * pad))
    d = ImageDraw.Draw(im)
    if track:
        x = pad - l
        for ch in s:
            d.text((x, pad - t), ch, font=fo, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0)); x += fo.getlength(ch) + track
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
    fr.alpha_composite(im, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0), min(im.width, W - x), min(im.height, H - y)))

def fade(t, s, e, f=0.35): return min(ease((t - s) / f), ease((e - t) / f))

# lower gradient for caption legibility + top gradient for labels
grad = Image.new("RGBA", (W, H))
gd = ImageDraw.Draw(grad)
for y in range(H):
    a = 0
    if y > H * .55: a = int(150 * ((y - H * .55) / (H * .45)) ** 1.4)
    if y < 380: a = max(a, int(110 * (1 - y / 380)))
    gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))

# stat cards: (start, end, [(text, font, size, colour, dy)], source)
CARDS = [
    (0.0, 6.6, [("$3.79", F_BLACK, 230, WARM, 0), ("BILLION", F_BOLD, 120, (255, 255, 255), 175),
                ("SALES THROUGH LAUNCH DAY · ROCKSTAR ESTIMATE", F_MED, 30, (235, 235, 235), 275)], "SOURCE: ROCKSTAR GAMES / TAKE-TWO"),
    (9.07, 14.3, [("32.5M", F_BLACK, 230, WARM, 0), ("COPIES SOLD BEFORE LAUNCH", F_BOLD, 56, (255, 255, 255), 165)], "SOURCE: ROCKSTAR GAMES"),
    (16.67, 19.85, [("GTA V · 2013", F_BOLD, 64, (230, 230, 230), -40), ("~$800M", F_BLACK, 190, (255, 255, 255), 100),
                    ("DAY ONE", F_MED, 36, (230, 230, 230), 220)], "SOURCE: TAKE-TWO (2013)"),
    (20.03, 24.3, [("≈4.7×", F_BLACK, 260, WARM, 0), ("BIGGER LAUNCH", F_BOLD, 64, (255, 255, 255), 175)], None),
    (24.63, 28.2, [("13 YEARS LATER", F_BOLD, 84, (255, 255, 255), 0)], None),
    (35.09, 41.6, [("NOV 19, 2026", F_BLACK, 130, (255, 255, 255), 0), ("PS5  ·  XBOX SERIES X|S", F_BOLD, 54, WARM, 120)], None),
    (47.3, 50.45, [("PC RELEASE DATE", F_BOLD, 72, (255, 255, 255), 0), ("NOT YET ANNOUNCED", F_BLACK, 84, WARM, 105)], "AS OF NOV 21, 2026"),
    (56.2, 58.6, [("WORTH IT", F_BLACK, 150, (255, 255, 255), -90), ("or", F_MED, 60, (230, 230, 230), 25),
                  ("OVERHYPED?", F_BLACK, 128, WARM, 140)], None),
    (58.6, 60.0, [("$3.79", F_BLACK, 230, WARM, 0), ("BILLION", F_BOLD, 120, (255, 255, 255), 175)], None),
]

# word-synced captions
timing = json.load(open(TIMING)); words = []
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
            parts = [txt(w.replace("BILLION", "billion").replace("MILLION", "million"), F_BOLD, 64,
                         WARM if s <= t < e + .04 else ((255, 255, 255) if s <= t else (200, 200, 200)), 3) for w, s, e in g]
            gap = -62; tw = sum(p.width for p in parts) + gap * (len(parts) - 1); sc = min(1, 900 / tw)
            x = W / 2 - tw * sc / 2
            for p in parts: put(fr, p, x + p.width * sc / 2, 1470, 1, sc); x += (p.width + gap) * sc
            return

def overlay(fr, t):
    fr.alpha_composite(grad)
    lab = txt("AI-GENERATED FOOTAGE · NOT GAMEPLAY", F_MED, 26, (230, 230, 230), track=2)
    put(fr, lab, 60 + lab.width / 2, 215, .85)
    for s, e, lines, src in CARDS:
        if s <= t < e:
            a = fade(t, s, e) if not (s == 0.0) else min(1, ease((e - t) / .35))
            for i, (tx, f, sz, col, dy) in enumerate(lines):
                k = ease((t - s - i * .12) / .4) if s > 0 else 1
                put(fr, txt(tx, f, sz, col), W / 2, 700 + dy + 30 * (1 - k), a * k)
            if src: put(fr, txt(src, F_MED, 26, (220, 220, 220), track=2), W / 2, 1060, a * .9)
    captions(fr, t)

# ---------- 3. render: decode the normalised clip, draw overlays, encode with VO mix
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", norm, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", VO_MIX, "-i", norm, "-filter_complex", "[2:a]volume=0.22[amb];[1:a][amb]amix=inputs=2:duration=first:normalize=0[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(DUR), OUT], stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(W * H * 4)
    if len(buf) < W * H * 4: break
    fr = Image.frombuffer("RGBA", (W, H), buf, "raw", "RGBA", 0, 1).copy()
    overlay(fr, n / FPS); enc.stdin.write(fr.tobytes()); n += 1
    if n % 300 == 0: print(f"{n}/{int(DUR*FPS)}", flush=True)
enc.stdin.close(); enc.wait(); os.remove(norm)
print("wrote", OUT)
