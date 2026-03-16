import { DocumentDetailScreen } from "@/components/features/documents/document-detail-screen";

export default async function DocumentDetailPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;

  return <DocumentDetailScreen documentId={documentId} />;
}
