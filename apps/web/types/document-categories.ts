import type { Messages } from "@/lib/i18n";

export interface DocumentCategory {
  id: string;
  name: string;
  label_key: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentCategoryDraft {
  name: string;
  label_key: string;
}

export interface DocumentCategoryPayload {
  name: string;
  label_key: string;
}

export interface DocumentCategoryValidationMessages {
  nameRequired: string;
  labelKeyRequired: string;
  labelKeyPattern: string;
}

export const DOCUMENT_CATEGORY_LABEL_KEY_PATTERN =
  "^[a-z0-9]+(?:_[a-z0-9]+)*$";

const documentCategoryLabelKeyRegex = new RegExp(DOCUMENT_CATEGORY_LABEL_KEY_PATTERN);

export function createEmptyDocumentCategoryDraft(): DocumentCategoryDraft {
  return {
    name: "",
    label_key: "",
  };
}

export function documentCategoryToDraft(
  category: DocumentCategory,
): DocumentCategoryDraft {
  return {
    name: category.name,
    label_key: category.label_key,
  };
}

export function cloneDocumentCategoryDraft(
  draft: DocumentCategoryDraft,
): DocumentCategoryDraft {
  return structuredClone(draft);
}

export function draftToDocumentCategoryPayload(
  draft: DocumentCategoryDraft,
): DocumentCategoryPayload {
  return {
    name: draft.name.trim(),
    label_key: draft.label_key.trim(),
  };
}

export function getDocumentCategoryValidationError(
  draft: DocumentCategoryDraft,
  messages: DocumentCategoryValidationMessages = {
    nameRequired: "Category name is required.",
    labelKeyRequired: "Label key is required.",
    labelKeyPattern: "Label key must use lowercase snake_case.",
  },
): string | null {
  if (!draft.name.trim()) {
    return messages.nameRequired;
  }

  if (!draft.label_key.trim()) {
    return messages.labelKeyRequired;
  }

  if (!documentCategoryLabelKeyRegex.test(draft.label_key.trim())) {
    return messages.labelKeyPattern;
  }

  return null;
}

export function slugifyDocumentCategoryLabelKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .replace(/_+/g, "_");
}

export function getDocumentCategoryDisplayName(
  category: Pick<DocumentCategory, "name" | "label_key">,
  messages: Messages,
): string {
  const translatedLabels = messages.documentCategoryLabels as Record<string, string>;
  return translatedLabels[category.label_key] ?? category.name;
}
