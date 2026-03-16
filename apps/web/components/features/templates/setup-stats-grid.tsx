import { FileStack, ListChecks, Shapes, Tag } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { useLocale } from "@/providers/locale-provider";

export function SetupStatsGrid({
  extractionTemplateCount,
  documentCategoryCount,
  totalModules,
  totalFields,
}: {
  extractionTemplateCount: number;
  documentCategoryCount: number;
  totalModules: number;
  totalFields: number;
}) {
  const { messages } = useLocale();

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
            <Shapes className="h-4 w-4" />
            {messages.stats.extractionTemplates}
          </div>
          <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
            {extractionTemplateCount}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
            <Tag className="h-4 w-4" />
            {messages.stats.documentCategories}
          </div>
          <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
            {documentCategoryCount}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
            <ListChecks className="h-4 w-4" />
            {messages.stats.modules}
          </div>
          <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
            {totalModules}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
            <FileStack className="h-4 w-4" />
            {messages.stats.fields}
          </div>
          <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
            {totalFields}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
