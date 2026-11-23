"""Drawbridge Getaway: a fully code-animated 2D short (9:16, ~18 s), with no AI video needed.

usage: python3 animate.py [out.mp4]
       PREVIEW=1.5,5,9.5,12.5 python3 animate.py      -> writes preview PNGs only
Writes build/frames.mp4 (picture) and build/audio.wav (score + SFX, made by sound.py),
then muxes them into the output.
"""
import math, os, subprocess, sys, json, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 24
HERE = os.path.dirname(os.path.abspath(__file__)); BUILD = os.path.join(HERE, "build"); os.makedirs(BUILD, exist_ok=True)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BUILD, "drawbridge_getaway.mp4")
PREVIEW = [float(x) for x in os.environ["PREVIEW"].split(",")] if os.environ.get("PREVIEW") else None
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FBL = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

CORAL, CORAL_D, CORAL_L = (255, 112, 98), (190, 66, 72), (255, 168, 140)
CREAM, GOLD, TEAL_D = (255, 236, 205), (255, 200, 110), (16, 46, 62)
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- timeline (film seconds)
T_INT = 3.0          # interior shot length
COUNT_END = 6.75     # countdown hits 0 -> bells + bridge starts lifting
END_CARD = 15.6
DUR = 18.0
# world (exterior) clock starts at T_INT. car speed / bridge geometry
V0, L, G = 1500.0, 780.0, 2600.0
ROAD = 1180.0
XB = V0 * 5.0                     # left leaf pivot (car reaches it at world 5.0 s)
XR = XB + 2 * L                   # right leaf pivot
XG = XB - 260.0                   # gate post
TR = COUNT_END - T_INT + 0.40     # world time leaves start rising
RATE, RATIO, THMAX = 26.0, 0.5, 44.0
def thL(tau): return min(THMAX, max(0.0, (tau - TR) * RATE))
def thR(tau): return thL(tau) * RATIO

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def eout(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

# ---------------------------------------------------------------- simulate the world clock per film frame
class Car: pass
def simulate():
    """Return per-frame dicts (film frames from T_INT to DUR) + event list."""
    frames, events = [], {}
    tau, x, y, ang, vx, vy, mode, s = 0.0, 0.0, ROAD, 0.0, V0, 0.0, "road", 0.0
    wheel = 0.0
    launch_tau = land_tau = None
    parts, smoke, debris = [], [], []
    p = [{"x": -640.0, "v": V0, "stop": XG - 330}, {"x": -1280.0, "v": V0, "stop": XG - 980}]
    gate_hit = None
    t = T_INT; shake = 0.0
    sub = 8
    while t < DUR + 1e-6:
        # slow motion while airborne (smooth ramps)
        if launch_tau is not None and land_tau is None: rate = 0.30
        elif land_tau is not None: rate = 0.30 + 0.70 * ease((tau - land_tau) / 0.25)
        else: rate = 1.0
        dtau = rate / FPS
        for _ in range(sub):
            d = dtau / sub; tau += d
            if mode == "road":
                x += vx * d; y = ROAD; ang = 0.0
                if x >= XB: mode, s = "leafL", x - XB
            elif mode == "leafL":
                s += V0 * 0.97 * d; a = math.radians(thL(tau))
                x = XB + s * math.cos(a); y = ROAD - s * math.sin(a); ang = thL(tau)
                if s >= L:
                    mode = "air"; launch_tau = tau; sp = V0 * 0.97
                    vx, vy = sp * math.cos(a), -sp * math.sin(a); events["launch"] = t
                    ang0 = ang
            elif mode == "air":
                x += vx * d; vy += G * d; y += vy * d
                k = (tau - launch_tau) / 1.14; ang = ang0 * (1 - ease(k)) - 6 * math.sin(math.pi * min(k, 1))
                if x > XR and y >= ROAD:
                    y = ROAD; mode = "road2"; land_tau = tau; vx = 1150.0; events["land"] = t; shake = 1.0
                    for i in range(70):
                        parts.append([x + rng.uniform(-200, 220), ROAD - 4, rng.uniform(-200, 1400), rng.uniform(-900, -150), rng.uniform(.35, .9), 0.0])
                    for i in range(14):
                        smoke.append([x + rng.uniform(-260, 260), ROAD - 20, rng.uniform(-120, 120), rng.uniform(-90, -30), 0.0, rng.uniform(1.2, 2.0), rng.uniform(40, 80)])
            elif mode == "road2":
                x += vx * d; y = ROAD; ang = 0.0
                ang = -3.0 * math.exp(-(tau - land_tau) * 6) * math.sin((tau - land_tau) * 30)
                if rng.random() < 0.5 and tau - land_tau < 0.6:
                    parts.append([x - 160 + rng.uniform(-30, 30), ROAD - 4, rng.uniform(-600, 100), rng.uniform(-500, -100), rng.uniform(.2, .5), 0.0])
            wheel += (vx if mode != "air" else 1900) * d / 44.0
            # gate smash
            if gate_hit is None and x + 250 >= XG and tau > 3.6:
                gate_hit = tau; events["gate"] = t
                for k in range(2):
                    debris.append({"x": XG - 80 - k * 150, "y": ROAD - 72, "vx": 1300 + k * 300, "vy": -700 - k * 250, "a": 0.0, "va": 700 + k * 300, "len": 150})
                for i in range(25):
                    parts.append([XG, ROAD - 70, rng.uniform(200, 1500), rng.uniform(-800, -100), rng.uniform(.2, .5), 1.0])
            # police
            for q in p:
                brake_at = q["stop"] - V0 ** 2 / (2 * 3000)
                if q["x"] < brake_at: q["x"] += q["v"] * d
                elif q["v"] > 0:
                    q["v"] = max(0.0, q["v"] - 3000 * d); q["x"] += q["v"] * d
                    if not q.get("sm") and q["v"] < 1300:
                        q["sm"] = 1; events.setdefault("brake", t)
                        for i in range(6): smoke.append([q["x"] - 150 + rng.uniform(-40, 40), ROAD - 15, rng.uniform(-150, -40), rng.uniform(-60, -20), 0.0, 1.4, 45])
            # particles: [x,y,vx,vy,life,kind]  kind 0 spark, 1 wood
            for pp in parts:
                pp[0] += pp[2] * d; pp[3] += 2400 * d; pp[1] += pp[3] * d; pp[4] -= d
                if pp[1] > ROAD and pp[0] < XB or pp[1] > ROAD and pp[0] > XR: pp[1] = ROAD; pp[3] *= -0.3
            parts = [pp for pp in parts if pp[4] > 0]
            for sm in smoke:
                sm[0] += sm[2] * d; sm[1] += sm[3] * d; sm[4] += d
            smoke = [sm for sm in smoke if sm[4] < sm[5]]
            for db in debris:
                db["x"] += db["vx"] * d; db["vy"] += G * d; db["y"] += db["vy"] * d; db["a"] += db["va"] * d
        if t >= COUNT_END and "bells" not in events: events["bells"] = t
        shake = max(0.0, shake - 1.0 / FPS / 0.45)
        frames.append(dict(t=t, tau=tau, x=x, y=y, ang=ang, wheel=wheel, mode=mode, police=[(q["x"], q["v"]) for q in p],
                           parts=[list(a) for a in parts], smoke=[list(a) for a in smoke], debris=[dict(a) for a in debris],
                           gate=gate_hit, shake=shake, launch=launch_tau, land=land_tau))
        t += 1.0 / FPS
    return frames, events

# ---------------------------------------------------------------- sprites
S = 2  # supersample for sprites
def poly(d, pts, fill, sx=0, sy=0, k=S): d.polygon([((px + sx) * k, (py + sy) * k) for px, py in pts], fill=fill)

def car_body(police=False, light=0):
    im = Image.new("RGBA", (600 * S, 260 * S)); d = ImageDraw.Draw(im)
    body = [(22, 150), (24, 112), (40, 100), (160, 94), (210, 52), (236, 44), (352, 44), (390, 86), (408, 92), (540, 98), (566, 112), (572, 140), (566, 158), (30, 160)]
    low, high = ((22, 22, 28), (240, 240, 245)) if police else (CORAL_D, CORAL)
    poly(d, body, high)
    poly(d, [(22, 128), (572, 128), (566, 158), (30, 160)], low)                       # lower shade
    if police: poly(d, [(22, 112), (572, 112), (572, 128), (22, 128)], (40, 60, 160))  # blue stripe
    else: poly(d, [(26, 114), (570, 116), (570, 124), (26, 122)], CREAM)                 # cream racing stripe
    poly(d, [(218, 56), (240, 50), (292, 50), (292, 90), (176, 92)], (24, 50, 66))       # rear window
    poly(d, [(302, 50), (348, 50), (380, 88), (302, 90)], (24, 50, 66))                  # side window
    poly(d, [(250, 54), (286, 54), (286, 62), (246, 62)], (70, 130, 150))                # glass glint
    if not police:                                                                     # Mari: curly high bun + hoop earring
        d.ellipse([318 * S, 60 * S, 346 * S, 90 * S], fill=(14, 10, 16)); d.ellipse([318 * S, 48 * S, 336 * S, 66 * S], fill=(14, 10, 16))
        d.ellipse([336 * S, 78 * S, 342 * S, 84 * S], outline=GOLD, width=S)
    else:
        d.ellipse([318 * S, 60 * S, 346 * S, 90 * S], fill=(10, 10, 14)); d.rectangle([314 * S, 56 * S, 350 * S, 64 * S], fill=(10, 10, 14))
    d.line([(160 * S, 95 * S), (236 * S, 45 * S), (352 * S, 45 * S), (392 * S, 87 * S), (540 * S, 99 * S)], fill=GOLD + (200,), width=3 * S)  # rim light
    for cx in (124, 452):                                                               # wheel arches
        d.ellipse([(cx - 56) * S, (160 - 56) * S, (cx + 56) * S, (160 + 56) * S], fill=(20, 14, 20))
    poly(d, [(560, 104), (574, 108), (574, 120), (562, 118)], (255, 248, 210))           # headlight
    poly(d, [(20, 112), (30, 110), (30, 124), (20, 124)], (255, 60, 60))                 # tail light
    d.rounded_rectangle([556 * S, 138 * S, 580 * S, 150 * S], 4 * S, fill=(220, 220, 230))  # chrome bumpers
    d.rounded_rectangle([12 * S, 138 * S, 36 * S, 150 * S], 4 * S, fill=(220, 220, 230))
    if police:
        cols = [(255, 40, 60), (40, 110, 255)] if light == 0 else [(40, 110, 255), (255, 40, 60)]
        d.rounded_rectangle([250 * S, 30 * S, 290 * S, 44 * S], 3 * S, fill=cols[0]); d.rounded_rectangle([292 * S, 30 * S, 332 * S, 44 * S], 3 * S, fill=cols[1])
    im = im.resize((600, 260), Image.LANCZOS)
    if police:   # light-bar glow
        g = Image.new("RGBA", im.size); gd = ImageDraw.Draw(g)
        c = (255, 40, 60) if light == 0 else (40, 110, 255)
        gd.ellipse([200, -20, 330, 90], fill=c + (150,)); g = g.filter(ImageFilter.GaussianBlur(26))
        g.alpha_composite(im); im = g
    return im

def wheel_sprite():
    r = 46; im = Image.new("RGBA", (2 * r * S, 2 * r * S)); d = ImageDraw.Draw(im); c = r * S
    d.ellipse([0, 0, 2 * c, 2 * c], fill=(18, 16, 20)); d.ellipse([c - 28 * S, c - 28 * S, c + 28 * S, c + 28 * S], fill=(205, 205, 215))
    for k in range(5):
        a = k * 2 * math.pi / 5; d.line([(c, c), (c + 24 * S * math.cos(a), c + 24 * S * math.sin(a))], fill=(120, 120, 130), width=6 * S)
    d.ellipse([c - 8 * S, c - 8 * S, c + 8 * S, c + 8 * S], fill=(90, 90, 100))
    return im.resize((2 * r, 2 * r), Image.LANCZOS)

BODY = {"hero": car_body(), "p0": car_body(True, 0), "p1": car_body(True, 1)}
WHEEL = wheel_sprite()

def car_image(kind, wheel_rot, ang):
    im = BODY[kind].copy()
    wr = WHEEL.rotate(-math.degrees(wheel_rot) % 360, Image.BICUBIC)
    for cx in (124, 452): im.alpha_composite(wr, (cx - 46, 160 - 46))
    if abs(ang) > 0.05: im = im.rotate(ang, Image.BICUBIC, expand=True)
    return im

def paste_car(fr, kind, wheel_rot, ang, sx, sy):
    """(sx, sy) = screen position of the car's ground contact point (local 298, 206)."""
    im = car_image(kind, wheel_rot, ang)
    vx, vy = 298 - 300, 206 - 130; a = math.radians(ang)
    rx = vx * math.cos(a) + vy * math.sin(a); ry = -vx * math.sin(a) + vy * math.cos(a)
    px, py = int(sx - (im.width / 2 + rx)), int(sy - (im.height / 2 + ry))
    if px > W or py > H or px + im.width < 0 or py + im.height < 0: return
    shadow_paste(fr, im, px, py)

def shadow_paste(fr, im, px, py):
    x0, y0 = max(px, 0), max(py, 0); x1, y1 = min(px + im.width, W), min(py + im.height, H)
    if x1 <= x0 or y1 <= y0: return
    fr.alpha_composite(im, (x0, y0), (x0 - px, y0 - py, x1 - px, y1 - py))

def palm(h, lean, dark=False, blur=0):
    w = int(h * 0.95); im = Image.new("RGBA", (w * S, (h + 40) * S)); d = ImageDraw.Draw(im)
    trunk = (70, 40, 60) if not dark else (28, 16, 30); frond = (40, 70, 70) if not dark else (20, 22, 34)
    bx, by = w / 2, h + 30; tx, ty = w / 2 + lean, 60
    pts = []
    for i in range(21):
        k = i / 20; x = bx + (tx - bx) * k + math.sin(k * math.pi) * lean * .35; y = by + (ty - by) * k; pts.append((x, y))
    for i in range(20):
        wdt = (16 - 9 * i / 20) * h / 400
        d.line([(pts[i][0] * S, pts[i][1] * S), (pts[i + 1][0] * S, pts[i + 1][1] * S)], fill=trunk, width=int(wdt * 2 * S))
    for k in range(9):
        a = -math.pi * (0.05 + 0.9 * k / 8) + math.pi * .0; ln = h * (0.36 + 0.08 * math.sin(k * 2.3))
        ex, ey = tx + math.cos(a) * ln, ty + math.sin(a) * ln * .55 + ln * .35
        mx, my = tx + math.cos(a) * ln * .5, ty + math.sin(a) * ln * .5 - ln * .05
        for j in range(12):
            u = j / 12; u2 = (j + 1) / 12
            def q(u):
                return ((1 - u) ** 2 * tx + 2 * (1 - u) * u * mx + u * u * ex, (1 - u) ** 2 * ty + 2 * (1 - u) * u * my + u * u * ey)
            p1, p2 = q(u), q(u2)
            d.line([(p1[0] * S, p1[1] * S), (p2[0] * S, p2[1] * S)], fill=frond, width=int(max(2, 14 * (1 - u) * h / 400) * S))
    im = im.resize((w, h + 40), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.BoxBlur(blur))
    return im

PALMS = [palm(420, 30), palm(470, -40), palm(390, 55)]
FG_PALMS = [palm(1100, 80, True, 6), palm(1000, -60, True, 6)]

# ---------------------------------------------------------------- static backdrops
def vgrad(stops, h, w=W):
    ys = np.arange(h)[:, None]; out = np.zeros((h, 1, 3))
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        m = (ys >= y0) & (ys <= y1); k = ((ys - y0) / max(1, y1 - y0)).clip(0, 1)
        col = np.array(c0)[None, None] * (1 - k[..., None]) + np.array(c1)[None, None] * k[..., None]
        out = np.where(m[..., None], col, out)
    return np.repeat(out, w, axis=1)

HORIZON = 960
sky = vgrad([(0, (34, 20, 66)), (380, (120, 40, 110)), (700, (226, 86, 120)), (880, (255, 150, 100)), (HORIZON, (255, 204, 140))], HORIZON)
sea_back = vgrad([(0, (255, 170, 130)), (40, (120, 90, 130)), (240, (40, 80, 110)), (H, (22, 56, 80))], H)
sea_front = vgrad([(0, (36, 86, 108)), (700, (12, 36, 56))], H)
SUN_C, SUN_R = (W * 0.60, 880), 250

def make_sky():
    im = Image.fromarray(sky.astype(np.uint8)).convert("RGBA")
    glow = Image.new("RGBA", (W, HORIZON)); gd = ImageDraw.Draw(glow)
    gd.ellipse([SUN_C[0] - 560, SUN_C[1] - 560, SUN_C[0] + 560, SUN_C[1] + 560], fill=(255, 170, 110, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(120)); im.alpha_composite(glow)
    sun = Image.new("RGBA", (W, HORIZON)); sd = ImageDraw.Draw(sun)
    for i in range(40):
        r = SUN_R * (1 - i / 40); k = i / 40
        sd.ellipse([SUN_C[0] - r, SUN_C[1] - r, SUN_C[0] + r, SUN_C[1] + r], fill=(255, int(150 + 85 * k), int(90 + 90 * k), 255))
    im.alpha_composite(sun.filter(ImageFilter.GaussianBlur(2)))
    # painterly cloud streaks
    cl = Image.new("RGBA", (W, HORIZON)); cd = ImageDraw.Draw(cl); r = random.Random(3)
    for i in range(26):
        y = r.uniform(120, 760); x = r.uniform(-300, W); ln = r.uniform(250, 700); th = r.uniform(14, 40)
        c = (255, r.randint(120, 190), r.randint(120, 170), r.randint(60, 130)) if y > 450 else (180, 90, 160, r.randint(50, 110))
        cd.ellipse([x, y, x + ln, y + th], fill=c)
    im.alpha_composite(cl.filter(ImageFilter.GaussianBlur(9)))
    return im
SKY = make_sky()

def make_skyline(width=4200):
    im = Image.new("RGBA", (width, 420)); d = ImageDraw.Draw(im); r = random.Random(11); x = 0
    base = 420
    while x < width:
        w = r.randint(60, 170); h = r.randint(60, 300); c = r.choice([(112, 62, 118), (98, 56, 112), (130, 74, 128), (88, 52, 104)])
        d.rectangle([x, base - h, x + w, base], fill=c)
        if r.random() < .5:   # art-deco stepped crown
            d.rectangle([x + w * .2, base - h - 26, x + w * .8, base - h], fill=c); d.rectangle([x + w * .38, base - h - 50, x + w * .62, base - h - 26], fill=c)
        for wy in range(int(base - h + 14), base - 10, 22):
            for wx in range(x + 10, x + w - 10, 18):
                if r.random() < .28: d.rectangle([wx, wy, wx + 6, wy + 9], fill=(255, r.randint(190, 235), r.randint(120, 170)))
        x += w + r.randint(-10, 30)
        if r.random() < .25: x += r.randint(60, 200)
    return im.filter(ImageFilter.GaussianBlur(1.2))
SKYLINE = make_skyline()

paper = rng.normal(0, 1, (H // 8, W // 8)); paper = np.array(Image.fromarray(((paper - paper.min()) / np.ptp(paper) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
streak = rng.normal(0, 1, (H // 4, W // 16)); streak = np.array(Image.fromarray(((streak - streak.min()) / np.ptp(streak) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).rotate(-25).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
TEX = (1 + (paper - .5) * .10 + (streak - .5) * .05)[..., None]
yy, xx = np.mgrid[0:H, 0:W]; VIG = (np.clip(1.15 - np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .75)) ** 2) * .55, .55, 1))[..., None].astype(np.float32)
GRAIN = [rng.normal(0, 5, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]

def finish(fr, f):
    a = np.asarray(fr.convert("RGB"), np.float32)
    small = Image.fromarray(a.astype(np.uint8)).resize((W // 6, H // 6), Image.BILINEAR)
    br = np.asarray(small, np.float32); br = np.clip(br - 170, 0, None) * 1.6
    bloom = np.asarray(Image.fromarray(br.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR), np.float32)
    a = a * TEX * VIG; a = 255 - (255 - a) * (255 - bloom * .55) / 255
    g = GRAIN[f % 4]; a += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    return a.clip(0, 255).astype(np.uint8)

# ---------------------------------------------------------------- text
_tc = {}
def txt(s, font, size, fill=(255, 255, 255), track=0, shadow=.75):
    k = (s, font, size, fill, track)
    if k in _tc: return _tc[k]
    fo = ImageFont.truetype(font, size); l, t, r, b = fo.getbbox(s); pad = 50
    im = Image.new("RGBA", (int(r - l + 2 * pad + track * len(s)), b - t + 2 * pad)); d = ImageDraw.Draw(im); x = pad - l
    for ch in s: d.text((x, pad - t), ch, font=fo, fill=fill); x += fo.getlength(ch) + track
    sh = Image.new("RGBA", im.size); sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * shadow)))
    sh.alpha_composite(im); _tc[k] = sh; return sh
def put(fr, im, cx, cy, a=1.0, scale=1.0):
    if a <= .01: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    shadow_paste(fr, im, int(cx - im.width / 2), int(cy - im.height / 2))

def countdown_overlay(fr, t):
    if t < COUNT_END:
        n = 10 - int(t / (COUNT_END / 10)); ph = (t / (COUNT_END / 10)) % 1
        put(fr, txt("THE BRIDGE LIFTS IN", FB, 46, CREAM, 4), W / 2, 210, min(1, t / .3))
        put(fr, txt(str(n), FBL, 230, (255, 255, 255) if n > 3 else (255, 90, 80)), W / 2, 370, min(1, t / .3), 1.0 + .18 * (1 - eout(ph * 3)))
    elif t < 8.6:
        a = min(1, (t - COUNT_END) / .15) * (1 if t < 8.3 else (8.6 - t) / .3); pulse = .75 + .25 * math.sin(t * 18)
        put(fr, txt("BRIDGE LIFTING!", FBL, 104, (255, 80, 70)), W / 2, 300, a * pulse)

# ---------------------------------------------------------------- scene 1: interior
def interior(t, f):
    fr = Image.new("RGBA", (W, H)); sh = math.sin(t * 37) * 4 + math.sin(t * 23) * 3
    # windshield view
    view = Image.fromarray(sky[:, :, :].astype(np.uint8)).convert("RGBA").resize((W, 760))
    vd = ImageDraw.Draw(view); vd.ellipse([540 - 150, 560 - 150, 540 + 150, 560 + 150], fill=(255, 205, 140))
    fr.alpha_composite(view, (0, 0))
    d = ImageDraw.Draw(fr)
    d.rectangle([0, 700, W, 1100], fill=(46, 84, 106))                     # sea
    for i in range(16): y = 705 + i * i * 1.5; d.line([(540 - 260 - i * 30, y), (540 + 260 + i * 30, y)], fill=(255, 190, 140, 40), width=2)
    vp = (540, 720)
    d.polygon([(vp[0] - 18, vp[1]), (vp[0] + 18, vp[1]), (W + 400, 1200), (-400, 1200)], fill=(70, 52, 70))   # road
    for k in range(10):                                                     # lane dashes rushing in
        z = ((k / 10 - t * 2.2) % 1); z = .03 + z * .97; z0 = z; z1 = z + .035
        def py(z): return vp[1] + (1200 - vp[1]) * z ** 2.2
        def pw(z): return 3 + 26 * z ** 2.2
        d.polygon([(540 - pw(z0), py(z0)), (540 + pw(z0), py(z0)), (540 + pw(z1), py(z1)), (540 - pw(z1), py(z1))], fill=(255, 225, 170))
    for k in range(8):                                                      # palms whipping past
        z = ((k / 8 - t * 1.4) % 1); sc = .08 + z ** 2.4 * 1.9; side = -1 if k % 2 else 1
        im = PALMS[k % 3]; im2 = im.resize((max(2, int(im.width * sc)), max(2, int(im.height * sc))))
        x = 540 + side * (60 + 900 * z ** 2.4) - im2.width / 2; y = vp[1] + (1200 - vp[1]) * z ** 2.2 - im2.height + 10
        shadow_paste(fr, im2, int(x), int(y))
    # cabin
    d.polygon([(0, 0), (W, 0), (W, 120), (0, 140)], fill=(16, 12, 20))
    d.polygon([(0, 0), (170, 0), (70, 1060), (0, 1060)], fill=(22, 16, 26)); d.polygon([(W, 0), (W - 170, 0), (W - 70, 1060), (W, 1060)], fill=(22, 16, 26))
    d.polygon([(0, 1040), (W, 1010), (W, H), (0, H)], fill=(28, 20, 30))
    d.line([(0, 1040), (W, 1010)], fill=(255, 150, 110), width=4)
    for gx in (260, 820): d.ellipse([gx - 70, 1120, gx + 70, 1260], outline=(255, 160, 90), width=5); d.line([(gx, 1190), (gx + 40 * math.cos(-2 + t * 1.1 + gx), 1190 + 40 * math.sin(-2 + t * 1.1 + gx))], fill=(255, 90, 70), width=5)
    # rear-view mirror with the police behind
    mx, my = 540 + sh * .3, 640; d.line([(540, 120), (mx, my - 80)], fill=(30, 26, 34), width=26)
    d.rounded_rectangle([mx - 290, my - 95, mx + 290, my + 95], 40, fill=(30, 26, 34))
    mir = Image.new("RGBA", (540, 150)); md = ImageDraw.Draw(mir)
    for y in range(150): md.line([(0, y), (540, y)], fill=(40 + y // 6, 30, 60 + y // 5))
    md.polygon([(250, 40), (290, 40), (540, 150), (0, 150)], fill=(60, 44, 62))
    flash = int(t * 8) % 2
    for (px, sc) in ((170, 1.0), (390, .62)):
        for j, c in enumerate([(255, 40, 60), (40, 110, 255)]):
            on = (j == flash); cx = px + (j - .5) * 46 * sc
            md.rounded_rectangle([cx - 20 * sc, 62 - 8 * sc, cx + 20 * sc, 62 + 8 * sc], 4, fill=c if on else tuple(v // 3 for v in c))
        md.ellipse([px - 60 * sc, 100 - 10 * sc, px - 30 * sc, 100 + 10 * sc], fill=(255, 250, 220)); md.ellipse([px + 30 * sc, 100 - 10 * sc, px + 60 * sc, 100 + 10 * sc], fill=(255, 250, 220))
    glow = mir.filter(ImageFilter.GaussianBlur(10)); mir.alpha_composite(glow)
    mask = Image.new("L", (540, 150)); ImageDraw.Draw(mask).rounded_rectangle([0, 0, 539, 149], 30, fill=255)
    fr.paste(mir, (int(mx - 270), my - 75), mask)
    # steering wheel + gloved hands + denim cuffs
    cx, cy, r = 540 + sh * .4, 1700, 470
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(58, 46, 60), width=84)
    d.arc([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6], 200, 340, fill=(255, 150, 110), width=6)
    d.polygon([(cx - 90, cy - 40), (cx + 90, cy - 40), (cx + 150, cy + 200), (cx - 150, cy + 200)], fill=(30, 24, 32))
    for side in (-1, 1):
        a = math.radians(-90 - side * 52); hx, hy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.polygon([(hx - 40 + side * 30, hy + 50), (hx + 40 + side * 30, hy + 50), (hx + 120 * side + 60, H), (hx + 120 * side - 160, H)], fill=(70, 110, 170))   # denim sleeve
        d.line([(hx - 40 + side * 30, hy + 60), (hx + 40 + side * 30, hy + 60)], fill=(170, 200, 230), width=10)
        d.ellipse([hx - 85, hy - 70, hx + 85, hy + 75], fill=(20, 18, 22)); d.arc([hx - 85, hy - 70, hx + 85, hy + 75], 190, 330, fill=(255, 150, 110), width=5)
        for k in range(4): fx = hx - 50 + k * 33; d.line([(fx, hy - 55), (fx, hy - 5)], fill=(50, 46, 54), width=5)
        d.ellipse([hx - 25, hy - 64, hx + 15, hy - 40], fill=(255, 200, 150))   # skin through fingerless glove
    # red/blue wash
    wash = Image.new("RGBA", (W, H), ((255, 40, 70) if flash == 0 else (50, 90, 255)) + (int(34 + 18 * math.sin(t * 50)),))
    fr.alpha_composite(wash)
    # hook text
    countdown_overlay(fr, t)
    a = min(1, t / .25) * (1 if t < 2.7 else (3 - t) / .3)
    put(fr, txt("Cops behind. Bridge ahead.", FB, 64), W / 2, 1110, a)
    return fr

# ---------------------------------------------------------------- scene 2: the chase (side view, one tracking shot)
def exterior(st, f):
    t, tau = st["t"], st["tau"]
    # camera
    anchor = 0.66 - 0.24 * ease((tau - 3.0) / 1.4)
    if st["land"] is None: camx = st["x"] - W * anchor
    else:
        k = ease((tau - st["land"] - 0.35) / 1.3); camx = st["x"] - W * 0.42 - (st["x"] - st["_landx"]) * k
    camx = st.setdefault("_camx", camx)
    lift = min(0.0, (st["y"] - ROAD)) * 0.62
    camy = lift
    sx = math.sin(t * 61) * 26 * st["shake"]; sy = math.cos(t * 47) * 22 * st["shake"]
    camx += sx; camy += sy
    def S_(wx, wy): return wx - camx, wy - camy
    fr = Image.new("RGBA", (W, H), (34, 20, 66, 255))
    # sky (barely moves) + skyline + back sea
    sky_off = int(-camy * 0.08)
    fr.alpha_composite(SKY, (0, sky_off))
    bk = Image.fromarray(sea_back.astype(np.uint8)).convert("RGBA"); fr.alpha_composite(bk, (0, HORIZON + sky_off))
    d = ImageDraw.Draw(fr)
    for i in range(70):                                                      # sun glints on the far water
        gy = HORIZON + sky_off + 8 + (i * 37 % 200); gx = SUN_C[0] + ((i * 97) % 300 - 150) * (1 + (gy - HORIZON) / 120) + 30 * math.sin(t * 2 + i)
        d.line([(gx - 26, gy), (gx + 26, gy)], fill=(255, 215, 150, 160), width=3)
    off = int(camx * 0.12) % (SKYLINE.width - W)
    fr.alpha_composite(SKYLINE.crop((off, 0, off + W, 420)), (0, HORIZON - 420 + sky_off + int(-camy * .1)))
    # helicopter + spotlight (early part of the chase)
    if tau < 5.2:
        hx = W * .78 + 60 * math.sin(t * .9) + max(0, tau - 3.8) * 500; hy = 300 + max(0, tau - 3.8) * -260 + 12 * math.sin(t * 2.1)
        car_sx = st["x"] - camx; gy0 = ROAD - camy
        spot = Image.new("RGBA", (W, H)); spd = ImageDraw.Draw(spot)
        swing = 140 * math.sin(t * 1.7); al = int(70 * (1 - ease((tau - 3.6) / .8)))
        spd.polygon([(hx - 10, hy + 20), (hx + 10, hy + 20), (car_sx + swing + 260, gy0 + 20), (car_sx + swing - 260, gy0 + 20)], fill=(255, 245, 210, al))
        fr.alpha_composite(spot.filter(ImageFilter.GaussianBlur(14)))
        d.ellipse([hx - 70, hy - 26, hx + 50, hy + 30], fill=(24, 18, 32)); d.line([(hx + 40, hy - 6), (hx + 170, hy - 18)], fill=(24, 18, 32), width=10)
        d.line([(hx - 170, hy - 40), (hx + 150, hy - 46)], fill=(24, 18, 32, 150), width=5); d.line([(hx - 40, hy + 40), (hx + 30, hy + 40)], fill=(24, 18, 32), width=5)
        d.ellipse([hx - 64, hy - 16, hx - 30, hy + 10], fill=(255, 200, 120))
    # far railing + background palms on the causeway
    gy = ROAD - camy
    for k in range(int((camx - 600) // 560), int((camx + W + 600) // 560) + 1):
        wx = k * 560 + 120
        if XB - 300 < wx < XR + 260: continue
        im = PALMS[k % 3]; px, py = S_(wx, ROAD - 20); shadow_paste(fr, im, int(px - im.width / 2), int(py - im.height))
    # control tower on the left pier
    tx, ty = S_(XB - 150, ROAD)
    d.rectangle([tx - 40, ty - 300, tx + 40, ty], fill=(150, 96, 110)); d.rectangle([tx - 62, ty - 360, tx + 62, ty - 290], fill=(170, 112, 124))
    d.rectangle([tx - 50, ty - 350, tx + 50, ty - 304], fill=(255, 210, 150)); d.polygon([(tx - 70, ty - 360), (tx + 70, ty - 360), (tx, ty - 410)], fill=(120, 70, 90))
    bells_on = t >= COUNT_END
    for k, lx in enumerate((tx - 30, tx + 30)):
        on = bells_on and (int(t * 4) + k) % 2 == 0
        if on: d.ellipse([lx - 34, ty - 470, lx + 34, ty - 402], fill=(255, 60, 50, 90))
        d.ellipse([lx - 14, ty - 450, lx + 14, ty - 422], fill=(255, 60, 50) if on else (90, 30, 30))
    # front sea, deck, pillars
    sfy = int(gy + 40)
    if sfy < H:
        fs = Image.fromarray(sea_front[: H - sfy].astype(np.uint8)).convert("RGBA"); fr.alpha_composite(fs, (0, sfy))
        for i in range(40):
            yy_ = sfy + 30 + (i * 53) % (H - sfy + 1); xx_ = (i * 211 - camx * 1.1 + t * 40) % (W + 200) - 100
            d.line([(xx_, yy_), (xx_ + 60 + i % 5 * 14, yy_)], fill=(140, 200, 210, 70), width=3)
        sx0, _ = S_(SUN_C[0] + camx, 0)
        for i in range(30):                                                  # sun path on the near water
            yy_ = sfy + 20 + i * 24; ww = 30 + i * 6
            d.line([(SUN_C[0] - ww + 20 * math.sin(t * 3 + i), yy_), (SUN_C[0] + ww + 20 * math.sin(t * 3 + i), yy_)], fill=(255, 190, 130, max(0, 110 - i * 4)), width=4)
    def deck(x0, x1):
        a, _ = S_(x0, 0); b, _ = S_(x1, 0); a, b = max(a, -10), min(b, W + 10)
        if b <= a: return
        d.rectangle([a, gy, b, gy + 46], fill=(150, 100, 118)); d.rectangle([a, gy + 30, b, gy + 46], fill=(110, 70, 92)); d.line([(a, gy), (b, gy)], fill=(255, 196, 150), width=4)
        k0 = int((x0 + camx * 0 if False else max(x0, camx - 200)) // 340)
        for k in range(k0, int(min(x1, camx + W + 200) // 340) + 1):
            px, _ = S_(k * 340, 0); d.rectangle([px - 26, gy + 46, px + 26, H], fill=(104, 66, 92)); d.rectangle([px - 26, gy + 46, px - 12, H], fill=(130, 86, 110))
    deck(camx - 400, XB - 180); deck(XR + 180, camx + W + 400)
    for (p0, p1) in ((XB - 180, XB + 30), (XR - 30, XR + 180)):            # bridge piers
        a, _ = S_(p0, 0); b, _ = S_(p1, 0); d.rectangle([a, gy, b, H], fill=(128, 84, 104)); d.rectangle([a, gy, a + 22, H], fill=(160, 110, 128)); d.line([(a, gy), (b, gy)], fill=(255, 196, 150), width=4)
    # gate arm (or its broken stub)
    gx_, _ = S_(XG, 0); d.rectangle([gx_ - 14, gy - 110, gx_ + 14, gy], fill=(230, 230, 236))
    if st["gate"] is None:
        k = ease((tau - (TR - 0.25)) / 0.6); ang = math.radians(90 * (1 - k))
        ex, ey = gx_ - 340 * math.cos(ang), gy - 92 - 340 * math.sin(ang)
        for j in range(8):
            u0, u1 = j / 8, (j + 1) / 8
            d.line([(gx_ + (ex - gx_) * u0, gy - 92 + (ey - gy + 92) * u0), (gx_ + (ex - gx_) * u1, gy - 92 + (ey - gy + 92) * u1)], fill=(235, 40, 50) if j % 2 else (250, 250, 250), width=16)
    else:
        d.line([(gx_, gy - 92), (gx_ - 50, gy - 92)], fill=(235, 40, 50), width=16)
    for db in st["debris"]:
        px, py = S_(db["x"], db["y"]); a = math.radians(db["a"]); hx_, hy_ = math.cos(a) * db["len"] / 2, math.sin(a) * db["len"] / 2
        d.line([(px - hx_, py - hy_), (px + hx_, py + hy_)], fill=(250, 250, 250), width=16); d.line([(px - hx_ * .3, py - hy_ * .3), (px + hx_ * .3, py + hy_ * .3)], fill=(235, 40, 50), width=16)
    # police cars
    flash = int(t * 8) % 2
    for i, (qx, qv) in enumerate(st["police"]):
        px, py = S_(qx, ROAD)
        if -400 < px < W + 400: paste_car(fr, "p%d" % ((flash + i) % 2), st["wheel"] * (qv / V0) * .9 + i, 0.0 if qv > 0 else 0.0, px, py)
    # bridge leaves
    def leaf(px, py, ang, direction):
        a = math.radians(ang); ux, uy = direction * math.cos(a), -math.sin(a); nx, ny = -uy * direction, ux * direction
        nx, ny = math.sin(a), math.cos(a)
        def P(s_, n_): return (px + ux * s_ + nx * n_, py + uy * s_ + ny * n_)
        d.polygon([P(-60, 0), P(L, 0), P(L, 46), P(-60, 46)], fill=(158, 106, 124))
        d.polygon([P(-60, 30), P(L, 30), P(L, 46), P(-60, 46)], fill=(112, 72, 94))
        d.line([P(-60, 0), P(L, 0)], fill=(255, 196, 150), width=4)
        d.line([P(0, -34), P(L, -34)], fill=(70, 50, 70), width=5)
        for k in range(0, int(L) + 1, 60): d.line([P(k, -34), P(k, 0)], fill=(70, 50, 70), width=4)
        for k in range(0, int(L) - 60, 120): d.line([P(k, 46), P(k + 60, 110 * (1 - k / L) + 46)], fill=(100, 66, 88), width=8)
    lpx, lpy = S_(XB, ROAD); leaf(lpx, lpy, thL(tau), 1)
    rpx, rpy = S_(XR, ROAD); leaf(rpx, rpy, thR(tau), -1)
    # smoke (soft layer)
    if st["smoke"]:
        sl = Image.new("RGBA", (W, H)); sd_ = ImageDraw.Draw(sl)
        for sm in st["smoke"]:
            k = sm[4] / sm[5]; px, py = S_(sm[0], sm[1]); r = sm[6] * (1 + 2.2 * k); a_ = int(110 * (1 - k))
            sd_.ellipse([px - r, py - r, px + r, py + r], fill=(235, 210, 220, a_))
        fr.alpha_composite(sl.filter(ImageFilter.GaussianBlur(18))); d = ImageDraw.Draw(fr)
    # hero car
    px, py = S_(st["x"], st["y"])
    paste_car(fr, "hero", st["wheel"], st["ang"], px, py)
    # sparks + splinters
    for pp in st["parts"]:
        px, py = S_(pp[0], pp[1]); ln = 0.018
        c = (255, 230, 150) if pp[5] == 0 else (250, 250, 250)
        d.line([(px, py), (px - pp[2] * ln, py - pp[3] * ln)], fill=c, width=4 if pp[5] == 0 else 6)
    # foreground palms (fast parallax, only on the causeway)
    for k in range(int((camx * 1.6 - 800) // 1700), int((camx * 1.6 + W + 800) // 1700) + 1):
        wx = k * 1700 + 900
        if XB * 1.6 - 1400 < wx < XR * 1.6 + 600: continue
        im = FG_PALMS[k % 2]; px = wx - camx * 1.6; py = H + 60 - camy * 1.3
        shadow_paste(fr, im, int(px - im.width / 2), int(py - im.height))
    # speed lines while airborne
    if st["launch"] is not None and st["land"] is None:
        for i in range(14):
            yy_ = (i * 137) % H; xx_ = (i * 331 - t * 900) % (W + 400) - 200
            d.line([(xx_, yy_), (xx_ + 220, yy_)], fill=(255, 240, 220, 60), width=3)
    # text
    countdown_overlay(fr, t)
    if st["land"] is not None:
        lt = t - st["_landt"]
        if 1.0 < lt < END_CARD - st["_landt"] + 1:
            put(fr, txt("SHE MADE IT.", FBL, 118), W / 2, 330, eout((lt - 1.0) / .35), 1 + .3 * (1 - eout((lt - 1.0) / .25)))
    return fr

def end_card(fr, t):
    k = ease((t - END_CARD) / .7)
    dark = Image.new("RGBA", (W, H), (14, 8, 24, int(170 * k))); fr.alpha_composite(dark)
    put(fr, txt("DRAWBRIDGE", FBL, 140, CORAL_L, 6), W / 2, 820, k)
    put(fr, txt("GETAWAY", FBL, 140, CORAL_L, 6), W / 2, 970, k)
    k2 = ease((t - END_CARD - .7) / .5)
    put(fr, txt("Should Mari get a Part 2?", FB, 60, CREAM), W / 2, 1160, k2)
    put(fr, txt("Comment YES", FM, 48, GOLD), W / 2, 1240, k2)

# ---------------------------------------------------------------- render
def main():
    sim, events = simulate()
    landx = next((s["x"] for s in sim if s["land"] is not None), None); landt = events.get("land", 99)
    for s in sim: s["_landx"] = landx; s["_landt"] = landt
    events["dur"] = DUR; json.dump(events, open(os.path.join(BUILD, "events.json"), "w"), indent=1)
    print("events", events, flush=True)
    by_t = {round(s["t"] * FPS): s for s in sim}
    total = int(DUR * FPS)
    def frame(f):
        t = f / FPS
        if t < T_INT: fr = interior(t, f)
        else:
            st = dict(by_t.get(f) or by_t[min(by_t, key=lambda k: abs(k - f))])
            fr = exterior(st, f)
        if t >= END_CARD: end_card(fr, t)
        a = finish(fr, f)
        if t < 0.25: a = (a * (t / .25)).astype(np.uint8)
        if t > DUR - .5: a = (a * max(0, (DUR - t) / .5)).astype(np.uint8)
        return a
    if PREVIEW:
        for p in PREVIEW: Image.fromarray(frame(int(p * FPS))).resize((540, 960)).save(os.path.join(BUILD, f"preview_{p:05.2f}.png"))
        return
    pic = os.path.join(BUILD, "frames.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", pic], stdin=subprocess.PIPE)
    for f in range(total):
        enc.stdin.write(frame(f).tobytes())
        if f % 48 == 0: print("frame", f, "/", total, flush=True)
    enc.stdin.close(); enc.wait()
    subprocess.run([sys.executable, os.path.join(HERE, "sound.py")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", os.path.join(BUILD, "audio.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT)

if __name__ == "__main__": main()
