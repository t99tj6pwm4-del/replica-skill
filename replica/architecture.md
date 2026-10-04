# Architecture: Me Studio (a personal rebuild of RealYou AI's core features)

Built as a website for iPhone instead of a native app, because there is no Mac
to build and install an iOS app. Add it to the Home Screen and it opens full
screen like an app.

## Stack

| layer | choice | why |
| --- | --- | --- |
| web | Next.js 16 (App Router) + TypeScript, in `me-studio/` | one project for screens and the small server part |
| styling | plain CSS with tokens in `app/globals.css` | a handful of screens, no framework needed |
| AI | fal.ai: `flux-lora-portrait-trainer` to learn the face, `flux-lora` to make photos | official public API, pay per use, no subscription |
| database | none | one person; persona in localStorage, photos in IndexedDB on the phone |
| auth | one password (`APP_PASSWORD`), HMAC session cookie | stops strangers spending the fal balance |
| payments, email, jobs | none | personal use; training is polled from the phone |
| hosting | Vercel (free tier) | connects to GitHub, holds the fal key server side |

## Data

No server tables. On the device:

- `localStorage["me-studio.persona"]`: state (training, ready, failed), fal job id, LoRA URL, selfie count, dates
- IndexedDB `me-studio/photos`: id, prompt, createdAt, image as a data URL

## API

| method path | does | who | input | output | flow |
| --- | --- | --- | --- | --- | --- |
| POST /api/login | checks the password, sets the cookie | anyone | password | ok | - |
| POST /api/logout | clears the cookie | signed in | - | ok | - |
| POST /api/persona | uploads the selfie zip to fal (deleted after 1 day), starts training | signed in | zip (multipart, max 4.4 MB) | jobId | F01 |
| GET /api/persona/[id] | training status | signed in | job id | state, loraUrl | F01 |
| POST /api/generate | makes 1, 2 or 4 photos with the LoRA | signed in | prompt, loraUrl (fal.media only), count, shape | images as data URLs | F02 |

Every API route checks the session itself, as well as `proxy.ts`.
`FAKE_AI=1` (with no `FAL_KEY`) runs practice mode: instant training and placeholder photos.

## The parts that bite

- Body size: Vercel caps requests at 4.5 MB, so the phone shrinks and zips the selfies first.
- Training takes about 10 minutes; the phone polls every 15 s and picks up after a reload.
- iPhone Safari can clear site storage after 7 days without a visit unless the site is on the Home Screen. Photos you love should be saved to Photos.
- Cost: about $3.60 per training (1500 steps), about 3 cents per photo.

## Build order

1. Vertical slice: S02 upload, S03 training, S05/S06 create and results. Done.
2. Must-haves: save/share, full-screen viewer. Done.
3. Should-haves: gallery, delete photo, delete everything, prompt ideas. Done.
4. Next: try it with a real fal key and tune the prompt wording and training steps.
