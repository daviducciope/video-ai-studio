import { ProjectDetail } from "@/components/project-detail";

type Props = {
  params: Promise<{ projectId: string }>;
};

export default async function ProjectDetailPage({ params }: Props) {
  const { projectId } = await params;
  return <ProjectDetail projectId={projectId} />;
}
