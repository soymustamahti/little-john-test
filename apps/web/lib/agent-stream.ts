import type { Messages } from "@/lib/i18n";
import type { AgentStreamEvent } from "@/types/aegra";

const STREAM_EVENT_LIMIT = 48;

export interface ProgressItem {
  phase: string;
  message: string;
}

export interface StreamTimelineItem {
  id: string;
  kind: "progress" | "interrupt" | "error" | "end";
  label: string;
  summary: string;
  occurredAt: number;
  variant: "default" | "accent" | "warm" | "success";
}

export function extractProgressItem(event: AgentStreamEvent): ProgressItem | null {
  if (String(event.event) !== "custom") {
    return null;
  }

  const payload = unwrapAgentPayload(event.data);
  if (!isRecord(payload)) {
    return null;
  }

  const phase = typeof payload.phase === "string" ? payload.phase : "working";
  const message = typeof payload.message === "string" ? payload.message : null;

  if (!message) {
    return null;
  }

  return { phase, message };
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function unwrapAgentPayload(value: unknown): unknown {
  if (isRecord(value) && "chunk" in value) {
    return value.chunk;
  }
  return value;
}

function formatMachineLabel(value: string): string {
  return value
    .split(/[/_|]+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}

export function buildStreamTimelineItem(
  event: AgentStreamEvent,
  messages: Messages,
): StreamTimelineItem | null {
  const eventName = String(event.event);
  const payload = unwrapAgentPayload(event.data);

  if (eventName === "custom") {
    const phase = isRecord(payload) && typeof payload.phase === "string"
      ? formatMachineLabel(payload.phase)
      : messages.documentProcessing.ai.eventLabels.custom;
    const summary = isRecord(payload) && typeof payload.message === "string"
      ? payload.message
      : messages.documentProcessing.ai.eventDescriptions.custom;

    return {
      id: event.id ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      kind: "progress",
      label: phase,
      summary,
      occurredAt: Date.now(),
      variant: "accent",
    };
  }

  if (eventName === "values") {
    const interrupts =
      isRecord(payload) && Array.isArray(payload.__interrupt__)
        ? payload.__interrupt__
        : null;

    if (!interrupts || interrupts.length === 0) {
      return null;
    }

    return {
      id: event.id ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      kind: "interrupt",
      label: messages.documentProcessing.ai.eventLabels.interrupt,
      summary: messages.documentProcessing.ai.eventDescriptions.interrupt,
      occurredAt: Date.now(),
      variant: "warm",
    };
  }

  if (eventName === "error") {
    const summary =
      isRecord(payload) && typeof payload.message === "string"
        ? payload.message
        : messages.documentProcessing.ai.eventDescriptions.error;

    return {
      id: event.id ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      kind: "error",
      label: messages.documentProcessing.ai.eventLabels.error,
      summary,
      occurredAt: Date.now(),
      variant: "warm",
    };
  }

  if (eventName === "end") {
    return {
      id: event.id ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      kind: "end",
      label: messages.documentProcessing.ai.eventLabels.end,
      summary: messages.documentProcessing.ai.eventDescriptions.end,
      occurredAt: Date.now(),
      variant: "success",
    };
  }

  return null;
}

export function upsertTimelineItem(
  currentItems: StreamTimelineItem[],
  timelineItem: StreamTimelineItem,
): StreamTimelineItem[] {
  const previousItem = currentItems[currentItems.length - 1];
  const isDuplicateInterrupt =
    timelineItem.kind === "interrupt" &&
    previousItem?.kind === "interrupt" &&
    previousItem.label === timelineItem.label &&
    previousItem.summary === timelineItem.summary;

  if (isDuplicateInterrupt) {
    return currentItems;
  }

  const shouldReplaceActiveProgress =
    timelineItem.kind === "progress" &&
    previousItem?.kind === "progress" &&
    previousItem.label === timelineItem.label;

  if (shouldReplaceActiveProgress && previousItem) {
    return [
      ...currentItems.slice(0, -1),
      {
        ...previousItem,
        summary: timelineItem.summary,
        occurredAt: timelineItem.occurredAt,
        variant: timelineItem.variant,
      },
    ];
  }

  return [...currentItems, timelineItem].slice(-STREAM_EVENT_LIMIT);
}

export function upsertProgressItem(
  currentItems: ProgressItem[],
  progressItem: ProgressItem,
): ProgressItem[] {
  const previousItem = currentItems[currentItems.length - 1];
  if (previousItem?.phase === progressItem.phase) {
    return [...currentItems.slice(0, -1), progressItem];
  }

  return [...currentItems, progressItem].slice(-STREAM_EVENT_LIMIT);
}
