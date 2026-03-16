"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useLocale } from "@/providers/locale-provider";
import {
  formatDocumentSize,
  getDocumentKindLabel,
  type Document,
} from "@/types/documents";

export function DocumentsTable({
  documents,
  selectedDocumentId,
  isLoading,
  errorMessage,
  onPreview,
  onSelect,
}: {
  documents: Document[];
  selectedDocumentId: string | null;
  isLoading: boolean;
  errorMessage: string | null;
  onPreview: (document: Document) => void;
  onSelect: (document: Document) => void;
}) {
  const { locale, messages, formatDate, formatText } = useLocale();

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-[color:var(--color-line)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="accent">{messages.documentsTable.badges.layer}</Badge>
              <Badge>
                {formatText(messages.documentsTable.badges.files, {
                  count: documents.length,
                })}
              </Badge>
            </div>
            <CardTitle className="mt-3 text-2xl">
              {messages.documentsTable.title}
            </CardTitle>
            <CardDescription>{messages.documentsTable.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6 text-sm text-[color:var(--color-muted)]">
            {messages.documentsTable.loading}
          </div>
        ) : null}

        {!isLoading && errorMessage ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-accent-warm)]">
            {errorMessage}
          </div>
        ) : null}

        {!isLoading && !errorMessage && !documents.length ? (
          <div className="border-t border-[color:var(--color-line)] p-6 text-sm text-[color:var(--color-muted)]">
            {messages.documentsTable.empty}
          </div>
        ) : null}

        {!isLoading && documents.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-[color:var(--color-background)]/70 text-[color:var(--color-muted)]">
                <tr>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentsTable.headers.document}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentsTable.headers.kind}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentsTable.headers.size}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentsTable.headers.created}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentsTable.headers.preview}
                  </th>
                  <th className="px-4 py-3 font-medium">
                    {messages.documentsTable.headers.open}
                  </th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => {
                  const isSelected = selectedDocumentId === document.id;

                  return (
                    <tr
                      key={document.id}
                      className={cn(
                        "cursor-pointer border-t border-[color:var(--color-line)] transition hover:bg-[color:var(--color-background)]/70",
                        isSelected ? "bg-[color:var(--color-accent-soft)]" : "bg-white",
                      )}
                      onClick={() => onSelect(document)}
                    >
                      <td className="px-4 py-4 align-top">
                        <div className="space-y-1">
                          <div className="font-medium text-[color:var(--color-ink)]">
                            {document.original_filename}
                          </div>
                          <div className="text-xs text-[color:var(--color-muted)]">
                            {document.content_type}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Badge variant="accent">
                          {getDocumentKindLabel(document.file_kind, messages)}
                        </Badge>
                      </td>
                      <td className="px-4 py-4 align-top text-[color:var(--color-ink)]">
                        {formatDocumentSize(document.size_bytes, locale)}
                      </td>
                      <td className="px-4 py-4 align-top text-[color:var(--color-muted)]">
                        {formatDate(document.created_at)}
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={(event) => {
                            event.stopPropagation();
                            onPreview(document);
                          }}
                        >
                          {messages.common.actions.preview}
                        </Button>
                      </td>
                      <td className="px-4 py-4 align-top">
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={(event) => {
                            event.stopPropagation();
                            onSelect(document);
                          }}
                        >
                          {messages.common.actions.view}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
