# Relight a clip (Higgsfield recipe)

Source: https://ruby-cotija-fb5.notion.site/Professional-lighting-in-one-prompt-with-Claude-41928691eca3816886b4f98e84e4fe97 (Shaan Johari). Saved 2026-11-20.
When to use it and the budget: Director standing answer 15 (`.claude/agents/fonzi-director.md`).

Team notes:
- **Model override (Alfonso, 2026-11-20, final): Wan 3.0 (`wan3_0`), 480p, always 4 s max** (MiniMax H3 Lite was
  6.25 credits in his app; Wan 3.0 is 3).
  480p, 9:16, duration 4, generate_audio false: 3 credits. Still ~2-3 credits, so ~6 per look (Seedance below: 80).
  In STEP 3 use generate_video with model wan3_0: image_references = [relit still], video_references = [the original
  clip trimmed to <= 4 s] (Wan 3.0 can't combine start_image with references). It regenerates rather than edits:
  check the moves still match before splicing.
  Price check 2026-11-20 (480p, 4 s): Wan 3.0 3 | Grok 1.5 Lite 4 | Wan 3.0 Prime 5 | MiniMax H3 Max 7.5 (5 s min) |
  Grok 1.5 10 | Seedance 2.0 12 | Seedance 2.5 edit 14 | Cinematic Studio 3.5/4.0 12-14. H3 regenerates rather than edits: check the moves still match before splicing.
- The Director suggests one look per new video (his choice, 2026-11-20); it runs only on his yes, and the video only after he approves the relit still. Never on another creator's clip.
- Works best on a locked-off (tripod) shot, a few seconds long; use the clip's own first frame.
- It changes lighting, not colour grade (he grades himself), so ask him which look; never pick a look on his behalf for a real video.
- The relit clip goes to `output/flow_pack/returned/` style: Cuts splices it back frame-exact in place of the original piece.

---
21-lighting-looks-sheet.jpg

Change the lighting of any clip after you've filmed it. Attach your clip, pick a look, paste one prompt. Claude relights a frame with Higgsfield, you approve it, then it relights the whole video to match. All 21 lighting looks from the reel are below, ready to paste.

Made by Shaan Johari · @viashaan

## What you need
1. A Higgsfield account. New to Higgsfield? Sign up here and you get a 3-day free trial: https://higgsfield.ai/s/higgsfield-commands-in-claude-ig-viashaan-gsLgqc
1. Claude with the Higgsfield connector. In Claude, go to Settings, then Connectors, then Add custom connector. Paste https://mcp.higgsfield.ai/mcp, press Connect and sign in to Higgsfield.
1. About 85 credits per look. The relit frame is a couple of credits, the relit video about 80.
1. A clip and one frame from it. A locked-off shot works best: camera on a tripod, a few seconds long. For the frame, screenshot the very first frame of the clip and crop out any buttons.

## The 3 steps

### 1. Connect Higgsfield

Sign up with the link above if you're new, then connect Higgsfield in Claude (Settings, Connectors, Add custom connector, paste the link, Connect).

### 2. Attach your clip and frame, paste the prompt

Start a new chat, attach your clip and its first frame, then paste the prompt below. Swap [LOOK] for any look from the list.

### 3. Approve the still, then get the video

Claude shows you the relit frame first and stops. Check it before you say go. The video costs about 40 times more than the still, so only make it once the still looks right. If it's off, ask for another still (it's a couple of credits). When it's right, reply "go" and Claude makes the video in a few minutes. To try another look, send "same again with" and the next look.

## The prompt

Copy all of it and paste it into Claude with your clip and frame attached.

```
Relight my clip with Higgsfield. Use the Higgsfield tools for every step. Follow these steps exactly and don't skip any.

INPUTS
- My clip and a still of its first frame are attached. If you can't read them directly, open the Higgsfield upload box (media_upload_widget) so I can upload them, the clip first, then continue.
- LOOK: [LOOK]

STEP 1. Upload the clip and the frame to Higgsfield (if they aren't there already): media_upload, then PUT each file to its upload_url with the headers Content-Type and If-None-Match: * , then media_confirm (type video for the clip, image for the frame). If Higgsfield asks how to pay (credits or a plan), ask me before you go on.

STEP 2. First fit the look to my shot. Look at my frame and note what's really in it (windows, blinds, lamps, screens, plants, mirrors). Rewrite LOOK so it works in my scene: keep its colour, direction, hardness and mood, but if it names something my shot doesn't have, the light comes from just out of frame instead (for example "cool blue moonlight from out of frame on the left" instead of "through the window"). Never add an object that isn't in my frame. Tell me the rewritten LOOK and use it everywhere below. Then relight the frame with generate_image: model Nano Banana 2, 2k, the same aspect ratio as my clip, the frame as the only image reference. Prompt: "Relight image 1. Do not move or resize anything: the person keeps the same size, pose and head position, and every object and the framing stay exactly the same. Change only the lighting: LOOK. Real photograph, natural skin texture." Wait with jobs_wait. Compare it with my frame: if anything moved, changed size or a new object appeared, make it again rather than fixing it (up to 3 tries) and keep the cleanest one. Show me the still, then STOP and wait for me. Do not start the video until I reply "go". If I ask for changes, make a new still and wait again.

STEP 3. Only after I reply "go": relight the clip with generate_video: model Seedance 2.5 video edit, 1080p, my clip as the source video and the relit frame from step 2 as the reference image. Prompt: "Relight this video to match the reference image exactly. Keep the person, their face, every movement, the room and the framing exactly as the source video, same timing. Change only the lighting to match the reference: LOOK. Steady light. Locked-off camera, real photograph look, natural skin." Wait with jobs_wait.

STEP 4. Show me the video link and tell me how many credits it used (check with transactions; other jobs on the account can move the balance at the same time).
```

## The 21 looks

Paste any of these in place of [LOOK]. They were written for a room with a window, a lamp and a screen, but your shot doesn't need any of those: Claude fits each look to what's in your frame and brings the light in from just out of frame when something's missing.
1. Cozy light: warm table lamps on, a soft golden glow across the room, evening, calm and cosy
1. Dappled sun: warm late afternoon sun through the plant leaves by the window, dappled leaf shadows on the wall, floor and clothes, the face in clean, soft, even sunlight
1. Moonlight: cool blue moonlight through the window, the room dark, lamps off
1. Top light: one hard warm spotlight straight down from the ceiling, a tight pool of light on the head, shoulders and the floor, eyes in shadow, the room falling into darkness
1. Red room: one red bulb, the whole room deep red and black, the lamp shade glowing red
1. Silhouette: the screen behind the head blazes bright teal-white with rays bursting out around it, the person a dark silhouette, the room dark teal
1. Neon split: pink neon from one side and blue neon from the other, dark room
1. Rembrandt: one spot lamp at 45 degrees, a triangle of light on the cheek, deep shadows, dark room
1. Split light: a warm dim room with one hard slit of light across the eyes
1. Rainy window: grey daylight through a rain-streaked window, raindrop shadows on the person and the wall
1. Screen glow: only the monitor is on, cold blue screen light on the face, the room dark
1. Blacklight: a dark room lit only by a glowing UV blacklight tube, deep violet light on the walls and the person, white things glowing blue-white
1. Rim light: a bright lamp behind the person rims the hair and shoulders, the front of them dark
1. Theatrical beam: one sharp beam of sunlight through drifting haze from the window, dust floating in the air, the room dark
1. Sun flare: low sun straight through the window into the lens, warm flare and haze
1. Water caustics: rippling blue water light dancing over the person and the walls, like a fish tank
1. High key: bright soft airy daylight filling the room, pale glowing walls, almost no shadows, screens off
1. Painter's window: soft overcast north light from the window, gentle painterly shadows
1. Teal and orange: cool teal window light on one side, a warm orange lamp on the other
1. Police lights: night, police lights outside the window throwing saturated red and blue light through the blinds, slatted shadows
1. Golden hour: low orange sun through the window, long warm shadows across the room

Bonus, the storm: night outside, lightning flashes through the window light the room cold white with hard shadows. Use it as the LOOK and add "two lightning flashes" to the video prompt in step 3.

## Tips
- Approve the still first. The still is a couple of credits, the video about 80. Never let Claude make the video before you've said the still is right.
- Lock the camera. A tripod shot relights cleanly. A moving camera makes the light drift.
- Use the clip's first frame. If the frame and the clip don't match, the person drifts in the video.
- Make the reel. Relight the same clip in a few looks, then cut them on the beat of a song, one look per hit, with the look's name on screen. Every clip stays on the same moment, so the person never jumps between cuts.

## If it goes wrong
- Claude can't see your files: it opens the Higgsfield upload box. Upload the clip first, then the frame.
- The relit frame changed the room or the person: Claude makes it again. A clean frame makes a clean video.
- The look needs something your shot doesn't have (a window, a screen, blinds): Claude brings that light in from just out of frame. If it adds the object anyway, ask for the still again with "nothing new in the frame".
- The video flickers: ask for "steady light, no flicker" and run step 3 again.
- Higgsfield asks how to pay: pick credits or your plan, and Claude carries on.
