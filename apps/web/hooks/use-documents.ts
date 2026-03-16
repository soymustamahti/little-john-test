"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteDocument,
  getDocument,
  listDocuments,
  uploadDocumentBatch,
} from "@/lib/api/documents";
import { getApiErrorMessage } from "@/lib/api/errors";

const DOCUMENTS_QUERY_KEY = ["documents"];

export function useDocumentsQuery() {
  return useQuery({
    queryKey: DOCUMENTS_QUERY_KEY,
    queryFn: listDocuments,
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
