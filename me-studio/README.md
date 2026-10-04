# Me Studio

A private website that makes realistic AI photos of you. Pick 12 to 20
selfies once, then describe any scene. A personal rebuild of the core of
RealYou AI; see `../replica/` for the plan.

## Settings (environment variables)

| name | what |
| --- | --- |
| `FAL_KEY` | API key from https://fal.ai/dashboard/keys. Pays for training (about $3.60) and photos (about 3¢ each). |
| `APP_PASSWORD` | the password you type to open the site |
| `FAKE_AI` | `1` for practice mode with no AI key: placeholder photos, nothing charged |

## Run locally

```
npm install
APP_PASSWORD=pick-one FAKE_AI=1 npm run dev
```

## Put it online (Vercel)

1. Import this GitHub repo at vercel.com/new.
2. Set **Root Directory** to `me-studio`.
3. Add `FAL_KEY` and `APP_PASSWORD` under Environment Variables, then Deploy.
4. On your iPhone, open the site in Safari, tap Share, then **Add to Home Screen**.
