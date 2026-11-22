"""Edit 6 Muse clips into the 60 s 'POV: Dream Worlds' Short: crossfades, captions, original music.

usage: python assemble.py [clip_dir] [out.mp4]
Looks for clip1.mp4 ... clip6.mp4. Missing clips become labelled placeholders, so this also makes a preview.
Run music.py first (writes build/music.wav).
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.join(HERE, "build")
CLIPS = sys.argv[1] if len(sys.argv) > 1 else HERE
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BUILD, "dream-worlds-pov.mp4")
W, H, FPS, SEG, XF, DUR = 1080, 1920, 30, 10.0, 0.8, 60.0
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
F_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
if not os.path.exists(F_SEMI): F_SEMI = F_BOLD
import json as _j
WORLDS = _j.load(open(os.environ["WORLDS_JSON"])) if os.environ.get("WORLDS_JSON") else ["The Floating Islands", "The Crystal Desert", "The Sky Ocean", "The Lantern Forest", "The Aurora River", "Home in the Clouds"]

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
_c = {}
def txt(s, f, size, fill=(255, 255, 255), track=0):
    k = (s, f, size, fill, track)
    if k in _c: return _c[k]
    fo = ImageFont.truetype(f, size); l, t, r, b = fo.getbbox(s); pad = 40
    im = Image.new("RGBA", (int(r - l + 2 * pad + track * len(s)), b - t + 2 * pad)); d = ImageDraw.Draw(im); x = pad - l
    if track:
        for ch in s: d.text((x, pad - t), ch, font=fo, fill=fill); x += fo.getlength(ch) + track
    else: d.text((x, pad - t), s, font=fo, fill=fill)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * .7)))
    sh.alpha_composite(im); _c[k] = sh; return sh
def put(fr, im, cx, cy, a=1.0):
    if a <= .01: return
    if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    fr.alpha_composite(im, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0), min(im.width, W - x), min(im.height, H - y)))

# ---------- 1. clips (or placeholders) -> crossfaded video track
paths, missing = [], []
os.makedirs(BUILD, exist_ok=True)
for i in range(6):
    p = os.path.join(CLIPS, f"clip{i + 1}.mp4")
    if not os.path.exists(p):
        missing.append(i + 1); p = os.path.join(BUILD, f"_ph{i + 1}.mp4"); png = p[:-4] + ".png"
        hue = [(30, 60, 90), (90, 50, 90), (20, 90, 110), (70, 60, 30), (20, 60, 70), (100, 70, 80)][i]
        im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
        for y in range(H): k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(c * (1.2 - k * .8)) for c in hue))
        im = im.convert("RGBA"); put(im, txt(f"MUSE CLIP {i + 1}", F_BOLD, 80, (200, 200, 210)), W / 2, 1150)
        put(im, txt(WORLDS[i], F_MED, 40, (200, 200, 210)), W / 2, 1240); im.convert("RGB").save(png)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-t", str(SEG), "-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", p], check=True)
    paths.append(p)
# segment lengths so the crossfaded total is exactly DUR
seg = (DUR + 5 * XF) / 6
inputs, filt = [], []
for i, p in enumerate(paths):
    inputs += ["-i", p]
    filt.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,"
                f"tpad=stop_mode=clone:stop_duration={seg:.3f},trim=duration={seg:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
prev = "v0"
for i in range(1, 6):
    off = i * (seg - XF)
    filt.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]"); prev = f"x{i}"
filt.append(f"[{prev}]fade=t=out:st={DUR - 1.2}:d=1.2:color=white[vout]")
norm = os.path.join(BUILD, "_norm.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[vout]",
                "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-t", str(DUR), norm], check=True)

# ---------- 2. captions
grad = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(grad)
for y in range(H):
    a = int(110 * (1 - y / 560)) if y < 560 else (int(90 * ((y - H * .75) / (H * .25)) ** 1.5) if y > H * .75 else 0)
    gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
starts = [i * (seg - XF) for i in range(6)]

LABEL = os.environ.get("LABEL", "AI-GENERATED")

def overlay(fr, t):
    fr.alpha_composite(grad)
    put(fr, txt(LABEL, F_MED, 24, (235, 235, 235), 3), 60 + txt(LABEL, F_MED, 24, (235, 235, 235), 3).width / 2 - 40, 200, .7)
    if t < 5.2:                                  # opening POV line
        a = min(ease((t - .3) / .6), ease((5.2 - t) / .5))
        put(fr, txt("POV: you found a road", F_BOLD, 66), W / 2, 380, a)
        put(fr, txt("that only exists in dreams", F_BOLD, 66), W / 2, 460, a)
    for i, s in enumerate(starts):               # small world title at the start of each clip
        lt = t - s - (5.4 if i == 0 else .6)
        if 0 <= lt < 3.2:
            a = min(ease(lt / .5), ease((3.2 - lt) / .6))
            put(fr, txt(f"WORLD {i + 1}", F_MED, 30, (255, 236, 200), 6), W / 2, 1560, a)
            put(fr, txt(WORLDS[i], F_SEMI, 58), W / 2, 1625, a)
    if t > 54.2:                                 # ending question
        a = ease((t - 54.2) / .6)
        put(fr, txt("Which world would you ride to?", F_BOLD, 60, (40, 40, 50) if t > 58.9 else (255, 255, 255)), W / 2, 820, a)
        put(fr, txt("Comment 1 to 6", F_MED, 46, (60, 60, 70) if t > 58.9 else (255, 236, 200)), W / 2, 905, a)

# ---------- 3. render with music
music = os.path.join(BUILD, "music.wav")
dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", norm, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", music, "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", "-t", str(DUR), OUT], stdin=subprocess.PIPE)
f = 0
while True:
    buf = dec.stdout.read(W * H * 4)
    if len(buf) < W * H * 4: break
    fr = Image.frombuffer("RGBA", (W, H), buf, "raw", "RGBA", 0, 1).copy(); overlay(fr, f / FPS)
    enc.stdin.write(fr.tobytes()); f += 1
enc.stdin.close(); enc.wait(); os.remove(norm)
print("wrote", OUT, "| placeholders:", missing or "none")
