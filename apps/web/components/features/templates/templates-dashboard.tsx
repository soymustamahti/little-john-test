"use client";

import axios from "axios";
import { useRouter } from "next/navigation";

import { SetupStatsGrid } from "@/components/features/templates/setup-stats-grid";
import { TemplatesTable } from "@/components/features/templates/templates-table";
import { Badge } from "@/components/ui/badge";
import { useDocumentCategoriesQuery } from "@/hooks/use-document-categories";
import { useTemplatesQuery } from "@/hooks/use-templates";
import { useLocale } from "@/providers/locale-provider";
import { getTemplateStats } from "@/types/templates";

function getErrorMessage(error: unknown, fallbackMessage: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

export function TemplatesDashboard() {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const templatesQuery = useTemplatesQuery();
  const documentCategoriesQuery = useDocumentCategoriesQuery();

  const templates = templatesQuery.data ?? [];
  const documentCategories = documentCategoriesQuery.data ?? [];
  const totalModules = templates.reduce(
    (count, template) => count + getTemplateStats(template.modules).moduleCount,
    0,
  );
  const totalFields = templates.reduce(
    (count, template) => count + getTemplateStats(template.modules).fieldCount,
    0,
  );

  return (
    <div className="space-y-6 px-4 py-6 sm:px-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="accent">{messages.templatesDashboard.badges.layer}</Badge>
          <Badge>
            {formatText(messages.templatesDashboard.badges.activeTemplates, {
              count: templates.length,
            })}
          </Badge>
        </div>
        <div>
          <h2 className="text-3xl font-semibold text-[color:var(--color-ink)]">
            {messages.templatesDashboard.title}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            {messages.templatesDashboard.description}
          </p>
        </div>
      </div>

      <SetupStatsGrid
        extractionTemplateCount={templates.length}
        documentCategoryCount={documentCategories.length}
        totalModules={totalModules}
        totalFields={totalFields}
      />

      <TemplatesTable
        templates={templates}
        selectedTemplateId={null}
        isLoading={templatesQuery.isLoading}
        errorMessage={
          templatesQuery.error
            ? getErrorMessage(templatesQuery.error, messages.common.apiError)
            : null
        }
        onCreate={() => router.push("/extraction-templates/new")}
        onSelect={(template) => router.push(`/extraction-templates/${template.id}`)}
      />
    </div>
  );
}
