import type { Messages } from "@/lib/i18n";

export type DocumentKind = "pdf" | "image" | "spreadsheet" | "docx";

export interface Document {
  id: string;
  original_filename: string;
  content_type: string;
  file_extension: string;
  file_kind: DocumentKind;
  size_bytes: number;
  sha256: string;
  public_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadSuccessResult {
  fileName: string;
  status: "success";
  document: Document;
}

export interface DocumentUploadFailureResult {
  fileName: string;
  status: "error";
  errorMessage: string;
}

export type DocumentUploadBatchResult =
  | DocumentUploadSuccessResult
  | DocumentUploadFailureResult;

export function getDocumentKindLabel(
  documentKind: DocumentKind,
  messages: Messages,
) {
  return messages.documentsShared.fileKinds[documentKind];
}

export function formatDocumentSize(sizeBytes: number, locale: string) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = sizeBytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }

  const maximumFractionDigits = unitIndex === 0 ? 0 : size >= 10 ? 1 : 2;

  return `${new Intl.NumberFormat(locale, {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  }).format(size)} ${units[unitIndex]}`;
}

export function getDocumentShaPreview(value: string) {
  if (value.length <= 16) {
    return value;
  }

  return `${value.slice(0, 10)}...${value.slice(-8)}`;
}
