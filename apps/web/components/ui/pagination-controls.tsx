"use client";

import { Button } from "@/components/ui/button";
import { useLocale } from "@/providers/locale-provider";

export function PaginationControls({
  page,
  pageSize,
  totalItems,
  totalPages,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const { messages, formatText } = useLocale();

  if (!totalItems) {
    return null;
  }

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[color:var(--color-line)] px-4 py-4">
      <div className="text-sm text-[color:var(--color-muted)]">
        <div>
          {formatText(messages.common.pagination.resultsSummary, {
            start,
            end,
            total: totalItems,
          })}
        </div>
        <div>
          {formatText(messages.common.pagination.pageStatus, {
            page,
            total: Math.max(totalPages, 1),
          })}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          type="button"
          size="sm"
          variant="ghost"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          {messages.common.pagination.previous}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="secondary"
          disabled={totalPages === 0 || page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          {messages.common.pagination.next}
        </Button>
      </div>
    </div>
  );
}
