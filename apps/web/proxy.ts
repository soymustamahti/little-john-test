import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import {
  ACCESS_GATE_COOKIE_NAME,
  isAccessGranted,
  normalizeAccessRedirect,
} from "@/lib/access-gate";

function isPublicPath(pathname: string): boolean {
  return pathname === "/access" || pathname.startsWith("/access/");
}

export function proxy(request: NextRequest): NextResponse {
  const { pathname, search } = request.nextUrl;

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const accessCookie = request.cookies.get(ACCESS_GATE_COOKIE_NAME)?.value;
  if (isAccessGranted(accessCookie)) {
    return NextResponse.next();
  }

  const accessUrl = new URL("/access", request.url);
  accessUrl.searchParams.set("next", normalizeAccessRedirect(`${pathname}${search}`));
  return NextResponse.redirect(accessUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
