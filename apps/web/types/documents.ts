import type { Messages } from "@/lib/i18n";

export type DocumentKind = "pdf" | "image" | "spreadsheet" | "docx";
export type DocumentClassificationStatus =
  | "unclassified"
  | "processing"
  | "pending_review"
  | "classified"
  | "failed";
export type DocumentClassificationMethod = "manual" | "ai";
export type DocumentExtractionStatus =
  | "not_started"
  | "processing"
  | "pending_review"
  | "confirmed"
  | "failed";
export type DocumentExtractionMethod = "ai";
export type ExtractionValueMode = "direct" | "inferred" | "not_found";
export type ScalarExtractionValue = string | number | boolean | null;

export interface DocumentClassificationCategory {
  id: string;
  name: string;
  label_key: string;
}

export interface SuggestedDocumentCategory {
  name: string;
  label_key: string;
}

export interface DocumentClassification {
  status: DocumentClassificationStatus;
  method: DocumentClassificationMethod | null;
  confidence: number | null;
  rationale: string | null;
  thread_id: string | null;
  error: string | null;
  sampled_chunk_indices: number[];
  excerpt_character_count: number | null;
  suggested_category: SuggestedDocumentCategory | null;
  category: DocumentClassificationCategory | null;
  classified_at: string | null;
}

export interface Document {
  id: string;
  original_filename: string;
  content_type: string;
  file_extension: string;
  file_kind: DocumentKind;
  size_bytes: number;
  sha256: string;
  public_url: string | null;
  classification: DocumentClassification;
  created_at: string;
  updated_at: string;
}

export interface DocumentClassificationSession {
  assistant_id: string;
  thread_id: string;
  document_id: string;
  status: DocumentClassificationStatus;
}

export interface DocumentExtractionEvidence {
  source_chunk_indices: number[];
  source_excerpt: string | null;
}

export interface ScalarExtractionField {
  kind: "scalar";
  key: string;
  label: string;
  value_type: "string" | "number" | "date" | "boolean";
  required: boolean;
  value: ScalarExtractionValue;
  raw_value: string | null;
  confidence: number;
  extraction_mode: ExtractionValueMode;
  evidence: DocumentExtractionEvidence | null;
}

export interface TableExtractionCell {
  key: string;
  label: string;
  value_type: "string" | "number" | "date" | "boolean";
  required: boolean;
  value: ScalarExtractionValue;
  raw_value: string | null;
  confidence: number;
  extraction_mode: ExtractionValueMode;
  evidence: DocumentExtractionEvidence | null;
}

export interface TableExtractionRow {
  row_index: number;
  confidence: number;
  cells: TableExtractionCell[];
}

export interface TableExtractionField {
  kind: "table";
  key: string;
  label: string;
  required: boolean;
  min_rows: number;
  rows: TableExtractionRow[];
}

export type DocumentExtractionField =
  | ScalarExtractionField
  | TableExtractionField;

export interface DocumentExtractionModule {
  key: string;
  label: string;
  fields: DocumentExtractionField[];
}

export interface DocumentExtractionResult {
  modules: DocumentExtractionModule[];
}

export interface DocumentExtractionTemplateSummary {
  id: string;
  name: string;
  locale: string;
}

export interface DocumentExtractionCorrectionMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface DocumentExtraction {
  document_id: string;
  status: DocumentExtractionStatus;
  method: DocumentExtractionMethod | null;
  template: DocumentExtractionTemplateSummary;
  thread_id: string | null;
  overall_confidence: number | null;
  reasoning_summary: string | null;
  error: string | null;
  correction_messages: DocumentExtractionCorrectionMessage[];
  result: DocumentExtractionResult | null;
  extracted_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentExtractionSession {
  assistant_id: string;
  thread_id: string;
  document_id: string;
  template_id: string;
  status: DocumentExtractionStatus;
}

export interface DocumentExtractionCorrectionSession {
  assistant_id: string;
  thread_id: string;
  document_id: string;
  status: DocumentExtractionStatus;
}

export interface DocumentExtractionReviewPayload {
  result: DocumentExtractionResult;
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

export function getDocumentClassificationStatusLabel(
  status: DocumentClassificationStatus,
  messages: Messages,
) {
  return messages.documentProcessing.statuses[status];
}

export function getDocumentExtractionStatusLabel(
  status: DocumentExtractionStatus,
  messages: Messages,
) {
  return messages.documentProcessing.extraction.statuses[status];
}
