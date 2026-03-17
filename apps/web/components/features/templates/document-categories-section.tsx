"use client";
import { useState } from "react";

import { useRouter } from "next/navigation";

import { DocumentCategoriesTable } from "@/components/features/templates/document-categories-table";
import { SetupStatsGrid } from "@/components/features/templates/setup-stats-grid";
import { Badge } from "@/components/ui/badge";
import { useDocumentCategoriesQuery } from "@/hooks/use-document-categories";
import { useDocumentsQuery } from "@/hooks/use-documents";
import { useTemplateMetricsQuery } from "@/hooks/use-templates";
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

const DOCUMENT_CATEGORIES_PAGE_SIZE = DEFAULT_PAGE_SIZE;

export function DocumentCategoriesSection() {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const [page, setPage] = useState(1);
  const categoriesQuery = useDocumentCategoriesQuery({
    page,
    pageSize: DOCUMENT_CATEGORIES_PAGE_SIZE,
  });
  const templateMetricsQuery = useTemplateMetricsQuery();
  const documentsQuery = useDocumentsQuery({ page: 1, pageSize: 1 });

  const categories = categoriesQuery.data?.items ?? [];
  const categoryCount = categoriesQuery.data?.total_items ?? 0;
  const totalPages = categoriesQuery.data?.total_pages ?? 0;
  const documentCount = documentsQuery.data?.total_items ?? 0;
  const totalModules = templateMetricsQuery.data?.totalModules ?? 0;
  const totalFields = templateMetricsQuery.data?.totalFields ?? 0;

  return (
    <div className="space-y-6 px-4 py-6 sm:px-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="warm">{messages.documentCategoriesSection.badges.layer}</Badge>
          <Badge>
            {formatText(messages.documentCategoriesSection.badges.routingTargets, {
              count: categoryCount,
            })}
          </Badge>
        </div>
        <div>
          <h2 className="text-3xl font-semibold text-[color:var(--color-ink)]">
            {messages.documentCategoriesSection.title}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            {messages.documentCategoriesSection.description}
          </p>
        </div>
      </div>

      <SetupStatsGrid
        extractionTemplateCount={templateMetricsQuery.data?.totalItems ?? 0}
        documentCategoryCount={categoryCount}
        documentCount={documentCount}
        totalModules={totalModules}
        totalFields={totalFields}
      />

      <DocumentCategoriesTable
        categories={categories}
        selectedCategoryId={null}
        isLoading={categoriesQuery.isLoading}
        errorMessage={
          categoriesQuery.error
            ? getApiErrorMessage(categoriesQuery.error, messages.common.apiError)
            : null
        }
        page={page}
        pageSize={DOCUMENT_CATEGORIES_PAGE_SIZE}
        totalItems={categoryCount}
        totalPages={totalPages}
        onPageChange={setPage}
        onCreate={() => router.push("/document-categories/new")}
        onSelect={(category) => router.push(`/document-categories/${category.id}`)}
      />
    </div>
  );
}
