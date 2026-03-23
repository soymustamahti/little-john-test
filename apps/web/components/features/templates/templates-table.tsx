import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { cn } from "@/lib/utils";
import { useLocale } from "@/providers/locale-provider";
import { getTemplateStats, type Template } from "@/types/templates";

export function TemplatesTable({
  templates,
  selectedTemplateId,
  isLoading,
  errorMessage,
  page,
  pageSize,
  totalItems,
  totalPages,
  onPageChange,
  onCreate,
  onSelect,
}: {
  templates: Template[];
  selectedTemplateId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onCreate: () => void;
  onSelect: (template: Template) => void;
}) {
  const { messages, formatDate, formatText } = useLocale();

  return (
    <Card className="overflow-hidden" data-tour="templates-table">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="accent">
                {messages.templatesTable.badges.layer}
              </Badge>
              <Badge>
                {formatText(messages.templatesTable.badges.schemas, {
                  count: totalItems,
                })}
              </Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">
              {messages.templatesTable.title}
            </CardTitle>
            <CardDescription>
              {messages.templatesTable.description}
            </CardDescription>
          </div>
          <Button data-tour="templates-create" onClick={onCreate}>
            {messages.templatesTable.createAction}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6 text-sm text-[color:var(--color-muted)]">
            {messages.templatesTable.loading}
          </div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-accent-warm)]">
            {errorMessage}
          </div>
        ) : null}

        {!isLoading && !errorMessage && !templates.length ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-muted)]">
            {messages.templatesTable.empty}
          </div>
        ) : null}

        {!isLoading && templates.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[color:var(--color-background)]/70 text-[color:var(--color-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">
                    {messages.templatesTable.headers.name}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.templatesTable.headers.locale}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.templatesTable.headers.modules}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.templatesTable.headers.fields}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.templatesTable.headers.updated}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.templatesTable.headers.open}
                  </th>
                </tr>
              </thead>
              <tbody>
                {templates.map((template) => {
                  const stats = getTemplateStats(template.modules);
                  const isSelected = selectedTemplateId === template.id;

                  return (
                    <tr
                      key={template.id}
                      className={cn(
                        "cursor-pointer border-t border-[color:var(--color-line)] transition hover:bg-[color:var(--color-background)]/70",
                        isSelected
                          ? "bg-[color:var(--color-accent-soft)]"
                          : "bg-white",
                      )}
                      onClick={() => onSelect(template)}
                    >
                      <td className="px-4 py-4 align-top">
                        <div className="space-y-1">
                          <div className="font-medium text-[color:var(--color-ink)]">
                            {template.name}
                          </div>
                          <div className="text-xs text-[color:var(--color-muted)]">
                            {template.description ??
                              messages.templatesTable.noDescription}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Badge
                          variant={template.locale === "fr" ? "warm" : "accent"}
                        >
                          {template.locale.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="px-4 py-4 align-top text-[color:var(--color-ink)]">
                        {stats.moduleCount}
                      </td>
                      <td className="px-4 py-4 align-top text-[color:var(--color-ink)]">
                        {stats.fieldCount}
                      </td>
                      <td className="px-4 py-4 align-top text-[color:var(--color-muted)]">
                        {formatDate(template.updated_at)}
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={(event) => {
                            event.stopPropagation();
                            onSelect(template);
                          }}
                        >
                          {messages.common.actions.view}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </CardContent>
      <PaginationControls
        page={page}
        pageSize={pageSize}
        totalItems={totalItems}
        totalPages={totalPages}
        onPageChange={onPageChange}
      />
    </Card>
  );
}
