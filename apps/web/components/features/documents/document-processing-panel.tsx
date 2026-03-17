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
import { useEffect, useRef, useState } from "react";

import { useDocumentCategoriesQuery } from "@/hooks/use-document-categories";
import {
  useCreateDocumentAiClassificationSessionMutation,
  useManualDocumentClassificationMutation,
} from "@/hooks/use-documents";
import { createAgentThread, streamAgentRun } from "@/lib/api/aegra";
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import type { AgentStreamEvent } from "@/types/aegra";
import type { Document } from "@/types/documents";
import { getDocumentCategoryDisplayName, slugifyDocumentCategoryLabelKey } from "@/types/document-categories";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const CATEGORY_PAGE_SIZE = 100;
const DOCUMENT_CLASSIFICATION_ASSISTANT_ID = "document_classification_agent";

interface ProgressItem {
  phase: string;
  message: string;
}

function extractProgressItem(event: AgentStreamEvent): ProgressItem | null {
  if (event.event !== "custom") {
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function unwrapAgentPayload(value: unknown): unknown {
  if (isRecord(value) && "chunk" in value) {
    return value.chunk;
  }
  return value;
}

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
  const { messages } = useLocale();
  const categoriesQuery = useDocumentCategoriesQuery({
    page: 1,
    pageSize: CATEGORY_PAGE_SIZE,
  });
  const manualClassificationMutation = useManualDocumentClassificationMutation();
  const aiSessionMutation = useCreateDocumentAiClassificationSessionMutation();

  const [selectedMode, setSelectedMode] = useState<"choose" | "manual" | "ai">("choose");
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [customCategoryName, setCustomCategoryName] = useState("");
  const [customCategoryLabelKey, setCustomCategoryLabelKey] = useState("");
  const [progressItems, setProgressItems] = useState<ProgressItem[]>([]);
  const [aiError, setAiError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamAbortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    setAiError(null);
    setProgressItems([]);
    setSelectedCategoryId(document.classification.category?.id ?? "");

    if (
      document.classification.status === "pending_review" &&
      document.classification.suggested_category
    ) {
      setSelectedMode("ai");
      setCustomCategoryName(document.classification.suggested_category.name);
      setCustomCategoryLabelKey(document.classification.suggested_category.label_key);
      return;
    }

    setSelectedMode("choose");
    setCustomCategoryName("");
    setCustomCategoryLabelKey("");
  }, [
    document.classification.category?.id,
    document.classification.status,
    document.classification.suggested_category,
    open,
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
  const pendingSuggestion = document.classification.suggested_category;
  const manualError = manualClassificationMutation.error
    ? getApiErrorMessage(
        manualClassificationMutation.error,
        messages.common.apiError,
      )
    : null;

  async function handleManualClassification() {
    if (!selectedCategoryId) {
      return;
    }

    try {
      await manualClassificationMutation.mutateAsync({
        documentId,
        categoryId: selectedCategoryId,
      });
      await onDocumentRefresh();
      onOpenChange(false);
    } catch {
      return;
    }
  }

  async function handleAiStart() {
    setAiError(null);
    setProgressItems([]);
    setSelectedMode("ai");

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
      await runAgentStream({
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

      await onDocumentRefresh();
      onOpenChange(false);
    } catch (error) {
      setAiError(getApiErrorMessage(error, messages.common.apiError));
    }
  }

  async function runAgentStream({
    threadId,
    payload,
  }: {
    threadId: string;
    payload: Parameters<typeof streamAgentRun>[0]["payload"];
  }) {
    const controller = new AbortController();
    streamAbortControllerRef.current = controller;
    setIsStreaming(true);
    setAiError(null);

    try {
      await streamAgentRun({
        threadId,
        payload,
        signal: controller.signal,
        onEvent: async (event) => {
          const progressItem = extractProgressItem(event);
          if (progressItem) {
            setProgressItems((currentItems) => [...currentItems, progressItem]);
          }

          if (event.event === "error") {
            const payload = unwrapAgentPayload(event.data);
            if (isRecord(payload) && typeof payload.message === "string") {
              setAiError(payload.message);
            }
          }
        },
      });
    } finally {
      setIsStreaming(false);
      streamAbortControllerRef.current = null;
      await onDocumentRefresh();
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
    <Card className="border-[color:var(--color-line-strong)]">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="accent">{messages.documentProcessing.badge}</Badge>
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
        {selectedMode === "choose" ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <button
              type="button"
              className="rounded-2xl border border-[color:var(--color-line)] bg-white p-5 text-left transition hover:border-[color:var(--color-accent)]"
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
              className="rounded-2xl border border-[color:var(--color-line)] bg-white p-5 text-left transition hover:border-[color:var(--color-accent)]"
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
                  !selectedCategoryId || manualClassificationMutation.isPending
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
            <div className="flex items-center gap-3 text-[color:var(--color-ink)]">
              <Bot className="h-5 w-5 text-[color:var(--color-accent)]" />
              <div className="text-lg font-semibold">
                {messages.documentProcessing.ai.title}
              </div>
            </div>

            {isStreaming ? (
              <div className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                  <LoaderCircle className="h-4 w-4 animate-spin text-[color:var(--color-accent)]" />
                  {messages.documentProcessing.ai.streamingTitle}
                </div>
                <div className="mt-4 space-y-3">
                  {progressItems.length ? (
                    progressItems.map((item, index) => (
                      <div
                        key={`${item.phase}-${index}`}
                        className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3"
                      >
                        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                          {item.phase.replaceAll("_", " ")}
                        </div>
                        <div className="mt-2 text-sm text-[color:var(--color-ink)]">
                          {item.message}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-[color:var(--color-muted)]">
                      {messages.documentProcessing.ai.streamingEmpty}
                    </div>
                  )}
                </div>
              </div>
            ) : null}

            {pendingSuggestion ? (
              <div className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4">
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
                      {pendingSuggestion.name}
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
                        placeholder={messages.documentProcessing.ai.customLabelKey}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
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
                      isStreaming || !customCategoryName.trim() || !customCategoryLabelKey.trim()
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

            {aiError ? (
              <div className="rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
                {aiError}
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              {!isStreaming && document.classification.status !== "pending_review" ? (
                <Button onClick={handleAiStart} disabled={aiSessionMutation.isPending}>
                  {aiSessionMutation.isPending
                    ? messages.documentProcessing.ai.startingAction
                    : messages.documentProcessing.ai.startAction}
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
