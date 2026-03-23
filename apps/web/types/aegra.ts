import type { StreamEvent, Thread } from "@langchain/langgraph-sdk";

export type AgentThread = Thread;

export interface AgentStreamEvent {
  id?: string;
  event: StreamEvent;
  data: unknown;
}
