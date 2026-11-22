"""British voiceover with Kokoro (local, offline). usage: python tts.py [speed]  -> build/voice.wav, build/timing.json"""
import json, os, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(HERE, "build")
speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.1
k = Kokoro('/home/user/tts/kokoro.onnx', '/home/user/tts/voices.bin')
sr = 24000; out = []; t = 0.0; timing = []
for sc in json.load(open(os.path.join(HERE, "script.json"))):
    for li, line in enumerate(sc['lines']):
        s, sr = k.create(line, voice='bm_george', speed=speed, lang='en-gb')
        idx = np.where(np.abs(s) > 0.01)[0]; s = s[max(idx[0] - 240, 0):idx[-1] + 480]
        timing.append({"scene": sc['scene'], "text": line, "start": round(t, 3), "end": round(t + len(s) / sr, 3)})
        out.append(s); t += len(s) / sr
        gap = 0.16 if li < len(sc['lines']) - 1 else 0.8
        out.append(np.zeros(int(gap * sr))); t += gap
sf.write(os.path.join(B, "voice.wav"), np.concatenate(out), sr)
json.dump(timing, open(os.path.join(B, "timing.json"), "w"), indent=1)
print(round(t, 2))
