# 5 Types of GTA 6 Players: publishing pack

## Title
5 Types of GTA 6 Players 🎮 Which One Are You?

## Caption
Every friend group has all five 😂 Law-Abider, Photographer, Speedrunner, Chaos Player or Completionist: which one are you? Comment your number 👇 and tag your #2 😈

## Hashtags
#GTA6 #GTAVI #Gaming #Gamers #Shorts

## A/B opening hooks
- A (used): "There are only five kinds of people playing GTA 6 right now. Which one are you?"
- B: "Your friend is definitely one of these five GTA 6 players."
- C: "Be honest: which GTA 6 player are you? Number two is the worst."

## Honesty notes
- This is comedy about player types, not news, so it contains no sales figures or release claims that could become outdated.
- All footage is AI-generated, shows people (never the game screen), and is labelled "AI-generated footage · not gameplay".
- The voice (Kokoro, British) and the music (generated in code) are original, with no copyrighted audio.

## How to build
```
python tts.py 1.1      # British voiceover   -> build/voice.wav, build/timing.json  (needs kokoro-onnx)
python music.py        # original music + mix -> build/mix.wav
python assemble.py <folder with clip1.mp4 … clip7.mp4>   # -> build/gta6-top5-players.mp4
```
