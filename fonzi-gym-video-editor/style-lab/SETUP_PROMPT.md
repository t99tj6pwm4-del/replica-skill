# Style Lab setup prompt

Source: https://ruby-cotija-fb5.notion.site/Style-Lab-3f428691eca38128a16bc80fcb2c6487 (template by Shaan Johari). Saved 2026-11-19.
Template: `style-lab.html` (read in full; plain page, no outside scripts). Publish with capabilities {db, user, assets} only with Alfonso's OK.

```
I want to build my own visual style with Style Lab (style-lab.html in this folder). Set it up and run it like this.

SETUP (once)
1. Publish style-lab.html as an artifact with capabilities {"db": {}, "user": {}, "assets": {}}, and reuse that same artifact for every round. Send me the link.
2. Ask me where my sound effects library is (one or more folders on this computer). If I don't have one, or a round needs a sound I don't have, offer to create it with an AI sound effects generator instead (ask which one I use, and only use one I've got access to). Scan it for audio files (wav, aif, aiff, mp3, flac, m4a, ogg). For each file, note the path, the pack (its top folder), the file name and its length. Group them by what they are, using folder and file names: clicks and UI, whooshes, hits and impacts, risers, glitches, foley, ambience, other. Save the full index as sound-library.json and a short summary (counts per group, the main packs) as SOUND-LIBRARY.md in this folder. Never upload or copy my library anywhere, except the few sounds that go into a round's renders.
3. Ask for my Instagram handle, or read the "profile/request" document if I typed it into Style Lab's "Preview as" box. Open my public profile page signed out: its og:image is my profile picture and its og:title has my name. Save the picture, upload it to the artifact's assets, and write profile/current {handle, name, pfp: <asset id>}, so the safe-zone preview shows my own account. If profile/current already has upl: true, I uploaded my own photo in Style Lab, so keep that photo and only fill in the handle and name. Do the same whenever I say "use my Instagram".
4. Use whatever animation setup you can run here (Remotion if it's installed, otherwise HTML and CSS rendered to video with a headless browser, or ffmpeg). Ask me before installing anything.

THE BRIEF (before round 1)
Interview me one question at a time. Wait for each answer before the next one, and follow up when an answer is vague:
1. What's the style for? (YouTube videos, reels, a brand, a client, something else)
2. Where will it live, and what shape is the video? (vertical 9:16, wide 16:9, square)
3. Who's watching, and what should they feel in the first second?
4. Send me three to five references you love and tell me what you love about each one.
5. What do you never want to see?
6. What do you already have that it should use: fonts, colours, a logo, a name?
7. How should things move? (snappy, smooth, bouncy, filmic, physical, glitchy, or "show me")
8. How should it sound?
9. What should we build first? (titles, captions, transitions, lower thirds, data graphics, sounds)
Then write the answers into STYLE.md as "The brief", read it back to me in five lines, and wait for my OK. Build only from my brief and my references, never from a style you've seen elsewhere. Only use fonts I already have or free fonts I'm allowed to use.

IDEAS LIBRARY
For techniques (how a move or effect is built), look through the motion graphics and explainer prompts in https://github.com/yihui-dev/awesome-opus5-5-videos (the prompts/ folder and data/videos.json). Borrow the technique, never the look: colours, fonts and feel always come from my brief. If an option is closely based on one of those prompts, say which one in its card description.

EACH ROUND (when I ask for one)
1. Make the options. Group them into sections by job (titles, captions, transitions, sounds, whatever we're working on), three to six options per section. Change one thing per option so the comparison is fair, and use the same words and footage across a section.
2. Sounds come from my library (picked from sound-library.json), or are made with AI when I've said that's fine. Never take sounds from anywhere else. Trim each one, give it short fades, keep peaks under -1 dB, and play it on a short animation of the thing it's for, so I hear it in context.
3. Render each option twice: a small looping preview (a muted MP4 or WebP under 2 MB) and a full-quality MP4 with sound.
4. Upload both to the artifact's assets and keep each asset id.
5. Clear the last round: delete every document in "cards" and "sections". Then write:
   - round/current: {title, round, intro, notes: [one line for each thing you changed since last round], aspect: "9:16" or whatever my brief says}
   - sections/<id>: {name, use: one line on what the section is for, order}
   - cards/<id>: {section, label, desc: one line on what's different about this one, preview: <asset id>, full: <asset id>, source: "<pack> / <file name>" for sounds, order}
   Put the round number in every card id (r2-03a) so notes never mix between rounds. Anything I've locked in goes in a "Locked in" section with locked: true, so the whole style stays in one place.
6. Send me the link.

WHEN I SAY "done"
1. Read the newest document in "submissions" (it holds every verdict and note) and the "notes" collection.
2. Tell me in a few lines what I kept, what I dropped, and any patterns in my notes.
3. Update STYLE.md: keeps go under "Locked", drops go under "Rejected" with my reason, and add open questions.
4. Build the next round from my notes. Fix every Maybe the way the note says, push the Keeps further with new variations, and leave out what I dropped. Never bring back something I rejected unless I ask.

When everything in a section is locked, write it up in STYLE.md as rules someone else could follow: fonts and sizes, colours, how things move and how long they take, which sounds go on what, and what never to do.
```
