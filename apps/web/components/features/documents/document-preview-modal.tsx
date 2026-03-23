"use client";

import { Eye, X } from "lucide-react";
import { useEffect } from "react";

import { DocumentPreviewContent } from "@/components/features/documents/document-preview-content";
import { Button } from "@/components/ui/button";
import { useLocale } from "@/providers/locale-provider";
import { getDocumentKindLabel, type Document } from "@/types/documents";

export function DocumentPreviewModal({
  document,
  open,
  onClose,
}: {
  document: Document | null;
  open: boolean;
  onClose: () => void;
}) {
  const { messages } = useLocale();

  useEffect(() => {
    if (!open) {
      return;
    }

    const originalOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";

    return () => {
      window.document.body.style.overflow = originalOverflow;
    };
  }, [open]);

  if (!open || !document) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-[rgba(17,24,39,0.58)] px-3 py-4 sm:px-6 sm:py-8">
      <div className="flex h-full max-h-[calc(100vh-2rem)] w-full max-w-6xl flex-col overflow-hidden rounded-[32px] border border-white/25 bg-[color:var(--color-background)] shadow-[0_28px_80px_rgba(15,23,42,0.35)]">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[color:var(--color-line)] bg-white/92 px-5 py-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2 text-sm text-[color:var(--color-muted)]">
              <Eye className="h-4 w-4 text-[color:var(--color-accent)]" />
              {messages.documentPreviewModal.badge}
              <span className="rounded-full bg-[color:var(--color-accent-soft)] px-2 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--color-accent)]">
                {getDocumentKindLabel(document.file_kind, messages)}
              </span>
            </div>
            <div className="mt-2 truncate text-xl font-semibold text-[color:var(--color-ink)]">
              {document.original_filename}
            </div>
          </div>

          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              <X className="h-4 w-4" />
              {messages.documentPreviewModal.closeAction}
            </Button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto bg-[linear-gradient(180deg,rgba(244,246,251,0.85),rgba(255,255,255,0.92))] p-4 sm:p-6">
          <DocumentPreviewContent document={document} variant="modal" />
        </div>
      </div>
    </div>
  );
}
