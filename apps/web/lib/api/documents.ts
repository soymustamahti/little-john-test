import { apiClient } from "@/lib/api/client";
import type {
  Document,
  DocumentUploadBatchResult,
  DocumentUploadFailureResult,
  DocumentUploadSuccessResult,
} from "@/types/documents";
import type { PaginatedResponse, PaginationParams } from "@/types/pagination";

export async function listDocuments(pagination: PaginationParams) {
  const response = await apiClient.get<PaginatedResponse<Document>>("/api/documents", {
    params: {
      page: pagination.page,
      page_size: pagination.pageSize,
    },
  });
  return response.data;
}

export async function getDocument(documentId: string) {
  const response = await apiClient.get<Document>(`/api/documents/${documentId}`);
  return response.data;
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<Document>("/api/documents", formData, {
    timeout: 120_000,
  });
  return response.data;
}

export async function getDocumentContent(documentId: string) {
  const response = await apiClient.get<ArrayBuffer>(
    `/api/documents/${documentId}/content`,
    {
      responseType: "arraybuffer",
    },
  );
  return response.data;
}

export function getDocumentContentUrl(documentId: string) {
  const baseUrl = apiClient.defaults.baseURL ?? "";
  return `${baseUrl}/api/documents/${documentId}/content`;
}

export async function uploadDocumentBatch(
  files: File[],
  getErrorMessage: (error: unknown, fallbackMessage: string) => string,
  fallbackMessage: string,
) {
  const results: DocumentUploadBatchResult[] = [];

  for (const file of files) {
    try {
      const document = await uploadDocument(file);
      const success: DocumentUploadSuccessResult = {
        fileName: file.name,
        status: "success",
        document,
      };
      results.push(success);
    } catch (error) {
      const failure: DocumentUploadFailureResult = {
        fileName: file.name,
        status: "error",
        errorMessage: getErrorMessage(error, fallbackMessage),
      };
      results.push(failure);
    }
  }

  return results;
}

export async function deleteDocument(documentId: string) {
  await apiClient.delete(`/api/documents/${documentId}`);
}
