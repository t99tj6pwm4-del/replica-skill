import { NextResponse } from "next/server";
import { aiMode, client, TRAINER, unconfiguredResponse } from "@/lib/ai";
import { requireSession } from "@/lib/require-session";

const FAKE_TRAINING_MS = 8000;

// Training status: { state: "queued" | "training" | "ready" | "failed", loraUrl? }
export async function GET(_request: Request, ctx: { params: Promise<{ id: string }> }) {
  const denied = await requireSession();
  if (denied) return denied;
  const { id } = await ctx.params;

  const mode = aiMode();
  if (id.startsWith("fake-")) {
    const started = Number(id.slice(5));
    if (mode !== "fake" || !Number.isFinite(started)) {
      return NextResponse.json({ state: "failed", error: "This was a practice persona. Make a real one." });
    }
    const done = Date.now() - started > FAKE_TRAINING_MS;
    return NextResponse.json(
      done ? { state: "ready", loraUrl: "https://fake.fal.media/practice-lora.safetensors" } : { state: "training" },
    );
  }
  if (mode !== "real") return NextResponse.json(unconfiguredResponse(), { status: 503 });

  const fal = client();
  try {
    const status = await fal.queue.status(TRAINER, { requestId: id });
    if (status.status === "IN_QUEUE") return NextResponse.json({ state: "queued" });
    if (status.status === "IN_PROGRESS") return NextResponse.json({ state: "training" });
  } catch (err) {
    console.error("training status failed", err);
    return NextResponse.json({ error: "Couldn't reach the AI service. Trying again soon." }, { status: 502 });
  }

  try {
    const result = await fal.queue.result(TRAINER, { requestId: id });
    const data = result.data as { diffusers_lora_file?: { url?: string } };
    const loraUrl = data.diffusers_lora_file?.url;
    if (!loraUrl) throw new Error("no lora file in result");
    return NextResponse.json({ state: "ready", loraUrl });
  } catch (err) {
    console.error("training result failed", err);
    return NextResponse.json({
      state: "failed",
      error: "Training didn't finish. Try again with clearer selfies of just you.",
    });
  }
}
