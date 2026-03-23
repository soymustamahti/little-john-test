import { apiClient } from "@/lib/api/client";
import type { Template, TemplatePayload } from "@/types/templates";

export async function listTemplates() {
  const response = await apiClient.get<Template[]>("/api/templates");
  return response.data;
}

export async function createTemplate(payload: TemplatePayload) {
  const response = await apiClient.post<Template>("/api/templates", payload);
  return response.data;
}

export async function updateTemplate(templateId: string, payload: TemplatePayload) {
  const response = await apiClient.patch<Template>(`/api/templates/${templateId}`, payload);
  return response.data;
}

export async function deleteTemplate(templateId: string) {
  await apiClient.delete(`/api/templates/${templateId}`);
}
