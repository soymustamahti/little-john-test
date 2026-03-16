import axios from "axios";

export function getApiErrorMessage(error: unknown, fallbackMessage: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}
