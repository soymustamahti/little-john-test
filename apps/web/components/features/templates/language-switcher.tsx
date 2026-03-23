"use client";

import { Button } from "@/components/ui/button";
import { type Locale } from "@/lib/i18n";
import { useLocale } from "@/providers/locale-provider";

export function LanguageSwitcher() {
  const { locale, setLocale, messages } = useLocale();

  const options: Array<{ value: Locale; label: string }> = [
    { value: "en", label: messages.common.language.english },
    { value: "fr", label: messages.common.language.french },
  ];

  return (
    <div className="space-y-2" data-tour="workspace-language">
      <div className="px-1 text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
        {messages.common.language.label}
      </div>
      <div className="grid grid-cols-2 gap-2">
        {options.map((option) => (
          <Button
            key={option.value}
            type="button"
            size="sm"
            variant={locale === option.value ? "default" : "secondary"}
            onClick={() => setLocale(option.value)}
            aria-pressed={locale === option.value}
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
