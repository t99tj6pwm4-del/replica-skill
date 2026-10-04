import { NextResponse } from "next/server";
import { aiMode, buildPrompt, client, GENERATOR, isFalUrl, unconfiguredResponse } from "@/lib/ai";
import { requireSession } from "@/lib/require-session";

export const maxDuration = 120;

const MAX_PROMPT = 500;

// Makes photos of you. Returns them as data URLs so the browser can keep
// copies without depending on fal's links staying up.
export async function POST(request: Request) {
  const denied = await requireSession();
  if (denied) return denied;

  const body = (await request.json().catch(() => ({}))) as {
    prompt?: unknown;
    loraUrl?: unknown;
    count?: unknown;
    shape?: unknown;
  };
  const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
  const loraUrl = typeof body.loraUrl === "string" ? body.loraUrl : "";
  const count = body.count === 1 || body.count === 2 || body.count === 4 ? body.count : 2;
  const shape = body.shape === "square_hd" || body.shape === "landscape_4_3" ? body.shape : "portrait_4_3";

  if (!prompt) return NextResponse.json({ error: "Describe the photo you want first." }, { status: 400 });
  if (prompt.length > MAX_PROMPT) {
    return NextResponse.json({ error: `Keep the description under ${MAX_PROMPT} characters.` }, { status: 400 });
  }
  if (!isFalUrl(loraUrl)) {
    return NextResponse.json({ error: "Your persona is missing. Set it up again in Settings." }, { status: 400 });
  }

  const mode = aiMode();
  if (mode === "unconfigured") return NextResponse.json(unconfiguredResponse(), { status: 503 });
  if (mode === "fake" || loraUrl.startsWith("https://fake.fal.media/")) {
    if (mode !== "fake") {
      return NextResponse.json({ error: "This was a practice persona. Make a real one in Settings." }, { status: 400 });
    }
    await new Promise((r) => setTimeout(r, 1500));
    return NextResponse.json({ images: Array.from({ length: count }, (_, i) => fakeImage(prompt, i, shape)) });
  }

  try {
    const fal = client();
    const result = await fal.subscribe(GENERATOR, {
      input: {
        prompt: buildPrompt(prompt),
        loras: [{ path: loraUrl, scale: 1 }],
        image_size: shape,
        num_images: count,
        output_format: "jpeg",
        enable_safety_checker: true,
      },
    });
    const data = result.data as { images?: { url: string }[]; has_nsfw_concepts?: boolean[] };
    const kept = (data.images ?? []).filter((_, i) => !data.has_nsfw_concepts?.[i]);
    if (kept.length === 0) {
      return NextResponse.json(
        { error: "The AI service blocked this one. Try describing it differently." },
        { status: 422 },
      );
    }
    const images = await Promise.all(kept.map((img) => toDataUrl(img.url)));
    return NextResponse.json({ images });
  } catch (err) {
    console.error("generate failed", err);
    return NextResponse.json(
      { error: "The photos didn't come through. Check your fal balance and try again." },
      { status: 502 },
    );
  }
}

async function toDataUrl(url: string): Promise<string> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`image fetch ${res.status}`);
  const type = res.headers.get("content-type") ?? "image/jpeg";
  const bytes = Buffer.from(await res.arrayBuffer());
  return `data:${type};base64,${bytes.toString("base64")}`;
}

function fakeImage(prompt: string, i: number, shape: string): string {
  const [w, h] = shape === "square_hd" ? [1024, 1024] : shape === "landscape_4_3" ? [1024, 768] : [768, 1024];
  const hue = (prompt.length * 37 + i * 70) % 360;
  const text = prompt.replace(/[<>&"]/g, "").slice(0, 60);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl(${hue},45%,38%)"/><stop offset="1" stop-color="hsl(${(hue + 60) % 360},50%,18%)"/></linearGradient></defs>
<rect width="100%" height="100%" fill="url(#g)"/>
<circle cx="${w / 2}" cy="${h * 0.42}" r="${w * 0.16}" fill="rgba(255,255,255,.18)"/>
<rect x="${w * 0.25}" y="${h * 0.6}" width="${w * 0.5}" height="${h * 0.4}" rx="${w * 0.2}" fill="rgba(255,255,255,.14)"/>
<text x="50%" y="${h * 0.12}" text-anchor="middle" font-family="sans-serif" font-size="${w * 0.04}" fill="#fff">Practice photo ${i + 1}</text>
<text x="50%" y="${h * 0.18}" text-anchor="middle" font-family="sans-serif" font-size="${w * 0.028}" fill="rgba(255,255,255,.8)">${text}</text>
</svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString("base64")}`;
}
