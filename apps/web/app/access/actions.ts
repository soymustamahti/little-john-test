"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  ACCESS_GATE_COOKIE_NAME,
  ACCESS_GATE_COOKIE_VALUE,
  getAccessPassword,
  normalizeAccessRedirect,
} from "@/lib/access-gate";

export async function unlockWorkspace(formData: FormData): Promise<void> {
  const password = String(formData.get("password") ?? "");
  const nextPath = normalizeAccessRedirect(String(formData.get("next") ?? ""));

  if (password !== getAccessPassword()) {
    redirect(`/access?error=invalid&next=${encodeURIComponent(nextPath)}`);
  }

  const cookieStore = await cookies();
  cookieStore.set(ACCESS_GATE_COOKIE_NAME, ACCESS_GATE_COOKIE_VALUE, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12,
  });

  redirect(nextPath);
}
