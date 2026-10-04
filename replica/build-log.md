# Build log

| ID | date | status | missing / notes |
| --- | --- | --- | --- |
| login | 2026-10-04 | done | password gate, not in the original |
| S01+S02 | 2026-10-04 | done | welcome and selfie picker merged into one screen |
| S03 | 2026-10-04 | done | progress is an estimate; fal's queue doesn't give a percentage |
| S04 | 2026-10-04 | skipped | no paywall for personal use |
| S05+S06 | 2026-10-04 | done | create and results on one screen |
| S07 | 2026-10-04 | done | share sheet on iPhone, download elsewhere |
| S08 | 2026-10-04 | done | |
| S09 | 2026-10-04 | done | |

Tested end to end in practice mode (`FAKE_AI=1`) on an iPhone 13 sized browser:
sign-in, wrong password, picking 5 then 13 selfies, removing one, training,
reload during training, making 4 photos, viewer, gallery, delete, settings.
API checks: no session gets 401, a non-fal LoRA URL gets 400.
Not yet tested with a real fal key.
