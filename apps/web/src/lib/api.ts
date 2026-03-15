import { Project } from "@/types/project";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function serializeErrorDetail(detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          const issue = item as { loc?: Array<string | number>; msg?: string };
          const field = issue.loc?.slice(1).join(" > ");
          return field && issue.msg ? `${field}: ${issue.msg}` : issue.msg;
        }
        return null;
      })
      .filter(Boolean);
    if (messages.length > 0) {
      return messages.join("\n");
    }
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail, null, 2);
  }
  return "Si e' verificato un errore inatteso.";
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(serializeErrorDetail(body.detail));
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
  character_notes?: string;
  lock_identity?: boolean;
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
    body: JSON.stringify({ variants_per_scene: 3 }),
  });
}

export function uploadProjectAssets(projectId: string, role: "primary" | "reference", files: File[]) {
  const formData = new FormData();
  formData.append("role", role);
  files.forEach((file) => formData.append("files", file));
  return apiRequest<Project>(`/projects/${projectId}/assets`, {
    method: "POST",
    body: formData,
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
