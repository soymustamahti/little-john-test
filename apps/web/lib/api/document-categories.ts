import { apiClient } from "@/lib/api/client";
import type {
  DocumentCategory,
  DocumentCategoryPayload,
} from "@/types/document-categories";

export async function listDocumentCategories() {
  const response = await apiClient.get<DocumentCategory[]>(
    "/api/document-categories",
  );
  return response.data;
}

export async function getDocumentCategory(categoryId: string) {
  const response = await apiClient.get<DocumentCategory>(
    `/api/document-categories/${categoryId}`,
  );
  return response.data;
}

export async function createDocumentCategory(
  payload: DocumentCategoryPayload,
) {
  const response = await apiClient.post<DocumentCategory>(
    "/api/document-categories",
    payload,
  );
  return response.data;
}

export async function updateDocumentCategory(
  categoryId: string,
  payload: DocumentCategoryPayload,
) {
  const response = await apiClient.patch<DocumentCategory>(
    `/api/document-categories/${categoryId}`,
    payload,
  );
  return response.data;
}

export async function deleteDocumentCategory(categoryId: string) {
  await apiClient.delete(`/api/document-categories/${categoryId}`);
}
