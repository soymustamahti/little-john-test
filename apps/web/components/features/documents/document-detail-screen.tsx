"use client";

import {
  ArrowLeft,
  ExternalLink,
  FileCheck2,
  Eye,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { DocumentProcessingPanel } from "@/components/features/documents/document-processing-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DocumentPreviewModal } from "@/components/features/documents/document-preview-modal";
import { useDeleteDocumentMutation, useDocumentQuery } from "@/hooks/use-documents";
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import { getDocumentCategoryDisplayName } from "@/types/document-categories";
import {
  getDocumentClassificationStatusLabel,
  formatDocumentSize,
  getDocumentKindLabel,
  getDocumentShaPreview,
} from "@/types/documents";

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-[color:var(--color-line)] bg-white px-4 py-3">
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
        {label}
      </div>
      <div className="mt-2 break-all text-sm font-medium text-[color:var(--color-ink)]">
        {value}
      </div>
    </div>
  );
}

export function DocumentDetailScreen({
  documentId,
}: {
  documentId: string;
}) {
  const router = useRouter();
  const { locale, messages, formatDate } = useLocale();
  const documentQuery = useDocumentQuery(documentId);
  const deleteDocumentMutation = useDeleteDocumentMutation();
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isProcessingPanelOpen, setIsProcessingPanelOpen] = useState(false);

  async function deleteDocument() {
    const document = documentQuery.data;
    if (!document) {
      return;
    }

    const confirmed = window.confirm(
      messages.documentDetailScreen.confirmDelete.replace(
        "{name}",
        document.original_filename,
      ),
    );

    if (!confirmed) {
      return;
    }

    try {
      await deleteDocumentMutation.mutateAsync(documentId);
      router.push("/documents");
    } catch {
      // Error is rendered below from the mutation state.
    }
  }

  if (documentQuery.isLoading) {
    return (
      <div className="px-4 py-6 sm:px-6">
        <Card>
          <CardContent className="p-6 text-sm text-[color:var(--color-muted)]">
            {messages.documentDetailScreen.loading}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (documentQuery.error || !documentQuery.data) {
    return (
      <div className="space-y-4 px-4 py-6 sm:px-6">
        <Button variant="secondary" onClick={() => router.push("/documents")}>
          <ArrowLeft className="h-4 w-4" />
          {messages.documentDetailScreen.backToDocuments}
        </Button>
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">
              {messages.documentDetailScreen.errorTitle}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[color:var(--color-accent-warm)]">
            {getApiErrorMessage(documentQuery.error, messages.common.apiError)}
          </CardContent>
        </Card>
      </div>
    );
  }

  const document = documentQuery.data;
  const deleteError = deleteDocumentMutation.error
    ? getApiErrorMessage(deleteDocumentMutation.error, messages.common.apiError)
    : null;
  const classification = document.classification;
  const classificationVariant =
    classification.status === "classified"
      ? "success"
      : classification.status === "pending_review" || classification.status === "failed"
        ? "warm"
        : classification.status === "processing"
          ? "accent"
          : "default";
  const classificationLabel = getDocumentClassificationStatusLabel(
    classification.status,
    messages,
  );
  const classifiedCategoryName = classification.category
    ? getDocumentCategoryDisplayName(classification.category, messages)
    : null;

  return (
    <div className="space-y-6 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-[color:var(--color-muted)]">
            {messages.common.labels.workspace} / {messages.documentDetailScreen.breadcrumbSection} /{" "}
            {document.original_filename}
          </p>
          <h2 className="mt-1 text-3xl font-semibold text-[color:var(--color-ink)]">
            {document.original_filename}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            {messages.documentDetailScreen.description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="accent">{messages.documentDetailScreen.badge}</Badge>
          <Button variant="secondary" onClick={() => router.push("/documents")}>
            <ArrowLeft className="h-4 w-4" />
            {messages.common.actions.backToList}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b border-[color:var(--color-line)]">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="accent">
                  {getDocumentKindLabel(document.file_kind, messages)}
                </Badge>
                <Badge>{document.file_extension.toUpperCase().replace(".", "")}</Badge>
              </div>
              <CardTitle className="mt-3 text-2xl">
                {messages.documentDetailScreen.cardTitle}
              </CardTitle>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setIsPreviewOpen(true)}
              >
                <Eye className="h-4 w-4" />
                {messages.common.actions.preview}
              </Button>
              {document.public_url ? (
                <a href={document.public_url} target="_blank" rel="noreferrer">
                  <Button type="button" variant="secondary">
                    <ExternalLink className="h-4 w-4" />
                    {messages.documentDetailScreen.openPublicUrl}
                  </Button>
                </a>
              ) : null}
              <Button
                type="button"
                onClick={() => setIsProcessingPanelOpen(true)}
              >
                <Sparkles className="h-4 w-4" />
                {messages.documentProcessing.openAction}
              </Button>
              <Button
                type="button"
                variant="danger"
                onClick={deleteDocument}
                disabled={deleteDocumentMutation.isPending}
              >
                <Trash2 className="h-4 w-4" />
                {deleteDocumentMutation.isPending
                  ? messages.common.actions.deleting
                  : messages.common.actions.delete}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/65 p-4">
            <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
              <FileCheck2 className="h-4 w-4 text-[color:var(--color-accent)]" />
              {messages.documentDetailScreen.summaryTitle}
              <Badge variant={classificationVariant}>{classificationLabel}</Badge>
              {classifiedCategoryName ? (
                <Badge variant="accent">{classifiedCategoryName}</Badge>
              ) : null}
            </div>
            <p className="mt-2 text-sm text-[color:var(--color-muted)]">
              {messages.documentDetailScreen.summaryDescription}
            </p>
            {classification.rationale ? (
              <p className="mt-3 text-sm text-[color:var(--color-ink)]">
                {classification.status === "pending_review"
                  ? messages.documentDetailScreen.pendingClassification.replace(
                      "{reason}",
                      classification.rationale,
                    )
                  : classification.rationale}
              </p>
            ) : null}
            {classification.error ? (
              <p className="mt-3 text-sm text-[color:var(--color-accent-warm)]">
                {classification.error}
              </p>
            ) : null}
          </div>

          {isProcessingPanelOpen ? (
            <DocumentProcessingPanel
              document={document}
              documentId={documentId}
              open={isProcessingPanelOpen}
              onOpenChange={setIsProcessingPanelOpen}
              onDocumentRefresh={() => documentQuery.refetch()}
            />
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
            <InfoRow
              label={messages.documentDetailScreen.fields.kind}
              value={getDocumentKindLabel(document.file_kind, messages)}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.contentType}
              value={document.content_type}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.size}
              value={formatDocumentSize(document.size_bytes, locale)}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.created}
              value={formatDate(document.created_at)}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.updated}
              value={formatDate(document.updated_at)}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.sha}
              value={getDocumentShaPreview(document.sha256)}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.classificationStatus}
              value={classificationLabel}
            />
            <InfoRow
              label={messages.documentDetailScreen.fields.classificationCategory}
              value={
                classifiedCategoryName ??
                (classification.suggested_category
                  ? getDocumentCategoryDisplayName(
                      classification.suggested_category,
                      messages,
                    )
                  : messages.documentDetailScreen.unclassifiedValue)
              }
            />
          </div>

          {deleteError ? (
            <div className="rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
              {deleteError}
            </div>
          ) : null}

          {!document.public_url ? (
            <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3 text-sm text-[color:var(--color-muted)]">
              {messages.documentDetailScreen.privateStorageNotice}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <DocumentPreviewModal
        document={document}
        open={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
      />
    </div>
  );
}
