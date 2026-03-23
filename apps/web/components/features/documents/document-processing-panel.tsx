"use client";

import {
  Bot,
  CheckCircle2,
  LoaderCircle,
  PencilLine,
  Sparkles,
  WandSparkles,
  X,
} from "lucide-react";
import { useEffect, useEffectEvent, useRef, useState } from "react";

import { DocumentExtractionReview } from "@/components/features/documents/document-extraction-review";
import { DocumentExtractionCorrectionChat } from "@/components/features/documents/document-extraction-correction-chat";
import { useDocumentCategoriesQuery } from "@/hooks/use-document-categories";
import {
  useConfirmDocumentExtractionReviewMutation,
  useCreateDocumentAiExtractionSessionMutation,
  useCreateDocumentAiClassificationSessionMutation,
  useDocumentExtractionQuery,
  useManualDocumentClassificationMutation,
} from "@/hooks/use-documents";
import { useTemplatesQuery } from "@/hooks/use-templates";
import { createAgentThread, streamAgentRun } from "@/lib/api/aegra";
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
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import type { Document, DocumentExtractionResult } from "@/types/documents";
import { getDocumentExtractionStatusLabel } from "@/types/documents";
import {
  formatDocumentCategoryName,
  getDocumentCategoryDisplayName,
  slugifyDocumentCategoryLabelKey,
} from "@/types/document-categories";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const CATEGORY_PAGE_SIZE = 100;
const TEMPLATE_PAGE_SIZE = 100;
const DOCUMENT_CLASSIFICATION_ASSISTANT_ID = "document_classification_agent";
const DOCUMENT_EXTRACTION_ASSISTANT_ID = "document_extraction_agent";

export function DocumentProcessingPanel({
  document,
  documentId,
  open,
  onOpenChange,
  onDocumentRefresh,
}: {
  document: Document;
  documentId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDocumentRefresh: () => Promise<unknown>;
}) {
  const { locale, messages } = useLocale();
  const categoriesQuery = useDocumentCategoriesQuery({
    page: 1,
    pageSize: CATEGORY_PAGE_SIZE,
  });
  const templatesQuery = useTemplatesQuery({
    page: 1,
    pageSize: TEMPLATE_PAGE_SIZE,
  });
  const extractionQuery = useDocumentExtractionQuery(documentId, open);
  const manualClassificationMutation =
    useManualDocumentClassificationMutation();
  const aiSessionMutation = useCreateDocumentAiClassificationSessionMutation();
  const extractionSessionMutation =
    useCreateDocumentAiExtractionSessionMutation();
  const extractionReviewMutation = useConfirmDocumentExtractionReviewMutation();

  const [selectedMode, setSelectedMode] = useState<"choose" | "manual" | "ai">(
    "choose",
  );
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [pendingExtractionTemplateId, setPendingExtractionTemplateId] =
    useState<string | null>(null);
  const [customCategoryName, setCustomCategoryName] = useState("");
  const [customCategoryLabelKey, setCustomCategoryLabelKey] = useState("");
  const [suggestionResolved, setSuggestionResolved] = useState(false);
  const [progressItems, setProgressItems] = useState<ProgressItem[]>([]);
  const [streamTimeline, setStreamTimeline] = useState<StreamTimelineItem[]>(
    [],
  );
  const [aiError, setAiError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeStreamKind, setActiveStreamKind] = useState<
    "classification" | "extraction" | null
  >(null);
  const initializedDocumentIdRef = useRef<string | null>(null);
  const streamAbortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!open) {
      initializedDocumentIdRef.current = null;
      return;
    }

    if (initializedDocumentIdRef.current === document.id) {
      return;
    }

    initializedDocumentIdRef.current = document.id;
    setAiError(null);
    setProgressItems([]);
    setStreamTimeline([]);
    setSelectedCategoryId(document.classification.category?.id ?? "");
    setSelectedTemplateId(extractionQuery.data?.template.id ?? "");
    setPendingExtractionTemplateId(null);
    setSuggestionResolved(false);

    if (
      document.classification.status === "pending_review" &&
      document.classification.suggested_category
    ) {
      setSuggestionResolved(false);
      setSelectedMode("ai");
      setCustomCategoryName(
        formatDocumentCategoryName(
          document.classification.suggested_category.name,
        ),
      );
      setCustomCategoryLabelKey(
        document.classification.suggested_category.label_key,
      );
      return;
    }

    if (
      document.classification.method === "ai" &&
      (document.classification.status === "processing" ||
        document.classification.status === "failed")
    ) {
      setSelectedMode("ai");
      setCustomCategoryName("");
      setCustomCategoryLabelKey("");
      return;
    }

    setSelectedMode("choose");
    setCustomCategoryName("");
    setCustomCategoryLabelKey("");
  }, [
    document.classification.category?.id,
    document.classification.method,
    document.classification.status,
    document.classification.suggested_category,
    document.id,
    extractionQuery.data?.template.id,
    open,
  ]);

  useEffect(() => {
    if (!open) {
      return;
    }

    setSelectedCategoryId(document.classification.category?.id ?? "");
  }, [document.classification.category?.id, open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    if (!selectedTemplateId && extractionQuery.data?.template.id) {
      setSelectedTemplateId(extractionQuery.data.template.id);
    }
  }, [extractionQuery.data?.template.id, open, selectedTemplateId]);

  useEffect(() => {
    if (!open) {
      return;
    }

    if (
      document.classification.method === "ai" &&
      (isStreaming ||
        document.classification.status === "processing" ||
        document.classification.status === "pending_review" ||
        document.classification.status === "failed")
    ) {
      setSelectedMode("ai");
    }

    if (
      document.classification.status === "pending_review" &&
      document.classification.suggested_category
    ) {
      setSuggestionResolved(false);
      setCustomCategoryName(
        formatDocumentCategoryName(
          document.classification.suggested_category.name,
        ),
      );
      setCustomCategoryLabelKey(
        document.classification.suggested_category.label_key,
      );
    }
  }, [
    document.classification.method,
    document.classification.status,
    document.classification.suggested_category,
    isStreaming,
    open,
  ]);

  const startPendingExtraction = useEffectEvent((templateId: string) => {
    void handleExtractionStart(templateId);
  });

  useEffect(() => {
    if (!open || !pendingExtractionTemplateId || isStreaming) {
      return;
    }

    if (document.classification.status === "classified") {
      const templateId = pendingExtractionTemplateId;
      setPendingExtractionTemplateId(null);
      startPendingExtraction(templateId);
      return;
    }

    if (document.classification.status === "failed") {
      setPendingExtractionTemplateId(null);
    }
  }, [
    document.classification.status,
    isStreaming,
    open,
    pendingExtractionTemplateId,
  ]);

  useEffect(() => {
    return () => {
      streamAbortControllerRef.current?.abort();
    };
  }, []);

  if (!open) {
    return null;
  }

  const categories = categoriesQuery.data?.items ?? [];
  const templates = templatesQuery.data?.items ?? [];
  const extraction = extractionQuery.data;
  const hasExtractionDraft = Boolean(extraction?.result);
  const pendingSuggestion = document.classification.suggested_category;
  const latestProgressItem = progressItems[progressItems.length - 1] ?? null;
  const streamStatusVariant = isStreaming
    ? "accent"
    : streamTimeline.length > 0
      ? "success"
      : "default";
  const streamStatusLabel = isStreaming
    ? messages.documentProcessing.ai.liveBadge
    : streamTimeline.length > 0
      ? messages.documentProcessing.ai.completeBadge
      : messages.documentProcessing.ai.idleBadge;
  const timeFormatter = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const manualError = manualClassificationMutation.error
    ? getApiErrorMessage(
        manualClassificationMutation.error,
        messages.common.apiError,
      )
    : null;
  const extractionError = extractionReviewMutation.error
    ? getApiErrorMessage(
        extractionReviewMutation.error,
        messages.common.apiError,
      )
    : null;
  const streamingTitle =
    activeStreamKind === "extraction"
      ? messages.documentProcessing.extraction.streamingTitle
      : messages.documentProcessing.ai.streamingTitle;
  const streamingEmptyMessage =
    activeStreamKind === "extraction"
      ? messages.documentProcessing.extraction.streamingEmpty
      : messages.documentProcessing.ai.streamingEmpty;
  const timelineEmptyMessage =
    activeStreamKind === "extraction"
      ? messages.documentProcessing.extraction.timelineEmpty
      : messages.documentProcessing.ai.timelineEmpty;

  async function handleManualClassification() {
    if (!selectedCategoryId) {
      return;
    }

    if (!selectedTemplateId) {
      setAiError(messages.documentProcessing.templateRequired);
      return;
    }

    try {
      await manualClassificationMutation.mutateAsync({
        documentId,
        categoryId: selectedCategoryId,
      });
      setPendingExtractionTemplateId(selectedTemplateId);
      await onDocumentRefresh();
    } catch {
      return;
    }
  }

  async function handleAiStart() {
    if (!selectedTemplateId) {
      setAiError(messages.documentProcessing.templateRequired);
      return;
    }

    setAiError(null);
    setProgressItems([]);
    setStreamTimeline([]);
    setSelectedMode("ai");
    setPendingExtractionTemplateId(selectedTemplateId);

    try {
      const session = await aiSessionMutation.mutateAsync(documentId);
      await createAgentThread({
        threadId: session.thread_id,
        metadata: {
          document_id: documentId,
          purpose: "document_classification",
        },
      });

      await runAgentStream({
        kind: "classification",
        threadId: session.thread_id,
        payload: {
          assistant_id: session.assistant_id,
          input: {
            document_id: documentId,
            thread_id: session.thread_id,
          },
          stream_mode: ["custom"],
          on_disconnect: "continue",
        },
      });
    } catch (error) {
      setAiError(getApiErrorMessage(error, messages.common.apiError));
    }
  }

  async function handleExtractionStart(templateId: string) {
    setAiError(null);
    setSelectedMode("ai");

    try {
      const session = await extractionSessionMutation.mutateAsync({
        documentId,
        templateId,
      });
      await createAgentThread({
        threadId: session.thread_id,
        metadata: {
          document_id: documentId,
          extraction_template_id: templateId,
          purpose: "document_extraction",
        },
      });

      await runAgentStream({
        kind: "extraction",
        threadId: session.thread_id,
        payload: {
          assistant_id: DOCUMENT_EXTRACTION_ASSISTANT_ID,
          input: {
            document_id: documentId,
            thread_id: session.thread_id,
            extraction_template_id: templateId,
          },
          stream_mode: ["custom"],
          on_disconnect: "continue",
        },
      });
    } catch (error) {
      setAiError(getApiErrorMessage(error, messages.common.apiError));
    }
  }

  async function handleSuggestedCategoryResponse(
    action: "accept" | "edit" | "ignore",
  ) {
    const threadId = document.classification.thread_id;
    if (!threadId) {
      setAiError(messages.documentProcessing.missingThread);
      return;
    }

    const resumeArgs =
      action === "accept"
        ? null
        : action === "ignore"
          ? null
          : {
              name: customCategoryName.trim(),
              label_key: customCategoryLabelKey.trim(),
            };

    try {
      setSuggestionResolved(true);
      await runAgentStream({
        kind: "classification",
        threadId,
        payload: {
          assistant_id: DOCUMENT_CLASSIFICATION_ASSISTANT_ID,
          command: {
            resume: [
              {
                type: action,
                args: resumeArgs,
              },
            ],
          },
          stream_mode: ["custom"],
          on_disconnect: "continue",
        },
      });
    } catch (error) {
      setSuggestionResolved(false);
      setAiError(getApiErrorMessage(error, messages.common.apiError));
    }
  }

  async function runAgentStream({
    kind,
    threadId,
    payload,
  }: {
    kind: "classification" | "extraction";
    threadId: string;
    payload: Parameters<typeof streamAgentRun>[0]["payload"];
  }) {
    const controller = new AbortController();
    streamAbortControllerRef.current = controller;
    setIsStreaming(true);
    setActiveStreamKind(kind);
    setAiError(null);

    try {
      await streamAgentRun({
        threadId,
        payload,
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
              setAiError(payload.message);
            }
          }
        },
      });
    } finally {
      setIsStreaming(false);
      setActiveStreamKind(null);
      streamAbortControllerRef.current = null;
      await Promise.all([onDocumentRefresh(), extractionQuery.refetch()]);
    }
  }

  async function handleExtractionReviewSave(result: DocumentExtractionResult) {
    if (!result) {
      return;
    }

    try {
      await extractionReviewMutation.mutateAsync({
        documentId,
        payload: {
          result,
        },
      });
      await Promise.all([extractionQuery.refetch(), onDocumentRefresh()]);
      onOpenChange(false);
    } catch {
      return;
    }
  }

  function handleCustomCategoryNameChange(value: string) {
    const previousSlug = slugifyDocumentCategoryLabelKey(customCategoryName);
    setCustomCategoryName(value);

    if (!customCategoryLabelKey || customCategoryLabelKey === previousSlug) {
      setCustomCategoryLabelKey(slugifyDocumentCategoryLabelKey(value));
    }
  }

  return (
    <Card
      className="border-[color:var(--color-line-strong)]"
      data-tour="processing-panel"
    >
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="accent">
                {messages.documentProcessing.badge}
              </Badge>
              {document.classification.status === "pending_review" ? (
                <Badge variant="warm">
                  {messages.documentProcessing.pendingBadge}
                </Badge>
              ) : null}
            </div>
            <CardTitle className="mt-3 text-2xl">
              {messages.documentProcessing.title}
            </CardTitle>
          </div>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
            {messages.documentProcessing.closeAction}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        <div className="space-y-2 rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4">
          <Label htmlFor="document-processing-template">
            {messages.documentProcessing.templateLabel}
          </Label>
          <select
            id="document-processing-template"
            data-tour="processing-template-select"
            className="flex h-11 w-full rounded-2xl border border-[color:var(--color-line)] bg-white px-4 text-sm text-[color:var(--color-ink)] outline-none focus:border-[color:var(--color-accent)]"
            value={selectedTemplateId}
            onChange={(event) => setSelectedTemplateId(event.target.value)}
            disabled={templatesQuery.isLoading}
          >
            <option value="">
              {templatesQuery.isLoading
                ? messages.documentProcessing.templateLoading
                : messages.documentProcessing.templatePlaceholder}
            </option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>
          <p className="text-xs text-[color:var(--color-muted)]">
            {messages.documentProcessing.templateDescription}
          </p>
        </div>

        {selectedMode === "choose" ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <button
              type="button"
              data-tour="processing-manual-option"
              className="rounded-2xl border border-[color:var(--color-line)] bg-white p-5 text-left transition duration-200 hover:-translate-y-1 hover:border-[color:var(--color-accent)] hover:shadow-[0_16px_36px_rgba(29,91,219,0.12)]"
              onClick={() => setSelectedMode("manual")}
            >
              <div className="flex items-center gap-3 text-[color:var(--color-ink)]">
                <CheckCircle2 className="h-5 w-5 text-[color:var(--color-success)]" />
                <div className="text-lg font-semibold">
                  {messages.documentProcessing.options.manualTitle}
                </div>
              </div>
              <p className="mt-3 text-sm text-[color:var(--color-muted)]">
                {messages.documentProcessing.options.manualDescription}
              </p>
            </button>

            <button
              type="button"
              data-tour="processing-ai-option"
              className="rounded-2xl border border-[color:var(--color-line)] bg-white p-5 text-left transition duration-200 hover:-translate-y-1 hover:border-[color:var(--color-accent)] hover:shadow-[0_16px_36px_rgba(29,91,219,0.12)]"
              onClick={handleAiStart}
              disabled={aiSessionMutation.isPending}
            >
              <div className="flex items-center gap-3 text-[color:var(--color-ink)]">
                <WandSparkles className="h-5 w-5 text-[color:var(--color-accent)]" />
                <div className="text-lg font-semibold">
                  {messages.documentProcessing.options.aiTitle}
                </div>
              </div>
              <p className="mt-3 text-sm text-[color:var(--color-muted)]">
                {messages.documentProcessing.options.aiDescription}
              </p>
            </button>
          </div>
        ) : null}

        {selectedMode === "manual" ? (
          <div className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-white p-5">
            <div className="flex items-center gap-3 text-[color:var(--color-ink)]">
              <CheckCircle2 className="h-5 w-5 text-[color:var(--color-success)]" />
              <div className="text-lg font-semibold">
                {messages.documentProcessing.manual.title}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="manual-document-category">
                {messages.documentProcessing.manual.selectLabel}
              </Label>
              <select
                id="manual-document-category"
                className="flex h-11 w-full rounded-2xl border border-[color:var(--color-line)] bg-white px-4 text-sm text-[color:var(--color-ink)] outline-none focus:border-[color:var(--color-accent)]"
                value={selectedCategoryId}
                onChange={(event) => setSelectedCategoryId(event.target.value)}
              >
                <option value="">
                  {messages.documentProcessing.manual.placeholder}
                </option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {getDocumentCategoryDisplayName(category, messages)}
                  </option>
                ))}
              </select>
            </div>

            {manualError ? (
              <div className="rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
                {manualError}
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Button
                onClick={handleManualClassification}
                disabled={
                  !selectedCategoryId ||
                  !selectedTemplateId ||
                  manualClassificationMutation.isPending
                }
              >
                {manualClassificationMutation.isPending
                  ? messages.documentProcessing.manual.savingAction
                  : messages.documentProcessing.manual.saveAction}
              </Button>
              <Button
                variant="secondary"
                onClick={() => setSelectedMode("choose")}
                disabled={manualClassificationMutation.isPending}
              >
                {messages.documentProcessing.backAction}
              </Button>
            </div>
          </div>
        ) : null}

        {selectedMode === "ai" ? (
          <div className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-white p-5">
            <div className="flex flex-wrap items-center gap-3 text-[color:var(--color-ink)]">
              <Bot className="h-5 w-5 text-[color:var(--color-accent)]" />
              <div className="text-lg font-semibold">
                {messages.documentProcessing.ai.title}
              </div>
              {extraction ? (
                <Badge
                  variant={
                    extraction.status === "confirmed" ? "success" : "accent"
                  }
                >
                  {getDocumentExtractionStatusLabel(
                    extraction.status,
                    messages,
                  )}
                </Badge>
              ) : null}
            </div>

            <div
              className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4"
              data-tour="processing-live-progress"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                    {isStreaming ? (
                      <LoaderCircle className="h-4 w-4 animate-spin text-[color:var(--color-accent)]" />
                    ) : (
                      <Bot className="h-4 w-4 text-[color:var(--color-accent)]" />
                    )}
                    {streamingTitle}
                    <Badge variant={streamStatusVariant}>
                      {streamStatusLabel}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-[color:var(--color-muted)]">
                    {latestProgressItem?.message ??
                      (isStreaming
                        ? streamingEmptyMessage
                        : timelineEmptyMessage)}
                  </p>
                </div>
              </div>

              <div className="mt-3 space-y-2">
                {streamTimeline.length ? (
                  streamTimeline.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start justify-between gap-3 rounded-xl border border-[color:var(--color-line)] bg-white px-3 py-2"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant={item.variant}>{item.label}</Badge>
                          <span className="truncate text-sm text-[color:var(--color-ink)]">
                            {item.summary}
                          </span>
                        </div>
                      </div>
                      <span className="shrink-0 text-[11px] text-[color:var(--color-muted)]">
                        {timeFormatter.format(item.occurredAt)}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-[color:var(--color-muted)]">
                    {isStreaming ? streamingEmptyMessage : timelineEmptyMessage}
                  </div>
                )}
              </div>
            </div>

            {document.classification.status === "pending_review" &&
            pendingSuggestion &&
            !suggestionResolved ? (
              <div
                className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4"
                data-tour="processing-category-suggestion"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="warm">
                    {messages.documentProcessing.ai.reviewBadge}
                  </Badge>
                  {document.classification.confidence !== null ? (
                    <Badge>
                      {messages.documentProcessing.ai.confidenceLabel.replace(
                        "{value}",
                        `${Math.round(document.classification.confidence * 100)}%`,
                      )}
                    </Badge>
                  ) : null}
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3">
                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                      {messages.documentProcessing.ai.suggestedName}
                    </div>
                    <div className="mt-2 text-sm font-medium text-[color:var(--color-ink)]">
                      {getDocumentCategoryDisplayName(
                        pendingSuggestion,
                        messages,
                      )}
                    </div>
                  </div>
                  <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3">
                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                      {messages.documentProcessing.ai.suggestedLabelKey}
                    </div>
                    <div className="mt-2 text-sm font-medium text-[color:var(--color-ink)]">
                      {pendingSuggestion.label_key}
                    </div>
                  </div>
                </div>

                {document.classification.rationale ? (
                  <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3">
                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                      {messages.documentProcessing.ai.rationaleTitle}
                    </div>
                    <div className="mt-2 text-sm text-[color:var(--color-ink)]">
                      {document.classification.rationale}
                    </div>
                  </div>
                ) : null}

                <div className="space-y-3 rounded-xl border border-[color:var(--color-line)] bg-white p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                    <PencilLine className="h-4 w-4 text-[color:var(--color-accent)]" />
                    {messages.documentProcessing.ai.customizeTitle}
                  </div>
                  <div className="grid gap-4 lg:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="custom-category-name">
                        {messages.documentProcessing.ai.customName}
                      </Label>
                      <Input
                        id="custom-category-name"
                        value={customCategoryName}
                        onChange={(event) =>
                          handleCustomCategoryNameChange(event.target.value)
                        }
                        placeholder={messages.documentProcessing.ai.customName}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="custom-category-label-key">
                        {messages.documentProcessing.ai.customLabelKey}
                      </Label>
                      <Input
                        id="custom-category-label-key"
                        value={customCategoryLabelKey}
                        onChange={(event) =>
                          setCustomCategoryLabelKey(
                            slugifyDocumentCategoryLabelKey(event.target.value),
                          )
                        }
                        placeholder={
                          messages.documentProcessing.ai.customLabelKey
                        }
                      />
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    data-tour="processing-category-suggestion-accept"
                    onClick={() => handleSuggestedCategoryResponse("accept")}
                    disabled={isStreaming}
                  >
                    <Sparkles className="h-4 w-4" />
                    {messages.documentProcessing.ai.acceptAction}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => handleSuggestedCategoryResponse("edit")}
                    disabled={
                      isStreaming ||
                      !customCategoryName.trim() ||
                      !customCategoryLabelKey.trim()
                    }
                  >
                    <PencilLine className="h-4 w-4" />
                    {messages.documentProcessing.ai.createCustomAction}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => handleSuggestedCategoryResponse("ignore")}
                    disabled={isStreaming}
                  >
                    {messages.documentProcessing.ai.dismissAction}
                  </Button>
                </div>
              </div>
            ) : null}

            {extraction?.result ? (
              <div className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="accent">
                    {messages.documentProcessing.extraction.reviewTitle}
                  </Badge>
                  <Badge
                    variant={
                      extraction.status === "confirmed" ? "success" : "warm"
                    }
                  >
                    {getDocumentExtractionStatusLabel(
                      extraction.status,
                      messages,
                    )}
                  </Badge>
                </div>
                <DocumentExtractionReview
                  key={extraction.updated_at}
                  extraction={extraction}
                  messages={messages}
                  isSaving={extractionReviewMutation.isPending}
                  onSave={handleExtractionReviewSave}
                />
                <DocumentExtractionCorrectionChat
                  documentId={documentId}
                  extraction={extraction}
                  onExtractionRefresh={async () => {
                    await extractionQuery.refetch();
                  }}
                />
              </div>
            ) : null}

            {aiError ? (
              <div className="rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
                {aiError}
              </div>
            ) : null}

            {extractionError ? (
              <div className="rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
                {extractionError}
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              {!isStreaming &&
              document.classification.status !== "pending_review" &&
              !hasExtractionDraft ? (
                <Button
                  onClick={handleAiStart}
                  disabled={aiSessionMutation.isPending}
                >
                  {aiSessionMutation.isPending
                    ? messages.documentProcessing.ai.startingAction
                    : messages.documentProcessing.ai.startAction}
                </Button>
              ) : null}
              {!isStreaming &&
              document.classification.status === "classified" &&
              !hasExtractionDraft ? (
                <Button
                  variant="secondary"
                  onClick={() => handleExtractionStart(selectedTemplateId)}
                  disabled={
                    !selectedTemplateId || extractionSessionMutation.isPending
                  }
                >
                  {extractionSessionMutation.isPending
                    ? messages.documentProcessing.extraction.startingAction
                    : messages.documentProcessing.extraction.startAction}
                </Button>
              ) : null}
              <Button
                variant="secondary"
                onClick={() => setSelectedMode("choose")}
                disabled={isStreaming}
              >
                {messages.documentProcessing.backAction}
              </Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
