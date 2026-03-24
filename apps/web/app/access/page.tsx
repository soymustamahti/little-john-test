import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { LockKeyhole } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DEFAULT_ACCESS_REDIRECT,
  ACCESS_GATE_COOKIE_NAME,
  isAccessGranted,
  normalizeAccessRedirect,
} from "@/lib/access-gate";

import { unlockWorkspace } from "./actions";

export default async function AccessPage({
  searchParams,
}: {
  searchParams: Promise<{
    error?: string;
    next?: string;
  }>;
}) {
  const params = await searchParams;
  const cookieStore = await cookies();
  const nextPath = normalizeAccessRedirect(params.next ?? DEFAULT_ACCESS_REDIRECT);
  const hasAccess = isAccessGranted(cookieStore.get(ACCESS_GATE_COOKIE_NAME)?.value);

  if (hasAccess) {
    redirect(nextPath);
  }

  const showError = params.error === "invalid";

  return (
    <main className="flex min-h-screen items-center justify-center bg-[color:var(--color-background)] px-4 py-10">
      <Card className="w-full max-w-md border-[color:var(--color-line)] bg-white/95 shadow-[0_28px_70px_rgba(24,32,51,0.12)]">
        <CardHeader className="space-y-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[color:var(--color-accent-soft)] text-[color:var(--color-accent)]">
            <LockKeyhole className="h-5 w-5" />
          </div>
          <div className="space-y-2">
            <CardTitle className="text-2xl text-[color:var(--color-ink)]">
              Workspace locked
            </CardTitle>
            <CardDescription className="text-sm text-[color:var(--color-muted)]">
              Enter the access password to open the Extract Agent operator workspace.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form action={unlockWorkspace} className="space-y-4">
            <input type="hidden" name="next" value={nextPath} />

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                placeholder="Enter password"
                required
              />
            </div>

            {showError ? (
              <p className="rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-warm-soft)] px-3 py-2 text-sm text-[color:var(--color-accent-warm)]">
                The password is incorrect.
              </p>
            ) : null}

            <div className="space-y-2">
              <Button type="submit" className="w-full">
                Unlock workspace
              </Button>
              <p className="text-xs text-[color:var(--color-muted)]">
                This is a web-only access gate. It is not a substitute for real backend
                authentication.
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
