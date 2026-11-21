# GTA 6 launch Short: Muse Video prompts (6 × 10 s, 9:16)

60 s total = 6 segments of about 10 s each. Generate segment 1 normally, then generate each later segment with
`resume_from_snapshot_id` = the previous segment's snapshot_id. Save them as `gta6-seg1.mp4` … `gta6-seg6.mp4`
in this folder, then run `assemble.py` (it adds the British voiceover, captions, stat cards and music).

**Ground rules for every segment**
- The footage is original and only *inspired by* a Florida crime-drama mood. No Rockstar or GTA logos, no game
  characters' likenesses, no box art and no game HUD. The finished video labels it "AI-generated footage · not gameplay".
- Don't ask the model for on-screen text or numbers (models render text badly). `assemble.py` adds all text.
- The narration is added afterwards (Muse doesn't accept audio input), so each prompt asks only for ambient sound.

---

## Segment 1 (0–10 s): Launch night

```
[10 seconds / 9:16 vertical] Midnight launch night outside an electronics store in a humid Florida city: the crowd erupts as the doors open.
Characters: a crowd of 20-30 gamers aged 18-35, varied ethnicities, casual streetwear, phones raised and filming; in the foreground, a young man about 25 in a white tee and black cap holds an unbranded black game box overhead.
Setting: city street at midnight, wet asphalt reflecting the warm white light of the store front, palm trees along the street, light haze, mood of excitement and celebration.
Beats (timeline):
  0-2 s: extreme close-up as cash and a bank card hit the counter, the receipt printer spits paper fast.
  2-6 s: the store doors slide open, the crowd surges forward, cheering, phone camera flashes.
  6-10 s: a low-angle push in on the young man as he raises the unbranded box overhead, the crowd blurred behind him.
Camera: handheld documentary feel; the first shot is macro, then a medium shot, ending on a low-angle slow push-in; shallow depth of field; realistic film-like grade, warm highlights, natural skin tones.
Sound: crowd cheering, sliding doors, receipt printer, city ambience. No dialogue.
Restrictions: no readable text, logos or brand names on screen; no neon-cyberpunk look; no game footage or HUD; no clipping through objects, no warped hands or faces, no extra fingers, no smoothed plastic skin.
```

## Segment 2 (10–20 s): The pre-order mountain, then 2013

```
[10 seconds / 9:16 vertical] This is segment 2 (10-20 s) of a 60-second Short. It continues segment 1's realistic documentary texture and warm film-like grade.
Characters: a warehouse worker about 40 in a high-vis vest; in the second half, a teenager about 16 in a 2013-era striped hoodie, seen from behind.
Setting: first half, a huge distribution warehouse at night under fluorescent light, conveyor belts carrying thousands of unbranded black game boxes; second half, a 2013-era teenager's bedroom at night, the old TV the only light source.
Beats (timeline):
  0-4 s: a high-angle drone shot moving down the conveyor belts: boxes stretch to the horizon, a sense of huge scale.
  4-6 s: the worker seals a stack of boxes onto a pallet with tape, close-up of his hands.
  6-10 s: a hard cut to 2013: the teenager sits cross-legged on the bedroom floor holding a previous-generation controller, the TV glow flickering, the image turning warm-yellow and grainy like nostalgic film.
Camera: the first half is a smooth high-angle push; the second half a static medium shot from behind; the 2013 section is lower in saturation with added film grain.
Sound: conveyor belt hum, tape tearing, quiet bedroom room tone. No dialogue.
Restrictions: no readable text or logos; no game footage on the TV (show only a blurred glow); no warped hands; no smoothed plastic skin.
```

## Segment 3 (20–30 s): Five times bigger, back to a Florida city

```
[10 seconds / 9:16 vertical] This is segment 3 (20-30 s) of a 60-second Short. It continues the previous segment's realistic texture, moving from nostalgic grey into vivid daylight colour.
Characters: none (landscape shots only).
Setting: a Miami-style coastal city at golden hour: art-deco buildings, rows of palm trees, a turquoise sea, speedboats leaving white wakes, mood of freedom and arrival.
Beats (timeline):
  0-3 s: a fast drone shot climbing straight up from the sea surface to reveal the whole coastline.
  3-7 s: the drone glides over a row of art-deco hotels and palm trees, a red sports car driving along the coast road below.
  7-10 s: a wide shot at sunset of the city skyline silhouette, the sun sinking into the sea.
Camera: drone aerials, steady and smooth, accelerating at the start and slowing near the end; true-to-life colour, no oversaturation.
Sound: sea wind, gulls, distant waves and engines. No dialogue.
Restrictions: no neon-cyberpunk look; no readable signs or logos; no distorted buildings or flickering; no game-style rendering, must look like real-world footage.
```

## Segment 4 (30–40 s): Partners in crime, launch day

```
[10 seconds / 9:16 vertical] This is segment 4 (30-40 s) of a 60-second Short. It continues the same coastal city, now at night, with a tense, cinematic crime-drama mood.
Characters: (original characters, deliberately not resembling any existing game character)
  Woman: about 28, Latina, long dark curly hair in a high ponytail, small gold hoop earrings, white tank top under an open olive bomber jacket.
  Man: about 32, white, short brown hair, light stubble, grey henley shirt, worn denim jacket.
Setting: a night-time coast road and a run-down motel car park; streetlights warm amber, distant police lights a faint red and blue, mood of danger and close partnership.
Beats (timeline):
  0-4 s: inside a vintage convertible driving fast at night, a two-shot from in front: the man drives, the woman looks back over her shoulder, wind in her hair.
  4-7 s: a close-up of the woman's eyes, red and blue light sweeping across her face.
  7-10 s: the car skids to a stop in the motel car park, they look at each other, cut to black.
Camera: a stabilised tracking shot from the front of the car, then a close-up, then a wide shot; anamorphic flares, cinematic 2.39-style grade (but output stays 9:16).
Sound: engine roar, wind, distant sirens, tyre squeal. No dialogue.
Restrictions: no resemblance to any real person or existing game character; no guns or violence shown; no readable text; no facial drift, no change in body proportions, no warped clothing, no deformed fingers; no smoothed plastic skin.
```

## Segment 5 (40–50 s): Launch day, then "what's next?"

```
[10 seconds / 9:16 vertical] This is segment 5 (40-50 s) of a 60-second Short. Same realistic texture; the mood turns from launch-day excitement to a darker, open question.
Characters: a player about 25, mixed race, short curly hair, black hoodie, wearing headphones.
Setting: first half, morning sunlight in a living room, the player tearing the shrink wrap off an unbranded game box; second half, the same living room late at night, lit only by the TV, rain outside the window.
Beats (timeline):
  0-3 s: close-up of fingers tearing the shrink wrap, sunlight sparkling through it.
  3-6 s: the player drops onto the sofa, excited, controller in hand (the TV is out of frame, its glow on their face).
  6-10 s: time lapse into night: the player still sits there, expression calm and thoughtful, rain on the window, the camera slowly pulling back.
Camera: macro close-up → medium shot → slow pull-back; the night section is cool and darker, low key.
Sound: shrink wrap tearing, sofa springs, rain, room tone. No dialogue.
Restrictions: no game footage on the TV; no readable text or logos; no warped hands; no smoothed plastic skin; no neon look.
```

## Segment 6 (50–60 s): Worth it or overhyped?

```
[10 seconds / 9:16 vertical] This is segment 6 (50-60 s) of a 60-second Short. Same realistic texture, lively and funny, ending on a callback to the opening.
Characters: two friends on a sofa:
  Friend A: about 24, Black, short twists, yellow tee, excitedly giving a big thumbs up.
  Friend B: about 26, East Asian, round glasses, grey hoodie, shaking his head with a thumbs down.
Setting: a cosy living room at night, warm lamp light, snacks on the table.
Beats (timeline):
  0-4 s: a two-shot: the friends turn to face each other mid-argument, A with a thumbs up, B with a thumbs down, both trying not to laugh.
  4-7 s: quick alternating close-ups of A's thumbs up and B's thumbs down.
  7-10 s: a hard cut to an aerial at night of the Florida city, the camera rising quickly (to echo the opening launch-night city and loop back).
Camera: handheld medium shot → quick alternating close-ups → drone rising; natural warm grade.
Sound: friendly laughter, sofa sounds, then city ambience. No intelligible dialogue.
Restrictions: no readable text or logos; no facial drift, no extra fingers or deformed hands; no smoothed plastic skin; no neon-cyberpunk look.
```
