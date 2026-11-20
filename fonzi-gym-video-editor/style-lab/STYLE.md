# Fonzi style (Style Lab)

## The brief (draft, from the standing rules; Alfonso still to confirm)
1. **For:** gym reels for FB Fonzi.stays.fit / IG @fonzi.stays.fit (his own footage, his own songs).
2. **Shape:** vertical 9:16, 1080x1920, 90 s ±1 s.
3. **Watching / first second:** hyped, "this guy is strong", "I want to train right now", and the video looks professional.
4. **References he loves** (look only; never download or reuse their videos):
   - **youngla x haddy_abdel** (name title): giant gold name title layered around the person: one line cut out behind him, one line in front of his chest, a small intro line on his chest. Use it for name moments. No running subtitles there, just the title.
   - **Canyon Hepi @canyonahika** (colour): moody teal & orange film look (Kodak 2383-style LUT), grain and glow, dark industrial gym, very cinematic. Keep the gold titles in it.
   - **Transitions**, all three:
     - Brayan Jimenez @bfitcreator (instagram.com/reel/DUtMFmODyZn): fade to black, match cut (squat front -> rear mid-rep), cut-out zoom.
     - Jon Cudi @cudiedits (instagram.com/reel/DfpUYeSMObY): camera wipe past a weight stack, luma fade, flicker mask, film burn.
     - Brandon Bartley @brandon.basics (instagram.com/reel/DYQiIaTRLXX): mask transition (hand over a plate), rise effect, pin effect.
   - (No reference #2 was sent.)
5. **Never:** non-English text except the Spanish pop-up lines, hashtags on screen, text over his face, stock or AI music, other creators' footage.
6. **Already has:** Montserrat (Black for titles), Documentary Gold layered titles (back word behind him), the three pop-up cards, honey + salt opener. Colours: 5-step teal & orange film grade (see `GRADE_AND_TRANSITIONS.md`), titles mustard gold #D4A017, Montserrat. Logo: `brand/fonzi_logo.png` (white drip "Fonzi" with horns, halo, devil tail; transparent PNG). His animated logo clip `input/fonzi_logo_anim.mp4` carries a small moving badge that looks like a Sora watermark, so it is not used (no-Sora rule); we animate the PNG ourselves.
7. **Movement:** cinematic, with the transitions above (match cuts, masks, wipes, luma/film-burn, cut-out zoom). Speed/feel: a mix: smooth cinematic moves between lifts, hard snaps on the big moments (titles, heaviest rep, beat drops).
8. **Sound:** his own songs; our own synthesised whoosh + pop (`sfx/`). SFX: only sounds we synthesise ourselves (free, `scripts/make_sfx.py`): whoosh, pop, and new hits, risers, clicks, film-burn crackle as needed. No packs, no AI sounds.
9. **Build first:** TODO (ask).

## Locked
- **Cut out + punch in, original background flickering to black** (r4-c2, round 4): the shot freezes on its last
  frame, he is cut out, the original background strobes to black behind him for 10 frames (irregular), then a
  5-frame punch-in on his chest/face with a shake, hard cut. Pop on the cut-out, clicks on the flickers, impact
  on the punch, whoosh into the next shot.
- **Gold name title, clean** (r1-t1, round 1): layered title over the footage, gold stays clean and flat (#D4A017, Montserrat Black): big word behind him, small intro line on his chest, second line in front of his chest. Whoosh in.
- **Gold name title + snap** (r1-t3, round 1): same, but it lands with a 2-frame white flash, a 1.08 -> 1 punch-in over 6 frames and a small shake, on an impact hit. For the big name moment.
- **Zoom through the shirt** (r1-x5, round 1) **with zoom blur** (r2-x5, round 2): punch into a dark object (his black tank) over 10 frames (ease-in, zoom to 6x, darkening 80%) with a radial zoom blur that builds as it speeds up; next shot fades up out of the dark over 8 frames. Whoosh 0.45 s before, impact on the cut.
- **Logo end card: flicker on** (r1-l2, round 1): flickers on like a sign warming up, then a steady glow. Clicks. **With real drips** (round 2, all three kept): drips run down from the halo, letters and tail after the flicker. Allowed amounts: a few slow drips (6, drops fall now and then), heavy drips (14, drops falling), wet paint (14, creep down and stay). Rotate between them across videos.

## Rejected
- **Cut out with the background flickering bright/overexposed** (round 4).
- **Cut out with a black background, or with a white outline** (round 3).
- **Flicker mask / light leak** (round 2, both versions dropped).
- **Slow luma fade 0.65 s** (round 2).
- **Zoom into the dumbbell, faster** (round 2): stay with the shirt + zoom blur.
- **Colour grading by the team** (round 1, 2026-11-19): "not what I wanted". Alfonso grades his videos himself. The team never grades: no `film_grade.py` in any edit, and Style Lab options are shown on ungraded footage. His 5-step spec stays in GRADE_AND_TRANSITIONS.md for reference only.

## Maybe
- Cut out with the background flickering to **white** (r4-c1, round 4, no note): asked him whether to keep it as an occasional alternate.

## Not chosen (round 1, unrated)
- Film gold title, film burn, rise, drip reveal logo, slam logo.

## Open questions
- Item 9 (what to build first): proposed round 1 = gold name title (youngla style), the teal & orange grade, transitions. Waiting for his OK.

## Rules for every video (written 2026-11-20 after round 4)
Tool: `scripts/style_fx.py` (snap / zoom / cutout / logo). Our own sounds only (`sfx/`). Never a colour grade.
1. **Name title**: gold layered title (#D4A017, Montserrat Black): big word behind him, small intro line on his
   chest, second line in front of his chest (`layered_title.py`). The big name moment lands with `style_fx.py snap`
   (flash + punch-in + shake + impact); exercise titles stay clean with a whoosh in.
2. **Transitions** (pick by moment, never more than one effect per cut, leave most cuts plain and on the beat):
   - `zoom`: between sets / exercises, into a dark object (his black tank by default) with zoom blur. Whoosh + impact.
   - `cutout --to black`: the hype moment (heaviest set, the drop): freeze, cut out, black strobe, punch-in.
     At most 1-2 per video.
3. **Logo end card**: `style_fx.py logo` last 3-3.5 s: flicker on + real drips; rotate `--drips slow|heavy|wet`.
4. **Never**: colour grade, flicker masks / light leaks, film burn, rise wipe, slow luma fade, cut-out with black
   or outline backgrounds, text over his face, hashtags, non-English (except the Spanish pop-up lines).
