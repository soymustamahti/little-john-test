"use client";

import {
  AlertCircle,
  ArrowUp,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  LoaderCircle,
  MessageSquareText,
  Search,
  Sparkles,
  User,
  WandSparkles,
  type LucideIcon,
} from "lucide-react";
import {
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCreateDocumentExtractionCorrectionSessionMutation } from "@/hooks/use-documents";
import {
  buildStreamTimelineItem,
  extractProgressItem,
  isRecord,
  type ProgressItem,
  type StreamTimelineItem,
  unwrapAgentPayload,
  upsertProgressItem,
} from "@/lib/agent-stream";
import { createAgentThread, streamAgentRun } from "@/lib/api/aegra";
import { getApiErrorMessage } from "@/lib/api/errors";
import { cn } from "@/lib/utils";
import { useLocale } from "@/providers/locale-provider";
import type {
  DocumentExtraction,
  DocumentExtractionField,
  DocumentExtractionResult,
} from "@/types/documents";

interface SuggestionPrompt {
  icon: LucideIcon;
  label: string;
  prompt: string;
}

interface TurnEventItem {
  id: string;
  kind: "progress" | "error" | "end" | "change";
  summary: string;
  occurredAt: number;
}

interface TurnEventGroup {
  id: string;
  userTurnIndex: number;
  summary: string;
  items: TurnEventItem[];
  status: "running" | "complete" | "error";
  expanded: boolean;
}

interface PendingTurnState {
  groupId: string;
  baselineResult: DocumentExtractionResult | null;
  correctionMessageCount: number;
}

type LocaleMessages = ReturnType<typeof useLocale>["messages"];

export function DocumentExtractionCorrectionChat({
  documentId,
  extraction,
  onExtractionRefresh,
}: {
  documentId: string;
  extraction: DocumentExtraction;
  onExtractionRefresh: () => Promise<unknown>;
}) {
  const { locale, messages } = useLocale();
  const correctionSessionMutation = useCreateDocumentExtractionCorrectionSessionMutation();

  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState(extraction.correction_messages);
  const [progressItems, setProgressItems] = useState<ProgressItem[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [eventGroups, setEventGroups] = useState<TurnEventGroup[]>([]);

  const streamAbortControllerRef = useRef<AbortController | null>(null);
  const conversationViewportRef = useRef<HTMLDivElement | null>(null);
  const pendingTurnRef = useRef<PendingTurnState | null>(null);

  useEffect(() => {
    if (!isStreaming) {
      setChatMessages(extraction.correction_messages);
    }
  }, [extraction.correction_messages, isStreaming]);

  useEffect(() => {
    return () => {
      streamAbortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    const viewport = conversationViewportRef.current;
    if (!viewport) {
      return;
    }

    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior: isStreaming ? "smooth" : "auto",
    });
  }, [chatMessages, eventGroups, isStreaming]);

  useEffect(() => {
    const pendingTurn = pendingTurnRef.current;
    if (!pendingTurn || isStreaming) {
      return;
    }

    if (extraction.correction_messages.length <= pendingTurn.correctionMessageCount) {
      return;
    }

    const changeItems = buildChangeItems(
      pendingTurn.baselineResult,
      extraction.result,
      messages,
    );

    setEventGroups((currentGroups) =>
      finalizeEventGroup(
        currentGroups,
        pendingTurn.groupId,
        changeItems,
        messages,
        extraction.status === "failed",
      ),
    );

    pendingTurnRef.current = null;
  }, [
    extraction.correction_messages.length,
    extraction.result,
    extraction.status,
    isStreaming,
    messages,
  ]);

  const latestProgressItem = progressItems[progressItems.length - 1] ?? null;
  const timeFormatter = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
  });
  const isBusy = isStreaming || correctionSessionMutation.isPending;
  const suggestionPrompts = useMemo<SuggestionPrompt[]>(
    () => [
      {
        icon: Sparkles,
        label: messages.documentProcessing.extraction.correction.suggestionDirectLabel,
        prompt: messages.documentProcessing.extraction.correction.suggestionDirectPrompt,
      },
      {
        icon: Search,
        label: messages.documentProcessing.extraction.correction.suggestionSearchLabel,
        prompt: messages.documentProcessing.extraction.correction.suggestionSearchPrompt,
      },
      {
        icon: WandSparkles,
        label: messages.documentProcessing.extraction.correction.suggestionSpreadsheetLabel,
        prompt:
          messages.documentProcessing.extraction.correction
            .suggestionSpreadsheetPrompt,
      },
    ],
    [messages],
  );

  async function handleSend() {
    const message = chatInput.trim();
    if (!message) {
      return;
    }

    const turnId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const userTurnIndex = chatMessages.filter((item) => item.role === "user").length;

    setChatError(null);
    setChatInput("");
    setProgressItems([]);
    setChatMessages((current) => [
      ...current,
      {
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      },
    ]);
    setEventGroups((currentGroups) => [
      ...currentGroups,
      {
        id: turnId,
        userTurnIndex,
        summary: messages.documentProcessing.extraction.correction.eventSummaryRunning,
        items: [],
        status: "running",
        expanded: true,
      },
    ]);

    pendingTurnRef.current = {
      groupId: turnId,
      baselineResult: extraction.result ? structuredClone(extraction.result) : null,
      correctionMessageCount: extraction.correction_messages.length,
    };

    try {
      const session = await correctionSessionMutation.mutateAsync(documentId);
      await createAgentThread({
        threadId: session.thread_id,
        metadata: {
          document_id: documentId,
          purpose: "document_extraction_correction",
        },
      });

      const controller = new AbortController();
      streamAbortControllerRef.current = controller;
      setIsStreaming(true);

      await streamAgentRun({
        threadId: session.thread_id,
        payload: {
          assistant_id: session.assistant_id,
          input: {
            document_id: documentId,
            thread_id: session.thread_id,
            user_message: message,
          },
          stream_mode: ["custom"],
          on_disconnect: "continue",
        },
        signal: controller.signal,
        onEvent: async (event) => {
          const timelineItem = buildStreamTimelineItem(event, messages);
          if (timelineItem) {
            setEventGroups((currentGroups) =>
              appendEventItem(
                currentGroups,
                turnId,
                {
                  id: timelineItem.id,
                  kind: mapTimelineItemKind(timelineItem.kind),
                  summary: compactEventSummary(timelineItem.summary),
                  occurredAt: timelineItem.occurredAt,
                },
                messages,
              ),
            );
          }

          const progressItem = extractProgressItem(event);
          if (progressItem) {
            setProgressItems((currentItems) =>
              upsertProgressItem(currentItems, progressItem),
            );
          }

          if (String(event.event) === "error") {
            const payload = unwrapAgentPayload(event.data);
            if (isRecord(payload) && typeof payload.message === "string") {
              setChatError(payload.message);
            }
          }
        },
      });
    } catch (error) {
      const messageText = getApiErrorMessage(error, messages.common.apiError);
      setChatError(messageText);
      setEventGroups((currentGroups) =>
        markEventGroupErrored(currentGroups, turnId, messageText, messages),
      );
      pendingTurnRef.current = null;
    } finally {
      setIsStreaming(false);
      streamAbortControllerRef.current = null;
      await onExtractionRefresh();
    }
  }

  function handleInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      void handleSend();
    }
  }

  function handleSuggestionPrompt(prompt: string) {
    setChatInput(prompt);
  }

  function toggleEventGroup(groupId: string) {
    setEventGroups((currentGroups) =>
      currentGroups.map((group) =>
        group.id === groupId ? { ...group, expanded: !group.expanded } : group,
      ),
    );
  }

  return (
    <section className="overflow-hidden rounded-[28px] border border-[color:var(--color-line)] bg-[radial-gradient(circle_at_top_left,rgba(207,226,255,0.42),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.98),rgba(247,245,239,0.94))] shadow-[0_24px_60px_rgba(20,27,45,0.08)]">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[color:var(--color-line)] px-5 py-5">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--color-ink)]">
            <MessageSquareText className="h-4 w-4 text-[color:var(--color-accent)]" />
            {messages.documentProcessing.extraction.correction.title}
          </div>
          <div className="max-w-3xl text-sm leading-6 text-[color:var(--color-muted)]">
            {messages.documentProcessing.extraction.correction.description}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{extraction.template.name}</Badge>
          <Badge variant={isBusy ? "accent" : "default"}>
            {isBusy
              ? messages.documentProcessing.extraction.correction.liveBadge
              : messages.documentProcessing.extraction.correction.idleBadge}
          </Badge>
        </div>
      </div>

      <div className="space-y-4 p-4">
        <div className="flex min-h-[38rem] flex-col rounded-[26px] border border-[color:var(--color-line)] bg-white/92">
          <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[color:var(--color-line)] px-5 py-4">
            <div className="space-y-1">
              <div className="text-sm font-semibold text-[color:var(--color-ink)]">
                {messages.documentProcessing.extraction.correction.conversationTitle}
              </div>
              <div className="text-xs leading-5 text-[color:var(--color-muted)]">
                {messages.documentProcessing.extraction.correction.conversationDescription}
              </div>
            </div>
            <Badge>
              {messages.documentProcessing.extraction.correction.messageCountLabel.replace(
                "{count}",
                String(chatMessages.length),
              )}
            </Badge>
          </div>

          <div
            ref={conversationViewportRef}
            className="flex-1 space-y-5 overflow-y-auto px-5 py-5"
          >
            {chatMessages.length ? (
              renderConversation({
                chatMessages,
                eventGroups,
                isBusy,
                latestProgressItem,
                messages,
                timeFormatter,
                onToggleEventGroup: toggleEventGroup,
              })
            ) : (
              <div className="rounded-[24px] border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-4 py-5 text-sm leading-6 text-[color:var(--color-muted)]">
                {messages.documentProcessing.extraction.correction.emptyChat}
              </div>
            )}
          </div>

          <div className="border-t border-[color:var(--color-line)] px-5 py-4">
            <div className="mb-3 flex flex-wrap gap-2">
              {suggestionPrompts.map((suggestion) => {
                const Icon = suggestion.icon;
                return (
                  <Button
                    key={suggestion.label}
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="rounded-full"
                    disabled={isBusy}
                    onClick={() => handleSuggestionPrompt(suggestion.prompt)}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {suggestion.label}
                  </Button>
                );
              })}
            </div>

            <div className="space-y-3">
              <Label htmlFor="extraction-correction-input">
                {messages.documentProcessing.extraction.correction.inputLabel}
              </Label>
              <Textarea
                id="extraction-correction-input"
                className="min-h-32 rounded-[24px] border-[color:var(--color-line)] bg-white/95 px-4 py-3 text-sm leading-6 text-[color:var(--color-ink)] shadow-none"
                placeholder={messages.documentProcessing.extraction.correction.inputPlaceholder}
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                onKeyDown={handleInputKeyDown}
              />
            </div>

            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <div className="space-y-1 text-xs text-[color:var(--color-muted)]">
                <div>{messages.documentProcessing.extraction.correction.hint}</div>
                <div>{messages.documentProcessing.extraction.correction.shortcutHint}</div>
              </div>
              <Button
                type="button"
                className="min-w-44"
                onClick={() => void handleSend()}
                disabled={!chatInput.trim() || isBusy}
              >
                {isBusy ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowUp className="h-4 w-4" />
                )}
                {isBusy
                  ? messages.documentProcessing.extraction.correction.sendingAction
                  : messages.documentProcessing.extraction.correction.sendAction}
              </Button>
            </div>
          </div>
        </div>

        {chatError ? (
          <div className="rounded-[20px] border border-[color:var(--color-warm-soft)] bg-white px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
            {chatError}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function renderConversation({
  chatMessages,
  eventGroups,
  isBusy,
  latestProgressItem,
  messages,
  timeFormatter,
  onToggleEventGroup,
}: {
  chatMessages: DocumentExtraction["correction_messages"];
  eventGroups: TurnEventGroup[];
  isBusy: boolean;
  latestProgressItem: ProgressItem | null;
  messages: LocaleMessages;
  timeFormatter: Intl.DateTimeFormat;
  onToggleEventGroup: (groupId: string) => void;
}) {
  const conversationNodes: ReactNode[] = [];
  let userTurnIndex = 0;

  for (const [index, message] of chatMessages.entries()) {
    const isAssistant = message.role === "assistant";
    const matchingGroup = !isAssistant
      ? eventGroups.find((group) => group.userTurnIndex === userTurnIndex)
      : null;

    conversationNodes.push(
      <div
        key={`${message.role}-${message.created_at}-${index}`}
        className={cn(
          "flex",
          isAssistant ? "justify-start pr-8" : "justify-end pl-12",
        )}
      >
        {isAssistant ? (
          <div className="w-full max-w-4xl">
            <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
              <Bot className="h-3.5 w-3.5 text-[color:var(--color-accent)]" />
              <span>
                {messages.documentProcessing.extraction.correction.assistantBadge}
              </span>
              <span className="text-[10px]">
                {timeFormatter.format(new Date(message.created_at))}
              </span>
            </div>
            <div className="mt-2 whitespace-pre-wrap text-[15px] leading-7 text-[color:var(--color-ink)]">
              {message.content}
            </div>
          </div>
        ) : (
          <div className="max-w-[78%] rounded-[28px] bg-[color:var(--color-ink)] px-5 py-4 text-[color:var(--color-paper)] shadow-[0_16px_36px_rgba(20,27,45,0.16)]">
            <div className="whitespace-pre-wrap text-[15px] leading-7">
              {message.content}
            </div>
            <div className="mt-3 flex items-center justify-end gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-white/62">
              <User className="h-3 w-3" />
              <span>{messages.documentProcessing.extraction.correction.userBadge}</span>
              <span>{timeFormatter.format(new Date(message.created_at))}</span>
            </div>
          </div>
        )}
      </div>,
    );

    if (matchingGroup) {
      const eventCountLabel =
        matchingGroup.items.length > 0
          ? messages.documentProcessing.extraction.correction.eventCountLabel.replace(
              "{count}",
              String(matchingGroup.items.length),
            )
          : null;

      conversationNodes.push(
        <div key={`events-${matchingGroup.id}`} className="max-w-4xl pr-8">
          <button
            type="button"
            className="flex w-full items-center justify-between gap-3 rounded-[20px] bg-[rgba(20,27,45,0.96)] px-4 py-3 text-left text-white shadow-[0_12px_28px_rgba(15,23,42,0.22)] transition hover:bg-[rgba(20,27,45,0.92)]"
            onClick={() => onToggleEventGroup(matchingGroup.id)}
          >
            <div className="flex min-w-0 items-center gap-2">
              {renderEventStatusIcon(matchingGroup.status)}
              <span className="truncate text-sm font-medium">
                {matchingGroup.summary}
              </span>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {eventCountLabel ? (
                <span className="rounded-full bg-white/10 px-2 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-white/76">
                  {eventCountLabel}
                </span>
              ) : null}
              {matchingGroup.expanded ? (
                <ChevronDown className="h-4 w-4 shrink-0 text-[rgba(255,255,255,0.78)]" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0 text-[rgba(255,255,255,0.78)]" />
              )}
            </div>
          </button>

          {matchingGroup.expanded ? (
            <div className="mt-2 rounded-[20px] border border-[color:var(--color-line)] bg-[color:var(--color-panel)]/94 px-4 py-3 shadow-[0_12px_32px_rgba(20,27,45,0.08)]">
              {matchingGroup.items.length ? (
                <div className="space-y-2">
                  {matchingGroup.items.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-2 text-xs leading-5 text-[color:var(--color-muted)]"
                    >
                      {renderEventItemIcon(item.kind)}
                      <span>{item.summary}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-start gap-2 text-xs leading-5 text-[color:var(--color-muted)]">
                  <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--color-accent)]" />
                  <span>
                    {isBusy && latestProgressItem
                      ? compactEventSummary(latestProgressItem.message)
                      : messages.documentProcessing.extraction.correction.activityEmpty}
                  </span>
                </div>
              )}
            </div>
          ) : null}
        </div>,
      );
    }

    if (!isAssistant) {
      userTurnIndex += 1;
    }
  }

  return conversationNodes;
}

function renderEventStatusIcon(status: TurnEventGroup["status"]) {
  if (status === "running") {
    return (
      <LoaderCircle className="h-4 w-4 shrink-0 animate-spin text-[rgba(255,255,255,0.82)]" />
    );
  }

  if (status === "error") {
    return (
      <AlertCircle className="h-4 w-4 shrink-0 text-[rgba(255,180,180,0.9)]" />
    );
  }

  return (
    <CheckCircle2 className="h-4 w-4 shrink-0 text-[rgba(167,243,208,0.9)]" />
  );
}

function renderEventItemIcon(kind: TurnEventItem["kind"]) {
  if (kind === "error") {
    return (
      <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--color-accent-warm)]" />
    );
  }

  if (kind === "change" || kind === "end") {
    return (
      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />
    );
  }

  return (
    <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--color-accent)]" />
  );
}

function mapTimelineItemKind(kind: StreamTimelineItem["kind"]): TurnEventItem["kind"] {
  if (kind === "error") {
    return "error";
  }

  if (kind === "end") {
    return "end";
  }

  return "progress";
}

function appendEventItem(
  eventGroups: TurnEventGroup[],
  groupId: string,
  item: TurnEventItem,
  messages: LocaleMessages,
): TurnEventGroup[] {
  return eventGroups.map((group) => {
    if (group.id !== groupId) {
      return group;
    }

    const nextItems = dedupeTurnEventItems([...group.items, item]);
    return {
      ...group,
      items: nextItems,
      summary:
        item.kind === "error"
          ? messages.documentProcessing.extraction.correction.eventSummaryError
          : item.summary,
      status: item.kind === "error" ? "error" : group.status,
    };
  });
}

function finalizeEventGroup(
  eventGroups: TurnEventGroup[],
  groupId: string,
  changeItems: TurnEventItem[],
  messages: LocaleMessages,
  forceError: boolean,
): TurnEventGroup[] {
  return eventGroups.map((group) => {
    if (group.id !== groupId) {
      return group;
    }

    if (forceError || group.status === "error") {
      return {
        ...group,
        expanded: false,
        status: "error",
        summary: messages.documentProcessing.extraction.correction.eventSummaryError,
      };
    }

    const nextItems = dedupeTurnEventItems([...group.items, ...changeItems]);
    const changeCount = changeItems.length;
    const summary =
      changeCount > 0
        ? messages.documentProcessing.extraction.correction.eventSummaryUpdated.replace(
            "{count}",
            String(changeCount),
          )
        : nextItems.length > 0
          ? messages.documentProcessing.extraction.correction.eventSummaryCompleted.replace(
              "{count}",
              String(nextItems.length),
            )
          : messages.documentProcessing.extraction.correction.eventSummaryNoChange;

    return {
      ...group,
      items: nextItems,
      summary,
      status: "complete",
      expanded: false,
    };
  });
}

function markEventGroupErrored(
  eventGroups: TurnEventGroup[],
  groupId: string,
  message: string,
  messages: LocaleMessages,
): TurnEventGroup[] {
  return eventGroups.map((group) => {
    if (group.id !== groupId) {
      return group;
    }

    return {
      ...group,
      items: dedupeTurnEventItems([
        ...group.items,
        {
          id: `${group.id}-error`,
          kind: "error",
          summary: compactEventSummary(message),
          occurredAt: Date.now(),
        },
      ]),
      summary: messages.documentProcessing.extraction.correction.eventSummaryError,
      status: "error",
      expanded: true,
    };
  });
}

function dedupeTurnEventItems(items: TurnEventItem[]): TurnEventItem[] {
  const deduped: TurnEventItem[] = [];
  for (const item of items) {
    const previous = deduped[deduped.length - 1];
    if (previous?.summary === item.summary && previous.kind === item.kind) {
      deduped[deduped.length - 1] = item;
      continue;
    }
    deduped.push(item);
  }
  return deduped.slice(-12);
}

function buildChangeItems(
  previousResult: DocumentExtractionResult | null,
  nextResult: DocumentExtractionResult | null,
  messages: LocaleMessages,
): TurnEventItem[] {
  if (!previousResult || !nextResult) {
    return [];
  }

  const items: TurnEventItem[] = [];
  const previousModules = new Map(
    previousResult.modules.map((moduleItem) => [moduleItem.key, moduleItem]),
  );

  for (const moduleItem of nextResult.modules) {
    const previousModule = previousModules.get(moduleItem.key);
    if (!previousModule) {
      continue;
    }

    const previousFields = new Map(
      previousModule.fields.map((field) => [field.key, field]),
    );

    for (const field of moduleItem.fields) {
      const previousField = previousFields.get(field.key);
      if (!previousField || !didFieldChange(previousField, field)) {
        continue;
      }

      items.push({
        id: `${moduleItem.key}-${field.key}`,
        kind: "change",
        summary:
          field.kind === "table"
            ? messages.documentProcessing.extraction.correction.eventTableChanged.replace(
                "{field}",
                field.label,
              )
            : messages.documentProcessing.extraction.correction.eventFieldChanged.replace(
                "{field}",
                field.label,
              ),
        occurredAt: Date.now(),
      });
    }
  }

  return items;
}

function didFieldChange(
  previousField: DocumentExtractionField,
  nextField: DocumentExtractionField,
): boolean {
  return JSON.stringify(previousField) !== JSON.stringify(nextField);
}

function compactEventSummary(value: string): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= 72) {
    return normalized;
  }
  return `${normalized.slice(0, 69).trimEnd()}...`;
}
