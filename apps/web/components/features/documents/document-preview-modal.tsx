"use client";

import mammoth from "mammoth";
import {
  Eye,
  FileSpreadsheet,
  FileText,
  LoaderCircle,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import * as XLSX from "xlsx";

import { Button } from "@/components/ui/button";
import { getDocumentContent, getDocumentContentUrl } from "@/lib/api/documents";
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import { getDocumentKindLabel, type Document } from "@/types/documents";

interface SpreadsheetSheetPreview {
  name: string;
  rows: string[][];
}

interface SpreadsheetPreview {
  sheets: SpreadsheetSheetPreview[];
  isTruncated: boolean;
}

function SpreadsheetPreviewView({
  preview,
}: {
  preview: SpreadsheetPreview;
}) {
  const { messages } = useLocale();

  return (
    <div className="space-y-5">
      {preview.sheets.map((sheet) => (
        <div
          key={sheet.name}
          className="rounded-2xl border border-[color:var(--color-line)] bg-white"
        >
          <div className="border-b border-[color:var(--color-line)] px-4 py-3 text-sm font-semibold text-[color:var(--color-ink)]">
            {sheet.name}
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <tbody>
                {sheet.rows.length ? (
                  sheet.rows.map((row, rowIndex) => (
                    <tr
                      key={`${sheet.name}-${rowIndex}`}
                      className="border-t border-[color:var(--color-line)] first:border-t-0"
                    >
                      {row.map((cell, cellIndex) => (
                        <td
                          key={`${sheet.name}-${rowIndex}-${cellIndex}`}
                          className="max-w-[280px] px-4 py-3 align-top text-[color:var(--color-ink)]"
                        >
                          {cell || "—"}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-4 text-[color:var(--color-muted)]">
                      {messages.documentPreviewModal.spreadsheet.emptySheet}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {preview.isTruncated ? (
        <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3 text-sm text-[color:var(--color-muted)]">
          {messages.documentPreviewModal.spreadsheet.truncated}
        </div>
      ) : null}
    </div>
  );
}

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
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [spreadsheetPreview, setSpreadsheetPreview] = useState<SpreadsheetPreview | null>(
    null,
  );

  useEffect(() => {
    if (!open || !document) {
      return;
    }

    let isCancelled = false;
    setErrorMessage(null);
    setTextPreview(null);
    setSpreadsheetPreview(null);

    if (document.file_kind === "pdf" || document.file_kind === "image") {
      return;
    }

    setIsLoading(true);

    void (async () => {
      try {
        const content = await getDocumentContent(document.id);

        if (isCancelled) {
          return;
        }

        if (document.file_kind === "docx") {
          const result = await mammoth.extractRawText({ arrayBuffer: content });
          if (!isCancelled) {
            setTextPreview(result.value);
          }
          return;
        }

        const workbook = XLSX.read(content, { type: "array" });
        const preview = buildSpreadsheetPreview(workbook);
        if (!isCancelled) {
          setSpreadsheetPreview(preview);
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(getApiErrorMessage(error, messages.common.apiError));
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      isCancelled = true;
    };
  }, [document, messages.common.apiError, open]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const originalOverflow = documentRef().body.style.overflow;
    documentRef().body.style.overflow = "hidden";

    return () => {
      documentRef().body.style.overflow = originalOverflow;
    };
  }, [open]);

  if (!open || !document) {
    return null;
  }

  const contentUrl = getDocumentContentUrl(document.id);

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
          {isLoading ? (
            <div className="flex h-full min-h-[360px] items-center justify-center gap-3 rounded-[28px] border border-[color:var(--color-line)] bg-white text-sm text-[color:var(--color-muted)]">
              <LoaderCircle className="h-5 w-5 animate-spin text-[color:var(--color-accent)]" />
              {messages.documentPreviewModal.loading}
            </div>
          ) : null}

          {!isLoading && errorMessage ? (
            <div className="rounded-[28px] border border-[color:var(--color-warm-soft)] bg-white px-5 py-4 text-sm text-[color:var(--color-accent-warm)]">
              {errorMessage}
            </div>
          ) : null}

          {!isLoading && !errorMessage && document.file_kind === "pdf" ? (
            <iframe
              title={document.original_filename}
              src={contentUrl}
              className="h-[75vh] w-full rounded-[28px] border border-[color:var(--color-line)] bg-white"
            />
          ) : null}

          {!isLoading && !errorMessage && document.file_kind === "image" ? (
            <div className="flex min-h-[360px] items-center justify-center rounded-[28px] border border-[color:var(--color-line)] bg-white p-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={contentUrl}
                alt={document.original_filename}
                className="max-h-[72vh] w-auto max-w-full rounded-2xl object-contain"
              />
            </div>
          ) : null}

          {!isLoading && !errorMessage && document.file_kind === "docx" ? (
            <div className="rounded-[28px] border border-[color:var(--color-line)] bg-white p-5">
              <div className="mb-4 flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                <FileText className="h-4 w-4 text-[color:var(--color-accent)]" />
                {messages.documentPreviewModal.docx.title}
              </div>
              <pre className="whitespace-pre-wrap text-sm leading-7 text-[color:var(--color-ink)]">
                {textPreview?.trim() || messages.documentPreviewModal.docx.empty}
              </pre>
            </div>
          ) : null}

          {!isLoading && !errorMessage && document.file_kind === "spreadsheet" ? (
            spreadsheetPreview ? (
              <div>
                <div className="mb-4 flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                  <FileSpreadsheet className="h-4 w-4 text-[color:var(--color-success)]" />
                  {messages.documentPreviewModal.spreadsheet.title}
                </div>
                <SpreadsheetPreviewView preview={spreadsheetPreview} />
              </div>
            ) : (
              <div className="rounded-[28px] border border-[color:var(--color-line)] bg-white px-5 py-4 text-sm text-[color:var(--color-muted)]">
                {messages.documentPreviewModal.spreadsheet.empty}
              </div>
            )
          ) : null}
        </div>
      </div>
    </div>
  );
}

function buildSpreadsheetPreview(workbook: XLSX.WorkBook): SpreadsheetPreview {
  const MAX_SHEETS = 3;
  const MAX_ROWS = 40;
  const MAX_COLUMNS = 12;

  let isTruncated = workbook.SheetNames.length > MAX_SHEETS;

  const sheets = workbook.SheetNames.slice(0, MAX_SHEETS).map((sheetName) => {
    const sheet = workbook.Sheets[sheetName];
    const rows = (XLSX.utils.sheet_to_json(sheet, {
      header: 1,
      raw: false,
      blankrows: false,
    }) as unknown[][]).map((row) =>
      row.slice(0, MAX_COLUMNS).map((cell) => String(cell ?? "")),
    );

    if (rows.length > MAX_ROWS || rows.some((row) => row.length > MAX_COLUMNS)) {
      isTruncated = true;
    }

    return {
      name: sheetName,
      rows: rows.slice(0, MAX_ROWS),
    };
  });

  return {
    sheets,
    isTruncated,
  };
}

function documentRef() {
  return window.document;
}
