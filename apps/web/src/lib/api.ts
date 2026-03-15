import { Project } from "@/types/project";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Unexpected API error");
  }

  return response.json() as Promise<T>;
}

export function listProjects() {
  return apiRequest<Project[]>("/projects");
}

export function createProject(payload: {
  title: string;
  prompt: string;
  style: string;
  duration_target: number;
  aspect_ratio: "9:16" | "16:9";
  avatar_notes?: string;
}) {
  return apiRequest<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getProject(projectId: string) {
  return apiRequest<Project>(`/projects/${projectId}`);
}

export function generateStoryboard(projectId: string) {
  return apiRequest<Project>(`/projects/${projectId}/storyboard`, {
    method: "POST",
  });
}

export function generatePreviews(projectId: string) {
  return apiRequest<Project>(`/projects/${projectId}/previews`, {
    method: "POST",
    body: JSON.stringify({ variants_per_scene: 1 }),
  });
}

export function selectScene(projectId: string, sceneId: string, previewId?: string) {
  return apiRequest<Project>(`/projects/${projectId}/scenes/${sceneId}/select`, {
    method: "POST",
    body: JSON.stringify({ preview_id: previewId ?? null }),
  });
}

export function renderProject(projectId: string) {
  return apiRequest<Project>(`/projects/${projectId}/render`, {
    method: "POST",
  });
}
