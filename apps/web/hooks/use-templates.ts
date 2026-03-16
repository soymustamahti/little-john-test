"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createTemplate,
  deleteTemplate,
  listTemplates,
  updateTemplate,
} from "@/lib/api/templates";
import type { TemplatePayload } from "@/types/templates";

const TEMPLATES_QUERY_KEY = ["templates"];

export function useTemplatesQuery() {
  return useQuery({
    queryKey: TEMPLATES_QUERY_KEY,
    queryFn: listTemplates,
  });
}

export function useCreateTemplateMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TemplatePayload) => createTemplate(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: TEMPLATES_QUERY_KEY });
    },
  });
}

export function useUpdateTemplateMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      payload,
    }: {
      templateId: string;
      payload: TemplatePayload;
    }) => updateTemplate(templateId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: TEMPLATES_QUERY_KEY });
    },
  });
}

export function useDeleteTemplateMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => deleteTemplate(templateId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: TEMPLATES_QUERY_KEY });
    },
  });
}
