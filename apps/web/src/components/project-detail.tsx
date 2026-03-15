"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { generatePreviews, generateStoryboard, getProject, renderProject, selectScene } from "@/lib/api";
import { Project } from "@/types/project";

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
    description: "Le varianti mock sono state generate per le scene.",
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
};

function getStatusMeta(status: string) {
  return STATUS_META[status] ?? {
    label: status,
    tone: "bg-slate-100 text-slate-700 border-slate-200",
    description: "Stato non classificato.",
  };
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
              <div className="flex items-center justify-between gap-4">
                <dt>Preview selezionate</dt>
                <dd>{project.storyboard?.scenes.filter((scene) => Boolean(scene.selected_preview_id)).length ?? 0}</dd>
              </div>
            </dl>
          </div>
        </div>

        {error ? (
          <div className="mt-5 rounded-[20px] border border-red-300/35 bg-red-100/90 px-4 py-3 text-sm text-red-900 whitespace-pre-wrap">
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

          <div className="mt-5">
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
            <p className="mt-1 text-sm text-ink/60">Ogni scena mostra tutte le varianti generate e la preview scelta esplicitamente.</p>
          </div>
          <span className="text-sm text-ink/55">{project.storyboard?.scenes.length ?? 0} scene</span>
        </div>

        <div className="grid gap-4">
          {project.storyboard?.scenes.map((scene) => (
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
                  </div>
                  <p className="mt-2 text-sm text-ink/75">{scene.visual_prompt}</p>
                  <p className="mt-2 text-sm text-ink/60">{scene.voiceover}</p>
                </div>
                <span className="rounded-full border border-ink/10 bg-white px-3 py-1 text-xs font-semibold text-ink/70">
                  {scene.duration_seconds}s
                </span>
              </div>

              {scene.previews.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {scene.previews.map((preview, index) => {
                    const isSelected = scene.selected_preview_id === preview.id;
                    return (
                      <div
                        key={preview.id}
                        className={`overflow-hidden rounded-[22px] border bg-white transition ${isSelected ? "border-accent shadow-[0_0_0_3px_rgba(239,141,50,0.18)]" : "border-ink/10"}`}
                      >
                        <img
                          src={resolveAssetUrl(preview.resolved_url ?? preview.url)}
                          alt={`Preview ${index + 1} - ${scene.title}`}
                          className="aspect-[4/3] w-full border-b border-ink/10 bg-paper object-cover"
                        />
                        <div className="grid gap-3 p-4">
                          <div>
                            <p className="text-sm font-semibold text-ink">Variante {index + 1}</p>
                            <p className="mt-1 line-clamp-3 text-xs text-ink/60">{preview.prompt}</p>
                          </div>
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
          ))}

          {!project.storyboard?.scenes.length ? (
            <div className="rounded-[24px] border border-dashed border-ink/15 bg-paper/50 p-6 text-sm text-ink/55">
              Nessuna scena disponibile finche' non generi lo storyboard.
            </div>
          ) : null}
        </div>
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
