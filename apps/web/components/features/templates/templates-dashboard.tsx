"use client";
import { useState } from "react";

import { useRouter } from "next/navigation";

import { SetupStatsGrid } from "@/components/features/templates/setup-stats-grid";
import { TemplatesTable } from "@/components/features/templates/templates-table";
import { Badge } from "@/components/ui/badge";
import { useDocumentCategoriesQuery } from "@/hooks/use-document-categories";
import { useDocumentsQuery } from "@/hooks/use-documents";
import { useTemplateMetricsQuery, useTemplatesQuery } from "@/hooks/use-templates";
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

const TEMPLATES_PAGE_SIZE = DEFAULT_PAGE_SIZE;

export function TemplatesDashboard() {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const [page, setPage] = useState(1);
  const templatesQuery = useTemplatesQuery({ page, pageSize: TEMPLATES_PAGE_SIZE });
  const templateMetricsQuery = useTemplateMetricsQuery();
  const documentCategoriesQuery = useDocumentCategoriesQuery({ page: 1, pageSize: 1 });
  const documentsQuery = useDocumentsQuery({ page: 1, pageSize: 1 });

  const templates = templatesQuery.data?.items ?? [];
  const templateCount = templatesQuery.data?.total_items ?? 0;
  const totalPages = templatesQuery.data?.total_pages ?? 0;
  const documentCategoryCount = documentCategoriesQuery.data?.total_items ?? 0;
  const documentCount = documentsQuery.data?.total_items ?? 0;
  const totalModules = templateMetricsQuery.data?.totalModules ?? 0;
  const totalFields = templateMetricsQuery.data?.totalFields ?? 0;

  return (
    <div className="space-y-6 px-4 py-6 sm:px-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="accent">{messages.templatesDashboard.badges.layer}</Badge>
          <Badge>
            {formatText(messages.templatesDashboard.badges.activeTemplates, {
              count: templateCount,
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
        extractionTemplateCount={templateMetricsQuery.data?.totalItems ?? 0}
        documentCategoryCount={documentCategoryCount}
        documentCount={documentCount}
        totalModules={totalModules}
        totalFields={totalFields}
      />

      <TemplatesTable
        templates={templates}
        selectedTemplateId={null}
        isLoading={templatesQuery.isLoading}
        errorMessage={
          templatesQuery.error
            ? getApiErrorMessage(templatesQuery.error, messages.common.apiError)
            : null
        }
        page={page}
        pageSize={TEMPLATES_PAGE_SIZE}
        totalItems={templateCount}
        totalPages={totalPages}
        onPageChange={setPage}
        onCreate={() => router.push("/extraction-templates/new")}
        onSelect={(template) => router.push(`/extraction-templates/${template.id}`)}
      />
    </div>
  );
}
