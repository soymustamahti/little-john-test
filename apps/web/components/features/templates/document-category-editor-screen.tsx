"use client";

import axios from "axios";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { DocumentCategoryDetailPanel } from "@/components/features/templates/document-category-detail-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCreateDocumentCategoryMutation,
  useDeleteDocumentCategoryMutation,
  useDocumentCategoryQuery,
  useUpdateDocumentCategoryMutation,
} from "@/hooks/use-document-categories";
import {
  cloneDocumentCategoryDraft,
  createEmptyDocumentCategoryDraft,
  documentCategoryToDraft,
  draftToDocumentCategoryPayload,
  getDocumentCategoryValidationError,
  type DocumentCategoryDraft,
} from "@/types/document-categories";

import { useLocale } from "@/providers/locale-provider";

function getErrorMessage(error: unknown, fallbackMessage: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

export function DocumentCategoryEditorScreen({
  categoryId,
}: {
  categoryId?: string;
}) {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const categoryQuery = useDocumentCategoryQuery(categoryId);
  const createCategoryMutation = useCreateDocumentCategoryMutation();
  const updateCategoryMutation = useUpdateDocumentCategoryMutation();
  const deleteCategoryMutation = useDeleteDocumentCategoryMutation();

  const [draft, setDraft] = useState<DocumentCategoryDraft | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<"neutral" | "success" | "danger">("neutral");

  const category = categoryQuery.data ?? null;
  const mode = categoryId ? "edit" : "create";
  const editorDraft =
    draft ?? (category ? documentCategoryToDraft(category) : createEmptyDocumentCategoryDraft());

  const isSaving = createCategoryMutation.isPending || updateCategoryMutation.isPending;
  const isDeleting = deleteCategoryMutation.isPending;
  const validationError = getDocumentCategoryValidationError(
    editorDraft,
    messages.documentCategoryValidation.nameRequired,
  );

  function replaceDraft(nextDraft: DocumentCategoryDraft) {
    setDraft(nextDraft);
  }

  function updateDraft(updater: (current: DocumentCategoryDraft) => DocumentCategoryDraft) {
    setDraft((current) => updater(cloneDocumentCategoryDraft(current ?? editorDraft)));
  }

  function resetDraft() {
    if (category) {
      replaceDraft(documentCategoryToDraft(category));
      setStatusMessage(messages.documentCategoryEditorScreen.status.reset);
      setStatusTone("neutral");
      return;
    }

    replaceDraft(createEmptyDocumentCategoryDraft());
    setStatusMessage(messages.documentCategoryEditorScreen.status.cleared);
    setStatusTone("neutral");
  }

  async function saveCategory() {
    if (validationError) {
      setStatusMessage(validationError);
      setStatusTone("danger");
      return;
    }

    const payload = draftToDocumentCategoryPayload(editorDraft);

    try {
      if (categoryId) {
        const updatedCategory = await updateCategoryMutation.mutateAsync({
          categoryId,
          payload,
        });
        replaceDraft(documentCategoryToDraft(updatedCategory));
        setStatusMessage(
          formatText(messages.documentCategoryEditorScreen.status.saved, {
            name: updatedCategory.name,
          }),
        );
        setStatusTone("success");
        return;
      }

      const createdCategory = await createCategoryMutation.mutateAsync(payload);
      setStatusMessage(
        formatText(messages.documentCategoryEditorScreen.status.created, {
          name: createdCategory.name,
        }),
      );
      setStatusTone("success");
      router.replace(`/document-categories/${createdCategory.id}`);
    } catch (error) {
      setStatusMessage(getErrorMessage(error, messages.common.apiError));
      setStatusTone("danger");
    }
  }

  async function deleteCategory() {
    if (!categoryId || !category) {
      return;
    }

    const confirmed = window.confirm(
      formatText(messages.documentCategoryEditorScreen.confirmDelete, {
        name: category.name,
      }),
    );
    if (!confirmed) {
      return;
    }

    try {
      await deleteCategoryMutation.mutateAsync(categoryId);
      router.push("/document-categories");
    } catch (error) {
      setStatusMessage(getErrorMessage(error, messages.common.apiError));
      setStatusTone("danger");
    }
  }

  if (categoryId && categoryQuery.isLoading) {
    return (
      <div className="px-4 py-6 sm:px-6">
        <Card>
          <CardContent className="p-6 text-sm text-[color:var(--color-muted)]">
            {messages.documentCategoryEditorScreen.loading}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (categoryId && categoryQuery.error) {
    return (
      <div className="space-y-4 px-4 py-6 sm:px-6">
        <Button
          variant="secondary"
          onClick={() => router.push("/document-categories")}
        >
          <ArrowLeft className="h-4 w-4" />
          {messages.documentCategoryEditorScreen.backToCategories}
        </Button>
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">
              {messages.documentCategoryEditorScreen.errorTitle}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[color:var(--color-accent-warm)]">
            {getErrorMessage(categoryQuery.error, messages.common.apiError)}
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
            {messages.common.labels.workspace} / {messages.documentCategoryEditorScreen.breadcrumbSection} /{" "}
            {mode === "create"
              ? messages.documentCategoryEditorScreen.breadcrumbCreate
              : category?.name ?? messages.documentCategoryEditorScreen.breadcrumbEditFallback}
          </p>
          <h2 className="mt-1 text-3xl font-semibold text-[color:var(--color-ink)]">
            {mode === "create"
              ? messages.documentCategoryEditorScreen.titleCreate
              : editorDraft.name || messages.documentCategoryEditorScreen.titleEditFallback}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            {messages.documentCategoryEditorScreen.description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="warm">{messages.documentCategoryEditorScreen.badge}</Badge>
          <Button
            variant="secondary"
            onClick={() => router.push("/document-categories")}
          >
            <ArrowLeft className="h-4 w-4" />
            {messages.common.actions.backToList}
          </Button>
        </div>
      </div>

      <DocumentCategoryDetailPanel
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
        onReset={resetDraft}
        onSave={saveCategory}
        onDelete={deleteCategory}
      />
    </div>
  );
}
