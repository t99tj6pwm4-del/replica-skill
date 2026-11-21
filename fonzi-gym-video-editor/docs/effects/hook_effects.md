# Hook effects (Alfonso, 2026-11-21)

Four 3-second hook effects, from @futurist__'s published CapCut methods. **We use only the method, never
@futurist__'s footage.** The team builds them with ffmpeg + Python (rembg cut-outs, the same as `layered_title` /
`style_fx.py`); the CapCut steps below are the reference for what each one must look like.

## Rules for all 4
- **Only as a 3-second hook at the start of Alfonso's own gym videos. One effect per video.**
- **Build ONE test at a time.** Ask Alfonso which effect and which gym clip first. Never build all 4 at once.
- **Staging:** every test is staged unposted as `~/workspace/upload_staging/<day>_<effect>_test.mp4`. Format: 9:16,
  1080x1920, 30 fps, H.264 + AAC. Verify it with ffprobe and sampled frames, then send him the file plus a frame.
  Nothing goes live without his yes. He posts himself; never post the same video twice.
- **Filming:**
  - Tripod, camera locked, never moved between takes.
  - Film an empty background plate first, in the same spot and the same light.
  - Effect 4 is the exception: it is a hand-held pan by a second person.
- **Text:** English only, Montserrat, mustard gold #D4A017, inside the safe area, never over his face mid-lift.
- **Audio:** his song or the gym audio only. No generated audio. The sounds we make ourselves in `sfx/` (click, impact,
  whoosh) are used as before.
- **CapCut:** no Pro CapCut features without his yes (only relevant if he does it himself in CapCut).
- **No colour grade** (standing answer 14). The white/overexposed flash frames are part of the effect, not a grade.
- **If the cut-out (Auto Removal / rembg) fails** on gym equipment (bar, plates, bench merged with him or cut through
  him), say so and STOP that effect. Never invent a workaround that changes his body or face.

## Effect 1: The Flash Effect (glowing white silhouette)
**Filming:** in the gym, dark background, one big lift or pose, then hold still. Plus the empty plate.

**CapCut steps:**
1. Import the empty background clip and the subject clip.
2. Go 6 frames forward from where he appears, split, and move that piece to an overlay track.
3. Overlay > Cutout > Remove Background / Custom Removal; paint over him to isolate him.
4. Adjust > Curves, drag the curve to top-left, then Exposure and White to max and Black to min, until he is a solid
   white silhouette.
5. Optional: Effects > Glow 2 to soften the edges.
6. Go 2 frames forward, split again, and delete the middle piece so the white flash lasts only 2-6 frames.
7. Add a camera shutter / click sound on the flash frame.

**Our build:**
- rembg mask of him from 6 frames after he appears, filled solid white over the plate/clip.
- An optional soft glow (Gaussian blur of the mask, screened on).
- Held 2-6 frames, then a hard cut back.
- `sfx/click.wav` on the flash frame.

## Effect 2: Make Yourself Float (floating clones)
**Filming:** same tripod spot, same framing, three takes:
1. the empty gym plate,
2. Alfonso walking in,
3. Alfonso jumping 3-4 times.

**CapCut steps:**
1. The empty plate is the base layer on the main track.
2. Walking clip: split at 0.2 s, move it to an overlay at top-left, Cutout > Auto Removal, then Adjust > Curves up to
   brighten.
3. Jumping clip: slow it to 0.4x, Cutout > Auto Removal, and position it mid-air on the right side.
4. Duplicate that jumping overlay 2-3 times. Place each clone at a different height and spot, and stagger their timing
   by a few frames.
5. At the peak of each jump, split 1 frame, then Adjust > Graphs and pull the white curve up to overexpose that one
   frame for the flash.
6. Export at 1080p and check that no clone overlaps his face.

**Our build:**
- Plate base, with per-frame rembg cut-outs of the walk and the jump. The jump is slowed to 0.4x (frame interpolation
  or frame hold; no AI motion).
- 2-3 staggered clones.
- One overexposed frame at each jump peak.
- QA: no clone over his face.

## Effect 3: The Speed Effect (super-speed jump)
**Filming:** Alfonso running or jumping in and out of frame, at 60 fps if possible, on the same tripod.

**CapCut steps:**
1. Import the clip, split at the start and end of the run/jump, and keep only the middle segment.
2. Select the middle segment > Speed > Standard, set to 15x-20x.
3. Effects > Motion Blur: Blur at max / about 20, Blend about 20, Times 2.
4. Optional pro version:
   - Screenshot his running poses and remove the backgrounds.
   - Add directional blur to the cut-outs and lay them as trailing overlays, pushed slightly off-frame.
   - Add a dust overlay.
   - Re-import, then add Motion Blur + Camera Shake.
5. Cut the speed burst to land exactly on a beat drop.

**Our build:**
- The middle segment sped up 15-20x, with frame-blend motion blur (ffmpeg `tmix`, about 20 frames, blended).
- Timed so it ends on a beat drop of his song (`librosa` beats, as in `cut_video.py`).
- The pro version only on his ask. Dust: only an overlay we make ourselves, no stock.

## Effect 4: The Spiderweb Effect (fall from the sky and land)
**Filming:** SAFE version only, with no real fall.
- One person films continuously while panning down from the ceiling.
- Then film the same pan again with Alfonso doing a small pretend jump from a bench or box, landing on the gym floor.

**CapCut steps:**
1. Import the continuous pan clip, trim it to the start of the pan, split at the end of the movement, and delete the
   middle so he appears mid-air.
2. Freeze the starting frame, use Cutout > Auto Removal to isolate him, and shrink the frozen subject small at the top
   of the frame.
3. Keyframe his position and scale from small/high to full-size/low over 0.5-0.8 s, with Animation > Ease In so he
   accelerates as he falls.
4. On the landing frame, add Motion Blur + Shake.
5. Add the on-screen title "THE SPIDERWEB EFFECT" in Montserrat for the first 2 seconds only.

**Our build:**
- Freeze frame plus a rembg cut-out, scaled and moved with ease-in over 0.5-0.8 s onto the landing frame.
- Motion blur (`tmix`) and our shake (as in `style_fx.py`) on landing.
- The title in gold #D4A017 Montserrat for 0-2 s, in the safe area, never over his face.
