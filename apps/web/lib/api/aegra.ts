import type {
  Command,
  StreamMode,
} from "@langchain/langgraph-sdk";

import type { AgentStreamEvent, AgentThread } from "@/types/aegra";
import { getLangGraphClient } from "@/lib/langgraph/client";

interface CreateThreadPayload {
  threadId: string;
  metadata?: Record<string, unknown>;
}

interface StreamRunPayload {
  assistant_id: string;
  input?: Record<string, unknown>;
  command?: Command;
  stream_mode?: StreamMode[];
  on_disconnect?: "cancel" | "continue";
}

interface LangGraphRunPayload {
  input?: Record<string, unknown>;
  command?: Command;
  streamMode?: StreamMode[];
  onDisconnect?: "cancel" | "continue";
  signal?: AbortSignal;
  streamResumable?: boolean;
}

export async function createAgentThread(payload: CreateThreadPayload) {
  return (await getLangGraphClient().threads.create({
    threadId: payload.threadId,
    ifExists: "do_nothing",
    metadata: payload.metadata,
  })) as AgentThread;
}

function toAgentStreamEvent(event: {
  id?: string;
  event: string;
  data: unknown;
}): AgentStreamEvent {
  return {
    id: event.id,
    event: event.event,
    data: event.data,
  };
}

function getRunPayload(
  payload: StreamRunPayload,
  signal?: AbortSignal,
): LangGraphRunPayload {
  return {
    input: payload.input,
    command: payload.command,
    streamMode: payload.stream_mode,
    onDisconnect: payload.on_disconnect,
    signal,
    streamResumable: payload.on_disconnect === "continue",
  };
}

export async function streamAgentRun({
  threadId,
  payload,
  signal,
  onEvent,
}: {
  threadId: string;
  payload: StreamRunPayload;
  signal?: AbortSignal;
  onEvent: (event: AgentStreamEvent) => void | Promise<void>;
}) {
  const client = getLangGraphClient();

  for await (const event of client.runs.stream(
    threadId,
    payload.assistant_id,
    getRunPayload(payload, signal),
  )) {
    await onEvent(toAgentStreamEvent(event));
  }
}
