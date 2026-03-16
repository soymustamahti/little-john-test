import {
  Columns3,
  FilePlus2,
  FolderPlus,
  Grip,
  Plus,
  RefreshCcw,
  Rows3,
  Save,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type {
  ScalarValueType,
  TableColumnDefinition,
  TemplateDraft,
  TemplateField,
  TemplateLocale,
  TemplateModule,
} from "@/types/templates";

function SelectField({
  value,
  onChange,
  options,
}: {
  value: string | number;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
}) {
  return (
    <select
      value={String(value)}
      onChange={(event) => onChange(event.target.value)}
      className="flex h-10 w-full rounded-xl border border-[color:var(--color-line)] bg-white px-3 text-sm text-[color:var(--color-ink)] outline-none focus:border-[color:var(--color-accent)]"
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function CheckboxField({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-[color:var(--color-ink)]">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 rounded border-[color:var(--color-line-strong)] accent-[color:var(--color-accent)]"
      />
      {label}
    </label>
  );
}

function ColumnEditor({
  column,
  onChange,
  onRemove,
}: {
  column: TableColumnDefinition;
  onChange: (nextColumn: TableColumnDefinition) => void;
  onRemove: () => void;
}) {
  return (
    <div className="rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/60 p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Columns3 className="h-4 w-4 text-[color:var(--color-muted)]" />
          <span className="text-sm font-medium text-[color:var(--color-ink)]">Column</span>
        </div>
        <Button type="button" size="sm" variant="ghost" onClick={onRemove}>
          Remove
        </Button>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Key</Label>
          <Input
            value={column.key}
            onChange={(event) => onChange({ ...column, key: event.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Label</Label>
          <Input
            value={column.label}
            onChange={(event) => onChange({ ...column, label: event.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Type</Label>
          <SelectField
            value={column.value_type}
            onChange={(value) =>
              onChange({ ...column, value_type: value as ScalarValueType })
            }
            options={[
              { label: "String", value: "string" },
              { label: "Number", value: "number" },
              { label: "Date", value: "date" },
              { label: "Boolean", value: "boolean" },
            ]}
          />
        </div>
        <div className="space-y-2">
          <Label>Description</Label>
          <Input
            value={column.description ?? ""}
            onChange={(event) => onChange({ ...column, description: event.target.value })}
          />
        </div>
      </div>
      <div className="mt-3">
        <CheckboxField
          checked={column.required}
          label="Required column"
          onChange={(checked) => onChange({ ...column, required: checked })}
        />
      </div>
    </div>
  );
}

function FieldEditor({
  field,
  onChange,
  onRemove,
  onAddColumn,
  onChangeColumn,
  onRemoveColumn,
}: {
  field: TemplateField;
  onChange: (nextField: TemplateField) => void;
  onRemove: () => void;
  onAddColumn: () => void;
  onChangeColumn: (columnIndex: number, nextColumn: TableColumnDefinition) => void;
  onRemoveColumn: (columnIndex: number) => void;
}) {
  return (
    <div className="rounded-2xl border border-[color:var(--color-line)] bg-white p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Grip className="h-4 w-4 text-[color:var(--color-muted)]" />
          <span className="text-sm font-medium text-[color:var(--color-ink)]">
            {field.kind === "table" ? "Table field" : "Scalar field"}
          </span>
        </div>
        <Button type="button" size="sm" variant="ghost" onClick={onRemove}>
          Remove field
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Key</Label>
          <Input
            value={field.key}
            onChange={(event) => onChange({ ...field, key: event.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Label</Label>
          <Input
            value={field.label}
            onChange={(event) => onChange({ ...field, label: event.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Kind</Label>
          <SelectField
            value={field.kind}
            onChange={(value) => {
              if (value === field.kind) {
                return;
              }

              if (value === "table") {
                onChange({
                  kind: "table",
                  key: field.key,
                  label: field.label,
                  required: field.required,
                  description: field.description,
                  min_rows: 0,
                  columns: [
                    {
                      key: "column_1",
                      label: "Column 1",
                      value_type: "string",
                      required: false,
                      description: "",
                    },
                  ],
                });
                return;
              }

              onChange({
                kind: "scalar",
                key: field.key,
                label: field.label,
                required: field.required,
                description: field.description,
                value_type: "string",
              });
            }}
            options={[
              { label: "Scalar", value: "scalar" },
              { label: "Table", value: "table" },
            ]}
          />
        </div>

        {field.kind === "table" ? (
          <div className="space-y-2">
            <Label>Minimum rows</Label>
            <Input
              type="number"
              min={0}
              value={field.min_rows}
              onChange={(event) =>
                onChange({
                  ...field,
                  min_rows: Number(event.target.value) || 0,
                })
              }
            />
          </div>
        ) : (
          <div className="space-y-2">
            <Label>Value type</Label>
            <SelectField
              value={field.value_type}
              onChange={(value) =>
                onChange({
                  ...field,
                  value_type: value as ScalarValueType,
                })
              }
              options={[
                { label: "String", value: "string" },
                { label: "Number", value: "number" },
                { label: "Date", value: "date" },
                { label: "Boolean", value: "boolean" },
              ]}
            />
          </div>
        )}
      </div>

      <div className="mt-3 grid gap-3">
        <div className="space-y-2">
          <Label>Description</Label>
          <Textarea
            className="min-h-20"
            value={field.description ?? ""}
            onChange={(event) => onChange({ ...field, description: event.target.value })}
          />
        </div>
        <CheckboxField
          checked={field.required}
          label="Required field"
          onChange={(checked) => onChange({ ...field, required: checked })}
        />
      </div>

      {field.kind === "table" ? (
        <div className="mt-5 space-y-3 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/45 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Rows3 className="h-4 w-4 text-[color:var(--color-muted)]" />
              <span className="text-sm font-medium text-[color:var(--color-ink)]">Columns</span>
            </div>
            <Button type="button" size="sm" variant="secondary" onClick={onAddColumn}>
              <Plus className="h-4 w-4" />
              Add column
            </Button>
          </div>

          {!field.columns.length ? (
            <div className="text-sm text-[color:var(--color-muted)]">
              Add at least one column for this table field.
            </div>
          ) : null}

          {field.columns.map((column, columnIndex) => (
            <ColumnEditor
              key={`${column.key}-${columnIndex}`}
              column={column}
              onChange={(nextColumn) => onChangeColumn(columnIndex, nextColumn)}
              onRemove={() => onRemoveColumn(columnIndex)}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ModuleEditor({
  moduleItem,
  onChange,
  onRemove,
  onAddScalarField,
  onAddTableField,
  onChangeField,
  onRemoveField,
  onAddColumn,
  onChangeColumn,
  onRemoveColumn,
}: {
  moduleItem: TemplateModule;
  onChange: (nextModule: TemplateModule) => void;
  onRemove: () => void;
  onAddScalarField: () => void;
  onAddTableField: () => void;
  onChangeField: (fieldIndex: number, nextField: TemplateField) => void;
  onRemoveField: (fieldIndex: number) => void;
  onAddColumn: (fieldIndex: number) => void;
  onChangeColumn: (
    fieldIndex: number,
    columnIndex: number,
    nextColumn: TableColumnDefinition,
  ) => void;
  onRemoveColumn: (fieldIndex: number, columnIndex: number) => void;
}) {
  return (
    <div className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/40 p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
            <Rows3 className="h-4 w-4" />
            Module
          </div>
          <Badge>{moduleItem.fields.length} fields</Badge>
        </div>
        <Button type="button" size="sm" variant="ghost" onClick={onRemove}>
          Remove module
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Module key</Label>
          <Input
            value={moduleItem.key}
            onChange={(event) => onChange({ ...moduleItem, key: event.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Module label</Label>
          <Input
            value={moduleItem.label}
            onChange={(event) => onChange({ ...moduleItem, label: event.target.value })}
          />
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h4 className="text-sm font-medium text-[color:var(--color-ink)]">Fields</h4>
          <div className="flex flex-wrap gap-2">
            <Button type="button" size="sm" variant="secondary" onClick={onAddScalarField}>
              <FilePlus2 className="h-4 w-4" />
              Add scalar
            </Button>
            <Button type="button" size="sm" variant="secondary" onClick={onAddTableField}>
              <Rows3 className="h-4 w-4" />
              Add table
            </Button>
          </div>
        </div>

        {!moduleItem.fields.length ? (
          <div className="rounded-xl border border-dashed border-[color:var(--color-line)] bg-white p-4 text-sm text-[color:var(--color-muted)]">
            No fields in this module yet.
          </div>
        ) : null}

        {moduleItem.fields.map((field, fieldIndex) => (
          <FieldEditor
            key={`${field.key}-${fieldIndex}`}
            field={field}
            onChange={(nextField) => onChangeField(fieldIndex, nextField)}
            onRemove={() => onRemoveField(fieldIndex)}
            onAddColumn={() => onAddColumn(fieldIndex)}
            onChangeColumn={(columnIndex, nextColumn) =>
              onChangeColumn(fieldIndex, columnIndex, nextColumn)
            }
            onRemoveColumn={(columnIndex) => onRemoveColumn(fieldIndex, columnIndex)}
          />
        ))}
      </div>
    </div>
  );
}

export function TemplateDetailPanel({
  draft,
  mode,
  validationError,
  statusMessage,
  statusTone,
  isSaving,
  isDeleting,
  onNameChange,
  onDescriptionChange,
  onLocaleChange,
  onAddModule,
  onChangeModule,
  onRemoveModule,
  onAddScalarField,
  onAddTableField,
  onChangeField,
  onRemoveField,
  onAddColumn,
  onChangeColumn,
  onRemoveColumn,
  onReset,
  onSave,
  onDelete,
}: {
  draft: TemplateDraft;
  mode: "create" | "edit";
  validationError: string | null;
  statusMessage: string | null;
  statusTone: "neutral" | "success" | "danger";
  isSaving: boolean;
  isDeleting: boolean;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onLocaleChange: (value: TemplateLocale) => void;
  onAddModule: () => void;
  onChangeModule: (moduleIndex: number, nextModule: TemplateModule) => void;
  onRemoveModule: (moduleIndex: number) => void;
  onAddScalarField: (moduleIndex: number) => void;
  onAddTableField: (moduleIndex: number) => void;
  onChangeField: (moduleIndex: number, fieldIndex: number, nextField: TemplateField) => void;
  onRemoveField: (moduleIndex: number, fieldIndex: number) => void;
  onAddColumn: (moduleIndex: number, fieldIndex: number) => void;
  onChangeColumn: (
    moduleIndex: number,
    fieldIndex: number,
    columnIndex: number,
    nextColumn: TableColumnDefinition,
  ) => void;
  onRemoveColumn: (moduleIndex: number, fieldIndex: number, columnIndex: number) => void;
  onReset: () => void;
  onSave: () => void;
  onDelete: () => void;
}) {
  return (
    <Card>
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="accent">
                {mode === "create" ? "New extraction template" : "Extraction details"}
              </Badge>
              <Badge>{draft.locale.toUpperCase()}</Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">
              {mode === "create"
                ? "Create extraction template"
                : draft.name || "Edit extraction template"}
            </CardTitle>
            <CardDescription>
              Define the structured fields that should be extracted after a
              document has been classified into the right category.
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={onReset}>
              <RefreshCcw className="h-4 w-4" />
              Reset
            </Button>
            {mode === "edit" ? (
              <Button type="button" variant="danger" onClick={onDelete} disabled={isDeleting}>
                <Trash2 className="h-4 w-4" />
                {isDeleting ? "Deleting..." : "Delete"}
              </Button>
            ) : null}
            <Button type="button" onClick={onSave} disabled={Boolean(validationError) || isSaving}>
              <Save className="h-4 w-4" />
              {isSaving ? "Saving..." : mode === "create" ? "Create" : "Save"}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Extraction template name</Label>
            <Input value={draft.name} onChange={(event) => onNameChange(event.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Locale</Label>
            <SelectField
              value={draft.locale}
              onChange={(value) => onLocaleChange(value as TemplateLocale)}
              options={[
                { label: "English", value: "en" },
                { label: "French", value: "fr" },
              ]}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Description</Label>
          <Textarea
            className="min-h-24"
            value={draft.description}
            onChange={(event) => onDescriptionChange(event.target.value)}
          />
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-medium text-[color:var(--color-ink)]">Modules</h3>
              <p className="text-sm text-[color:var(--color-muted)]">
                Group fields by business area like vendor info, payment details, or line items.
              </p>
            </div>
            <Button type="button" variant="secondary" onClick={onAddModule}>
              <FolderPlus className="h-4 w-4" />
              Add module
            </Button>
          </div>

          {!draft.modules.length ? (
            <div className="rounded-2xl border border-dashed border-[color:var(--color-line)] bg-[color:var(--color-background)]/40 p-6 text-sm text-[color:var(--color-muted)]">
              No modules yet. Add one to start defining fields.
            </div>
          ) : null}

          {draft.modules.map((moduleItem, moduleIndex) => (
            <ModuleEditor
              key={`${moduleItem.key}-${moduleIndex}`}
              moduleItem={moduleItem}
              onChange={(nextModule) => onChangeModule(moduleIndex, nextModule)}
              onRemove={() => onRemoveModule(moduleIndex)}
              onAddScalarField={() => onAddScalarField(moduleIndex)}
              onAddTableField={() => onAddTableField(moduleIndex)}
              onChangeField={(fieldIndex, nextField) =>
                onChangeField(moduleIndex, fieldIndex, nextField)
              }
              onRemoveField={(fieldIndex) => onRemoveField(moduleIndex, fieldIndex)}
              onAddColumn={(fieldIndex) => onAddColumn(moduleIndex, fieldIndex)}
              onChangeColumn={(fieldIndex, columnIndex, nextColumn) =>
                onChangeColumn(moduleIndex, fieldIndex, columnIndex, nextColumn)
              }
              onRemoveColumn={(fieldIndex, columnIndex) =>
                onRemoveColumn(moduleIndex, fieldIndex, columnIndex)
              }
            />
          ))}
        </div>

        {validationError ? (
          <div className="rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]">
            {validationError}
          </div>
        ) : null}

        {statusMessage ? (
          <div
            className={
              statusTone === "danger"
                ? "rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]"
                : statusTone === "success"
                  ? "rounded-xl border border-[color:var(--color-success-soft)] bg-white px-4 py-3 text-sm text-[color:var(--color-success)]"
                  : "rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3 text-sm text-[color:var(--color-muted)]"
            }
          >
            {statusMessage}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
