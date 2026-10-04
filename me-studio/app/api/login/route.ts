import { NextResponse } from "next/server";
import { isValidPassword, passwordConfigured, sessionToken, SESSION_COOKIE } from "@/lib/auth";

export async function POST(request: Request) {
  if (!passwordConfigured()) {
    return NextResponse.json(
      { error: "No password is set. Add APP_PASSWORD in your hosting settings, then redeploy." },
      { status: 503 },
    );
  }
  const body = (await request.json().catch(() => ({}))) as { password?: unknown };
  const password = typeof body.password === "string" ? body.password : "";
  if (!(await isValidPassword(password))) {
    // Slow down guessing.
    await new Promise((r) => setTimeout(r, 800));
    return NextResponse.json({ error: "That password isn't right." }, { status: 401 });
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, await sessionToken(), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 180,
  });
  return res;
}
