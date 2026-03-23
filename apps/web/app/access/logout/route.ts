import { NextResponse } from "next/server";

import { ACCESS_GATE_COOKIE_NAME } from "@/lib/access-gate";

export async function GET(request: Request): Promise<NextResponse> {
  const response = NextResponse.redirect(new URL("/access", request.url));
  response.cookies.set(ACCESS_GATE_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    expires: new Date(0),
  });
  return response;
}
