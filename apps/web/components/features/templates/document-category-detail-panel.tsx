import { FolderInput, RefreshCcw, Save, Tags, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLocale } from "@/providers/locale-provider";
import {
  getDocumentCategoryDisplayName,
  type DocumentCategoryDraft,
} from "@/types/document-categories";

export function DocumentCategoryDetailPanel({
  draft,
  mode,
  validationError,
  statusMessage,
  statusTone,
  isSaving,
  isDeleting,
  onNameChange,
  onLabelKeyChange,
  onReset,
  onSave,
  onDelete,
}: {
  draft: DocumentCategoryDraft;
  mode: "create" | "edit";
  validationError: string | null;
  statusMessage: string | null;
  statusTone: "neutral" | "success" | "danger";
  isSaving: boolean;
  isDeleting: boolean;
  onNameChange: (value: string) => void;
  onLabelKeyChange: (value: string) => void;
  onReset: () => void;
  onSave: () => void;
  onDelete: () => void;
}) {
  const { messages } = useLocale();
  const displayName = getDocumentCategoryDisplayName(draft, messages);
  const validationClassName =
    "rounded-xl border border-[color:var(--color-warm-soft)] bg-[color:var(--color-background)] px-4 py-3 text-sm text-[color:var(--color-accent-warm)]";

  const statusClassName =
    statusTone === "danger"
      ? validationClassName
      : statusTone === "success"
        ? "rounded-xl border border-[color:var(--color-success-soft)] bg-white px-4 py-3 text-sm text-[color:var(--color-success)]"
        : "rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3 text-sm text-[color:var(--color-muted)]";

  return (
    <Card>
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="warm">
                {mode === "create"
                  ? messages.documentCategoryDetailPanel.badges.new
                  : messages.documentCategoryDetailPanel.badges.details}
              </Badge>
              <Badge>{messages.documentCategoryDetailPanel.badges.routingTarget}</Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">
              {mode === "create"
                ? messages.documentCategoryDetailPanel.titleCreate
                : displayName || messages.documentCategoryDetailPanel.titleEditFallback}
            </CardTitle>
            <CardDescription>
              {messages.documentCategoryDetailPanel.description}
            </CardDescription>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={onReset}>
              <RefreshCcw className="h-4 w-4" />
              {messages.common.actions.reset}
            </Button>
            {mode === "edit" ? (
              <Button type="button" variant="danger" onClick={onDelete} disabled={isDeleting}>
                <Trash2 className="h-4 w-4" />
                {isDeleting
                  ? messages.common.actions.deleting
                  : messages.common.actions.delete}
              </Button>
            ) : null}
            <Button type="button" onClick={onSave} disabled={Boolean(validationError) || isSaving}>
              <Save className="h-4 w-4" />
              {isSaving
                ? messages.common.actions.saving
                : mode === "create"
                  ? messages.common.actions.create
                  : messages.common.actions.save}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 pt-6">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>{messages.documentCategoryDetailPanel.fields.name}</Label>
              <Input value={draft.name} onChange={(event) => onNameChange(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>{messages.documentCategoryDetailPanel.fields.labelKey}</Label>
              <Input
                value={draft.label_key}
                onChange={(event) => onLabelKeyChange(event.target.value)}
              />
            </div>
          </div>

          <div className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-background)]/55 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
              <Tags className="h-4 w-4 text-[color:var(--color-accent-warm)]" />
              {messages.documentCategoryDetailPanel.preview.title}
            </div>
            <p className="mt-3 text-sm text-[color:var(--color-muted)]">
              {messages.documentCategoryDetailPanel.preview.description}
            </p>
            <div className="mt-4 space-y-3">
              <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3">
                <div className="text-xs uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                  {messages.documentCategoryDetailPanel.preview.translatedLabel}
                </div>
                <div className="mt-2 flex items-center gap-2 text-sm font-medium text-[color:var(--color-ink)]">
                  <FolderInput className="h-4 w-4 text-[color:var(--color-accent)]" />
                  {displayName || messages.documentCategoryDetailPanel.preview.untitled}
                </div>
              </div>
              <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3">
                <div className="text-xs uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                  {messages.documentCategoryDetailPanel.preview.classifierName}
                </div>
                <div className="mt-2 text-sm font-medium text-[color:var(--color-ink)]">
                  {draft.name.trim() || messages.documentCategoryDetailPanel.preview.untitled}
                </div>
              </div>
              <div className="rounded-xl border border-[color:var(--color-line)] bg-white px-4 py-3">
                <div className="text-xs uppercase tracking-[0.16em] text-[color:var(--color-muted)]">
                  {messages.documentCategoryDetailPanel.preview.labelKey}
                </div>
                <div className="mt-2 text-sm font-medium text-[color:var(--color-ink)]">
                  {draft.label_key.trim() || "-"}
                </div>
              </div>
            </div>
          </div>
        </div>

        {validationError ? <div className={validationClassName}>{validationError}</div> : null}

        {statusMessage ? <div className={statusClassName}>{statusMessage}</div> : null}
      </CardContent>
    </Card>
  );
}
