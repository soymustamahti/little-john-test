"use client";

import mammoth from "mammoth";
import { FileSpreadsheet, FileText, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { getDocument, GlobalWorkerOptions } from "pdfjs-dist";
import * as XLSX from "xlsx";

import { getDocumentContent } from "@/lib/api/documents";
import { getApiErrorMessage } from "@/lib/api/errors";
import { cn } from "@/lib/utils";
import { useLocale } from "@/providers/locale-provider";
import type { Document } from "@/types/documents";

GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.mjs",
  import.meta.url,
).toString();

interface SpreadsheetSheetPreview {
  name: string;
  rows: string[][];
}

interface SpreadsheetPreview {
  sheets: SpreadsheetSheetPreview[];
  isTruncated: boolean;
}

interface PdfPreviewPage {
  pageNumber: number;
  dataUrl: string;
}

function PdfPreviewView({
  pages,
  fileName,
}: {
  pages: PdfPreviewPage[];
  fileName: string;
}) {
  return (
    <div className="space-y-4">
      {pages.map((page) => (
        <div
          key={`${fileName}-${page.pageNumber}`}
          className="overflow-hidden rounded-[28px] border border-[color:var(--color-line)] bg-white shadow-[0_18px_40px_rgba(20,27,45,0.08)]"
        >
          <div className="border-b border-[color:var(--color-line)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
            Page {page.pageNumber}
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={page.dataUrl}
            alt={`${fileName} - page ${page.pageNumber}`}
            className="h-auto w-full bg-[color:var(--color-background)] object-contain"
          />
        </div>
      ))}
    </div>
  );
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

export function DocumentPreviewContent({
  document,
  variant = "inline",
}: {
  document: Document;
  variant?: "inline" | "modal";
}) {
  const { messages } = useLocale();
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [binaryPreviewUrl, setBinaryPreviewUrl] = useState<string | null>(null);
  const [pdfPreviewPages, setPdfPreviewPages] = useState<PdfPreviewPage[] | null>(null);
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [spreadsheetPreview, setSpreadsheetPreview] = useState<SpreadsheetPreview | null>(
    null,
  );

  useEffect(() => {
    let isCancelled = false;
    let createdObjectUrl: string | null = null;
    setErrorMessage(null);
    setBinaryPreviewUrl(null);
    setPdfPreviewPages(null);
    setTextPreview(null);
    setSpreadsheetPreview(null);

    setIsLoading(true);

    void (async () => {
      try {
        const content = await getDocumentContent(document.id);

        if (isCancelled) {
          return;
        }

        if (document.file_kind === "pdf") {
          const pdfPages = await buildPdfPreviewPages(content, variant);
          if (!isCancelled) {
            setPdfPreviewPages(pdfPages);
          }
          return;
        }

        if (document.file_kind === "image") {
          createdObjectUrl = URL.createObjectURL(
            new Blob([content], {
              type: document.content_type,
            }),
          );

          if (!isCancelled) {
            setBinaryPreviewUrl(createdObjectUrl);
          }
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
      if (createdObjectUrl) {
        URL.revokeObjectURL(createdObjectUrl);
      }
    };
  }, [
    document.content_type,
    document.file_kind,
    document.id,
    messages.common.apiError,
    variant,
  ]);

  const pdfHeightClassName = variant === "modal" ? "h-[75vh]" : "h-[36rem]";
  const imageHeightClassName = variant === "modal" ? "max-h-[72vh]" : "max-h-[32rem]";
  const imageContainerClassName =
    variant === "modal" ? "min-h-[360px]" : "min-h-[28rem]";

  return (
    <>
      {isLoading ? (
        <div className="flex h-full min-h-[320px] items-center justify-center gap-3 rounded-[28px] border border-[color:var(--color-line)] bg-white text-sm text-[color:var(--color-muted)]">
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
        pdfPreviewPages?.length ? (
          <div className={cn(pdfHeightClassName, "overflow-y-auto pr-1")}>
            <PdfPreviewView
              pages={pdfPreviewPages}
              fileName={document.original_filename}
            />
          </div>
        ) : null
      ) : null}

      {!isLoading && !errorMessage && document.file_kind === "image" ? (
        binaryPreviewUrl ? (
          <div
            className={cn(
              imageContainerClassName,
              "flex items-center justify-center rounded-[28px] border border-[color:var(--color-line)] bg-white p-4",
            )}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={binaryPreviewUrl}
              alt={document.original_filename}
              className={cn(
                imageHeightClassName,
                "w-auto max-w-full rounded-2xl object-contain",
              )}
            />
          </div>
        ) : null
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
    </>
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

async function buildPdfPreviewPages(
  content: ArrayBuffer,
  variant: "inline" | "modal",
): Promise<PdfPreviewPage[]> {
  const loadingTask = getDocument({ data: content });
  const pdf = await loadingTask.promise;
  const scale = variant === "modal" ? 1.45 : 1.15;
  const pages: PdfPreviewPage[] = [];

  try {
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber);
      const viewport = page.getViewport({ scale });
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");

      if (!context) {
        continue;
      }

      canvas.width = Math.ceil(viewport.width);
      canvas.height = Math.ceil(viewport.height);

      await page.render({
        canvas: canvas,
        canvasContext: context,
        viewport,
      }).promise;

      pages.push({
        pageNumber,
        dataUrl: canvas.toDataURL("image/jpeg", 0.92),
      });

      page.cleanup();
    }
  } finally {
    await pdf.destroy();
  }

  return pages;
}
