"use client";

import {
  ArrowUp,
  Bot,
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
  upsertTimelineItem,
} from "@/lib/agent-stream";
import { createAgentThread, streamAgentRun } from "@/lib/api/aegra";
import { getApiErrorMessage } from "@/lib/api/errors";
import { cn } from "@/lib/utils";
import { useLocale } from "@/providers/locale-provider";
import type { DocumentExtraction } from "@/types/documents";

interface SuggestionPrompt {
  icon: LucideIcon;
  label: string;
  prompt: string;
}

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
  const [streamTimeline, setStreamTimeline] = useState<StreamTimelineItem[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const streamAbortControllerRef = useRef<AbortController | null>(null);
  const conversationViewportRef = useRef<HTMLDivElement | null>(null);
  const activityViewportRef = useRef<HTMLDivElement | null>(null);

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
  }, [chatMessages, isStreaming, progressItems.length]);

  useEffect(() => {
    const viewport = activityViewportRef.current;
    if (!viewport) {
      return;
    }

    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior: "smooth",
    });
  }, [streamTimeline]);

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
        prompt: messages.documentProcessing.extraction.correction.suggestionSpreadsheetPrompt,
      },
    ],
    [messages],
  );

  async function handleSend() {
    const message = chatInput.trim();
    if (!message) {
      return;
    }

    setChatError(null);
    setChatInput("");
    setProgressItems([]);
    setStreamTimeline([]);
    setChatMessages((current) => [
      ...current,
      {
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      },
    ]);

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
          setStreamTimeline((currentItems) => {
            const timelineItem = buildStreamTimelineItem(event, messages);
            if (!timelineItem) {
              return currentItems;
            }
            return upsertTimelineItem(currentItems, timelineItem);
          });

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
      setChatError(getApiErrorMessage(error, messages.common.apiError));
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
          <Badge variant="default">{extraction.template.name}</Badge>
          <Badge variant={isBusy ? "accent" : "default"}>
            {isBusy
              ? messages.documentProcessing.extraction.correction.liveBadge
              : messages.documentProcessing.extraction.correction.idleBadge}
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 p-4 lg:grid-cols-[minmax(0,1.75fr)_minmax(300px,1fr)]">
        <div className="flex min-h-[38rem] flex-col rounded-[26px] border border-[color:var(--color-line)] bg-white/90">
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
            className="flex-1 space-y-4 overflow-y-auto px-5 py-5"
          >
            {chatMessages.length ? (
              chatMessages.map((message, index) => {
                const isAssistant = message.role === "assistant";

                return (
                  <div
                    key={`${message.role}-${message.created_at}-${index}`}
                    className={cn("flex", isAssistant ? "justify-start" : "justify-end")}
                  >
                    <div
                      className={cn(
                        "max-w-[85%] rounded-[24px] border px-4 py-3 shadow-[0_10px_24px_rgba(20,27,45,0.06)]",
                        isAssistant
                          ? "border-[color:var(--color-line)] bg-[color:var(--color-panel)] text-[color:var(--color-ink)]"
                          : "border-transparent bg-[color:var(--color-ink)] text-[color:var(--color-paper)]",
                      )}
                    >
                      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] opacity-80">
                        {isAssistant ? (
                          <Bot className="h-3.5 w-3.5" />
                        ) : (
                          <User className="h-3.5 w-3.5" />
                        )}
                        <span>
                          {isAssistant
                            ? messages.documentProcessing.extraction.correction.assistantBadge
                            : messages.documentProcessing.extraction.correction.userBadge}
                        </span>
                        <span className="text-[10px] opacity-70">
                          {timeFormatter.format(new Date(message.created_at))}
                        </span>
                      </div>
                      <div className="mt-2 whitespace-pre-wrap text-sm leading-6">
                        {message.content}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="rounded-[24px] border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-4 py-5 text-sm leading-6 text-[color:var(--color-muted)]">
                {messages.documentProcessing.extraction.correction.emptyChat}
              </div>
            )}

            {isBusy ? (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-[24px] border border-[color:var(--color-line)] bg-[color:var(--color-panel)] px-4 py-3 shadow-[0_10px_24px_rgba(20,27,45,0.06)]">
                  <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--color-muted)]">
                    <LoaderCircle className="h-3.5 w-3.5 animate-spin text-[color:var(--color-accent)]" />
                    {messages.documentProcessing.extraction.correction.liveBadge}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[color:var(--color-ink)]">
                    {latestProgressItem?.message
                      ?? messages.documentProcessing.extraction.correction.activityEmpty}
                  </div>
                </div>
              </div>
            ) : null}
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

        <aside className="space-y-4">
          <div className="rounded-[26px] border border-[color:var(--color-line)] bg-white/90 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--color-ink)]">
              <WandSparkles className="h-4 w-4 text-[color:var(--color-accent)]" />
              {messages.documentProcessing.extraction.correction.currentActivityTitle}
            </div>
            <div className="mt-3 rounded-[20px] border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-4 py-4">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--color-muted)]">
                {latestProgressItem?.phase
                  ? latestProgressItem.phase.split("_").join(" ")
                  : messages.documentProcessing.extraction.correction.idleBadge}
              </div>
              <div className="mt-2 text-sm leading-6 text-[color:var(--color-ink)]">
                {latestProgressItem?.message
                  ?? messages.documentProcessing.extraction.correction.activityEmpty}
              </div>
            </div>
          </div>

          <div className="rounded-[26px] border border-[color:var(--color-line)] bg-white/90 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-semibold text-[color:var(--color-ink)]">
                {messages.documentProcessing.extraction.correction.activityTitle}
              </div>
              <Badge>
                {messages.documentProcessing.extraction.correction.eventCountLabel.replace(
                  "{count}",
                  String(streamTimeline.length),
                )}
              </Badge>
            </div>

            {streamTimeline.length ? (
              <div
                ref={activityViewportRef}
                className="mt-4 max-h-[30rem] space-y-3 overflow-y-auto pr-1"
              >
                {streamTimeline.map((item) => (
                  <div
                    key={item.id}
                    className={cn(
                      "rounded-[20px] border px-4 py-3",
                      getTimelineItemClasses(item.variant),
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-[color:var(--color-ink)]">
                        {item.label}
                      </div>
                      <div className="text-xs text-[color:var(--color-muted)]">
                        {timeFormatter.format(new Date(item.occurredAt))}
                      </div>
                    </div>
                    <div className="mt-1 text-sm leading-6 text-[color:var(--color-muted)]">
                      {item.summary}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-4 rounded-[20px] border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-4 py-4 text-sm leading-6 text-[color:var(--color-muted)]">
                {messages.documentProcessing.extraction.correction.activityEmpty}
              </div>
            )}
          </div>
        </aside>
      </div>

      {chatError ? (
        <div className="border-t border-[color:var(--color-line)] bg-[color:var(--color-background)]/90 px-5 py-4">
          <div className="rounded-[20px] border border-[color:var(--color-warm-soft)] bg-white px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
            {chatError}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function getTimelineItemClasses(
  variant: StreamTimelineItem["variant"],
): string {
  switch (variant) {
    case "accent":
      return "border-[color:rgba(66,99,235,0.18)] bg-[color:rgba(66,99,235,0.06)]";
    case "warm":
      return "border-[color:rgba(213,92,50,0.2)] bg-[color:rgba(213,92,50,0.07)]";
    case "success":
      return "border-[color:rgba(43,138,62,0.18)] bg-[color:rgba(43,138,62,0.08)]";
    default:
      return "border-[color:var(--color-line)] bg-[color:var(--color-background)]/70";
  }
}
