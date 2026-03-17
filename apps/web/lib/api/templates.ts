import { apiClient } from "@/lib/api/client";
import type { PaginatedResponse, PaginationParams } from "@/types/pagination";
import type { Template, TemplatePayload } from "@/types/templates";

export async function listTemplates(pagination: PaginationParams) {
  const response = await apiClient.get<PaginatedResponse<Template>>(
    "/api/extraction-templates",
    {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
      },
    },
  );
  return response.data;
}

export async function getTemplate(templateId: string) {
  const response = await apiClient.get<Template>(
    `/api/extraction-templates/${templateId}`,
  );
  return response.data;
}

export async function createTemplate(payload: TemplatePayload) {
  const response = await apiClient.post<Template>(
    "/api/extraction-templates",
    payload,
  );
  return response.data;
}

export async function updateTemplate(
  templateId: string,
  payload: TemplatePayload,
) {
  const response = await apiClient.patch<Template>(
    `/api/extraction-templates/${templateId}`,
    payload,
  );
  return response.data;
}

export async function deleteTemplate(templateId: string) {
  await apiClient.delete(`/api/extraction-templates/${templateId}`);
}
