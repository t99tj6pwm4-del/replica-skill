import { NextResponse } from "next/server";
import { aiMode, client, TRAINER, TRAINING_STEPS, TRIGGER, unconfiguredResponse } from "@/lib/ai";
import { requireSession } from "@/lib/require-session";

export const maxDuration = 60;

const MAX_ZIP_BYTES = 4_400_000; // Vercel rejects request bodies over 4.5 MB.

// Starts training a face model from a zip of selfies. Returns a job id the
// app polls with GET /api/persona/[id].
export async function POST(request: Request) {
  const denied = await requireSession();
  if (denied) return denied;

  const form = await request.formData().catch(() => null);
  const zip = form?.get("selfies");
  if (!(zip instanceof Blob) || zip.size === 0) {
    return NextResponse.json({ error: "No selfies were sent." }, { status: 400 });
  }
  if (zip.size > MAX_ZIP_BYTES) {
    return NextResponse.json({ error: "The selfies are too large to send. Try fewer photos." }, { status: 413 });
  }

  const mode = aiMode();
  if (mode === "unconfigured") return NextResponse.json(unconfiguredResponse(), { status: 503 });
  if (mode === "fake") return NextResponse.json({ jobId: `fake-${Date.now()}` });

  try {
    const fal = client();
    // The selfies are only needed for training, so fal deletes them after a day.
    const url = await fal.storage.upload(zip, { lifecycle: { expiresIn: "1d" } });
    const { request_id } = await fal.queue.submit(TRAINER, {
      input: { images_data_url: url, trigger_phrase: TRIGGER, steps: TRAINING_STEPS },
    });
    return NextResponse.json({ jobId: request_id });
  } catch (err) {
    console.error("training submit failed", err);
    return NextResponse.json(
      { error: "The AI service didn't accept the photos. Check your fal balance and try again." },
      { status: 502 },
    );
  }
}
