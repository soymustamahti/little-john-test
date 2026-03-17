"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { DocumentPreviewModal } from "@/components/features/documents/document-preview-modal";
import { DocumentUploadPanel } from "@/components/features/documents/document-upload-panel";
import { DocumentsTable } from "@/components/features/documents/documents-table";
import { SetupStatsGrid } from "@/components/features/templates/setup-stats-grid";
import { Badge } from "@/components/ui/badge";
import { useDocumentCategoriesQuery } from "@/hooks/use-document-categories";
import { useDocumentsQuery, useUploadDocumentsMutation } from "@/hooks/use-documents";
import { useTemplateMetricsQuery } from "@/hooks/use-templates";
import { getApiErrorMessage } from "@/lib/api/errors";
import { useLocale } from "@/providers/locale-provider";
import type { Document, DocumentUploadBatchResult } from "@/types/documents";
import { DEFAULT_PAGE_SIZE } from "@/types/pagination";

const DOCUMENTS_PAGE_SIZE = DEFAULT_PAGE_SIZE;

export function DocumentsSection() {
  const router = useRouter();
  const { messages, formatText } = useLocale();
  const [page, setPage] = useState(1);
  const documentsQuery = useDocumentsQuery({ page, pageSize: DOCUMENTS_PAGE_SIZE });
  const templateMetricsQuery = useTemplateMetricsQuery();
  const categoriesQuery = useDocumentCategoriesQuery({ page: 1, pageSize: 1 });
  const uploadDocumentsMutation = useUploadDocumentsMutation(messages.common.apiError);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadResults, setUploadResults] = useState<DocumentUploadBatchResult[]>([]);
  const [previewDocument, setPreviewDocument] = useState<Document | null>(null);

  const documents = documentsQuery.data?.items ?? [];
  const documentCount = documentsQuery.data?.total_items ?? 0;
  const totalPages = documentsQuery.data?.total_pages ?? 0;
  const extractionTemplateCount = templateMetricsQuery.data?.totalItems ?? 0;
  const documentCategoryCount = categoriesQuery.data?.total_items ?? 0;
  const totalModules = templateMetricsQuery.data?.totalModules ?? 0;
  const totalFields = templateMetricsQuery.data?.totalFields ?? 0;

  async function handleUpload() {
    if (!selectedFiles.length) {
      return;
    }

    try {
      const results = await uploadDocumentsMutation.mutateAsync(selectedFiles);
      setUploadResults(results);
      const hasSuccessfulUpload = results.some((result) => result.status === "success");

      if (hasSuccessfulUpload) {
        setSelectedFiles([]);
      }
    } catch (error) {
      setUploadResults([
        {
          fileName: selectedFiles[0]?.name ?? "upload",
          status: "error",
          errorMessage: getApiErrorMessage(error, messages.common.apiError),
        },
      ]);
    }
  }

  return (
    <div className="space-y-6 px-4 py-6 sm:px-6">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="accent">{messages.documentsSection.badges.layer}</Badge>
          <Badge>
            {formatText(messages.documentsSection.badges.uploaded, {
              count: documentCount,
            })}
          </Badge>
        </div>
        <div>
          <h2 className="text-3xl font-semibold text-[color:var(--color-ink)]">
            {messages.documentsSection.title}
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-[color:var(--color-muted)]">
            {messages.documentsSection.description}
          </p>
        </div>
      </div>

      <SetupStatsGrid
        extractionTemplateCount={extractionTemplateCount}
        documentCategoryCount={documentCategoryCount}
        documentCount={documentCount}
        totalModules={totalModules}
        totalFields={totalFields}
      />

      <DocumentUploadPanel
        selectedFiles={selectedFiles}
        uploadResults={uploadResults}
        isUploading={uploadDocumentsMutation.isPending}
        onFileSelection={(files) => {
          setSelectedFiles(files ? Array.from(files) : []);
          setUploadResults([]);
        }}
        onUpload={handleUpload}
        onClear={() => {
          setSelectedFiles([]);
          setUploadResults([]);
        }}
      />

      <DocumentsTable
        documents={documents}
        selectedDocumentId={null}
        isLoading={documentsQuery.isLoading}
        errorMessage={
          documentsQuery.error
            ? getApiErrorMessage(documentsQuery.error, messages.common.apiError)
            : null
        }
        page={page}
        pageSize={DOCUMENTS_PAGE_SIZE}
        totalItems={documentCount}
        totalPages={totalPages}
        onPageChange={setPage}
        onPreview={(document) => setPreviewDocument(document)}
        onSelect={(document) => router.push(`/documents/${document.id}`)}
      />

      <DocumentPreviewModal
        document={previewDocument}
        open={Boolean(previewDocument)}
        onClose={() => setPreviewDocument(null)}
      />
    </div>
  );
}
