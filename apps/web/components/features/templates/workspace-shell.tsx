"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileStack,
  LogOut,
  Shapes,
  Sparkles,
  Tag,
} from "lucide-react";

import {
  TOUR_RESTART_EVENT,
  WorkspaceOnboardingTour,
} from "@/components/features/onboarding/workspace-onboarding-tour";
import { LanguageSwitcher } from "@/components/features/templates/language-switcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useLocale } from "@/providers/locale-provider";

function NavLink({
  href,
  icon: Icon,
  label,
  isActive,
  tourId,
}: {
  href: string;
  icon: typeof Shapes;
  label: string;
  isActive: boolean;
  tourId?: string;
}) {
  return (
    <Link
      href={href}
      data-tour={tourId}
      className={cn(
        "flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium transition",
        isActive
          ? "bg-[color:var(--color-accent-soft)] text-[color:var(--color-accent)]"
          : "text-[color:var(--color-muted)] hover:bg-white/70 hover:text-[color:var(--color-ink)]",
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </Link>
  );
}

export function WorkspaceShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { messages } = useLocale();

  return (
    <main className="min-h-screen bg-[color:var(--color-background)]">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside className="w-full border-b border-[color:var(--color-line)] bg-white/90 p-4 lg:w-64 lg:border-b-0 lg:border-r lg:p-6">
          <div className="space-y-6">
            <div data-tour="workspace-overview">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--color-muted)]">
                {messages.shell.workspaceLabel}
              </p>
              <h1 className="mt-2 text-2xl font-semibold text-[color:var(--color-ink)]">
                {messages.shell.title}
              </h1>
              <p className="mt-2 text-sm text-[color:var(--color-muted)]">
                {messages.shell.description}
              </p>
            </div>

            <nav className="space-y-2">
              <div className="px-4 pt-1 text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                {messages.shell.documentSetup}
              </div>
              <NavLink
                href="/extraction-templates"
                icon={Shapes}
                label={messages.shell.extractionTemplates}
                isActive={pathname.startsWith("/extraction-templates")}
                tourId="nav-templates"
              />
              <NavLink
                href="/document-categories"
                icon={Tag}
                label={messages.shell.documentCategories}
                isActive={pathname.startsWith("/document-categories")}
                tourId="nav-categories"
              />
              <NavLink
                href="/documents"
                icon={FileStack}
                label={messages.shell.documents}
                isActive={pathname.startsWith("/documents")}
                tourId="nav-documents"
              />
            </nav>

            <LanguageSwitcher />

            <Button
              type="button"
              variant="secondary"
              className="w-full justify-start"
              data-tour="tour-restart"
              onClick={() => window.dispatchEvent(new Event(TOUR_RESTART_EVENT))}
            >
              <Sparkles className="h-4 w-4" />
              {messages.joyride.replayAction}
            </Button>

            <Link
              href="/access/logout"
              className="flex items-center gap-3 rounded-xl border border-[color:var(--color-line)] px-4 py-3 text-sm font-medium text-[color:var(--color-muted)] transition hover:bg-white hover:text-[color:var(--color-ink)]"
              prefetch={false}
            >
              <LogOut className="h-4 w-4" />
              Lock workspace
            </Link>

            <Card className="border-dashed">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                  <Sparkles className="h-4 w-4 text-[color:var(--color-accent)]" />
                  {messages.shell.starterSetupTitle}
                </div>
                <p className="mt-2 text-sm text-[color:var(--color-muted)]">
                  {messages.shell.starterSetupDescription}
                </p>
              </CardContent>
            </Card>
          </div>
        </aside>

        <div className="flex-1">{children}</div>
      </div>
      <WorkspaceOnboardingTour />
    </main>
  );
}
