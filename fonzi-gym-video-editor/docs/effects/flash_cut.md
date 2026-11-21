# Film-strip flash cut (Higgsfield recipe)

Source: https://ruby-cotija-fb5.notion.site/Make-the-film-flash-cut-with-Claude-40e28691eca38106b1d4f50d3017025c
Saved verbatim from Alfonso's message, 2026-11-19. When to use it and the credit budget: see the Director's standing answer 13 (`.claude/agents/fonzi-director.md`).

Team notes:
- Our videos are vertical: pass `1080x1920` to run.sh. Steps 2 and 3 stay 16:9.
- SELFIES: his own selfies (ask once). If none, use `references/character_sheet_*.png` + `expressions_*.png` (max 7 refs).
- Cost: 15 x gpt_image_2_5 2k high = 41.25 credits, plus 15 outpaints. Quote with estimate_image_cost before running.
- Download flashcut.mp4 into `output/effects/flashcut.mp4`; the Cuts agent places it (hook/intro), length counts toward the 90 s.

---

Make me a film-strip flash cut with Higgsfield. Use the Higgsfield tools for every step. Follow these steps exactly and don't skip any.

INPUTS
- My selfies are attached. If you can't read them directly, open the Higgsfield upload box (media_upload_widget) so I can upload them, then continue.
- OUTFIT: [a red hoodie]
- SETTING: [a city street at night, wet road, streetlights and car lights behind]

STEP 1. Upload my selfies to Higgsfield and keep their media ids.

STEP 2. Make 15 photos of me with generate_image_batch (12 in the first batch, 3 in the second):
- model gpt_image_2_5, variant sunburst, quality high, resolution 2k, aspect_ratio 16:9
- medias: all my selfies, role image_references
- prompt for each, with OUTFIT and SETTING from INPUTS and SCENE replaced by line 1-15 below:
  "Real 35mm night film still, photo of the person in the reference images (same face, skin, hair and likeness exactly), wearing OUTFIT, in SETTING. LIGHTING IS CRITICAL: one hard warm streetlight key light from the LEFT side of the frame only, striking the left half of the face; the right half of the face falls into deep natural shadow, a hard shadow line down the nose, no fill light. Scene: SCENE. HEAD POSE IS CRITICAL: head facing the lens dead square, level, not turned, not tilted, chin level, calm intense stare straight into the lens, mouth closed. Tight close-up, face centred, eyes about 42% down from the top of the frame, both ears equally visible. Shot on film, shallow depth of field, real skin texture. No text, no logo, no watermark."
  1 teal-green street glow, warm bokeh
  2 deep navy sky, a yellow streetlight top left, blue-green bokeh
  3 very dark street, red and white car lights in bokeh
  4 a little closer, warm bokeh behind
  5 almost black background, faint gold bokeh
  6 navy night, blue bokeh on the right
  7 yellow and red bokeh, warm night
  8 dark background, sodium-orange glow
  9 red and white car lights in bokeh on the right
  10 a big yellow bokeh ball top left, small gold bokeh
  11 yellow bokeh on both sides
  12 white and red bokeh low on the right
  13 teal shop glow far behind, soft bokeh
  14 very dark, gold bokeh on the right edge
  15 dark warm night, dim bokeh
- Wait for all 15 with jobs_wait. Keep each result URL in order as s00 to s14 (line 1 = s00).

STEP 3. Expand each of the 15 photos with outpaint_image: image_id = that photo's job id, aspect_ratio 16:9, width 5120, height 2880 (they may come back smaller, use them as they are). Wait for all 15 (one can take several minutes; keep waiting, don't resubmit) and keep each result URL as s00 to s14.

STEP 4. Build the flash cut in the Higgsfield sandbox with sandbox_exec:
a) Run: mkdir -p /home/user/flash && cd /home/user/flash && curl -sfL -o kit.zip https://d2ol7oe51mr4n9.cloudfront.net/user_3GqzmWPIHg7iolqr77a3qJK8UKR/3abfd9eb-9421-4c04-8bbb-36e778cf5eff.zip && unzip -oq kit.zip && mkdir -p kit/shots kit/outpaint && ls kit/run.sh
   (If this first call times out while the sandbox starts up, run it again: it's safe to repeat.)
b) Download the 15 photos to kit/shots/s00.png ... kit/shots/s14.png and the 15 expanded photos to kit/outpaint/s00.png ... kit/outpaint/s14.png with curl -sfL (photo from step 2 and outpaint from step 3 with the same number go to the same name). Check there are 15 files in each folder.
c) Run bash /home/user/flash/kit/run.sh with background:true and size "xl" ([1920x1080] is the default; pass 1080x1920 as the first argument for a vertical version; steps 2 and 3 stay 16:9 either way). Poll it every 30 seconds with a foreground sandbox_exec running: sleep 30; tail -5 <the log_path it returned>, until it prints DONE (about 5-10 minutes, the first run also installs the tools).
d) If the log says STOP with lines starting with REDO, regenerate only those photos (same prompt and line from step 2), expand them again (step 3), put them in shots/ and outpaint/ under the same names, delete kit/locked and kit/frames, and run run.sh again. If the sandbox stops the job before DONE (it has a 15-minute limit), just run run.sh again: it carries on from the last finished stage.

STEP 5. Give me the video: call media_upload for flashcut.mp4 (content_type video/mp4), then in ONE sandbox_exec run curl -f -X PUT -H "Content-Type: video/mp4" -H "If-None-Match: *" --upload-file /home/user/flash/kit/flashcut.mp4 '<upload_url>', then media_confirm (type video), and show me the link. Then show me three frames: in the sandbox, shrink kit/frames/00005.png, 00030.png and 00055.png to 640x360 JPGs (360x640 for the vertical version) (python3 with Pillow) and pass those three JPGs as image_paths.

Tell me how many credits it used.
