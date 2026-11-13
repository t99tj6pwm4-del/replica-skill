# CapCut effects + transitions library

> How this project uses it: the editor renders with ffmpeg + Remotion, not inside the CapCut app. This
> library is the style rulebook. Every effect / transition the agents pick is named from here and
> rendered by `scripts/effects.py` as the closest ffmpeg / Remotion equivalent in the SAME category
> (the effects log says "ffmpeg equivalent of <CapCut name>"). Names are never invented.

IMPORTANT HONEST NOTE FOR THE AGENT: CapCut publishes NO exhaustive list of every single effect. It ships hundreds of effects, renames them between versions, and changes them seasonally. This library is the COMPLETE category list from CapCut's own pages, plus the named effects CapCut / TikTok / catalogs list under each category. If an exact effect name is missing in the installed CapCut version, use the closest effect in the same category — do NOT invent a new effect name, do NOT stop the edit, do NOT use a Pro effect without asking Alfonso first.

================================================================
PART A — VIDEO EFFECTS (applied ON a clip, not between clips)
Where to find in CapCut: Effects > Video Effects. Categories below are CapCut's own.
Browse categories like Trending, Opening & Closing, Lens, Light, Retro, Star, and more.

A1. Trending
- What it is: the current viral effects, changes weekly / seasonally. Use for hooks only.
- Named examples: Shake, Black Flash, Glitch, Blur, 3D, VHS Distortion, Retro Glitch, Flicker text, Kinetic typography
- Gym use: Shake (0.3s on a hard rep / beat drop only), Black Flash (hook cut only)

A2. Opening & Closing
- What it is: animated intros / outros, title sequences, logo reveals.
- Named examples: Camera Focus, TV On
- Gym use: Camera Focus for the first 2 seconds (hook), TV On for the closing "Save this" card only. Never in the middle of a set.

A3. Lens
- Wide lens up close / GoPro look, Fisheye, long lens, background blur, chromatic aberration
- Named examples: Fisheye, Chromatic, Wide Lens
- Gym use: Fisheye / wide lens for a close-up rep, Chromatic for a 0.3s glitch hit only

A4. Light
- Lens flares, light leaks, glow, God Rays, Limelight, Sun Flashes, Leak 1, Sequin Bokeh
- Gym use: light leak / lens flare on a hero shot only, 2-3 frames, never over a face while talking

A5. Retro
- VHS, 80s, Pixel, Arcade, Dark Night, film grain, color distortion, old-school film
- Named examples: VHS, Old Film, Film Grain, Dark Night, Retro Glitch
- Gym use: VHS / film grain for a throwback / transformation flashback only, never on the main current lift

A6. Star / Spark / Sparkle
- Star sparkles, glitter, spark particles
- Gym use: almost never. Only on a celebration / PR moment, 0.5s max.

A7. Nightclub
- Neon lights, disco visuals, strobe, club lights
- Gym use: only for a night / party song moment, never on a normal gym set

A8. Glitch
- RGB Split, Digital Glitch, Signal Glitch, chromatic split, TV interference
- Gym use: RGB Split / Digital Glitch on a beat drop / hard cut, under 0.4s

A9. Distortion
- Ripple, warp, wave, psychedelic warp, stretch
- Named examples: Ripple
- Gym use: Ripple on a transition into a new exercise only, subtle

A10. Blur
- Background blur, Gaussian blur, Motion blur, Vertical Blur
- Gym use: background blur to isolate Alfonso, motion blur on a fast rep

A11. Body (see Part B — these are in Video Effects too)
- Body effects automatically detect people and add motion trails, body outlines, dynamic shadows, particle effects that follow gestures

A12. Nature / Particles / Butterfly
- Rain, snow, dust, bokeh, leaves, butterflies, particles
- Gym use: dust / bokeh for a cinematic hero shot only, never rain / snow in a gym

A13. Vlog
- Vlog presets, clean everyday look, light color + stabilisation feel
- Gym use: default clean look for talking / coaching moments

A14. Love / Mood / Dark / Split / Texture / D3D / Cartoon / TV / Celebrate / Halloween / Christmas
- Love: hearts, soft glow. Mood: moody colour. Dark: low-key lighting, dramatic shadows. Split: split-screen layouts. Texture: film / paper texture. D3D: 3D / cartoon depth. Cartoon: Sketch, Cartoon, Comic book. TV: TV On / Off, static. Celebrate: confetti, fireworks. Halloween / Christmas: seasonal only.
- Gym use: Dark for a silhouette / hero shot, Split for half you / half equipment, Cartoon NEVER for a real gym lift (Alfonso hates cartoon look), Celebrate only for a PR, seasonal effects NEVER unless the video is about that holiday

A15. Dreamy Glow / Halo
- Soft bloom, halo glow, dreamy focus
- Gym use: Dreamy Gaze / soft bloom on a transformation / before-after only

A16. Pro (paid)
- Pro-only effects. DO NOT use without Alfonso's explicit yes. If an effect is Pro, skip it and pick the closest free one in the same category.

A17. Decor / Screen / Motion / Edits / Interface / Graffiti
- Decorative overlays, screen overlays, motion graphics, interface frames, graffiti
- Gym use: motion graphics for lower-thirds / progress bar only, never graffiti over his face

================================================================
PART B — BODY EFFECTS (applied to the person in the frame)
Where to find: Effects > Body Effects. CapCut auto-detects the person.
Categories: Trending, Pro, Clone, Hallucination, Stroke, Hair Salon, Role, Glowing Lines, Superpowers, Portrait, Mask, Funny Faces, Selfie, Dark, Background, Mood, Image

Named examples, with gym use:
- Outline: glowing outline tracing the body — use on a hard rep, 1s max
- Laser Eyes: NEVER on Alfonso (joke effect, breaks the serious gym look)
- Mechanical Rings: NEVER unless a sci-fi song moment
- Clone: duplicate body — use for a before / after or "two angles at once" moment only
- Hallucination: ghost / echo trail — use for a slow-mo rep, subtle
- Stroke / Glowing Lines: dynamic lines / halos to enhance movement — use on a punchline / hardest rep
- Superpowers: energy aura — use on a PR only, 1s max
- Portrait / Selfie / Mask: face reshape, slim, smooth skin, big eyes — DO NOT use. Never reshape Alfonso's face or body. This is a hard rule.
- Funny Faces: NEVER
- Hair Salon / Role: NEVER
- Background: background removal / replace — use only if the gym background is distracting, keep the real gym if possible
- Mood: mood glow on the person — use sparingly on a hero shot
- Body Retouch: Slim, Smooth Skin, Big Eyes, Face Reshape — DO NOT use

Body effect rule: 1 body effect max per video, 1 second max, never on a talking / coaching moment, never reshape the body.

================================================================
PART C — FILTERS (colour grade, applied to a whole clip)
Where to find: Filters tab. 11 categories: Featured, Pro, Portrait, Life, Mono, Movies, Retro, Night Scene, Scenery, Food, Style
Plus in the editor: Retro, Life, Movie, Scenery, etc.
- Warm, Cool, Cinematic, B&W, Vintage — use Cinematic / Warm for gym, B&W for a throwback only
- Portrait: skin / face grade — keep natural, never over-smooth
- Life / Scenery: natural daylight grade
- Mono: black and white
- Movies: film look
- Retro: vintage film
- Night Scene: dark / night grade
- Food / Style: do NOT use for gym
Filter rule: ONE filter per video, applied consistently to all clips, never change filter mid-video.

================================================================
PART D — TRANSITIONS (applied BETWEEN two clips, in the join)
Where to find: tap / click the white square between two clips on the timeline, or Transitions tab on desktop, drag onto the join. Set duration with the slider.
CapCut's own transition categories: Overlay, Camera, Blur, Basic, Light Effect, Glitch, Distortion, Slide, Split, Mask, MG, Social Media
Plus: Night, Blur, Overlay, Moment, Camera

D1. Basic / The Cut (DEFAULT)
- Hard Cut: no duration, straight cut. DEFAULT for gym edits. Use this almost always.
- Fade / Dissolve: one image fades out while the next fades in. 0.3-0.5s. Use only when time has passed.
- Fade to Black / Black Fade: 0.5-1s. Use only when a section is ending.
- Match Cut: two clips share a shape or movement, no duration. Use when the bar / body position matches across the cut.

D2. Camera
- Zoom In / Zoom Out / Pull In / Pull Out: 0.2-0.4s. Use when pushing into a detail.
- Whip Pan / Velocity Zoom / Camera In/Out: fast horizontal blur, 0.2-0.3s, both clips already moving sideways. Use on a beat drop, synced to the song.
- Shaky Inhale: shaky camera breath in. Use on a hard rep only.
- Whirl / Spin / Swirl: frame spins like a vortex. Use sparingly, dance / high-energy only, never on a heavy lift.
- 3D Spin / Cube / 3D Flip: rotating cube / card flip. Use for a new exercise section only, never every cut.

D3. Slide / Wipe / Mask
- Slide: one clip slides out left / right / up / down, next slides in. Use for a new exercise.
- Wipe: next clip wipes across the screen. Use for a new exercise.
- Mask Wipe / Smooth Mask Wipe: masked wipe, clean. Use for a clean section change.
- Split: split-screen transition. Use for half you / half equipment.

D4. Blur
- Vertical Blur, Blur Dissolve, Motion Blur transition. Use for a soft section change, 0.3-0.5s.

D5. Overlay
- Subtle overlay transitions, film burns, light leaks. Use for a retro / warm section change.
- Film Burns and Light Leaks: warm flashes of light, retro feel. Use on a transformation moment.

D6. Light Effect
- White Flash, Dark Flash, Glare, Glare II, Light Leak Flash. Use on a beat drop, 0.2-0.3s, never on a talking moment.

D7. Glitch
- RGB Split, Digital Glitch, Signal Glitch 2, TV interference. Use on a beat drop, under 0.4s.

D8. Distortion
- Warp / ripple transition between clips. Use sparingly.

D9. Night
- Night / dark transitions, moody fade. Use for a night gym / silhouette moment only.

D10. Moment
- Moment transitions, highlight / slow-mo bridge. Use for a PR / hardest rep only.

D11. MG (Motion Graphics)
- Animated graphic transitions, shapes / text wipe. Use for a title / section card only.

D12. Social Media
- Sassy / fun transitions, trending social styles. Use sparingly, only if it fits the song / trend, never on a serious lift.

D13. AI Transitions
- AI tab in the transitions panel. CapCut analyses the two clips and generates a morphing bridge. Use only if the hard cut looks bad, and check the face / room did not morph. If it morphs, revert to a hard cut.

D14. Audio transitions (J Cut / L Cut)
- J Cut: audio from the next clip starts before the video cuts. L Cut: audio from the current clip continues over the next clip. Use for storytelling / coaching, to keep his voice flowing across a cut. This is an audio transition, not a visual one.

Transition rules for gym edits:
- DEFAULT IS A HARD CUT. A transition must earn its place.
- Max 1 transition per 3 cuts. Never transition every cut.
- Duration: 0.2-0.5s for energy transitions, 0.5-1s only for Fade to Black at a section end.
- Never use a spin / glitch / flash on a heavy lift where it hides the form.
- Never use two different fancy transitions back-to-back.
- If a clip is very short, CapCut may refuse a transition (not enough frames) — use a hard cut instead, do not force it.
- Some transitions are Pro / paid. Check before building an edit around one. If Pro, skip it.

================================================================
PART E — HOW THE AGENT USES THIS LIBRARY
- Text/Visuals Agent: picks 1 video effect max per clip, 1 body effect max per video, 1 filter per video, transitions per Part D rules.
- Multicam / Multi-Shot Agent: transitions are BETWEEN the 4 multicam angles. Default is a hard cut to the new angle (see the 100-shot library). Use a transition only if the hard cut jars.
- Cuts Agent: hard cuts only, no effects, no transitions. Effects are added later by Text/Visuals.
- Final Approval / QA: check — no effect hides Alfonso's face, form, or the bar; no effect changes his body shape; no cartoon effect; no Pro effect used without approval; transitions are 0.2-0.5s (except Fade to Black 0.5-1s); audio is still his song / his voice only, no stock / AI music; captions are still readable over the effect.
- Log every effect / transition used in output/effects_log.md (video, timestamp, effect name, category, duration). Never repeat the exact same effect + transition combo in the next video unless Alfonso asks for it.

Test checklist to rerun:
- docs/capcut_effects_library.md exists with Parts A-E
- A test edit uses: 1 filter, 1 video effect on a hard rep, 1 transition (0.3s) between two exercises, hard cuts everywhere else, no body reshape, no cartoon, no Pro effect
- QA pass/fail report lists each effect / transition and its duration
- Dry-run only. NOTHING is posted to Meta without Alfonso's approval.


================================================================
EXPANSION v2 — Nov 13, 2026 — added from web + community sources
Reddit note: Reddit's r/CapCut threads did NOT come back in search — Reddit blocks / does not index those threads in the search I used, so no direct Reddit quotes are in here. The expansion below is from CapCut's own pages, YouTube creators, and the open CapCut AI Director catalog (indexed from CapCut Desktop Pro, Mar 10 2026), plus ForkFree's effect finder.

F1. THE SCALE — WHY THE LIST IS SO BIG
- CapCut's effect finder indexes 36,000+ IDs, 7,000 verified. CapCut hides effect names and IDs, so finding the one you saw in a video means scrolling hundreds of thumbnails.
- Animations alone: ~1,985 total (Trending ~480 + Non-Trending ~1,505)
- Video Effects alone: 500+ built-in effects, constantly growing
- So this library is NOT every single preset by name — it is every category + the top named effects in each. The agent must search by NAME in CapCut (Transitions tab > search name, drag onto the cut) — that is how you find a hidden effect in seconds.

F2. HIDDEN TRANSITIONS — NAMES + IDs (from CapCut Desktop, Sep 29 2026, may change)
- Star-Cut Spin: 7576586764060609847
- RGB Spin: 7499818905565744437
- How to find: Open the Transitions tab and search the name, then drag it onto the cut between two clips. If you build projects with scripts, the ID is what a CapCut project file uses.
- Source video: "24 CapCut Transitions You Didn't Know Existed" — 24 transitions, each shown twice on real footage, with exact name, what it does, and its ID.

F3. TOP 108 TRANSITIONS / EFFECTS — NAMED, FROM THE CAPCUT AI DIRECTOR CATALOG
Flash / Light transitions:
White Flash, Dark Flash, Flash, Glare II, Heartwarming Flash
- White Flash: full-frame white burst, 4-8 frames, beat drops / dramatic reveals
- Dark Flash: full-frame dark/black burst, 4-8 frames, moody / dramatic
- Glare II: lens glare with light bleed, 10-20 frames, cinematic / golden hour
- Heartwarming Flash: soft warm flash, 8-15 frames, emotional moments only

Blur / Smooth transitions:
Simple Blur, Radial Blur, Blur Focus, Bubble Blur
- Simple Blur: clean gaussian blur dissolve, 10-20 frames, smooth scene changes
- Radial Blur: blur radiating from center, 8-18 frames, focus / dramatic reveal
- Blur Focus: rack-focus blur, 12-20 frames, subject reveals / before-after
- Bubble Blur: soft bubble-shaped blur, 12-22 frames, dreamy only

Camera / Motion transitions:
Shaky Inhale, Swipe Left, Delay Zoom, Rebound Zoom, Dive & Bounce, Pull In, Shake Snap
- Shaky Inhale: camera shake with zoom-pull-in, 6-15 frames, energy spikes / beat drops
- Swipe Left: horizontal swipe revealing next scene, 6-12 frames, social-media native
- Delay Zoom: delayed zoom-in, 10-20 frames, emphasis / anticipation
- Rebound Zoom: zoom with elastic bounce-back, 8-15 frames, fun reveals
- Dive & Bounce: downward dive with bounce, 10-18 frames, action / sports edits — GYM USE THIS
- Pull In: camera pull-in zoom, 8-15 frames, subject reveals

Glitch / Digital transitions:
Snap Hack, Comic Cut, Signal Glitch 2
- Snap Hack: digital snap with glitch, 4-10 frames, tech / edgy
- Comic Cut: comic-book panel cut, 6-12 frames — DO NOT use for gym, Alfonso hates cartoon look
- Signal Glitch 2: TV signal interference, 6-12 frames, retro / error moments

Overlay / Creative transitions:
Black Fade, Overlap Fade, Slice Reveal, Film Fade, Snap Rack, Pastel Motion
- Black Fade: fade to black, 15-30 frames, scene endings / chapter breaks
- Overlap Fade: cross-dissolve with overlapping frames, 15-30 frames, time passage / montage
- Slice Reveal: sliced panel reveal, 8-15 frames, product / before-after
- Film Fade: analog film fade with grain, 12-24 frames, cinematic / retro
- Snap Rack: quick rack-focus snap, 4-10 frames, fast reveals / talking heads

Creative / Specialty transitions:
Ripping Wipe, Dream Jitter
- Ripping Wipe: paper-tear reveal, 8-15 frames, dramatic reveals / transformations
- Dream Jitter: jittery shake with dreamy blur, 8-15 frames, memory / dream sequences

Shake / Motion effects (in-clip):
Camera Shake, Repeat Shake, Shake Impact
- Camera Shake: use on collision / landing / hardest rep, 0.3s only
- Repeat Shake, Shake Impact: same rule, 1 per video max for impact

Glow / Light effects (in-clip):
God Rays, Limelight, Sun Flashes, Leak 1, Sequin Bokeh
- God Rays, Limelight, Sun Flashes: animated sun / lens flare overlay, hero shot only
- Leak 1: light leak, pair with film grain / retro filter

Glow / Aura body effects:
Dreamy Gaze, Spotlight, Neon Silhouette
- Dreamy Gaze: soft focus bloom, ethereal portrait mood
- Spotlight: spotlight on the subject
- Neon Silhouette: neon outline tracing the body — dance / nightclub only, PRO in some versions

F4. ANIMATIONS — IN / OUT / COMBO (~1,985 total)
Where to find: select a clip > Animation tab > In | Out | Combo. Each has: Trending | Basic | Light | Glitch | Mask | 3D | Vibration (In/Out) or Trending | Basic | 3D | Cam Motion (Combo)

Animation > In (Trending, ~200+):
Flash In, Swoosh, Cross Open, Fade In, Zoom 1, Focus, Pulse, Swing Left, Rock Vertically, Zoom 2, Fall In, Zoom Flip, Grand Appears, Zoom Out, Rock Laterally, Energy Boom, Inky Smoke, Shake Zoom, Retro Fade-in 2, Magic Cube 3, Turbulence II, Sunset Flare, Double Static, Flame Delivery, Color Flashes, Shake 2, Particle Blast, Explosion Undone, Chroma Wave, Swing, Side Flipping, Mono Fade, Wave Shake, Fly In, Pixelation, Film Wheel, Center Warp, TV Flits, Metallic 2026, Popshot Shift, Glam Flash, Newspaper In, Sonic Magenta, Slow Landing, Pixel Jammer, Night Fever, VHS Purple, Twinkle Zoom, Space Rider, Uncrumpling, Pixel Load, Firework Sorter, Screen Wipe, Galactic Holes, Frame Display, Steam Nights, Brick Down, Target Broken, Push In, Glow Closet, Clone Pack, Drop Pic, Fairy Fire, Balloon Blown, Earth Zoom, Cyber Warp, Duplicate Slide, Ring Back 3, TV Beam, Digital Morph, Rain Ripples, Spin Up T, Turn Spiral, Swirl, Fire Masters, Dye Spread, Smoke Tear, Golden Sand, Sprite Dance, Mirror Bloom, Fallen Cards, Double Open, Triple Iris, Blow Down, Ultra Filter, Back To Earth, Ink Face, Digital Result, Meteor Pass, Electric Finish, Crystal Freeze, Retro Dance, Light Widen, Distort Level, Anime Punch, Pull Apart, MirrorAcles, Digital Space, Paint Mess, Snowflakes, Flash Intro, Lava Spread, Blinking Eye, Sun Burst, Dizzy Spin
- Gym use: Flash In / Fade In / Zoom 1 / Focus for the hook (first 2s), Pulse / Shake Zoom for a hard rep, Retro Fade-in for a throwback. Never use Anime / Cartoon / Comic animations on a real lift.

Animation > Out (Trending, ~180+):
Smoke, Black Hole, Flash Out, Fade Out, Blur Dissolve, Shake Slide, Drain Fades, Fold, Blur Out, Blow Ends, Brighten Out, Side Slide, Cross Close, Quick Fan-out, Smoke Doors, TV Off, Blinking Out, Horizontal Blur, Blink Shut, Dazzling Out, Glitch Outro, Zoom In, Happy Ending, Stitched Out, Finger Swipe, Cross Shake, Quick Exit, Starry Flight, Swoosh, Zoom Flip, Neat Shatter, Magic Q Out, Scrolled Up, Sticky Note, Whirl Under, Drag Out, Destroyer, Wave Outro, Trembling Out, Heart Particles, Freeze Out, Blood Drops, Shake Zoom, Ripple, Paper Crack, Frame Thin, Black Archive, Turbulence III, Bokeh Boom, Warm Exit, Phone Error, Soul Up, Flash Outro, Collision, Mini Zoom, Jump Away, RGB Scanlines, Rotate Out 1, Cam Down, Drop Down, Glass Spin, Fallen Gallery, Dust Eater, Color Flashes, Buzz Off, Energy Burst, Out of Body, Dimension, Dust Scatters, Paper Shed, Zoom Out, Insert Film, Sheet Flips, Black Nibble, Magic Ms 2, Cyber Warp, Aura Flash, Anime Frame, Perpetual Out, Space Warp, Fall Out, Shattered, Cyber Escape, Outro Drop, Stick Sand, Cube Close, Old TV, Dreadful Exit, Zero Laspin, Crushed Out, Lumin Flash, Soft Slide, Rosette Down, Blue Glitter, Sleep Mode, Film Reel, Triple Q-out, Scroll Rounds, Pixel Instant, Quit Station, Punch Mares, Palette Catcher, Space Seas, Heart Beat, Sketch View, Parallel Globe, Magic Starts T, Bright Admin, Trace Shut, Broke Away, Snapstick, Peel Apart, Side Popping, Book Shut, Curtain Shut, Target Killer, Writing Out, Red Spin-out, TV Off, Flash Pull-out, Fold Harness, Screen Flash, Grey Mask, Square Luna, B&W Movie, Ice Cube, Rotate Ironing, Ghost Drape, Spin & Warp, Stagger Out, Stone Shake, Slide Left, Sky Writing, Canvas Scroll, Come Ping, Phone Toss, Warning Light, Bounce Away, Yanked Out, Bolts Out, Newspaper Out, Slow Wave, Cash Out, Rotating Star, 3-part Reveal, Flipbook, Puzzle, Shake Switch, Maple Cover, Slice Apart, Twin Ashes, Blur Cloud, Shrunk Cards, Fairy Fly, Tri-fold Shut, Point Out, Power Off, Glitch Plain 2, Tri Wipe, Photo Album, Lumin Mantra, Fading Mixers, Lagging Out, Collapse Out, Whirl, Fizzle Off, Disperse, Horror Q Exit, Clone Apart, Fall Away, TV Intro, Golden Sand
- Gym use: Fade Out / Blur Dissolve / TV Off for the ending card only. Never use Blood / Horror / Death animations.

Animation > Combo (Trending, ~100+):
Dynamic Shake 6, Bouncy Rush, Polpi Candy, Zoom 1, Zoom 2, Fall Right, Wave Station, Distort Left, Pendulum 1, Bounce 1, Bend-Zoom, Wave Motion, Pan Right, Pendulum 2, Bounce 2, Pan Left, Roll InOut 2, Fall Spin, Wobble, Sway Out, Spin Fall, Rise Spin, Roll InOut 1, Distort Night, 3D Card 5, Sprint Stop 1, Blast 1, Sway In, Fall Bottom Right, Blinds, Trisect 1, Waltzer 2, Right Zoom, Fall Left, Waltzer 1, Angle 1, Rollercoaster 1, Falling, Left Zoom, Flip 2, Rotate Fade, Fall Bottom Left, Slide Wave, Stirring, Wave Slide, Slip a Side 2, Wave Option, Train 2, Spin, Dynamic Shake 1, 3D Card 2, Train 4, Blast 2, Train 1, Funhouse 1, Sprint Stop 2, Flash Moment 1, Trisect 2, Slip a Side 1, Spin Rise, Yo-yo 2, Zoom Spin, Distort French, Train 3, Smaller, Cube 3, 3D Card 1, Enter Bounce, Snatch Bounce, Funhouse 2, 3D Card 6, Flash Moment 6, Triplets 1, Fan Out, Spin Out, Spin In, Pirate Ship 4, Slice Late 2, Pirate Ship 1, Smartphone 1, Smartphone 3, Pirate Ship 2, Zoom-Roll, Revolver 2, Yo-yo 1, Pirate Ship 3, Blast Casino 2, Puzzle, Sliding Doors 1, Crystal 1, Triplets 2, Cube, Quarter 2, Cube 2, Split Down 2, Angle 2, Magic Cube 1, Smartphone 2, 3D Card 4, 3D Card 5, Blast Casino 1, Revolver 1, Flip II, Split Down 1, Slice Late 1, Crystal 2, Quarter 1, Rollercoaster 2
- Gym use: Dynamic Shake / Bounce / Zoom Spin / Wobble for a text / caption animation only, never on the main video clip. Combo animations are for text / stickers, not for Alfonso's face.

F5. SPEED / VELOCITY — THE GYM EDIT WEAPON
Speed > Curve (PRO) — 8 preset curves: None, Custom, Montage, Hero, Bullet, Jump out, Flash in, Flash out
- Hero: slow-to-fast ramp, ideal for a single highlight / hardest rep
- Montage: rapid multi-action sequences
- Bullet: bullet-time slow-mo
- Flash in / Flash out: flash speed ramp

Speed > Velocity Effects — 6 presets: None, Flash, Blur shake, Fade blur, Retro zoom, Rainbow
- Flash, Blur shake: use on a beat drop
- Retro zoom: use on a throwback moment
- Rainbow: NEVER for gym

Velocity edit recipes (from creators, gym-specific):
- Gym Velocity: lifting / entrance clip, Speed Curve fast approach, hard slow on the peak rep, add shake + dark moody grade, sync the slow to the heaviest beat. Search in CapCut: "gym velocity template hard"
- Velocity With Shake: build a smooth speed curve first, at the beat drop add a quick scale bounce (zoom 100 to 115 to 100), or import a shake preset, add a white flash frame on the drop, keep the shake short
- Velocity Transition Pack: build speed curves on each clip, between clips use a zoom or spin transition on the beat, add a flash frame at each cut
- Sports edit rule: Zoom Transition (push into action), Whip Cut (fast pan-blur), Flash Transition (white/black frame on hard beat hits), Motion Blur (camera movement between shots). Keep transitions 0.2-0.4s for aggressive pacing. Shake / Glitch in-clip: limit to 2-3 moments across the entire edit. Overuse removes all impact.
- Flash Shake Transition (gym tutorial, viral): Shake effect under Trending, Speed 16, Intensity 38, duplicate the clip layer, then apply 'BW Flash Snap' effect for a high-contrast black-and-white flash. Alternates rapidly between color and monochrome on a pose / flex.

F6. SHAKE — ALL THE TYPES (not one preset)
CapCut offers several shake-related effects, and exact names change by platform / device / region / version.
- Shake Transition: vibration between two clips
- Zoom Shake: rapid zoom + screen vibration, sports / automotive / energetic
- Blur Shake: movement + directional blur, velocity edits
- Camera Shake: in-clip shake, collision / landing moments
- Screen Shake / Flash Shake: screen vibration + flash
- How to find: Effects > search "shake, camera shake, screen shake, vibration, tremble, zoom shake, blur shake, jitter"
- Gym use: shake on a beat drop / hardest rep only, 0.3s, synced exactly to the beat — half a beat off looks like a mistake

F7. TRANSITION CHEAT SHEET — BY CATEGORY
Basic: Dissolve, Fade, Cross Fade, Wipe
Zoom: Zoom In, Zoom Out, Zoom Blur, Pull In, Delay Zoom, Rebound Zoom
Slide: Slide Left / Right / Up / Down, Swipe Left, Push Up, Wipe
3D: Cube, Flip, Rotate, Fold, 3D Spin, 3D Card
Blur: Blur In/Out, Radial Blur, Simple Blur, Blur Focus, Bubble Blur
Glitch: RGB Split, Digital Glitch, Shake, Snap Hack, Signal Glitch 2
Light: Flash, Light Leak, Rays, White Flash, Dark Flash, Glare II, Heartwarming Flash
Mask: Circle wipe, Heart, Star shapes, Smooth Mask Wipe
Distort: Stretch, Squeeze, Whirl, Ripple, Warp Slide
Trending: Trending TikTok transitions, Velocity Zoom, Morph / Seamless Object Pass, Tear Off Reveal, Phone Swipe, Change Channel, Pull Down

F8. FILTERS — NAMED ONES CREATORS ACTUALLY USE
- Red Tea: most versatile filter, portraits / food / landscapes
- Inception: warm up clips, golden hour
- Orange Blue: rich oranges and blues, scenic / beach
- Teal and Orange: high-contrast Hollywood look, cinematic
- Green Orange Style + Love City 2: warmth + cinematic vibes, Filter Intensity 50%, Soft Effect 20%
- Vivid, Fresh, Golden, Retro, Film, Mono, Teal Orange, Candy, Moody — filter thumbnails, use the strength slider, Apply to all
- Filter rule still stands: ONE filter per video, applied consistently to all clips.

F9. TEXT / CAPTION ANIMATIONS (for the YouTube-style captions)
- Typewriter, Highlighter Sweep, Glitch Text, Punch-in Text, Shake Text, Mask Rise, Strike & Replace, Flash Cut (3-4 frame white flash on every jump cut), Glow Flash Cut, Camera Shake (text)
- Flash Cut: a 3-4 frame white flash on every jump cut — makes each cut feel intentional. Use on hard cuts in a talking / coaching moment, not on every rep.
- Use for captions / kinetic text only, never as a video effect on Alfonso's face.

F10. UPDATED AGENT RULES (v2)
- Search by NAME in CapCut to find a hidden effect — do not scroll thumbnails for 10 minutes
- Velocity / speed ramp is now a core gym tool: Hero curve on the hardest rep, Montage for a multi-exercise sequence, Flash / Blur Shake velocity effect on a beat drop
- Animations are for TEXT / TITLES / END CARDS, not for the main video clip — In for the hook, Out for the ending, Combo for captions
- Shake: max 2-3 moments per video, 0.3s, synced to the beat
- Flash Shake (Shake Speed 16 / Intensity 38 + BW Flash Snap) is approved for a flex / PR pose only
- Log every effect / transition / animation / velocity curve used in output/effects_log.md
- Test checklist v2: docs/capcut_effects_library.md includes Parts A-F + F1-F10, a test edit uses Hero speed curve on a hard rep, 1 velocity effect, 1 named transition from F3 (e.g. Shaky Inhale or Pull In), 1 Animation In on the hook title, hard cuts everywhere else, QA pass/fail report
