"use client";

import axios from "axios";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { TemplateDetailPanel } from "@/components/features/templates/template-detail-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCreateTemplateMutation,
  useDeleteTemplateMutation,
  useTemplateQuery,
  useUpdateTemplateMutation,
} from "@/hooks/use-templates";
import { useLocale } from "@/providers/locale-provider";
import {
  cloneDraft,
  createEmptyModule,
  createEmptyScalarField,
  createEmptyTableColumn,
  createEmptyTableField,
  createEmptyTemplateDraft,
  draftToPayload,
  getDraftValidationError,
  templateToDraft,
  type TableColumnDefinition,
  type TemplateDraft,
  type TemplateField,
  type TemplateModule,
} from "@/types/templates";

function getErrorMessage(error: unknown, fallbackMessage: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

export function ExtractionTemplateEditorScreen({
  templateId,
}: {
  templateId?: string;
}) {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const templateQuery = useTemplateQuery(templateId);
  const createTemplateMutation = useCreateTemplateMutation();
  const updateTemplateMutation = useUpdateTemplateMutation();
  const deleteTemplateMutation = useDeleteTemplateMutation();

  const [draft, setDraft] = useState<TemplateDraft | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<"neutral" | "success" | "danger">("neutral");

  const template = templateQuery.data ?? null;
  const mode = templateId ? "edit" : "create";
  const editorDraft =
    draft ?? (template ? templateToDraft(template) : createEmptyTemplateDraft());
  const draftLabels = messages.templateShared;

  const isSaving = createTemplateMutation.isPending || updateTemplateMutation.isPending;
  const isDeleting = deleteTemplateMutation.isPending;
  const validationError = getDraftValidationError(editorDraft, draftLabels.validation);

  function replaceDraft(nextDraft: TemplateDraft) {
    setDraft(nextDraft);
  }

  function updateDraft(updater: (current: TemplateDraft) => TemplateDraft) {
    setDraft((current) => updater(cloneDraft(current ?? editorDraft)));
  }

  function resetDraft() {
    if (template) {
      replaceDraft(templateToDraft(template));
      setStatusMessage(messages.templateEditorScreen.status.reset);
      setStatusTone("neutral");
      return;
    }

    replaceDraft(createEmptyTemplateDraft());
    setStatusMessage(messages.templateEditorScreen.status.cleared);
    setStatusTone("neutral");
  }

  async function saveTemplate() {
    if (validationError) {
      setStatusMessage(validationError);
      setStatusTone("danger");
      return;
    }

    const payload = draftToPayload(editorDraft);

    try {
      if (templateId) {
        const updatedTemplate = await updateTemplateMutation.mutateAsync({
          templateId,
          payload,
        });
        replaceDraft(templateToDraft(updatedTemplate));
        setStatusMessage(
          formatText(messages.templateEditorScreen.status.saved, {
            name: updatedTemplate.name,
          }),
        );
        setStatusTone("success");
        return;
      }

      const createdTemplate = await createTemplateMutation.mutateAsync(payload);
      setStatusMessage(
        formatText(messages.templateEditorScreen.status.created, {
          name: createdTemplate.name,
        }),
      );
      setStatusTone("success");
      router.replace(`/extraction-templates/${createdTemplate.id}`);
    } catch (error) {
      setStatusMessage(getErrorMessage(error, messages.common.apiError));
      setStatusTone("danger");
    }
  }

  async function deleteTemplate() {
    if (!templateId || !template) {
      return;
    }

    const confirmed = window.confirm(
      formatText(messages.templateEditorScreen.confirmDelete, {
        name: template.name,
      }),
    );
    if (!confirmed) {
      return;
    }

    try {
      await deleteTemplateMutation.mutateAsync(templateId);
      router.push("/extraction-templates");
    } catch (error) {
      setStatusMessage(getErrorMessage(error, messages.common.apiError));
      setStatusTone("danger");
    }
  }

  function updateModule(moduleIndex: number, nextModule: TemplateModule) {
    updateDraft((current) => {
      current.modules[moduleIndex] = nextModule;
      return current;
    });
  }

  function addModule() {
    updateDraft((current) => ({
      ...current,
      modules: [
        ...current.modules,
        createEmptyModule(current.modules.length + 1, draftLabels),
      ],
    }));
  }

  function removeModule(moduleIndex: number) {
    updateDraft((current) => ({
      ...current,
      modules: current.modules.filter((_, index) => index !== moduleIndex),
    }));
  }

  function addField(moduleIndex: number, kind: "scalar" | "table") {
    updateDraft((current) => {
      const moduleItem = current.modules[moduleIndex];
      const nextField =
        kind === "table"
          ? createEmptyTableField(moduleItem.fields.length + 1, draftLabels)
          : createEmptyScalarField(moduleItem.fields.length + 1, draftLabels);
      moduleItem.fields.push(nextField);
      return current;
    });
  }

  function changeField(moduleIndex: number, fieldIndex: number, nextField: TemplateField) {
    updateDraft((current) => {
      current.modules[moduleIndex].fields[fieldIndex] = nextField;
      return current;
    });
  }

  function removeField(moduleIndex: number, fieldIndex: number) {
    updateDraft((current) => {
      current.modules[moduleIndex].fields = current.modules[moduleIndex].fields.filter(
        (_, index) => index !== fieldIndex,
      );
      return current;
    });
  }

  function addColumn(moduleIndex: number, fieldIndex: number) {
    updateDraft((current) => {
      const field = current.modules[moduleIndex].fields[fieldIndex];
      if (field.kind !== "table") {
        return current;
      }

      field.columns.push(createEmptyTableColumn(field.columns.length + 1, draftLabels));
      return current;
    });
  }

  function changeColumn(
    moduleIndex: number,
    fieldIndex: number,
    columnIndex: number,
    nextColumn: TableColumnDefinition,
  ) {
    updateDraft((current) => {
      const field = current.modules[moduleIndex].fields[fieldIndex];
      if (field.kind !== "table") {
        return current;
      }

      field.columns[columnIndex] = nextColumn;
      return current;
    });
  }

  function removeColumn(moduleIndex: number, fieldIndex: number, columnIndex: number) {
    updateDraft((current) => {
      const field = current.modules[moduleIndex].fields[fieldIndex];
      if (field.kind !== "table") {
        return current;
      }

      field.columns = field.columns.filter((_, index) => index !== columnIndex);
      return current;
    });
  }

  if (templateId && templateQuery.isLoading) {
    return (
      <div className="px-4 py-6 sm:px-6">
        <Card>
          <CardContent className="p-6 text-sm text-[color:var(--color-muted)]">
            {messages.templateEditorScreen.loading}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (templateId && templateQuery.error) {
    return (
      <div className="space-y-4 px-4 py-6 sm:px-6">
        <Button
          variant="secondary"
          onClick={() => router.push("/extraction-templates")}
        >
          <ArrowLeft className="h-4 w-4" />
          {messages.templateEditorScreen.backToTemplates}
        </Button>
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">
              {messages.templateEditorScreen.errorTitle}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[color:var(--color-accent-warm)]">
            {getErrorMessage(templateQuery.error, messages.common.apiError)}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 px-4 py-6 sm:px-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-[color:var(--color-muted)]">
            {messages.common.labels.workspace} / {messages.templateEditorScreen.breadcrumbSection} /{" "}
            {mode === "create"
              ? messages.templateEditorScreen.breadcrumbCreate
              : template?.name ?? messages.templateEditorScreen.breadcrumbEditFallback}
          </p>
          <h2 className="mt-1 text-3xl font-semibold text-[color:var(--color-ink)]">
            {mode === "create"
              ? messages.templateEditorScreen.titleCreate
              : editorDraft.name || messages.templateEditorScreen.titleEditFallback}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            {messages.templateEditorScreen.description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="accent">{messages.templateEditorScreen.badge}</Badge>
          <Button
            variant="secondary"
            onClick={() => router.push("/extraction-templates")}
          >
            <ArrowLeft className="h-4 w-4" />
            {messages.common.actions.backToList}
          </Button>
        </div>
      </div>

      <TemplateDetailPanel
        draft={editorDraft}
        mode={mode}
        validationError={validationError}
        statusMessage={statusMessage}
        statusTone={statusTone}
        isSaving={isSaving}
        isDeleting={isDeleting}
        onNameChange={(value) =>
          updateDraft((current) => ({
            ...current,
            name: value,
          }))
        }
        onDescriptionChange={(value) =>
          updateDraft((current) => ({
            ...current,
            description: value,
          }))
        }
        onLocaleChange={(value) =>
          updateDraft((current) => ({
            ...current,
            locale: value,
          }))
        }
        onAddModule={addModule}
        onChangeModule={updateModule}
        onRemoveModule={removeModule}
        onAddScalarField={(moduleIndex) => addField(moduleIndex, "scalar")}
        onAddTableField={(moduleIndex) => addField(moduleIndex, "table")}
        onChangeField={changeField}
        onRemoveField={removeField}
        onAddColumn={addColumn}
        onChangeColumn={changeColumn}
        onRemoveColumn={removeColumn}
        onReset={resetDraft}
        onSave={saveTemplate}
        onDelete={deleteTemplate}
      />
    </div>
  );
}
