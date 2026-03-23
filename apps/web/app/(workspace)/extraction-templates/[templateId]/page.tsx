import { ExtractionTemplateEditorScreen } from "@/components/features/templates/extraction-template-editor-screen";

export default async function ExtractionTemplateDetailPage({
  params,
}: {
  params: Promise<{ templateId: string }>;
}) {
  const { templateId } = await params;

  return <ExtractionTemplateEditorScreen templateId={templateId} />;
}
