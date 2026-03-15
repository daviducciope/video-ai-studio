"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createProject } from "@/lib/api";

export function ProjectForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(event.currentTarget);
    try {
      const project = await createProject({
        title: String(formData.get("title") ?? ""),
        prompt: String(formData.get("prompt") ?? ""),
        style: String(formData.get("style") ?? ""),
        duration_target: Number(formData.get("duration_target") ?? "45"),
        aspect_ratio: String(formData.get("aspect_ratio") ?? "16:9") as "9:16" | "16:9",
        avatar_notes: String(formData.get("avatar_notes") ?? ""),
      });
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore durante la creazione");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="panel grid gap-5" onSubmit={handleSubmit}>
      <div>
        <h1 className="text-3xl font-semibold">Nuovo progetto</h1>
        <p className="mt-2 text-sm text-ink/65">
          Inserisci i dati essenziali. Il workflow creativo parte dal prompt ma resta controllabile.
        </p>
      </div>

      <label className="grid gap-2 text-sm font-medium">
        Titolo
        <input className="field" name="title" placeholder="Campagna teaser prodotto AI" required />
      </label>

      <label className="grid gap-2 text-sm font-medium">
        Prompt
        <textarea
          className="field min-h-32"
          name="prompt"
          placeholder="Descrivi il video, il tono e l'obiettivo narrativo"
          required
        />
      </label>

      <div className="grid gap-5 md:grid-cols-3">
        <label className="grid gap-2 text-sm font-medium">
          Stile
          <input className="field" name="style" defaultValue="cinematic" required />
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Durata target
          <input className="field" name="duration_target" type="number" defaultValue={45} min={15} max={300} required />
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Formato
          <select className="field" name="aspect_ratio" defaultValue="16:9">
            <option value="16:9">16:9</option>
            <option value="9:16">9:16</option>
          </select>
        </label>
      </div>

      <label className="grid gap-2 text-sm font-medium">
        Note avatar / personaggio
        <textarea className="field min-h-24" name="avatar_notes" placeholder="Dettagli opzionali sul volto o sul personaggio" />
      </label>

      {error ? <p className="text-sm text-red-700">{error}</p> : null}

      <div className="flex items-center justify-end gap-3">
        <button className="btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Creazione..." : "Crea progetto"}
        </button>
      </div>
    </form>
  );
}
