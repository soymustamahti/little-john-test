import enMessages from "@/messages/en.json";
import frMessages from "@/messages/fr.json";

export const SUPPORTED_LOCALES = ["en", "fr"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_STORAGE_KEY = "little-john.locale";
export const LOCALE_COOKIE_KEY = "little-john.locale";

const MESSAGES = {
  en: enMessages,
  fr: frMessages,
} as const;

export type Messages = (typeof MESSAGES)[Locale];

export function isLocale(value: string | null | undefined): value is Locale {
  return value === "en" || value === "fr";
}

export function getMessages(locale: Locale): Messages {
  return MESSAGES[locale];
}

export function getLocaleFromValue(value: string | null | undefined): Locale {
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export function getIntlLocale(locale: Locale) {
  return locale === "fr" ? "fr-FR" : "en-US";
}

export function formatMessage(
  template: string,
  values: Record<string, string | number> = {},
) {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    const value = values[key];

    if (value === undefined) {
      return match;
    }

    return String(value);
  });
}
