"use client";

import { Badge } from "@/components/ui/badge";
import type { Messages } from "@/lib/i18n";
import type {
  DocumentExtraction,
  ScalarExtractionValue,
  TableExtractionRow,
} from "@/types/documents";
import { getDocumentExtractionStatusLabel } from "@/types/documents";

function toConfidencePercent(value: number) {
  return Math.round(value * 100);
}

function renderScalarValue(value: ScalarExtractionValue) {
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return String(value);
}

function renderRowPreview(row: TableExtractionRow) {
  return row.cells
    .slice(0, 3)
    .map((cell) => `${cell.label}: ${renderScalarValue(cell.value)}`)
    .join(" • ");
}

export function DocumentExtractionOverview({
  extraction,
  messages,
}: {
  extraction: DocumentExtraction;
  messages: Messages;
}) {
  if (!extraction.result) {
    return (
      <div className="rounded-2xl border border-[color:var(--color-line)] bg-white px-4 py-4 text-sm text-[color:var(--color-muted)]">
        {messages.documentProcessing.extraction.emptyState}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="accent">{extraction.template.name}</Badge>
        <Badge variant={extraction.status === "confirmed" ? "success" : "warm"}>
          {getDocumentExtractionStatusLabel(extraction.status, messages)}
        </Badge>
        {extraction.overall_confidence !== null ? (
          <Badge>
            {messages.documentProcessing.extraction.overallConfidence.replace(
              "{value}",
              `${toConfidencePercent(extraction.overall_confidence)}%`,
            )}
          </Badge>
        ) : null}
      </div>

      {extraction.reasoning_summary ? (
        <div className="rounded-2xl border border-[color:var(--color-line)] bg-white px-4 py-3">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
            {messages.documentProcessing.extraction.reasoningTitle}
          </div>
          <div className="mt-2 text-sm leading-6 text-[color:var(--color-ink)]">
            {extraction.reasoning_summary}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        {extraction.result.modules.map((moduleItem) => (
          <section
            key={moduleItem.key}
            className="space-y-4 rounded-[24px] border border-[color:var(--color-line)] bg-white p-4"
          >
            <div className="space-y-1">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                {messages.documentProcessing.extraction.moduleLabel}
              </div>
              <div className="text-lg font-semibold text-[color:var(--color-ink)]">
                {moduleItem.label}
              </div>
            </div>

            <div className="space-y-3">
              {moduleItem.fields.map((field) =>
                field.kind === "scalar" ? (
                  <div
                    key={field.key}
                    className="rounded-[20px] border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                          {field.label}
                        </div>
                        <div className="mt-2 text-sm font-medium text-[color:var(--color-ink)]">
                          {renderScalarValue(field.value)}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge>{field.extraction_mode}</Badge>
                        <Badge>{toConfidencePercent(field.confidence)}%</Badge>
                      </div>
                    </div>
                    {field.evidence?.source_excerpt ? (
                      <div className="mt-3 text-xs leading-5 text-[color:var(--color-muted)]">
                        {field.evidence.source_excerpt}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div
                    key={field.key}
                    className="rounded-[20px] border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                          {field.label}
                        </div>
                        <div className="mt-2 text-sm font-medium text-[color:var(--color-ink)]">
                          {messages.documentDetailScreen.tableRowsLabel.replace(
                            "{count}",
                            String(field.rows.length),
                          )}
                        </div>
                      </div>
                      <Badge>{field.rows.length}</Badge>
                    </div>

                    {field.rows.length ? (
                      <div className="mt-3 space-y-2">
                        {field.rows.slice(0, 3).map((row) => (
                          <div
                            key={`${field.key}-${row.row_index}`}
                            className="rounded-2xl border border-[color:var(--color-line)] bg-white px-3 py-2 text-xs leading-5 text-[color:var(--color-muted)]"
                          >
                            {renderRowPreview(row)}
                          </div>
                        ))}
                        {field.rows.length > 3 ? (
                          <div className="text-xs text-[color:var(--color-muted)]">
                            {messages.documentDetailScreen.moreRowsLabel.replace(
                              "{count}",
                              String(field.rows.length - 3),
                            )}
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <div className="mt-3 text-xs text-[color:var(--color-muted)]">
                        {messages.documentProcessing.extraction.tableEmpty}
                      </div>
                    )}
                  </div>
                ),
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
