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

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while talking to the API.";
}

export function DocumentCategoryEditorScreen({
  categoryId,
}: {
  categoryId?: string;
}) {
  const router = useRouter();
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
  const validationError = getDocumentCategoryValidationError(editorDraft);

  function replaceDraft(nextDraft: DocumentCategoryDraft) {
    setDraft(nextDraft);
  }

  function updateDraft(updater: (current: DocumentCategoryDraft) => DocumentCategoryDraft) {
    setDraft((current) => updater(cloneDocumentCategoryDraft(current ?? editorDraft)));
  }

  function resetDraft() {
    if (category) {
      replaceDraft(documentCategoryToDraft(category));
      setStatusMessage("Changes reset to the last saved version.");
      setStatusTone("neutral");
      return;
    }

    replaceDraft(createEmptyDocumentCategoryDraft());
    setStatusMessage("Draft cleared.");
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
        setStatusMessage(`Saved "${updatedCategory.name}".`);
        setStatusTone("success");
        return;
      }

      const createdCategory = await createCategoryMutation.mutateAsync(payload);
      setStatusMessage(`Created "${createdCategory.name}".`);
      setStatusTone("success");
      router.replace(`/document-categories/${createdCategory.id}`);
    } catch (error) {
      setStatusMessage(getErrorMessage(error));
      setStatusTone("danger");
    }
  }

  async function deleteCategory() {
    if (!categoryId || !category) {
      return;
    }

    const confirmed = window.confirm(`Delete "${category.name}"?`);
    if (!confirmed) {
      return;
    }

    try {
      await deleteCategoryMutation.mutateAsync(categoryId);
      router.push("/document-categories");
    } catch (error) {
      setStatusMessage(getErrorMessage(error));
      setStatusTone("danger");
    }
  }

  if (categoryId && categoryQuery.isLoading) {
    return (
      <div className="px-4 py-6 sm:px-6">
        <Card>
          <CardContent className="p-6 text-sm text-[color:var(--color-muted)]">
            Loading document category...
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
          Back to document categories
        </Button>
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Unable to load document category</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[color:var(--color-accent-warm)]">
            {getErrorMessage(categoryQuery.error)}
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
            Workspace / Document categories / {mode === "create" ? "New" : category?.name ?? "Edit"}
          </p>
          <h2 className="mt-1 text-3xl font-semibold text-[color:var(--color-ink)]">
            {mode === "create" ? "New document category" : editorDraft.name || "Edit document category"}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            Review one classification target at a time, then save or delete it
            from a dedicated detail view instead of splitting the screen.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="warm">Classification target</Badge>
          <Button
            variant="secondary"
            onClick={() => router.push("/document-categories")}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to list
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
