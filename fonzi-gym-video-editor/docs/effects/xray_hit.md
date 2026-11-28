# X-ray hit (Higgsfield recipe)

Source: https://ruby-cotija-fb5.notion.site/Make-the-x-ray-effect-with-Claude-or-Codex-40728691eca3813a9161ea2e8271b8da
Saved verbatim from Alfonso's message, 2026-11-19. When to use it and the credit budget: see the Director's standing answer 13 (`.claude/agents/fonzi-director.md`).

Team notes:
- CLIP: a short piece (2-4 s) cut from `output/cut_version.mp4` that ends on the hit moment (hardest rep or the song drop), sharp frame, head in frame. Never another creator's footage.
- Cost: 3 tries x 2.75 = 8.25 credits (gpt_image_2_6 2k high).
- Download xray.mp4 into `output/effects/xray.mp4`; the Cuts agent splices it back frame-exact in place of that piece. Put the whoosh SFX at the hit start time the build prints.

---

Add the x-ray hit to my clip with Higgsfield: tracking boxes lock onto the person, then it flashes negative, snaps back, holds an x-ray of them for a split second and hard cuts. Use the Higgsfield tools for every step, with credits (no project or folder needed). Follow these steps exactly and don't skip any.

INPUTS
- My clip is attached. If you can't read it directly, open the Higgsfield upload box (media_upload_widget) so I can upload it, then continue.
- CUT: [end] (where the hit ends and the video cuts: "end" is straight after the clip's last frame. Or give a frame number counted from 0, and anything after it plays as normal.)

STEP 1. Upload the clip to Higgsfield (if it isn't there already) and keep its URL.

STEP 2. Set up the kit in the Higgsfield sandbox with sandbox_exec. First pick a fresh folder just for this run, /home/user/xray-<6 random digits>, and use it as DIR everywhere below (other chats on your account share the sandbox, so never reuse a folder).
a) Run: mkdir -p DIR && cd DIR && curl -sfL -o kit.zip https://d2ol7oe51mr4n9.cloudfront.net/user_3GqzmWPIHg7iolqr77a3qJK8UKR/d962ec5e-eeb1-4002-9208-af3523124c88.zip && unzip -oq kit.zip && mkdir -p kit/clips kit/tries && ls kit/run.sh
   (If this first call times out while the sandbox starts up, run it again: it's safe to repeat.)
b) Download the clip to DIR/kit/clips/clip.mp4 with curl -sfL.
c) Run: bash DIR/kit/run.sh frame   (add --cut <frame number> if CUT isn't "end")
   It installs its tools first, which can take a minute or two: run it with background:true, then check its log every 30 seconds (sleep 30; tail -5 <log_path>) until it prints the aspect ratio. It saves DIR/kit/xray-source.jpg (the exact frame the x-ray replaces) and prints the aspect ratio for the x-ray. Then, in a separate foreground sandbox_exec (for example ls DIR/kit), pass DIR/kit/frame-small.jpg as an image_path and look closely: the person, everything they're wearing and holding, the background and the light. If they're blurred mid-move or their head is cut off, tell me and suggest an earlier CUT instead of carrying on.

STEP 3. Upload the frame: call media_upload for xray-source.jpg (content_type image/jpeg), then in ONE sandbox_exec run curl -f -X PUT -H "Content-Type: image/jpeg" -H "If-None-Match: *" --upload-file DIR/kit/xray-source.jpg '<upload_url>', then media_confirm (type image). Keep the media id.

STEP 4. Make 3 x-ray tries with generate_image directly (not a preset or any other tool): model gpt_image_2_6, quality high, resolution 2k, aspect_ratio = the one step 2c printed, count 3, medias = the frame only (role image_references). Fill in the brackets in this prompt from what you saw in the frame:
"Edit this exact frame. Keep the camera, framing, pose, [everything they're wearing and holding], [the background] and light with every edge in the same place. Turn it into a medical x-ray where their head shows only bone: a skull, the teeth and the dark nasal cavity, and nothing of their face. No lips, no nose, no skin, no eyebrows, no facial features at all: where the nose was there is only the triangular nasal opening of the skull, where the mouth was there are only bare teeth. The skull is fitted to their head and matches its angle: turned the same way, tilted the same way, the jaw bone follows their jawline, the chin bone ends exactly where their chin was, the jaw no wider than their face. Neck vertebrae, collarbones, ribs and the bones of their arms and hands show through. [What they're wearing and holding] turn translucent like x-ray film with their seams readable. Cold blue-cyan x-ray film tint over the whole frame, background included, bright bone and dark soft tissue. Photoreal, not an illustration, no glow outlines, no text."
If the tool asks whether to spend free-trial generations or credits, ask me once and go with my answer (free-trial generations come one per call, so then make 3 calls). Keep calling jobs_wait (it waits up to 15 seconds each time) until all 3 are done, about a minute.

STEP 5. Keep the best one: download the 3 results to DIR/kit/tries/x1.png, x2.png and x3.png with curl -sfL, then run: bash DIR/kit/run.sh tries   (with image_paths DIR/kit/tries.jpg in the same call)
   tries.jpg shows the frame and each try, each with a close-up of the head. Keep the try where the skull sits inside their head at the same angle, the chin bone ends where their chin was, and everything else (clothes, background, framing) stayed put. The edge match it prints breaks a tie (higher is better). If all 3 are bad (a face still showing, a drawing, the framing moved), tell me and make 3 more, once.

STEP 6. Build the hit: run cp DIR/kit/tries/<your pick> DIR/kit/xray.png && bash DIR/kit/run.sh build   (with the same --cut if you used one)
   Give the call timeout_seconds 120 and image_paths DIR/kit/frames.jpg, DIR/kit/fit.jpg and DIR/kit/hud.jpg. It fits the x-ray onto the frame, tracks three points on the person, and builds it: the tracking boxes lock on about half a second before the hit, then 4 frames negative, 3 as shot, 3 frames of x-ray, hard cut (the counts scale with the frame rate). Check the x-ray sits on the frame (fit.jpg) and the boxes sit on the person, not the background (hud.jpg). If a box sits on the background, run the build again with --points "x,y;x,y;x,y" (fractions of the frame, the main box first, on strong detail like a logo, a zip or an edge of what they hold).

STEP 7. Give me the video: call media_upload for xray.mp4 (content_type video/mp4), then in ONE sandbox_exec run curl -f -X PUT -H "Content-Type: video/mp4" -H "If-None-Match: *" --upload-file DIR/kit/xray.mp4 '<upload_url>', then media_confirm (type video), and show me the link. Tell me the time the hit starts (the build prints it) so I can put a sound there.

Tell me how many credits it used: each x-ray try costs 2.75, so 3 tries is 8.25 (check with transactions; other jobs on the account can move the balance at the same time).
