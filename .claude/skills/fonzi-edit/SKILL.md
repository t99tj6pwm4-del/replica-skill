---
name: fonzi-edit
description: >-
  Cuts raw gym footage into a short vertical edit: keeps every lift in its
  original order, trims each to a stretch of reps, hard cuts, original sound
  levelled, no music, no captions. Takes a video file or a Google Drive share
  link and an optional length (default 90 seconds). Use when the user types
  /fonzi-edit, pastes a Drive link to raw gym footage, or says "edit this
  gym video", "cut this down", "make the reel", "90 sec", "60 second version".
---

# fonzi-edit

One tool in this folder. It needs `ffmpeg` and `ffprobe` on the PATH and
nothing else.

```bash
python3 .claude/skills/fonzi-edit/fonzi_edit.py SOURCE --out OUT.mp4
python3 .claude/skills/fonzi-edit/fonzi_edit.py SOURCE --seconds 60 --out OUT.mp4
python3 .claude/skills/fonzi-edit/fonzi_edit.py SOURCE --plan-only --out OUT.mp4
python3 .claude/skills/fonzi-edit/fonzi_edit.py SOURCE --segments 4-12,30-36 --out OUT.mp4
```

`SOURCE` is a local video or a Google Drive share link. The Drive file must be
shared as "anyone with the link"; the tool downloads it itself, so the Drive
connector is not needed.

## The house style

These are settled. Do not ask about them and do not change them unless the
user says so in this request.

- **Length:** 90 seconds unless the user gives another number. A bare number
  in the request ("60", "45 sec") is the length.
- **No music.** The original sound from each clip, levelled to one loudness.
- **Text overlays on every lift:** the exercise name, white bold capitals
  with a black outline, lower third, fading in at the start of each clip.
  Always add them, every time. Pass `--labels 'NAME|NAME|...'` (one per clip,
  empty for none). Name each lift from what the frames show and tell the
  user the names so they can correct them.
- **No captions of speech, no speed changes, no filters.**
- **Every lift stays, in the order it was shot.** Each one is trimmed, none
  is reordered.
- **Hard cuts** between lifts, one short fade out at the very end.
- **Camera setup is dropped:** the moments where the phone is being propped
  up or adjusted between lifts.
- **Output:** the source's size and frame rate (normally vertical 720x1280 at
  30 fps), H.264 video with AAC sound, so it plays anywhere.

## Step 1: make the edit

Write the output outside the repository, in the session scratchpad or a
folder the user names. Video files are never committed here.

```bash
python3 .claude/skills/fonzi-edit/fonzi_edit.py "<link or path>" --out <dir>/fonzi-edit.mp4
```

How it chooses:

1. It finds every point where the picture changes completely. Raw footage is
   a string of clips shot back to back, so each change is a new lift.
2. A clip shorter than 5 seconds is treated as camera setup and dropped.
3. The length is shared equally between the clips that are left. A clip too
   short for its share gives all it has and the rest is shared again.
4. From each clip it keeps one window, a little before the middle, and stays
   half a second clear of both ends.

It prints the plan as JSON and writes three files next to the output:
the video, `NAME.plan.json` (what was kept, in source seconds) and
`NAME.sheet.jpg` (a contact sheet of the finished edit with timestamps).

## Step 2: check it

Open `NAME.sheet.jpg` and look at every row before sending anything.

- Each lift should show the lifter mid-set, not walking in, racking the
  weight or reaching for the phone.
- No clip should be a face filling the frame while the camera is being set.
- The last frames should be the last clip of the source.

The tool cannot see reps. It picks windows by position, so one may start on a
setup moment or split a rep badly. When a window is wrong, read the segment
list in `NAME.plan.json`, move that one window inside its clip, and render
again with every segment listed:

```bash
python3 .claude/skills/fonzi-edit/fonzi_edit.py "<link or path>" \
  --segments 4-12,30-36,47-56,76-85 --out <dir>/fonzi-edit.mp4
```

`--plan-only` writes the plan and a contact sheet of the source without
rendering, for when the footage needs a look first. A source that is one long
unbroken take has no clip changes to find: look at the source sheet and pick
the segments by hand.

Keep the total at the length asked for. Take a second from a longer clip when
another needs one more.

## Step 3: hand it over

Send the video file to the user. Then say, in a few lines:

- the length, size and format
- which lifts are in it and where each was taken from in the raw footage
- what was dropped
- that the cut is not timed to reps, if no window was adjusted by hand
- whether the sound was listened to or only levelled (it is only levelled
  unless you have a way to hear it)

Do not commit the video, the plan or the sheet.

## When it cannot run

- **The Drive link will not download:** the file is private. Ask the user to
  set sharing to "anyone with the link", or to upload the file.
- **No ffmpeg:** say so. Do not try another route that changes the look.
- **The source is shorter than the length asked for:** the tool keeps what
  there is and says so. Pass that on.
