"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createTemplate,
  deleteTemplate,
  getTemplate,
  listTemplates,
  updateTemplate,
} from "@/lib/api/templates";
import type { PaginationParams } from "@/types/pagination";
import type { TemplatePayload } from "@/types/templates";
import { getTemplateStats } from "@/types/templates";

const TEMPLATES_QUERY_KEY = ["templates"];

export function useTemplatesQuery(pagination: PaginationParams) {
  return useQuery({
    queryKey: [...TEMPLATES_QUERY_KEY, pagination.page, pagination.pageSize],
    queryFn: () => listTemplates(pagination),
    placeholderData: (previousData) => previousData,
  });
}

export function useTemplateQuery(templateId: string | undefined) {
  return useQuery({
    queryKey: [...TEMPLATES_QUERY_KEY, templateId],
    queryFn: () => getTemplate(templateId as string),
    enabled: Boolean(templateId),
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

export function useTemplateMetricsQuery(pageSize = 100) {
  return useQuery({
    queryKey: [...TEMPLATES_QUERY_KEY, "metrics", pageSize],
    queryFn: async () => {
      let page = 1;
      let totalPages = 1;
      let totalItems = 0;
      let totalModules = 0;
      let totalFields = 0;

      while (page <= totalPages) {
        const response = await listTemplates({ page, pageSize });
        totalItems = response.total_items;
        totalPages = response.total_pages || 0;

        for (const template of response.items) {
          const stats = getTemplateStats(template.modules);
          totalModules += stats.moduleCount;
          totalFields += stats.fieldCount;
        }

        if (totalPages === 0) {
          break;
        }

        page += 1;
      }

      return {
        totalItems,
        totalModules,
        totalFields,
      };
    },
  });
}
