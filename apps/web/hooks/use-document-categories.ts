"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createDocumentCategory,
  deleteDocumentCategory,
  getDocumentCategory,
  listDocumentCategories,
  updateDocumentCategory,
} from "@/lib/api/document-categories";
import type { PaginationParams } from "@/types/pagination";
import type { DocumentCategoryPayload } from "@/types/document-categories";

const DOCUMENT_CATEGORIES_QUERY_KEY = ["document-categories"];

export function useDocumentCategoriesQuery(pagination: PaginationParams) {
  return useQuery({
    queryKey: [
      ...DOCUMENT_CATEGORIES_QUERY_KEY,
      pagination.page,
      pagination.pageSize,
    ],
    queryFn: () => listDocumentCategories(pagination),
    placeholderData: (previousData) => previousData,
  });
}

export function useDocumentCategoryQuery(categoryId: string | undefined) {
  return useQuery({
    queryKey: [...DOCUMENT_CATEGORIES_QUERY_KEY, categoryId],
    queryFn: () => getDocumentCategory(categoryId as string),
    enabled: Boolean(categoryId),
  });
}

export function useCreateDocumentCategoryMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: DocumentCategoryPayload) =>
      createDocumentCategory(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: DOCUMENT_CATEGORIES_QUERY_KEY,
      });
    },
  });
}

export function useUpdateDocumentCategoryMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      categoryId,
      payload,
    }: {
      categoryId: string;
      payload: DocumentCategoryPayload;
    }) => updateDocumentCategory(categoryId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: DOCUMENT_CATEGORIES_QUERY_KEY,
      });
    },
  });
}

export function useDeleteDocumentCategoryMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (categoryId: string) => deleteDocumentCategory(categoryId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: DOCUMENT_CATEGORIES_QUERY_KEY,
      });
    },
  });
}
