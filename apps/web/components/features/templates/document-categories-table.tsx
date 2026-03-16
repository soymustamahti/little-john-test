import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { DocumentCategory } from "@/types/document-categories";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

export function DocumentCategoriesTable({
  categories,
  selectedCategoryId,
  isLoading,
  errorMessage,
  onCreate,
  onSelect,
}: {
  categories: DocumentCategory[];
  selectedCategoryId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  onCreate: () => void;
  onSelect: (category: DocumentCategory) => void;
}) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="warm">Classification layer</Badge>
              <Badge>{categories.length} categories</Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">Document categories</CardTitle>
            <CardDescription>
              Define the normalized document types your classifier can assign
              before routing and extraction.
            </CardDescription>
          </div>
          <Button variant="secondary" onClick={onCreate}>
            Create category
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6 text-sm text-[color:var(--color-muted)]">
            Loading categories...
          </div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-accent-warm)]">
            {errorMessage}
          </div>
        ) : null}

        {!isLoading && !errorMessage && !categories.length ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-muted)]">
            No categories yet. Add a few normalized document types so uploads can
            be classified before extraction.
          </div>
        ) : null}

        {!isLoading && categories.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[color:var(--color-background)]/70 text-[color:var(--color-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Updated</th>
                  <th className="px-4 py-3 font-medium">Open</th>
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => {
                  const isSelected = selectedCategoryId === category.id;

                  return (
                    <tr
                      key={category.id}
                      className={cn(
                        "cursor-pointer border-t border-[color:var(--color-line)] transition hover:bg-[color:var(--color-background)]/70",
                        isSelected ? "bg-[color:var(--color-warm-soft)]/65" : "bg-white",
                      )}
                      onClick={() => onSelect(category)}
                    >
                      <td className="px-4 py-4 align-top">
                        <div className="space-y-1">
                          <div className="font-medium text-[color:var(--color-ink)]">
                            {category.name}
                          </div>
                          <div className="text-xs text-[color:var(--color-muted)]">
                            Used as a normalized routing target.
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Badge variant="accent">Classifier output</Badge>
                      </td>
                      <td className="px-4 py-4 align-top text-[color:var(--color-muted)]">
                        {formatDate(category.updated_at)}
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={(event) => {
                            event.stopPropagation();
                            onSelect(category);
                          }}
                        >
                          View
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
    </Card>
  );
}
