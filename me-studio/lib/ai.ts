import { fal } from "@fal-ai/client";

export const TRAINER = "fal-ai/flux-lora-portrait-trainer";
export const GENERATOR = "fal-ai/flux-lora";
// A made-up word the trainer ties to your face. Prompts get it added.
export const TRIGGER = "MSTDOK";
// 1500 steps costs about $3.60 on fal (billed per step). More steps can look
// more like you but cost more.
export const TRAINING_STEPS = 1500;

export type Mode = "real" | "fake" | "unconfigured";

export function aiMode(): Mode {
  if (process.env.FAL_KEY) return "real";
  if (process.env.FAKE_AI === "1") return "fake";
  return "unconfigured";
}

let configured = false;
export function client() {
  if (!configured) {
    fal.config({ credentials: process.env.FAL_KEY });
    configured = true;
  }
  return fal;
}

// Only accept LoRA files that fal itself produced.
export function isFalUrl(raw: string): boolean {
  try {
    const u = new URL(raw);
    return (
      u.protocol === "https:" &&
      (u.hostname === "fal.media" || u.hostname.endsWith(".fal.media"))
    );
  } catch {
    return false;
  }
}

export function buildPrompt(userPrompt: string): string {
  return `photo of ${TRIGGER} person, ${userPrompt.trim()}, realistic photo, natural skin texture`;
}

export function unconfiguredResponse() {
  return {
    error:
      "The AI service isn't set up yet. Add FAL_KEY in your hosting settings, then redeploy.",
  };
}
