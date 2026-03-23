import { apiClient } from "@/lib/api/client";
import type {
  DocumentCategory,
  DocumentCategoryPayload,
} from "@/types/document-categories";
import type { PaginatedResponse, PaginationParams } from "@/types/pagination";

export async function listDocumentCategories(pagination: PaginationParams) {
  const response = await apiClient.get<PaginatedResponse<DocumentCategory>>(
    "/api/document-categories",
    {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
      },
    },
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
