import { DocumentCategoryEditorScreen } from "@/components/features/templates/document-category-editor-screen";

export default async function DocumentCategoryDetailPage({
  params,
}: {
  params: Promise<{ categoryId: string }>;
}) {
  const { categoryId } = await params;

  return <DocumentCategoryEditorScreen categoryId={categoryId} />;
}
