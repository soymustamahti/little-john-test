"use client";

import { CloudUpload, FileText, ImageIcon, Sheet, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useLocale } from "@/providers/locale-provider";
import type { DocumentUploadBatchResult } from "@/types/documents";

function StatusItem({
  result,
}: {
  result: DocumentUploadBatchResult;
}) {
  const { messages } = useLocale();

  return (
    <div className="rounded-2xl border border-[color:var(--color-line)] bg-white px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-[color:var(--color-ink)]">
            {result.fileName}
          </div>
          <div
            className={`mt-2 text-sm ${
              result.status === "success"
                ? "text-[color:var(--color-success)]"
                : "text-[color:var(--color-accent-warm)]"
            }`}
          >
            {result.status === "success"
              ? messages.documentUploadPanel.status.uploaded
              : result.errorMessage}
          </div>
        </div>
        <Badge variant={result.status === "success" ? "success" : "warm"}>
          {result.status === "success"
            ? messages.documentUploadPanel.status.successBadge
            : messages.documentUploadPanel.status.errorBadge}
        </Badge>
      </div>
    </div>
  );
}

export function DocumentUploadPanel({
  selectedFiles,
  uploadResults,
  isUploading,
  onFileSelection,
  onUpload,
  onClear,
}: {
  selectedFiles: File[];
  uploadResults: DocumentUploadBatchResult[];
  isUploading: boolean;
  onFileSelection: (files: FileList | null) => void;
  onUpload: () => void;
  onClear: () => void;
}) {
  const { messages, formatText } = useLocale();

  return (
    <Card className="overflow-hidden" data-tour="documents-upload">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="accent">{messages.documentUploadPanel.badges.intake}</Badge>
              <Badge>{messages.documentUploadPanel.badges.secure}</Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">
              {messages.documentUploadPanel.title}
            </CardTitle>
            <CardDescription>
              {messages.documentUploadPanel.description}
            </CardDescription>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={onClear}
              disabled={!selectedFiles.length || isUploading}
            >
              <X className="h-4 w-4" />
              {messages.documentUploadPanel.clearAction}
            </Button>
            <Button
              type="button"
              onClick={onUpload}
              disabled={!selectedFiles.length || isUploading}
              data-tour="documents-upload-action"
            >
              <CloudUpload className="h-4 w-4" />
              {isUploading
                ? messages.documentUploadPanel.uploadingAction
                : formatText(messages.documentUploadPanel.uploadAction, {
                    count: selectedFiles.length,
                  })}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        <label
          htmlFor="documents-upload-input"
          className="block cursor-pointer rounded-[28px] border border-dashed border-[color:var(--color-line-strong)] bg-[linear-gradient(135deg,rgba(229,237,255,0.6),rgba(255,255,255,0.92))] p-6 transition hover:border-[color:var(--color-accent)] hover:bg-[linear-gradient(135deg,rgba(229,237,255,0.8),rgba(255,255,255,0.98))]"
          data-tour="documents-dropzone"
        >
          <input
            id="documents-upload-input"
            type="file"
            multiple
            className="sr-only"
            accept=".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,.bmp,.docx,.xlsx,.xls,.ods,.csv"
            onChange={(event) => onFileSelection(event.target.files)}
          />

          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
            <div>
              <div className="flex items-center gap-3 text-[color:var(--color-ink)]">
                <div className="rounded-2xl bg-white p-3 shadow-[0_12px_24px_rgba(29,91,219,0.12)]">
                  <CloudUpload className="h-6 w-6 text-[color:var(--color-accent)]" />
                </div>
                <div>
                  <div className="text-lg font-semibold">
                    {messages.documentUploadPanel.dropzone.title}
                  </div>
                  <div className="text-sm text-[color:var(--color-muted)]">
                    {messages.documentUploadPanel.dropzone.description}
                  </div>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Badge variant="accent">
                  <FileText className="mr-2 h-3.5 w-3.5" />
                  PDF + DOCX
                </Badge>
                <Badge variant="warm">
                  <ImageIcon className="mr-2 h-3.5 w-3.5" />
                  PNG / JPG / WEBP / TIFF / BMP
                </Badge>
                <Badge variant="success">
                  <Sheet className="mr-2 h-3.5 w-3.5" />
                  XLSX / XLS / ODS / CSV
                </Badge>
              </div>
            </div>

            <div className="rounded-2xl border border-[color:var(--color-line)] bg-white/88 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                {messages.documentUploadPanel.selection.title}
              </div>
              <div className="mt-3 space-y-2">
                {selectedFiles.length ? (
                  selectedFiles.map((file) => (
                    <div
                      key={`${file.name}-${file.size}-${file.lastModified}`}
                      className="rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-3 py-2 text-sm text-[color:var(--color-ink)]"
                    >
                      {file.name}
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-3 py-4 text-sm text-[color:var(--color-muted)]">
                    {messages.documentUploadPanel.selection.empty}
                  </div>
                )}
              </div>
            </div>
          </div>
        </label>

        {uploadResults.length ? (
          <div className="space-y-3">
            <div className="text-sm font-medium text-[color:var(--color-ink)]">
              {messages.documentUploadPanel.status.title}
            </div>
            <div className="grid gap-3">
              {uploadResults.map((result) => (
                <StatusItem
                  key={`${result.fileName}-${result.status}`}
                  result={result}
                />
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
