# Recon map: RealYou AI - Photos of You (iOS)

Scope: the core loop only. Upload selfies, train a personal "persona", type a scene, get realistic photos of yourself, save or share them.
For: the user's personal use. One person, their own face, not published on the App Store, no payments.
Date: 2026-10-04

## Sources

| # | source | URL | notes |
| --- | --- | --- | --- |
| 1 | App Store listing | https://apps.apple.com/us/app/-/id6670333062 | description, in-app purchases, 4.3 stars (261 ratings), v1.6.11, iOS 17+ |
| 2 | Privacy policy | https://walter-labs.com/persona/privacy | not read in detail yet |
| 3 | Terms of use | http://www.walter-labs.com/persona/terms | not read; the clone uses public sources only, no account |
| 4 | Third-party listing | https://creati.ai/ai-tools/persona-ai/ | the app is also known as "Persona AI" |

No help center, changelog or walkthrough videos were found. The screens below are inferred from the listing text and are marked as guesses where they are.

## Core loop

Upload 12 to 20 selfies once, then type any scene ("me hiking in Patagonia at golden hour") and get photos that look like real photos of you.

## Screens

| ID | screen | route / how to reach | purpose | key components | states seen |
| --- | --- | --- | --- | --- | --- |
| S01 | Welcome | first launch | explain the app, start setup | hero image, Get started button | default |
| S02 | Selfie upload | S01 > Get started | pick 12 to 20 selfies from Photos | photo picker, photo grid, counter (n/20), tips, Continue | empty, partial (<12), ready, too many |
| S03 | Persona training | S02 > Continue | wait while the model learns your face | progress indicator, time estimate | in progress, done, failed |
| S04 | Paywall | before training (per reviews) | pay to create a persona | plan cards, Restore | default, purchase failed. **Skipped in the clone** |
| S05 | Create (prompt) | home tab | describe a scene and generate | prompt box, style suggestions, Generate button, credits left | empty, typing, generating, error, out of credits |
| S06 | Results | after S05 | view the generated photos | photo grid, full-screen viewer | loading, filled, error |
| S07 | Photo detail | tap a photo in S06 or S08 | look closer, save, share | full-screen image, Save, Share, Delete | default |
| S08 | Gallery | gallery tab | every photo made so far | photo grid | empty, filled |
| S09 | Settings | gear icon | manage persona and data | redo persona, delete all data | default |

## Flows

```
F01 Set up my persona (once)
    S01 -> S02 -> S03
    happy path taps: about 5, plus picking 12-20 photos
    edge: fewer than 12 photos, blurry or group photos, sunglasses, training fails, app closed during training

F02 Make a photo of me
    S05 -> S06 -> S07
    happy path taps: 3 (type, Generate, tap a result)
    edge: vague prompt, prompt blocked by the AI provider's safety filter, slow network, face looks wrong

F03 Save or share a photo
    S07 -> iOS share sheet
    happy path taps: 2

F04 Delete my data
    S09 -> confirm
    edge: reviews say the original has no way to delete photos; the clone should
```

## Components

| component | variants | states | used on |
| --- | --- | --- | --- |
| Button | primary, secondary, destructive | default, pressed, disabled, loading | all |
| Photo grid | picker, results, gallery | empty, loading placeholders, filled | S02, S06, S08 |
| Prompt box | single field with suggestions | empty, typing, disabled while generating | S05 |
| Progress view | training, generating | running, done, failed | S03, S05 |
| Full-screen photo viewer | - | default, zoomed | S07 |
| Tab bar | Create, Gallery | - | S05, S08 |

## Inferred data model

```
Persona     id, status (uploading | training | ready | failed), selfie_count,
            model_ref (id of the trained face model at the AI provider), created_at
            evidence: listing "upload 12-20 selfies", "Create Your Persona" purchase
            confidence: high

Selfie      id, persona_id, local_file, uploaded_url
            evidence: listing
            confidence: high

Generation  id, persona_id, prompt, status (queued | running | done | failed),
            created_at, error
            evidence: "Pack of 10 / 25 Generations" purchases
            confidence: high

Photo       id, generation_id, file, width, height, saved_to_photos (bool)
            evidence: listing "instant sharing"
            confidence: medium (how many photos per generation is a guess)
```

Relationships: Persona 1-n Selfie, Persona 1-n Generation, Generation 1-n Photo.
For a one-person app there is no User entity and no server database; everything can live on the phone.

## Feature matrix

See `features.csv`. Must: 9, should: 5, could: 3, skip: 3.

## Out of scope (cannot or should not be cloned)

- Their own AI model and tuning. The clone uses a hosted image model that learns a face from photos; results will look different.
- Payments, subscriptions and the paywall. Not needed for personal use.
- The RealYou name, icon, screenshots and marketing text.
- Photos of anyone other than the user. The clone is for your own face only.

## Size

Screens 8 (S04 skipped), flows 4, entities 4.

Hard parts:
1. **The AI itself.** Training a face model and generating photos runs on a paid AI service (roughly a few dollars per persona and a few cents per photo). It needs an API key, and the key must not sit inside the app where it can be pulled out; a tiny server or serverless function holds it.
2. **Installing on your iPhone.** Needs a Mac with Xcode. A free Apple account works, but the app stops opening after 7 days until you reinstall it from the Mac. The $99/year developer account removes that limit.
3. **Long waits.** Training takes minutes; the app must survive being closed and pick up where it left off.

Size: **S** (a weekend) for a working personal version, if you have a Mac.
