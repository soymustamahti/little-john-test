"use client";

import axios from "axios";
import { FileStack, LayoutDashboard, ListChecks, Shapes, Sparkles } from "lucide-react";
import { useState } from "react";

import { TemplateDetailPanel } from "@/components/features/templates/template-detail-panel";
import { TemplatesTable } from "@/components/features/templates/templates-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  useCreateTemplateMutation,
  useDeleteTemplateMutation,
  useTemplatesQuery,
  useUpdateTemplateMutation,
} from "@/hooks/use-templates";
import {
  cloneDraft,
  createEmptyModule,
  createEmptyScalarField,
  createEmptyTableColumn,
  createEmptyTableField,
  createEmptyTemplateDraft,
  draftToPayload,
  getDraftValidationError,
  getTemplateStats,
  templateToDraft,
  type TableColumnDefinition,
  type Template,
  type TemplateDraft,
  type TemplateField,
  type TemplateModule,
} from "@/types/templates";

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while talking to the API.";
}

function Sidebar() {
  return (
    <aside className="w-full border-b border-[color:var(--color-line)] bg-white/90 p-4 lg:w-64 lg:border-b-0 lg:border-r lg:p-6">
      <div className="space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--color-muted)]">
            Dashboard
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-[color:var(--color-ink)]">
            Little John
          </h1>
          <p className="mt-2 text-sm text-[color:var(--color-muted)]">
            Simple operator workspace for template management.
          </p>
        </div>

        <nav className="space-y-2">
          <button
            type="button"
            className="flex w-full items-center gap-3 rounded-xl bg-[color:var(--color-accent-soft)] px-4 py-3 text-left text-sm font-medium text-[color:var(--color-accent)]"
          >
            <Shapes className="h-4 w-4" />
            Templates
          </button>
          <div className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-[color:var(--color-muted)]">
            <LayoutDashboard className="h-4 w-4" />
            Overview
          </div>
          <div className="flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-[color:var(--color-muted)]">
            <FileStack className="h-4 w-4" />
            Documents
          </div>
        </nav>

        <Card className="border-dashed">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
              <Sparkles className="h-4 w-4 text-[color:var(--color-accent)]" />
              Seeded examples
            </div>
            <p className="mt-2 text-sm text-[color:var(--color-muted)]">
              Use the seeded invoice, PO, contract, and French invoice templates as starting
              points.
            </p>
          </CardContent>
        </Card>
      </div>
    </aside>
  );
}

export function TemplatesDashboard() {
  const templatesQuery = useTemplatesQuery();
  const createTemplateMutation = useCreateTemplateMutation();
  const updateTemplateMutation = useUpdateTemplateMutation();
  const deleteTemplateMutation = useDeleteTemplateMutation();

  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [draft, setDraft] = useState<TemplateDraft | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<"neutral" | "success" | "danger">("neutral");

  const templates = templatesQuery.data ?? [];
  const activeTemplate = isCreatingNew
    ? null
    : templates.find((template) => template.id === selectedTemplateId) ??
      (templates[0] ?? null);
  const activeTemplateId = activeTemplate?.id ?? null;
  const editorDraft = draft ?? (activeTemplate ? templateToDraft(activeTemplate) : createEmptyTemplateDraft());

  const isSaving = createTemplateMutation.isPending || updateTemplateMutation.isPending;
  const isDeleting = deleteTemplateMutation.isPending;
  const validationError = getDraftValidationError(editorDraft);

  const totalModules = templates.reduce(
    (count, template) => count + getTemplateStats(template.modules).moduleCount,
    0,
  );
  const totalFields = templates.reduce(
    (count, template) => count + getTemplateStats(template.modules).fieldCount,
    0,
  );

  function replaceDraft(nextDraft: TemplateDraft) {
    setDraft(nextDraft);
  }

  function updateDraft(updater: (current: TemplateDraft) => TemplateDraft) {
    setDraft((current) => updater(cloneDraft(current ?? editorDraft)));
  }

  function selectTemplate(template: Template) {
    setSelectedTemplateId(template.id);
    setIsCreatingNew(false);
    replaceDraft(templateToDraft(template));
    setStatusMessage(null);
  }

  function startNewTemplate() {
    setSelectedTemplateId(null);
    setIsCreatingNew(true);
    replaceDraft(createEmptyTemplateDraft());
    setStatusMessage("New template draft ready.");
    setStatusTone("neutral");
  }

  function resetDraft() {
    if (activeTemplate) {
      replaceDraft(templateToDraft(activeTemplate));
      setStatusMessage("Changes reset to the last saved version.");
      setStatusTone("neutral");
      return;
    }

    replaceDraft(createEmptyTemplateDraft());
    setStatusMessage("Draft cleared.");
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
      if (activeTemplateId) {
        const updatedTemplate = await updateTemplateMutation.mutateAsync({
          templateId: activeTemplateId,
          payload,
        });
        setSelectedTemplateId(updatedTemplate.id);
        setIsCreatingNew(false);
        replaceDraft(templateToDraft(updatedTemplate));
        setStatusMessage(`Saved "${updatedTemplate.name}".`);
        setStatusTone("success");
        return;
      }

      const createdTemplate = await createTemplateMutation.mutateAsync(payload);
      setSelectedTemplateId(createdTemplate.id);
      setIsCreatingNew(false);
      replaceDraft(templateToDraft(createdTemplate));
      setStatusMessage(`Created "${createdTemplate.name}".`);
      setStatusTone("success");
    } catch (error) {
      setStatusMessage(getErrorMessage(error));
      setStatusTone("danger");
    }
  }

  async function deleteTemplate() {
    if (!activeTemplateId || !activeTemplate) {
      return;
    }

    const confirmed = window.confirm(`Delete "${activeTemplate.name}"?`);
    if (!confirmed) {
      return;
    }

    try {
      await deleteTemplateMutation.mutateAsync(activeTemplateId);
      setSelectedTemplateId(null);
      setIsCreatingNew(false);
      setDraft(null);
      setStatusMessage(`Deleted "${activeTemplate.name}".`);
      setStatusTone("success");
    } catch (error) {
      setStatusMessage(getErrorMessage(error));
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
      modules: [...current.modules, createEmptyModule(current.modules.length + 1)],
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
          ? createEmptyTableField(moduleItem.fields.length + 1)
          : createEmptyScalarField(moduleItem.fields.length + 1);
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

      field.columns.push(createEmptyTableColumn(field.columns.length + 1));
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

  return (
    <main className="min-h-screen bg-[color:var(--color-background)]">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Sidebar />

        <div className="flex-1">
          <header className="border-b border-[color:var(--color-line)] bg-white/75 px-4 py-5 sm:px-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm text-[color:var(--color-muted)]">Dashboard / Templates</p>
                <h2 className="mt-1 text-3xl font-semibold text-[color:var(--color-ink)]">
                  Template management
                </h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{templates.length} templates</Badge>
                <Button variant="secondary" onClick={startNewTemplate}>
                  New template
                </Button>
              </div>
            </div>
          </header>

          <div className="space-y-6 px-4 py-6 sm:px-6">
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
                    <Shapes className="h-4 w-4" />
                    Templates
                  </div>
                  <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
                    {templates.length}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
                    <ListChecks className="h-4 w-4" />
                    Modules
                  </div>
                  <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
                    {totalModules}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 text-sm text-[color:var(--color-muted)]">
                    <FileStack className="h-4 w-4" />
                    Fields
                  </div>
                  <p className="mt-3 text-3xl font-semibold text-[color:var(--color-ink)]">
                    {totalFields}
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.15fr)]">
              <TemplatesTable
                templates={templates}
                selectedTemplateId={activeTemplateId}
                isLoading={templatesQuery.isLoading}
                errorMessage={templatesQuery.error ? getErrorMessage(templatesQuery.error) : null}
                onCreate={startNewTemplate}
                onSelect={selectTemplate}
              />

              <TemplateDetailPanel
                draft={editorDraft}
                mode={activeTemplateId ? "edit" : "create"}
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
          </div>
        </div>
      </div>
    </main>
  );
}
