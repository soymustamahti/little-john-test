export type TemplateLocale = "en" | "fr";
export type ScalarValueType = "string" | "number" | "date" | "boolean";
export type TemplateFieldKind = "scalar" | "table";

export interface ScalarTemplateField {
  kind: "scalar";
  key: string;
  label: string;
  required: boolean;
  description: string | null;
  value_type: ScalarValueType;
}

export interface TableColumnDefinition {
  key: string;
  label: string;
  value_type: ScalarValueType;
  required: boolean;
  description: string | null;
}

export interface TableTemplateField {
  kind: "table";
  key: string;
  label: string;
  required: boolean;
  description: string | null;
  min_rows: number;
  columns: TableColumnDefinition[];
}

export type TemplateField = ScalarTemplateField | TableTemplateField;

export interface TemplateModule {
  key: string;
  label: string;
  fields: TemplateField[];
}

export interface Template {
  id: string;
  name: string;
  description: string | null;
  locale: TemplateLocale;
  modules: TemplateModule[];
  created_at: string;
  updated_at: string;
}

export interface TemplateDraft {
  name: string;
  description: string;
  locale: TemplateLocale;
  modules: TemplateModule[];
}

export interface TemplatePayload {
  name: string;
  description: string | null;
  locale: TemplateLocale;
  modules: TemplateModule[];
}

function emptyDescription() {
  return "";
}

export function createEmptyTableColumn(index: number): TableColumnDefinition {
  return {
    key: `column_${index}`,
    label: `Column ${index}`,
    value_type: "string",
    required: false,
    description: emptyDescription(),
  };
}

export function createEmptyScalarField(index: number): ScalarTemplateField {
  return {
    kind: "scalar",
    key: `field_${index}`,
    label: `Field ${index}`,
    required: false,
    description: emptyDescription(),
    value_type: "string",
  };
}

export function createEmptyTableField(index: number): TableTemplateField {
  return {
    kind: "table",
    key: `table_${index}`,
    label: `Table ${index}`,
    required: false,
    description: emptyDescription(),
    min_rows: 0,
    columns: [createEmptyTableColumn(1)],
  };
}

export function createEmptyModule(index: number): TemplateModule {
  return {
    key: `module_${index}`,
    label: `Module ${index}`,
    fields: [],
  };
}

export function createEmptyTemplateDraft(): TemplateDraft {
  return {
    name: "",
    description: "",
    locale: "en",
    modules: [],
  };
}

export function templateToDraft(template: Template): TemplateDraft {
  return {
    name: template.name,
    description: template.description ?? "",
    locale: template.locale,
    modules: structuredClone(template.modules),
  };
}

export function draftToPayload(draft: TemplateDraft): TemplatePayload {
  return {
    name: draft.name.trim(),
    description: draft.description.trim() || null,
    locale: draft.locale,
    modules: draft.modules.map((moduleItem) => ({
      key: moduleItem.key.trim(),
      label: moduleItem.label.trim(),
      fields: moduleItem.fields.map((field) => {
        if (field.kind === "table") {
          return {
            kind: "table",
            key: field.key.trim(),
            label: field.label.trim(),
            required: field.required,
            description: field.description?.trim() || null,
            min_rows: field.min_rows,
            columns: field.columns.map((column) => ({
              key: column.key.trim(),
              label: column.label.trim(),
              value_type: column.value_type,
              required: column.required,
              description: column.description?.trim() || null,
            })),
          };
        }

        return {
          kind: "scalar",
          key: field.key.trim(),
          label: field.label.trim(),
          required: field.required,
          description: field.description?.trim() || null,
          value_type: field.value_type,
        };
      }),
    })),
  };
}

export function cloneDraft(draft: TemplateDraft): TemplateDraft {
  return structuredClone(draft);
}

export function getDraftValidationError(draft: TemplateDraft): string | null {
  if (!draft.name.trim()) {
    return "Template name is required.";
  }

  for (const moduleItem of draft.modules) {
    if (!moduleItem.key.trim() || !moduleItem.label.trim()) {
      return "Each module needs both a key and a label.";
    }

    for (const field of moduleItem.fields) {
      if (!field.key.trim() || !field.label.trim()) {
        return "Each field needs both a key and a label.";
      }

      if (field.kind === "table") {
        for (const column of field.columns) {
          if (!column.key.trim() || !column.label.trim()) {
            return "Each table column needs both a key and a label.";
          }
        }
      }
    }
  }

  return null;
}

export function getTemplateStats(modules: TemplateModule[]) {
  let requiredFields = 0;
  let scalarFields = 0;
  let tableFields = 0;
  let tableColumns = 0;

  for (const moduleItem of modules) {
    for (const field of moduleItem.fields) {
      if (field.required) {
        requiredFields += 1;
      }

      if (field.kind === "table") {
        tableFields += 1;
        tableColumns += field.columns.length;
      } else {
        scalarFields += 1;
      }
    }
  }

  return {
    moduleCount: modules.length,
    requiredFields,
    scalarFields,
    tableFields,
    tableColumns,
    fieldCount: scalarFields + tableFields,
  };
}
