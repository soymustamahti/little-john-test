"use client";

import axios from "axios";
import { useRouter } from "next/navigation";

import { DocumentCategoriesTable } from "@/components/features/templates/document-categories-table";
import { SetupStatsGrid } from "@/components/features/templates/setup-stats-grid";
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

export function DocumentCategoriesSection() {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const categoriesQuery = useDocumentCategoriesQuery();
  const templatesQuery = useTemplatesQuery();

  const categories = categoriesQuery.data ?? [];
  const templates = templatesQuery.data ?? [];
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
          <Badge variant="warm">{messages.documentCategoriesSection.badges.layer}</Badge>
          <Badge>
            {formatText(messages.documentCategoriesSection.badges.routingTargets, {
              count: categories.length,
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
        extractionTemplateCount={templates.length}
        documentCategoryCount={categories.length}
        totalModules={totalModules}
        totalFields={totalFields}
      />

      <DocumentCategoriesTable
        categories={categories}
        selectedCategoryId={null}
        isLoading={categoriesQuery.isLoading}
        errorMessage={
          categoriesQuery.error
            ? getErrorMessage(categoriesQuery.error, messages.common.apiError)
            : null
        }
        onCreate={() => router.push("/document-categories/new")}
        onSelect={(category) => router.push(`/document-categories/${category.id}`)}
      />
    </div>
  );
}
