import axios from "axios";

import { apiClient } from "@/lib/api/client";
import type {
  Document,
  DocumentExtractionCorrectionActivityPayload,
  DocumentExtractionCorrectionSession,
  DocumentClassificationSession,
  DocumentExtraction,
  DocumentExtractionReviewPayload,
  DocumentExtractionSession,
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

export async function classifyDocumentManually(
  documentId: string,
  categoryId: string,
) {
  const response = await apiClient.post<Document>(
    `/api/documents/${documentId}/classification/manual`,
    {
      category_id: categoryId,
    },
  );
  return response.data;
}

export async function createDocumentAiClassificationSession(documentId: string) {
  const response = await apiClient.post<DocumentClassificationSession>(
    `/api/documents/${documentId}/classification/ai-session`,
  );
  return response.data;
}

export async function createDocumentAiExtractionSession(
  documentId: string,
  templateId: string,
) {
  const response = await apiClient.post<DocumentExtractionSession>(
    `/api/documents/${documentId}/extraction/ai-session`,
    {
      template_id: templateId,
    },
  );
  return response.data;
}

export async function createDocumentExtractionCorrectionSession(documentId: string) {
  const response = await apiClient.post<DocumentExtractionCorrectionSession>(
    `/api/documents/${documentId}/extraction/correction-session`,
  );
  return response.data;
}

export async function saveDocumentExtractionCorrectionActivity(
  documentId: string,
  payload: DocumentExtractionCorrectionActivityPayload,
) {
  const response = await apiClient.put<DocumentExtraction>(
    `/api/documents/${documentId}/extraction/correction-activity`,
    payload,
  );
  return response.data;
}

export async function getDocumentExtraction(documentId: string) {
  try {
    const response = await apiClient.get<DocumentExtraction>(
      `/api/documents/${documentId}/extraction`,
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function confirmDocumentExtractionReview(
  documentId: string,
  payload: DocumentExtractionReviewPayload,
) {
  const response = await apiClient.put<DocumentExtraction>(
    `/api/documents/${documentId}/extraction/review`,
    payload,
  );
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
