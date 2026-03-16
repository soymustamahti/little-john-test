import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getTemplateStats, type Template } from "@/types/templates";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function TemplatesTable({
  templates,
  selectedTemplateId,
  isLoading,
  errorMessage,
  onCreate,
  onSelect,
}: {
  templates: Template[];
  selectedTemplateId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  onCreate: () => void;
  onSelect: (template: Template) => void;
}) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <CardTitle className="text-2xl">Templates</CardTitle>
            <CardDescription>
              Browse every template, then open one row to edit its structure.
            </CardDescription>
          </div>
          <Button onClick={onCreate}>Create template</Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6 text-sm text-[color:var(--color-muted)]">Loading templates...</div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-accent-warm)]">
            {errorMessage}
          </div>
        ) : null}

        {!isLoading && !errorMessage && !templates.length ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-muted)]">
            No templates yet. Seed them from the API package or create one here.
          </div>
        ) : null}

        {!isLoading && templates.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[color:var(--color-background)]/70 text-[color:var(--color-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Locale</th>
                  <th className="px-4 py-3 font-medium">Modules</th>
                  <th className="px-4 py-3 font-medium">Fields</th>
                  <th className="px-4 py-3 font-medium">Updated</th>
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
                        isSelected ? "bg-[color:var(--color-accent-soft)]" : "bg-white",
                      )}
                      onClick={() => onSelect(template)}
                    >
                      <td className="px-4 py-4 align-top">
                        <div className="space-y-1">
                          <div className="font-medium text-[color:var(--color-ink)]">
                            {template.name}
                          </div>
                          <div className="text-xs text-[color:var(--color-muted)]">
                            {template.description ?? "No description"}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Badge variant={template.locale === "fr" ? "warm" : "accent"}>
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
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
