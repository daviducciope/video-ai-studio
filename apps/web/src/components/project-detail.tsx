"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  generateProjectVideo,
  generatePreviews,
  generateSceneVideo,
  generateStoryboard,
  getProject,
  regenerateScenePreviews,
  renderProject,
  selectScene,
} from "@/lib/api";
import { PreviewAsset, Project } from "@/types/project";

type Props = {
  projectId: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function resolveAssetUrl(url: string | null | undefined) {
  if (!url) {
    return "";
  }
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  return `${API_BASE_URL}${url}`;
}

const STATUS_META: Record<string, { label: string; tone: string; description: string }> = {
  draft: {
    label: "Draft",
    tone: "bg-slate-100 text-slate-700 border-slate-200",
    description: "Brief salvato. Storyboard non ancora generato.",
  },
  storyboard_ready: {
    label: "Storyboard pronto",
    tone: "bg-amber-100 text-amber-800 border-amber-200",
    description: "Scene e script sono disponibili.",
  },
  previews_ready: {
    label: "Preview pronte",
    tone: "bg-sky-100 text-sky-800 border-sky-200",
    description: "Le varianti preview sono state generate e sono pronte per la selezione manuale.",
  },
  rendering: {
    label: "Rendering",
    tone: "bg-violet-100 text-violet-800 border-violet-200",
    description: "Render mock in corso con output in preparazione.",
  },
  ready: {
    label: "Ready",
    tone: "bg-emerald-100 text-emerald-800 border-emerald-200",
    description: "Output finale disponibile.",
  },
  video_ready: {
    label: "Video pronto",
    tone: "bg-emerald-100 text-emerald-800 border-emerald-200",
    description: "Clip video disponibile nel backend storage configurato.",
  },
};

function getStatusMeta(status: string) {
  return STATUS_META[status] ?? {
    label: status,
    tone: "bg-slate-100 text-slate-700 border-slate-200",
    description: "Stato non classificato.",
  };
}

function getPreviewModeMeta(mode: string) {
  if (mode === "real") {
    return {
      label: "Real preview",
      tone: "border-emerald-200 bg-emerald-100 text-emerald-800",
      cardTone: "border-emerald-200/80 bg-[linear-gradient(180deg,rgba(236,253,245,0.96),rgba(255,255,255,0.98))]",
    };
  }
  if (mode === "mock_fallback") {
    return {
      label: "Mock fallback",
      tone: "border-amber-200 bg-amber-100 text-amber-800",
      cardTone: "border-amber-200/90 bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(255,255,255,0.98))]",
    };
  }
  return {
    label: "Mock preview",
    tone: "border-slate-200 bg-slate-100 text-slate-700",
    cardTone: "border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.98),rgba(255,255,255,0.98))]",
  };
}

function getIdentityTone(label: string | null | undefined) {
  if (label === "alto") {
    return "bg-emerald-100 text-emerald-800 border-emerald-200";
  }
  if (label === "medio") {
    return "bg-amber-100 text-amber-800 border-amber-200";
  }
  return "bg-slate-100 text-slate-700 border-slate-200";
}

function pickPrimaryPreview(project: Project): PreviewAsset | null {
  const previews = project.storyboard?.scenes
    .map((scene) => scene.previews.find((preview) => preview.id === scene.selected_preview_id) ?? scene.previews[0] ?? null)
    .filter((preview): preview is PreviewAsset => Boolean(preview));
  return previews?.[0] ?? null;
}

function formatBackendLabel(value: string | null | undefined) {
  if (!value) {
    return "n/a";
  }
  return value.replaceAll("_", " ");
}

function getVideoJobTone(status: string | null | undefined) {
  if (status === "done") {
    return "border-emerald-200 bg-emerald-100 text-emerald-800";
  }
  if (status === "fallback") {
    return "border-amber-200 bg-amber-100 text-amber-800";
  }
  if (status === "failed" || status === "expired") {
    return "border-red-200 bg-red-100 text-red-800";
  }
  return "border-ink/10 bg-paper text-ink/70";
}

export function ProjectDetail({ projectId }: Props) {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di caricamento.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, [projectId]);

  async function runAction(action: string, task: () => Promise<Project>) {
    setBusyAction(action);
    setError(null);
    try {
      const data = await task();
      setProject(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Azione non riuscita.");
    } finally {
      setBusyAction(null);
    }
  }

  if (loading) {
    return <div className="panel text-sm text-ink/60">Caricamento progetto...</div>;
  }

  if (!project) {
    return <div className="panel text-sm text-red-700">{error ?? "Progetto non trovato"}</div>;
  }

  const statusMeta = getStatusMeta(project.status);
  const leadPreview = pickPrimaryPreview(project);
  const identityScore = leadPreview?.identity_strength_score ?? 0;
  const identityLabel = leadPreview?.identity_strength_label ?? "basso";
  const identityReason =
    leadPreview?.identity_strength_reason ?? "Score non disponibile finche' non viene generata almeno una preview.";
  const previewModeMeta = getPreviewModeMeta(project.preview_generation_mode);
  const primaryImagePresent = Boolean(project.identity_pack?.primary_image);
  const referenceCount = project.identity_pack?.reference_images.length ?? 0;
  const selectedCount = project.storyboard?.scenes.filter((scene) => Boolean(scene.selected_preview_id)).length ?? 0;

  return (
    <div className="grid gap-6">
      <section className="panel overflow-hidden bg-[linear-gradient(135deg,rgba(14,27,45,0.98),rgba(49,92,132,0.9))] text-paper">
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="text-sm uppercase tracking-[0.22em] text-paper/60">Project Detail</p>
            <h1 className="mt-2 text-3xl font-semibold">{project.title}</h1>
            <p className="mt-3 max-w-3xl text-sm text-paper/80">{project.prompt}</p>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                className="btn-primary bg-paper text-ink hover:bg-paper/90"
                onClick={() => runAction("storyboard", () => generateStoryboard(projectId))}
                disabled={busyAction !== null}
              >
                {busyAction === "storyboard" ? "Generazione storyboard..." : "Genera storyboard"}
              </button>
              <button
                className="btn-secondary border-paper/20 bg-white/10 text-paper hover:border-paper hover:text-paper"
                onClick={() => runAction("previews", () => generatePreviews(projectId))}
                disabled={busyAction !== null || !project.storyboard}
              >
                {busyAction === "previews" ? "Generazione preview..." : "Genera preview"}
              </button>
              <button
                className="btn-secondary border-paper/20 bg-white/10 text-paper hover:border-paper hover:text-paper"
                onClick={() => runAction("render", () => renderProject(projectId))}
                disabled={busyAction !== null || !project.storyboard}
              >
                {busyAction === "render" ? "Render in corso..." : "Render finale"}
              </button>
              <button
                className="btn-secondary border-paper/20 bg-white/10 text-paper hover:border-paper hover:text-paper"
                onClick={() => runAction("video", () => generateProjectVideo(projectId))}
                disabled={busyAction !== null || !project.storyboard}
              >
                {busyAction === "video" ? "Generazione video..." : "Genera video reale"}
              </button>
              <Link href="/" className="btn-secondary border-paper/20 bg-white/10 text-paper hover:border-paper hover:text-paper">
                Torna alla dashboard
              </Link>
            </div>
          </div>

          <div className="grid gap-4 rounded-[28px] border border-paper/15 bg-white/8 p-5">
            <div className={`inline-flex w-fit rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${statusMeta.tone}`}>
              {statusMeta.label}
            </div>
            <p className="text-sm text-paper/80">{statusMeta.description}</p>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-paper/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-paper/82">
                Configured backend: {formatBackendLabel(project.preview_backend)}
              </span>
              <span className="rounded-full border border-paper/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-paper/82">
                Effective backend: {formatBackendLabel(project.preview_backend_effective)}
              </span>
              <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${previewModeMeta.tone}`}>
                {previewModeMeta.label}
              </span>
              <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${getVideoJobTone(project.video_job?.status)}`}>
                Video job: {project.video_job?.status ?? "idle"}
              </span>
            </div>
            <dl className="grid gap-3 text-sm text-paper/78">
              <div className="flex items-center justify-between gap-4 border-b border-paper/10 pb-2">
                <dt>Stile</dt>
                <dd>{project.style}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-b border-paper/10 pb-2">
                <dt>Formato</dt>
                <dd>{project.aspect_ratio}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-b border-paper/10 pb-2">
                <dt>Durata target</dt>
                <dd>{project.duration_target}s</dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-b border-paper/10 pb-2">
                <dt>Preview selezionate</dt>
                <dd>{selectedCount}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Ultimo modello</dt>
                <dd>{project.preview_model_name ?? "n/a"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-t border-paper/10 pt-2">
                <dt>Video backend</dt>
                <dd>{formatBackendLabel(project.video_backend_effective)}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Video model</dt>
                <dd>{project.video_model_name ?? "n/a"}</dd>
              </div>
            </dl>
            {project.preview_backend_message ? (
              <div className="rounded-[20px] border border-amber-300/35 bg-amber-100/90 px-4 py-3 text-sm text-amber-950">
                {project.preview_backend_message}
              </div>
            ) : null}
            {project.video_backend_message ? (
              <div className="rounded-[20px] border border-amber-300/35 bg-amber-100/90 px-4 py-3 text-sm text-amber-950">
                {project.video_backend_message}
              </div>
            ) : null}
          </div>
        </div>

        {error ? (
          <div className="mt-5 whitespace-pre-wrap rounded-[20px] border border-red-300/35 bg-red-100/90 px-4 py-3 text-sm text-red-900">
            {error}
          </div>
        ) : null}
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <article className="panel">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Identity pack</h2>
              <p className="mt-1 text-sm text-ink/60">Asset locali del personaggio, note e lock di coerenza.</p>
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${project.identity_pack?.lock_identity ? "border-ink/20 bg-ink text-paper" : "border-ink/10 bg-paper text-ink/65"}`}>
              {project.identity_pack?.lock_identity ? "Identity locked" : "Identity flessibile"}
            </span>
          </div>

          {project.identity_pack?.primary_image ? (
            <div className="overflow-hidden rounded-[24px] border border-ink/10 bg-paper/50">
              <img
                src={resolveAssetUrl(project.identity_pack.primary_image.resolved_url ?? project.identity_pack.primary_image.url)}
                alt="Avatar principale"
                className="aspect-[4/3] w-full object-cover"
              />
            </div>
          ) : (
            <div className="rounded-[24px] border border-dashed border-ink/15 bg-paper/50 p-6 text-sm text-ink/55">
              Nessuna immagine principale caricata.
            </div>
          )}

          <div className="mt-5">
            <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Character bible</p>
            <p className="mt-2 text-sm leading-6 text-ink/72">
              {project.identity_pack?.character_notes || "Nessuna nota personaggio salvata."}
            </p>
          </div>

          <div className="mt-5 grid gap-4">
            <div className="rounded-[22px] border border-ink/10 bg-white p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Identity strength</p>
                  <p className="mt-1 text-sm text-ink/70">{identityReason}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-ink">{identityScore}%</p>
                  <span className={`mt-1 inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${getIdentityTone(identityLabel)}`}>
                    {identityLabel}
                  </span>
                </div>
              </div>
              <div className="mt-3 h-2 rounded-full bg-ink/8">
                <div className="h-2 rounded-full bg-[linear-gradient(90deg,#1e293b,#ef8d32)]" style={{ width: `${identityScore}%` }} />
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-wide">
                <span className={`rounded-full px-3 py-1 ${primaryImagePresent ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"}`}>
                  {primaryImagePresent ? "Primary image presente" : "Primary image assente"}
                </span>
                <span className="rounded-full bg-white px-3 py-1 text-ink/65">{referenceCount} reference</span>
                <span className={`rounded-full px-3 py-1 ${project.identity_pack?.lock_identity ? "bg-ink text-paper" : "bg-slate-100 text-slate-700"}`}>
                  {project.identity_pack?.lock_identity ? "Lock identity on" : "Lock identity off"}
                </span>
              </div>
            </div>

            <div className="rounded-[22px] border border-ink/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(244,247,251,0.98))] p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Preview engine status</p>
                  <p className="mt-1 text-sm text-ink/68">
                    Trasparenza sul backend configurato, quello effettivo e l&apos;ultimo esito di generazione.
                  </p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${previewModeMeta.tone}`}>
                  {previewModeMeta.label}
                </span>
              </div>
              <div className="mt-4 grid gap-2 text-sm text-ink/72">
                <div className="flex items-center justify-between gap-4">
                  <span>Configured</span>
                  <span>{formatBackendLabel(project.preview_backend)}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Effettivo</span>
                  <span>{formatBackendLabel(project.preview_backend_effective)}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Model</span>
                  <span>{project.preview_model_name ?? "n/a"}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Ultima generazione</span>
                  <span>{project.preview_last_generated_at ? new Date(project.preview_last_generated_at).toLocaleString("it-IT") : "n/a"}</span>
                </div>
              </div>
              {project.preview_generation_mode === "mock_fallback" ? (
                <div className="mt-4 rounded-[18px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  Il backend reale non ha completato la richiesta. Le preview restano disponibili tramite fallback mock.
                </div>
              ) : null}
            </div>

            <div className="rounded-[22px] border border-ink/10 bg-white p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Video generation</p>
                  <p className="mt-1 text-sm text-ink/68">Stato reale del provider video e fallback eventuale.</p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${getVideoJobTone(project.video_job?.status)}`}>
                  {project.video_job?.status ?? "idle"}
                </span>
              </div>
              <div className="mt-4 grid gap-2 text-sm text-ink/72">
                <div className="flex items-center justify-between gap-4">
                  <span>Configured</span>
                  <span>{formatBackendLabel(project.video_backend)}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Effettivo</span>
                  <span>{formatBackendLabel(project.video_backend_effective)}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Mode</span>
                  <span>{formatBackendLabel(project.video_generation_mode)}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Model</span>
                  <span>{project.video_model_name ?? "n/a"}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span>Ultima generazione</span>
                  <span>{project.video_last_generated_at ? new Date(project.video_last_generated_at).toLocaleString("it-IT") : "n/a"}</span>
                </div>
              </div>
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Reference images</p>
                <span className="text-xs text-ink/45">{project.identity_pack?.reference_images.length ?? 0}/8</span>
              </div>
              {project.identity_pack?.reference_images.length ? (
                <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                  {project.identity_pack.reference_images.map((asset) => (
                    <a
                      key={asset.id}
                      href={resolveAssetUrl(asset.resolved_url ?? asset.url)}
                      target="_blank"
                      rel="noreferrer"
                      className="overflow-hidden rounded-[20px] border border-ink/10 bg-white transition hover:border-accent/60"
                    >
                      <img src={resolveAssetUrl(asset.resolved_url ?? asset.url)} alt={asset.file_name} className="aspect-square w-full object-cover" />
                    </a>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink/55">Nessuna reference caricata.</p>
              )}
            </div>
          </div>
        </article>

        <article className="panel">
          <h2 className="text-xl font-semibold">Storyboard</h2>
          {project.storyboard ? (
            <div className="mt-4 grid gap-4 text-sm text-ink/75">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Titolo raffinato</p>
                <p className="mt-1 text-lg font-semibold text-ink">{project.storyboard.refined_title}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Overview</p>
                <p className="mt-1">{project.storyboard.overview}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Script</p>
                <p className="mt-1">{project.storyboard.script}</p>
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-ink/60">Genera lo storyboard per creare scene, script e beat del video.</p>
          )}
        </article>
      </section>

      <section className="panel">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Scene e preview</h2>
            <p className="mt-1 text-sm text-ink/60">Ogni scena mostra varianti, stato backend e note di coerenza leggibili.</p>
          </div>
          <span className="text-sm text-ink/55">{project.storyboard?.scenes.length ?? 0} scene</span>
        </div>

        <div className="grid gap-4">
          {project.storyboard?.scenes.map((scene) => {
            const sceneBusy = busyAction === `regenerate-${scene.id}`;
            const sceneVideoBusy = busyAction === `scene-video-${scene.id}`;
            return (
              <div key={scene.id} className="rounded-[26px] border border-ink/10 bg-paper/50 p-5">
                <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-semibold">{scene.title}</h3>
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/55">
                        {scene.beat}
                      </span>
                      {scene.selected_preview_id ? (
                        <span className="rounded-full bg-accent/15 px-3 py-1 text-xs font-semibold text-accent">
                          Preview selezionata
                        </span>
                      ) : null}
                      <span className="rounded-full border border-ink/10 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/55">
                        Rev {scene.preview_revision || 0}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-ink/75">{scene.visual_prompt}</p>
                    <p className="mt-2 text-sm text-ink/60">{scene.voiceover}</p>
                    {scene.preview_history_note ? (
                      <p className="mt-2 text-xs text-ink/52">{scene.preview_history_note}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-ink/10 bg-white px-3 py-1 text-xs font-semibold text-ink/70">
                      {scene.duration_seconds}s
                    </span>
                    <button
                      className="btn-secondary"
                      onClick={() => runAction(`regenerate-${scene.id}`, () => regenerateScenePreviews(projectId, scene.id))}
                      disabled={busyAction !== null}
                    >
                      {sceneBusy ? "Rigenerazione scena in corso..." : "Rigenera solo questa scena"}
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => runAction(`scene-video-${scene.id}`, () => generateSceneVideo(projectId, scene.id))}
                      disabled={busyAction !== null}
                    >
                      {sceneVideoBusy ? "Generazione clip..." : "Genera clip scena"}
                    </button>
                  </div>
                </div>

                {sceneBusy ? (
                  <div className="mb-4 rounded-[18px] border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
                    Sto rigenerando solo questa scena. Le altre preview restano invariate.
                  </div>
                ) : null}

                {scene.generated_video ? (
                  <div className="mb-4 rounded-[22px] border border-ink/10 bg-white p-4">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${getVideoJobTone(project.video_job?.target_id === scene.id ? project.video_job?.status : scene.generated_video.video_generation_mode === "mock_fallback" ? "fallback" : "done")}`}>
                        {scene.generated_video.video_generation_mode === "real" ? "xAI reale" : scene.generated_video.video_generation_mode === "mock_fallback" ? "Mock fallback" : "Mock"}
                      </span>
                      <span className="rounded-full border border-ink/10 bg-paper px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/60">
                        {formatBackendLabel(scene.generated_video.video_backend)}
                      </span>
                      <span className="rounded-full border border-ink/10 bg-paper px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/60">
                        {formatBackendLabel(scene.generated_video.source_mode)}
                      </span>
                    </div>
                    <video
                      controls
                      className="aspect-video w-full rounded-[18px] border border-ink/10 bg-ink/95"
                      src={resolveAssetUrl(scene.generated_video.resolved_url ?? scene.generated_video.url)}
                    />
                    <div className="mt-3 grid gap-2 text-xs text-ink/65 md:grid-cols-3">
                      <p>Provider: {scene.generated_video.video_backend}</p>
                      <p>Model: {scene.generated_video.provider_model_name ?? "n/a"}</p>
                      <p>Status: {scene.generated_video.provider_status ?? "n/a"}</p>
                      <p>Durata: {scene.generated_video.duration_seconds ?? "n/a"}s</p>
                      <p>Aspect ratio: {scene.generated_video.aspect_ratio ?? "n/a"}</p>
                      <p>Resolution: {scene.generated_video.resolution ?? "n/a"}</p>
                    </div>
                    {scene.generated_video.fallback_message ? (
                      <div className="mt-3 rounded-[18px] border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                        Fallback: {scene.generated_video.fallback_message}
                      </div>
                    ) : null}
                  </div>
                ) : null}

                {scene.previews.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {scene.previews.map((preview) => {
                      const isSelected = scene.selected_preview_id === preview.id;
                      const modeMeta = getPreviewModeMeta(preview.generation_mode);
                      return (
                        <div
                          key={preview.id}
                          className={`overflow-hidden rounded-[22px] border bg-white transition ${modeMeta.cardTone} ${isSelected ? "shadow-[0_0_0_3px_rgba(239,141,50,0.18)]" : ""}`}
                        >
                          <img
                            src={resolveAssetUrl(preview.resolved_url ?? preview.url)}
                            alt={`Preview ${preview.variant_index} - ${scene.title}`}
                            className={`aspect-[4/3] w-full border-b object-cover ${preview.generation_mode === "real" ? "border-emerald-200/60 bg-emerald-50" : preview.generation_mode === "mock_fallback" ? "border-amber-200/70 bg-amber-50" : "border-slate-200 bg-paper"}`}
                          />
                          <div className="grid gap-3 p-4">
                            <div>
                              <div className="flex flex-wrap items-center gap-2">
                                <p className="text-sm font-semibold text-ink">Variante {preview.variant_index}</p>
                                <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${modeMeta.tone}`}>
                                  {modeMeta.label}
                                </span>
                                <span className="rounded-full border border-ink/10 bg-paper px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-ink/60">
                                  {formatBackendLabel(preview.generation_backend)}
                                </span>
                                {preview.identity_strength_label ? (
                                  <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${getIdentityTone(preview.identity_strength_label)}`}>
                                    Identity {preview.identity_strength_label}
                                  </span>
                                ) : null}
                              </div>
                              <p className="mt-1 line-clamp-4 text-xs text-ink/60">{preview.positive_prompt ?? preview.source_prompt ?? preview.prompt}</p>
                            </div>

                            <div className="grid gap-2 rounded-[18px] border border-ink/10 bg-paper/60 p-3 text-xs text-ink/62">
                              <div className="flex items-center justify-between gap-3">
                                <span>Configured</span>
                                <span>{formatBackendLabel(preview.configured_backend)}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3">
                                <span>Model</span>
                                <span>{preview.model_name ?? "n/a"}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3">
                                <span>Seed</span>
                                <span>{preview.seed ?? "n/a"}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3">
                                <span>Retry</span>
                                <span>{preview.retry_count}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3">
                                <span>Durata</span>
                                <span>{preview.generation_duration_ms ? `${preview.generation_duration_ms} ms` : "n/a"}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3">
                                <span>Status</span>
                                <span>{preview.status}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3">
                                <span>Creata</span>
                                <span>{new Date(preview.created_at).toLocaleString("it-IT")}</span>
                              </div>
                            </div>

                            <div className="grid gap-2 rounded-[18px] border border-ink/10 bg-white p-3 text-xs text-ink/60">
                              <p className="font-semibold text-ink">Coerenza e regia</p>
                              <p className="line-clamp-2">{preview.consistency_notes ?? "Nessuna nota di coerenza."}</p>
                              <p className="line-clamp-2">{preview.camera_notes ?? "Nessuna nota camera."}</p>
                              <p className="line-clamp-2">{preview.lighting_notes ?? "Nessuna nota lighting."}</p>
                              <p className="line-clamp-2">{preview.wardrobe_notes ?? "Nessuna nota wardrobe."}</p>
                            </div>

                            {preview.fallback_reason ? (
                              <div className="rounded-[18px] border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                                Fallback: {preview.fallback_reason}
                              </div>
                            ) : null}

                            <button
                              className={isSelected ? "btn-primary" : "btn-secondary"}
                              onClick={() =>
                                runAction(`select-${scene.id}-${preview.id}`, () =>
                                  selectScene(projectId, scene.id, preview.id),
                                )
                              }
                              disabled={busyAction !== null}
                            >
                              {busyAction === `select-${scene.id}-${preview.id}`
                                ? "Selezione..."
                                : isSelected
                                  ? "Preview attiva"
                                  : "Usa questa preview"}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-ink/55">Nessuna preview ancora generata.</p>
                )}
              </div>
            );
          })}

          {!project.storyboard?.scenes.length ? (
            <div className="rounded-[24px] border border-dashed border-ink/15 bg-paper/50 p-6 text-sm text-ink/55">
              Nessuna scena disponibile finche' non generi lo storyboard.
            </div>
          ) : null}
        </div>
      </section>

      <section className="panel">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold">Video clip progetto</h2>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${getVideoJobTone(project.video_job?.target_type === "project" ? project.video_job?.status : project.project_video?.video_generation_mode === "mock_fallback" ? "fallback" : project.project_video ? "done" : "idle")}`}>
            {project.video_job?.target_type === "project" ? project.video_job?.status ?? "idle" : project.project_video ? "done" : "idle"}
          </span>
        </div>

        {project.project_video ? (
          <div className="grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
            <video
              controls
              className="aspect-video w-full rounded-[24px] border border-ink/10 bg-ink/95"
              src={resolveAssetUrl(project.project_video.resolved_url ?? project.project_video.url)}
            />
            <div className="rounded-[22px] border border-ink/10 bg-white p-4 text-sm text-ink/70">
              <p className="font-semibold text-ink">{project.project_video.summary}</p>
              <div className="mt-3 grid gap-2">
                <p>Provider: {project.project_video.video_backend}</p>
                <p>Model: {project.project_video.provider_model_name ?? "n/a"}</p>
                <p>Mode: {formatBackendLabel(project.project_video.source_mode)}</p>
                <p>Durata: {project.project_video.duration_seconds ?? "n/a"}s</p>
                <p>Aspect ratio: {project.project_video.aspect_ratio ?? "n/a"}</p>
                <p>Resolution: {project.project_video.resolution ?? "n/a"}</p>
                <p>Identity mode: {formatBackendLabel(project.project_video.identity_mode)}</p>
              </div>
              {project.project_video.fallback_message ? (
                <div className="mt-4 rounded-[18px] border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                  Fallback: {project.project_video.fallback_message}
                </div>
              ) : null}
            </div>
          </div>
        ) : (
          <p className="text-sm text-ink/60">Genera un video progetto per salvare un clip mp4 nel nostro storage locale o S3.</p>
        )}
      </section>

      <section className="panel">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold">Render status e output</h2>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${project.render_job?.status === "completed" ? "border-emerald-200 bg-emerald-100 text-emerald-800" : "border-ink/10 bg-paper text-ink/70"}`}>
            {project.render_job?.status ?? "idle"}
          </span>
        </div>

        {project.render_job ? (
          <div className="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-[22px] border border-ink/10 bg-paper/50 p-4">
              <p className="text-sm font-semibold">Log essenziali</p>
              <ul className="mt-3 grid gap-2 text-sm text-ink/70">
                {project.render_job.logs.map((log) => (
                  <li key={log}>{log}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-[22px] border border-ink/10 bg-white p-4">
              <p className="text-sm font-semibold">Output disponibili</p>
              <div className="mt-3 grid gap-3">
                {project.outputs.length === 0 ? (
                  <p className="text-sm text-ink/55">Nessun output ancora disponibile.</p>
                ) : (
                  project.outputs.map((output) => (
                    <a
                      key={output.id}
                      href={resolveAssetUrl(output.resolved_url ?? output.url)}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-[18px] border border-ink/10 bg-paper/50 p-4 transition hover:border-accent/60"
                    >
                      <p className="font-semibold">{output.file_name}</p>
                      <p className="mt-1 text-sm text-ink/65">{output.summary}</p>
                    </a>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-ink/60">Lancia il render finale per generare output scaricabili.</p>
        )}
      </section>
    </div>
  );
}
