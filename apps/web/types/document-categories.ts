export interface DocumentCategory {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentCategoryDraft {
  name: string;
}

export interface DocumentCategoryPayload {
  name: string;
}

export function createEmptyDocumentCategoryDraft(): DocumentCategoryDraft {
  return {
    name: "",
  };
}

export function documentCategoryToDraft(
  category: DocumentCategory,
): DocumentCategoryDraft {
  return {
    name: category.name,
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
  };
}

export function getDocumentCategoryValidationError(
  draft: DocumentCategoryDraft,
  nameRequiredMessage = "Category name is required.",
): string | null {
  if (!draft.name.trim()) {
    return nameRequiredMessage;
  }

  return null;
}
