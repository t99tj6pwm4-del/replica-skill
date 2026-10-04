import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { isValidSession, SESSION_COOKIE } from "./auth";

// Every API route checks the session itself, not only the proxy.
export async function requireSession(): Promise<NextResponse | null> {
  const jar = await cookies();
  if (await isValidSession(jar.get(SESSION_COOKIE)?.value)) return null;
  return NextResponse.json({ error: "Sign in again." }, { status: 401 });
}
