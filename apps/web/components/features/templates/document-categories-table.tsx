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
import {
  getDocumentCategoryDisplayName,
  type DocumentCategory,
} from "@/types/document-categories";

export function DocumentCategoriesTable({
  categories,
  selectedCategoryId,
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
  categories: DocumentCategory[];
  selectedCategoryId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onCreate: () => void;
  onSelect: (category: DocumentCategory) => void;
}) {
  const { messages, formatDate, formatText } = useLocale();

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="warm">{messages.documentCategoriesTable.badges.layer}</Badge>
              <Badge>
                {formatText(messages.documentCategoriesTable.badges.categories, {
                  count: totalItems,
                })}
              </Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">
              {messages.documentCategoriesTable.title}
            </CardTitle>
            <CardDescription>
              {messages.documentCategoriesTable.description}
            </CardDescription>
          </div>
          <Button variant="secondary" onClick={onCreate}>
            {messages.documentCategoriesTable.createAction}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6 text-sm text-[color:var(--color-muted)]">
            {messages.documentCategoriesTable.loading}
          </div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-accent-warm)]">
            {errorMessage}
          </div>
        ) : null}

        {!isLoading && !errorMessage && !categories.length ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-muted)]">
            {messages.documentCategoriesTable.empty}
          </div>
        ) : null}

        {!isLoading && categories.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[color:var(--color-background)]/70 text-[color:var(--color-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentCategoriesTable.headers.category}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentCategoriesTable.headers.role}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentCategoriesTable.headers.updated}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentCategoriesTable.headers.open}
                  </th>
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => {
                  const isSelected = selectedCategoryId === category.id;
                  const displayName = getDocumentCategoryDisplayName(category, messages);

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
                            {displayName}
                          </div>
                          <div className="text-xs text-[color:var(--color-muted)]">
                            {formatText(messages.documentCategoriesTable.classifierName, {
                              name: category.name,
                            })}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Badge variant="accent">
                          {messages.documentCategoriesTable.badges.classifierOutput}
                        </Badge>
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
