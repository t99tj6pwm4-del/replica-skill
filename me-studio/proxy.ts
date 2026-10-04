import { NextResponse, type NextRequest } from "next/server";
import { isValidSession, SESSION_COOKIE } from "@/lib/auth";

export async function proxy(request: NextRequest) {
  if (await isValidSession(request.cookies.get(SESSION_COOKIE)?.value)) {
    return NextResponse.next();
  }
  if (request.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.json({ error: "Sign in again." }, { status: 401 });
  }
  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  return NextResponse.redirect(url);
}

export const config = {
  // Everything except the sign-in page, its API, Next's own files and the
  // icons/manifest the home screen needs before you sign in.
  matcher: [
    "/((?!login|api/login|_next/static|_next/image|favicon.ico|icon.svg|apple-icon|manifest.webmanifest).*)",
  ],
};
