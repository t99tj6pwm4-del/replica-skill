// Single-user password gate. The cookie holds an HMAC of the password, so
// changing APP_PASSWORD signs everyone out.
export const SESSION_COOKIE = "me_studio_session";

async function hmac(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return Buffer.from(sig).toString("hex");
}

export function passwordConfigured(): boolean {
  return (process.env.APP_PASSWORD ?? "").length > 0;
}

export async function sessionToken(): Promise<string> {
  return hmac(process.env.APP_PASSWORD ?? "", "me-studio-session-v1");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function isValidSession(value: string | undefined): Promise<boolean> {
  if (!passwordConfigured() || !value) return false;
  return safeEqual(value, await sessionToken());
}

export async function isValidPassword(input: string): Promise<boolean> {
  if (!passwordConfigured()) return false;
  // Compare HMACs so the check takes the same time whatever the input.
  const [a, b] = await Promise.all([
    hmac("me-studio-compare", input),
    hmac("me-studio-compare", process.env.APP_PASSWORD ?? ""),
  ]);
  return safeEqual(a, b);
}
