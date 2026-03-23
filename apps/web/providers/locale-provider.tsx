"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  DEFAULT_LOCALE,
  LOCALE_COOKIE_KEY,
  LOCALE_STORAGE_KEY,
  formatMessage,
  getIntlLocale,
  getMessages,
  type Locale,
  type Messages,
} from "@/lib/i18n";

interface LocaleContextValue {
  locale: Locale;
  messages: Messages;
  setLocale: (nextLocale: Locale) => void;
  formatDate: (value: string | Date) => string;
  formatText: (template: string, values?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function syncDocument(locale: Locale, messages: Messages) {
  document.documentElement.lang = locale;
  document.title = messages.metadata.title;

  const descriptionElement = document.querySelector('meta[name="description"]');
  if (descriptionElement) {
    descriptionElement.setAttribute("content", messages.metadata.description);
  }
}

export function LocaleProvider({
  initialLocale = DEFAULT_LOCALE,
  children,
}: {
  initialLocale?: Locale;
  children: ReactNode;
}) {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const messages = getMessages(locale);

  useEffect(() => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
    document.cookie = `${LOCALE_COOKIE_KEY}=${locale}; path=/; max-age=31536000; samesite=lax`;
    syncDocument(locale, messages);
  }, [locale, messages]);

  return (
    <LocaleContext.Provider
      value={{
        locale,
        messages,
        setLocale,
        formatDate(value) {
          const date = value instanceof Date ? value : new Date(value);

          if (Number.isNaN(date.getTime())) {
            return typeof value === "string" ? value : "";
          }

          return new Intl.DateTimeFormat(getIntlLocale(locale), {
            month: "short",
            day: "numeric",
            year: "numeric",
          }).format(date);
        },
        formatText(template, values) {
          return formatMessage(template, values);
        },
      }}
    >
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);

  if (!context) {
    throw new Error("useLocale must be used within a LocaleProvider.");
  }

  return context;
}
