import { Client } from "@langchain/langgraph-sdk";

import { apiClient } from "@/lib/api/client";

let client: Client | null = null;
let clientApiUrl: string | null = null;

function resolveApiUrl() {
  return apiClient.defaults.baseURL ?? "http://localhost:2026";
}

export function getLangGraphClient() {
  const apiUrl = resolveApiUrl();

  if (client === null || clientApiUrl !== apiUrl) {
    client = new Client({
      apiUrl,
    });
    clientApiUrl = apiUrl;
  }

  return client;
}
