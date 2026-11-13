---
name: fonzi-edit
description: >-
  Turns raw gym footage into a finished vertical reel in the house style: every
  lift kept in order and trimmed, crossfades between exercises, b-roll
  cutaways, slow-mo, a dark graded look, and motion graphics (title card,
  progress bar, "EXERCISE 03 / 08" lower thirds, tracked callouts that follow
  the muscle, kinetic captions, viewfinder corners, cam badges, save-this end
  card). No music. Takes a video file or a Google Drive link and an optional
  length (default 90 seconds). Use when the user types /fonzi-edit, pastes a
  Drive link to raw gym footage, or says "edit this gym video", "cut this
  down", "make the reel", "90 sec", "60 second version".
---

# fonzi-edit

The reference for the look is the user's own `final_edit.mp4` (a "HEAVY CURL DAY"
reel): dark graded footage, yellow and white graphics, a title slam at the start,
a thin progress bar across the top, an exercise lower third, a yellow tag on a
ring that follows the muscle, big condensed captions with the key word in yellow,
yellow corner brackets, little CAM / SLOW-MO badges, and a SAVE THIS end card.
**Do this every time. Plain text labels are not acceptable.**

Needs `ffmpeg`, `ffprobe`, Python 3 with `numpy`, `Pillow` and `opencv-python-headless`
(`pip install opencv-python-headless` if missing). Fonts are in `fonts/`.

## The house style (settled, do not ask)

- **Length:** 90 seconds unless the user gives another number.
- **No music.** The original sound of each clip, levelled.
- **Every lift stays, in the order shot**, each trimmed to a stretch of reps. Camera
  setup moments are dropped.
- **Graphics on every edit:** title card, progress bar and exercise name, lower third
  per exercise, a caption about every 5 to 6 s, a tracked callout on about every second
  clip, corner brackets, CAM tags, end card with the channel handle.
- **Virtual multi-cam:** every clip after the first switches angle once or twice by hard
  cutting to a punch-in of the same footage (`cams` in the recipe: `at`, `zoom`, `cx`, `cy`).
  A CAM 1 / CAM 2 / CAM 3 badge shows at each switch (wide, medium, tight). Aim each
  punch-in at the working muscle or the face, never at empty clothing or wall, and switch
  outside any tracked callout.
- **B-roll:** about one cutaway per exercise, 1.1 s, a punched-in close-up from the
  raw footage over the lift while its sound carries on.
- **Transitions:** crossfade (0.3 s) between exercises, hard cut inside the same
  exercise. Slow-mo (0.5x) on one strong rep near the end.
- **Look:** 1080x1920, 30 fps, slightly contrasty and desaturated with a vignette.

## Three agents do the design work. Run all three, every time

1. **`fonzi-overlays`**: title, captions, callouts and tracking anchors.
2. **`fonzi-broll`**: the cutaway list.
3. **`fonzi-transitions`**: the transition for each join.

They return pieces of the recipe. The recipe format is `recipe.example.json`
(a complete, working example for a real edit).

## Steps

1. **Find the clips.** Run the cutter's planner to get the clip boundaries and a contact sheet:

   ```bash
   python3 .claude/skills/fonzi-edit/fonzi_edit.py "<link or file>" --plan-only --out <dir>/plan.mp4
   ```

   Raw footage is clips shot back to back; each scene change is a new lift. Drop clips
   under 5 s (setup). Look at the sheet and choose a window per clip so the windows add
   up to the target length (slow-mo clips count double: a 4 s source window at 0.5x is 8 s).
   Name each lift from what the frames show.
2. **Write the recipe** `<dir>/recipe.json` with the three agents' output.
3. **Render the base first** to place callouts accurately:

   ```bash
   python3 .claude/skills/fonzi-edit/fonzi_recipe.py "<link or file>" <dir>/recipe.json --out <dir>/final.mp4 --stage base
   ```

   Extract a frame at each callout time with a 0.1 grid, look at it, and set each `anchor`.
4. **Render everything:** same command without `--stage` (or `--stage graphics` to reuse the base).
   About 4 minutes for 90 s.
5. **Check it.** Pull frames from the title, a lower third, the middle of every callout
   (the ring must sit on the named muscle), a caption, a b-roll insert, the slow-mo clip and the
   end card. Fix and re-render the graphics stage only when something is off.
6. **Hand it over:** send the video. Say the length, which lifts are in it, that exercise
   names and coaching cues are read off the frames and may need correcting, and that the
   sound was levelled but not listened to. Never commit the video.

## Notes

- Tracking is optical flow on the callout's anchor point. It holds on a muscle that stays in
  frame; if the camera jumps (a cut) it holds still rather than flying off.
- Rendering the whole source in one filter runs out of memory, which is why the base is cut
  into small per-clip files first.
- The simpler `fonzi_edit.py SOURCE --seconds 90 --out x.mp4` still exists for a quick plain
  cut with `--labels` text and `--transitions`. It is not the house style.
- A private Drive link will not download: ask the user to set it to "anyone with the link".
