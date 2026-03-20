"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Messages } from "@/lib/i18n";
import type {
  DocumentExtraction,
  DocumentExtractionResult,
  ScalarExtractionValue,
  TableExtractionCell,
} from "@/types/documents";

function toConfidencePercent(value: number) {
  return Math.round(value * 100);
}

function renderScalarValue(value: ScalarExtractionValue) {
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}

export function DocumentExtractionReview({
  extraction,
  messages,
  isSaving,
  onSave,
}: {
  extraction: DocumentExtraction;
  messages: Messages;
  isSaving: boolean;
  onSave: (draft: DocumentExtractionResult) => Promise<void>;
}) {
  const [draft, setDraft] = useState<DocumentExtractionResult | null>(
    extraction.result ? structuredClone(extraction.result) : null,
  );

  if (!draft) {
    return (
      <div className="rounded-2xl border border-[color:var(--color-line)] bg-white px-4 py-4 text-sm text-[color:var(--color-muted)]">
        {messages.documentProcessing.extraction.emptyState}
      </div>
    );
  }

  function updateScalarValue(
    moduleIndex: number,
    fieldIndex: number,
    nextValue: ScalarExtractionValue,
  ) {
    setDraft((current) => {
      if (!current) {
        return current;
      }
      const nextDraft = structuredClone(current);
      const field = nextDraft.modules[moduleIndex]?.fields[fieldIndex];
      if (!field || field.kind !== "scalar") {
        return current;
      }
      field.value = nextValue;
      return nextDraft;
    });
  }

  function updateTableCellValue(
    moduleIndex: number,
    fieldIndex: number,
    rowIndex: number,
    cellKey: string,
    nextValue: ScalarExtractionValue,
  ) {
    setDraft((current) => {
      if (!current) {
        return current;
      }
      const nextDraft = structuredClone(current);
      const field = nextDraft.modules[moduleIndex]?.fields[fieldIndex];
      if (!field || field.kind !== "table") {
        return current;
      }
      const row = field.rows[rowIndex];
      const cell = row?.cells.find((candidate) => candidate.key === cellKey);
      if (!cell) {
        return current;
      }
      cell.value = nextValue;
      return nextDraft;
    });
  }

  function renderCellValueInput(
    cell: TableExtractionCell,
    moduleIndex: number,
    fieldIndex: number,
    rowIndex: number,
  ) {
    if (cell.value_type === "boolean") {
      return (
        <select
          className="flex h-11 w-full rounded-2xl border border-[color:var(--color-line)] bg-white px-4 text-sm text-[color:var(--color-ink)] outline-none focus:border-[color:var(--color-accent)]"
          value={
            cell.value === null || cell.value === undefined
              ? ""
              : String(cell.value)
          }
          onChange={(event) => {
            const nextValue = event.target.value;
            updateTableCellValue(
              moduleIndex,
              fieldIndex,
              rowIndex,
              cell.key,
              nextValue === "" ? null : nextValue === "true",
            );
          }}
        >
          <option value="">{messages.documentProcessing.extraction.emptyValue}</option>
          <option value="true">{messages.documentProcessing.extraction.booleanTrue}</option>
          <option value="false">{messages.documentProcessing.extraction.booleanFalse}</option>
        </select>
      );
    }

    return (
      <Input
        type={cell.value_type === "number" ? "number" : "text"}
        step={cell.value_type === "number" ? "any" : undefined}
        value={renderScalarValue(cell.value)}
        onChange={(event) => {
          const nextValue = event.target.value;
          updateTableCellValue(
            moduleIndex,
            fieldIndex,
            rowIndex,
            cell.key,
            cell.value_type === "number"
              ? nextValue === ""
                ? null
                : Number(nextValue)
              : nextValue || null,
          );
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="accent">{extraction.template.name}</Badge>
        {extraction.overall_confidence !== null ? (
          <Badge>
            {messages.documentProcessing.extraction.overallConfidence.replace(
              "{value}",
              `${toConfidencePercent(extraction.overall_confidence)}%`,
            )}
          </Badge>
        ) : null}
        <Badge
          variant={extraction.status === "confirmed" ? "success" : "warm"}
        >
          {messages.documentProcessing.extraction.statuses[extraction.status]}
        </Badge>
      </div>

      {extraction.reasoning_summary ? (
        <div className="rounded-2xl border border-[color:var(--color-line)] bg-white px-4 py-3">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
            {messages.documentProcessing.extraction.reasoningTitle}
          </div>
          <div className="mt-2 text-sm text-[color:var(--color-ink)]">
            {extraction.reasoning_summary}
          </div>
        </div>
      ) : null}

      {draft.modules.map((moduleItem, moduleIndex) => (
        <div
          key={moduleItem.key}
          className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-white p-4"
        >
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
              {messages.documentProcessing.extraction.moduleLabel}
            </div>
            <div className="mt-1 text-lg font-semibold text-[color:var(--color-ink)]">
              {moduleItem.label}
            </div>
          </div>

          {moduleItem.fields.map((field, fieldIndex) => {
            if (field.kind === "scalar") {
              return (
                <div
                  key={field.key}
                  className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4"
                >
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_150px]">
                    <div className="space-y-2">
                      <Label htmlFor={`${field.key}-value`}>
                        {field.label}
                      </Label>
                      {field.value_type === "boolean" ? (
                        <select
                          id={`${field.key}-value`}
                          className="flex h-11 w-full rounded-2xl border border-[color:var(--color-line)] bg-white px-4 text-sm text-[color:var(--color-ink)] outline-none focus:border-[color:var(--color-accent)]"
                          value={
                            field.value === null || field.value === undefined
                              ? ""
                              : String(field.value)
                          }
                          onChange={(event) => {
                            const nextValue = event.target.value;
                            updateScalarValue(
                              moduleIndex,
                              fieldIndex,
                              nextValue === "" ? null : nextValue === "true",
                            );
                          }}
                        >
                          <option value="">
                            {messages.documentProcessing.extraction.emptyValue}
                          </option>
                          <option value="true">
                            {messages.documentProcessing.extraction.booleanTrue}
                          </option>
                          <option value="false">
                            {messages.documentProcessing.extraction.booleanFalse}
                          </option>
                        </select>
                      ) : (
                        <Input
                          id={`${field.key}-value`}
                          type={field.value_type === "number" ? "number" : "text"}
                          step={field.value_type === "number" ? "any" : undefined}
                          value={renderScalarValue(field.value)}
                          onChange={(event) => {
                            const nextValue = event.target.value;
                            updateScalarValue(
                              moduleIndex,
                              fieldIndex,
                              field.value_type === "number"
                                ? nextValue === ""
                                  ? null
                                  : Number(nextValue)
                                : nextValue || null,
                            );
                          }}
                        />
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label>{messages.documentProcessing.extraction.fieldConfidence}</Label>
                      <div className="flex h-11 items-center rounded-2xl border border-[color:var(--color-line)] bg-white px-4 text-sm text-[color:var(--color-ink)]">
                        {toConfidencePercent(field.confidence)}%
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge>{field.extraction_mode}</Badge>
                    {field.required ? (
                      <Badge variant="warm">
                        {messages.documentProcessing.extraction.requiredBadge}
                      </Badge>
                    ) : null}
                  </div>

                  <div className="mt-3 text-xs text-[color:var(--color-muted)]">
                    {field.evidence?.source_chunk_indices.length
                      ? messages.documentProcessing.extraction.sourceChunks.replace(
                          "{value}",
                          field.evidence.source_chunk_indices.join(", "),
                        )
                      : messages.documentProcessing.extraction.noSource}
                  </div>
                  {field.evidence?.source_excerpt ? (
                    <div className="mt-2 text-sm text-[color:var(--color-ink)]">
                      {field.evidence.source_excerpt}
                    </div>
                  ) : null}
                </div>
              );
            }

            return (
              <div
                key={field.key}
                className="space-y-4 rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/70 p-4"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <div className="text-lg font-semibold text-[color:var(--color-ink)]">
                    {field.label}
                  </div>
                  <Badge>{field.rows.length} rows</Badge>
                </div>

                {field.rows.length ? (
                  field.rows.map((row, rowIndex) => (
                    <div
                      key={`${field.key}-${row.row_index}`}
                      className="rounded-2xl border border-[color:var(--color-line)] bg-white p-4"
                    >
                      <div className="mb-3 flex flex-wrap items-center gap-2">
                        <Badge variant="accent">
                          {messages.documentProcessing.extraction.rowLabel.replace(
                            "{value}",
                            String(row.row_index + 1),
                          )}
                        </Badge>
                        <Badge>
                          {messages.documentProcessing.extraction.rowConfidence.replace(
                            "{value}",
                            `${toConfidencePercent(row.confidence)}%`,
                          )}
                        </Badge>
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        {row.cells.map((cell) => (
                          <div key={`${row.row_index}-${cell.key}`} className="space-y-2">
                            <Label>{cell.label}</Label>
                            {renderCellValueInput(
                              cell,
                              moduleIndex,
                              fieldIndex,
                              rowIndex,
                            )}
                            <div className="flex h-11 items-center rounded-2xl border border-[color:var(--color-line)] bg-white px-4 text-sm text-[color:var(--color-ink)]">
                              {toConfidencePercent(cell.confidence)}%
                            </div>
                            <div className="text-xs text-[color:var(--color-muted)]">
                              {cell.evidence?.source_chunk_indices.length
                                ? messages.documentProcessing.extraction.sourceChunks.replace(
                                    "{value}",
                                    cell.evidence.source_chunk_indices.join(", "),
                                  )
                                : messages.documentProcessing.extraction.noSource}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-[color:var(--color-muted)]">
                    {messages.documentProcessing.extraction.tableEmpty}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={() => onSave(draft)}
          disabled={isSaving}
        >
          {isSaving
            ? messages.documentProcessing.extraction.savingAction
            : messages.documentProcessing.extraction.saveAction}
        </Button>
        <div className="self-center text-xs text-[color:var(--color-muted)]">
          {messages.documentProcessing.extraction.reviewHint}
        </div>
      </div>
    </div>
  );
}
