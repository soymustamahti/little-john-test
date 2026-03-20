"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  classifyDocumentManually,
  confirmDocumentExtractionReview,
  createDocumentAiExtractionSession,
  createDocumentAiClassificationSession,
  deleteDocument,
  getDocument,
  getDocumentExtraction,
  listDocuments,
  uploadDocumentBatch,
} from "@/lib/api/documents";
import { getApiErrorMessage } from "@/lib/api/errors";
import type { DocumentExtractionReviewPayload } from "@/types/documents";
import type { PaginationParams } from "@/types/pagination";

const DOCUMENTS_QUERY_KEY = ["documents"];

export function useDocumentsQuery(pagination: PaginationParams) {
  return useQuery({
    queryKey: [...DOCUMENTS_QUERY_KEY, pagination.page, pagination.pageSize],
    queryFn: () => listDocuments(pagination),
    placeholderData: (previousData) => previousData,
  });
}

export function useDocumentQuery(documentId: string | undefined) {
  return useQuery({
    queryKey: [...DOCUMENTS_QUERY_KEY, documentId],
    queryFn: () => getDocument(documentId as string),
    enabled: Boolean(documentId),
  });
}

export function useUploadDocumentsMutation(fallbackErrorMessage: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (files: File[]) =>
      uploadDocumentBatch(files, getApiErrorMessage, fallbackErrorMessage),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY });
    },
  });
}

export function useDeleteDocumentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => deleteDocument(documentId),
    onSuccess: async (_, documentId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY }),
        queryClient.removeQueries({ queryKey: [...DOCUMENTS_QUERY_KEY, documentId] }),
      ]);
    },
  });
}

export function useManualDocumentClassificationMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      documentId,
      categoryId,
    }: {
      documentId: string;
      categoryId: string;
    }) => classifyDocumentManually(documentId, categoryId),
    onSuccess: async (document) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY }),
        queryClient.setQueryData([...DOCUMENTS_QUERY_KEY, document.id], document),
      ]);
    },
  });
}

export function useCreateDocumentAiClassificationSessionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      createDocumentAiClassificationSession(documentId),
    onSuccess: async (_, documentId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY }),
        queryClient.invalidateQueries({
          queryKey: [...DOCUMENTS_QUERY_KEY, documentId],
        }),
      ]);
    },
  });
}

export function useDocumentExtractionQuery(
  documentId: string | undefined,
  enabled = true,
) {
  return useQuery({
    queryKey: [...DOCUMENTS_QUERY_KEY, documentId, "extraction"],
    queryFn: () => getDocumentExtraction(documentId as string),
    enabled: Boolean(documentId) && enabled,
  });
}

export function useCreateDocumentAiExtractionSessionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      documentId,
      templateId,
    }: {
      documentId: string;
      templateId: string;
    }) => createDocumentAiExtractionSession(documentId, templateId),
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({
        queryKey: [...DOCUMENTS_QUERY_KEY, variables.documentId, "extraction"],
      });
    },
  });
}

export function useConfirmDocumentExtractionReviewMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      documentId,
      payload,
    }: {
      documentId: string;
      payload: DocumentExtractionReviewPayload;
    }) => confirmDocumentExtractionReview(documentId, payload),
    onSuccess: async (extraction, variables) => {
      await Promise.all([
        queryClient.setQueryData(
          [...DOCUMENTS_QUERY_KEY, variables.documentId, "extraction"],
          extraction,
        ),
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY }),
      ]);
    },
  });
}
