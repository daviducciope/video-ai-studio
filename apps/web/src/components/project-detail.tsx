"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { generatePreviews, generateStoryboard, getProject, renderProject, selectScene } from "@/lib/api";
import { Project } from "@/types/project";

type Props = {
  projectId: string;
};

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
      setError(err instanceof Error ? err.message : "Errore di caricamento");
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
      setError(err instanceof Error ? err.message : "Azione non riuscita");
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

  return (
    <div className="grid gap-6">
      <section className="panel">
        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.22em] text-ink/45">Project Detail</p>
            <h1 className="mt-2 text-3xl font-semibold">{project.title}</h1>
            <p className="mt-3 max-w-3xl text-sm text-ink/70">{project.prompt}</p>
          </div>
          <div className="rounded-[22px] bg-paper px-4 py-3 text-sm text-ink/80">
            <div>{project.style}</div>
            <div>{project.aspect_ratio}</div>
            <div>{project.duration_target}s</div>
            <div className="font-semibold text-accent">{project.status}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            className="btn-primary"
            onClick={() => runAction("storyboard", () => generateStoryboard(projectId))}
            disabled={busyAction !== null}
          >
            {busyAction === "storyboard" ? "Generazione storyboard..." : "Genera storyboard"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => runAction("previews", () => generatePreviews(projectId))}
            disabled={busyAction !== null || !project.storyboard}
          >
            {busyAction === "previews" ? "Generazione preview..." : "Genera preview"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => runAction("render", () => renderProject(projectId))}
            disabled={busyAction !== null || !project.storyboard}
          >
            {busyAction === "render" ? "Render in corso..." : "Render finale"}
          </button>
          <Link href="/" className="btn-secondary">
            Torna alla dashboard
          </Link>
        </div>

        {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
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
            <p className="mt-4 text-sm text-ink/60">Genera lo storyboard per creare scene e script.</p>
          )}
        </article>

        <article className="panel">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-xl font-semibold">Scene e preview</h2>
            <span className="text-sm text-ink/55">{project.storyboard?.scenes.length ?? 0} scene</span>
          </div>

          <div className="grid gap-4">
            {project.storyboard?.scenes.map((scene) => (
              <div key={scene.id} className="rounded-[24px] border border-ink/10 bg-paper/50 p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold">{scene.title}</h3>
                    <p className="text-xs uppercase tracking-[0.18em] text-ink/45">{scene.beat}</p>
                  </div>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-ink/70">
                    {scene.duration_seconds}s
                  </span>
                </div>

                <p className="mb-2 text-sm text-ink/75">{scene.visual_prompt}</p>
                <p className="mb-4 text-sm text-ink/60">{scene.voiceover}</p>

                {scene.previews.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${scene.previews[0].url}`}
                      alt={`Preview ${scene.title}`}
                      className="w-full rounded-[20px] border border-ink/10 bg-white"
                    />
                    <button
                      className={scene.selected ? "btn-primary" : "btn-secondary"}
                      onClick={() =>
                        runAction(`select-${scene.id}`, () =>
                          selectScene(projectId, scene.id, scene.previews[0]?.id),
                        )
                      }
                      disabled={busyAction !== null}
                    >
                      {busyAction === `select-${scene.id}`
                        ? "Selezione..."
                        : scene.selected
                          ? "Selezionata"
                          : "Seleziona scena"}
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-ink/55">Nessuna preview ancora generata.</p>
                )}
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold">Render status e output</h2>
          <span className="rounded-full bg-paper px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/70">
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
                      href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${output.url}`}
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
