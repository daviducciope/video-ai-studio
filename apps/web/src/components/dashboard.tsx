"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listProjects } from "@/lib/api";
import { Project } from "@/types/project";

export function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listProjects()
      .then(setProjects)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="grid gap-6">
      <section className="panel overflow-hidden bg-[linear-gradient(135deg,rgba(16,32,51,0.96),rgba(43,76,109,0.92))] text-paper">
        <div className="grid gap-4 md:grid-cols-[1.6fr_0.8fr]">
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.24em] text-paper/70">MVP locale</p>
            <h1 className="max-w-2xl text-4xl font-semibold leading-tight">
              Workflow reale per passare da prompt a storyboard, preview e render finale.
            </h1>
            <p className="max-w-2xl text-sm text-paper/78">
              Backend FastAPI, dashboard Next.js e pipeline mock pronta per evolvere verso
              ComfyUI, ffmpeg e AWS.
            </p>
          </div>
          <div className="grid gap-3 rounded-[24px] border border-paper/15 bg-white/8 p-4 text-sm">
            <div>
              <span className="block text-paper/60">Progetti</span>
              <span className="text-3xl font-semibold">{projects.length}</span>
            </div>
            <div>
              <span className="block text-paper/60">Stato</span>
              <span className="text-lg font-medium">CLI-first, UI-friendly</span>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Progetti recenti</h2>
            <p className="text-sm text-ink/65">Crea un progetto e poi genera storyboard, preview e render.</p>
          </div>
          <Link href="/projects/new" className="btn-primary">
            Crea progetto
          </Link>
        </div>

        {loading ? <p className="text-sm text-ink/60">Caricamento progetti...</p> : null}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}

        {!loading && !error && projects.length === 0 ? (
          <div className="rounded-[24px] border border-dashed border-ink/15 bg-paper/60 p-8 text-sm text-ink/70">
            Nessun progetto presente. Usa "Nuovo progetto" per iniziare il workflow.
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="rounded-[24px] border border-ink/10 bg-white p-5 transition hover:-translate-y-0.5 hover:border-accent/60">
              <div className="mb-3 flex items-center justify-between gap-4">
                <h3 className="text-lg font-semibold">{project.title}</h3>
                <span className="rounded-full bg-paper px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink/70">
                  {project.status}
                </span>
              </div>
              <p className="mb-4 text-sm text-ink/70">{project.prompt}</p>
              <div className="flex gap-3 text-xs text-ink/55">
                <span>{project.style}</span>
                <span>{project.aspect_ratio}</span>
                <span>{project.duration_target}s</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
