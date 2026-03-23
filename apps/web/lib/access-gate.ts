export const ACCESS_GATE_COOKIE_NAME = "little_john_access";
export const ACCESS_GATE_COOKIE_VALUE = "little-john-access-granted-v1-7f3a1b";
export const DEFAULT_ACCESS_PASSWORD = "little-john-demo-access";
export const DEFAULT_ACCESS_REDIRECT = "/extraction-templates";

export function getAccessPassword(): string {
  return process.env.APP_ACCESS_PASSWORD ?? DEFAULT_ACCESS_PASSWORD;
}

export function normalizeAccessRedirect(value: string | null | undefined): string {
  if (!value || !value.startsWith("/")) {
    return DEFAULT_ACCESS_REDIRECT;
  }

  if (value.startsWith("/access")) {
    return DEFAULT_ACCESS_REDIRECT;
  }

  return value;
}

export function isAccessGranted(cookieValue: string | undefined): boolean {
  return cookieValue === ACCESS_GATE_COOKIE_VALUE;
}
