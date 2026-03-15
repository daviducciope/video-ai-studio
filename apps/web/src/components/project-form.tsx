"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useMemo, useState } from "react";

import { createProject, uploadProjectAssets } from "@/lib/api";

type FormErrors = Partial<Record<"title" | "prompt" | "duration_target" | "primary_image" | "reference_images", string>>;

const TITLE_MIN_LENGTH = 5;
const PROMPT_MIN_LENGTH = 20;
const DURATION_MIN = 15;
const DURATION_MAX = 300;
const MAX_REFERENCE_IMAGES = 8;

function formatFileList(files: File[]) {
  if (files.length === 0) {
    return "Nessun file selezionato";
  }
  return files.map((file) => file.name).join(", ");
}

export function ProjectForm() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [primaryImage, setPrimaryImage] = useState<File | null>(null);
  const [referenceImages, setReferenceImages] = useState<File[]>([]);

  const primaryImageLabel = useMemo(() => formatFileList(primaryImage ? [primaryImage] : []), [primaryImage]);
  const referenceImagesLabel = useMemo(() => formatFileList(referenceImages), [referenceImages]);

  function validate(formData: FormData): FormErrors {
    const nextErrors: FormErrors = {};
    const title = String(formData.get("title") ?? "").trim();
    const prompt = String(formData.get("prompt") ?? "").trim();
    const durationTarget = Number(formData.get("duration_target") ?? "0");

    if (title.length < TITLE_MIN_LENGTH) {
      nextErrors.title = `Inserisci un titolo di almeno ${TITLE_MIN_LENGTH} caratteri.`;
    }
    if (prompt.length < PROMPT_MIN_LENGTH) {
      nextErrors.prompt = `Descrivi meglio il video: servono almeno ${PROMPT_MIN_LENGTH} caratteri.`;
    }
    if (!Number.isFinite(durationTarget) || durationTarget < DURATION_MIN || durationTarget > DURATION_MAX) {
      nextErrors.duration_target = `La durata deve essere compresa tra ${DURATION_MIN} e ${DURATION_MAX} secondi.`;
    }
    if (referenceImages.length > MAX_REFERENCE_IMAGES) {
      nextErrors.reference_images = `Puoi caricare al massimo ${MAX_REFERENCE_IMAGES} immagini reference.`;
    }
    if (primaryImage && !primaryImage.type.startsWith("image/")) {
      nextErrors.primary_image = "L'immagine principale deve essere un file immagine valido.";
    }
    return nextErrors;
  }

  function handlePrimaryImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setPrimaryImage(file);
    setFieldErrors((current) => ({ ...current, primary_image: undefined }));
  }

  function handleReferenceImagesChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    setReferenceImages(files);
    setFieldErrors((current) => ({ ...current, reference_images: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(event.currentTarget);
    const nextErrors = validate(formData);
    setFieldErrors(nextErrors);

    if (Object.values(nextErrors).some(Boolean)) {
      setError("Controlla i campi evidenziati prima di continuare.");
      setSubmitting(false);
      return;
    }

    try {
      let project = await createProject({
        title: String(formData.get("title") ?? "").trim(),
        prompt: String(formData.get("prompt") ?? "").trim(),
        style: String(formData.get("style") ?? "").trim(),
        duration_target: Number(formData.get("duration_target") ?? "45"),
        aspect_ratio: String(formData.get("aspect_ratio") ?? "16:9") as "9:16" | "16:9",
        avatar_notes: String(formData.get("character_notes") ?? "").trim(),
        character_notes: String(formData.get("character_notes") ?? "").trim(),
        lock_identity: formData.get("lock_identity") === "on",
      });

      if (primaryImage) {
        project = await uploadProjectAssets(project.id, "primary", [primaryImage]);
      }
      if (referenceImages.length > 0) {
        project = await uploadProjectAssets(project.id, "reference", referenceImages);
      }

      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore durante la creazione del progetto.");
    } finally {
      setSubmitting(false);
    }
  }

  function fieldClass(name: keyof FormErrors) {
    return fieldErrors[name] ? "field border-red-300 focus:border-red-500" : "field";
  }

  return (
    <form className="panel grid gap-7" onSubmit={handleSubmit}>
      <div>
        <h1 className="text-3xl font-semibold">Nuovo progetto</h1>
        <p className="mt-2 max-w-3xl text-sm text-ink/65">
          Inserisci un brief chiaro e, se vuoi, aggancia un identity pack locale per mantenere il personaggio coerente lungo storyboard, preview e render mock.
        </p>
      </div>

      {error ? (
        <div className="rounded-[22px] border border-red-200 bg-red-50 px-4 py-3 text-sm whitespace-pre-wrap text-red-800">
          {error}
        </div>
      ) : null}

      <section className="grid gap-5">
        <div>
          <h2 className="text-lg font-semibold">Brief progetto</h2>
          <p className="mt-1 text-sm text-ink/60">Validazione locale minima prima della chiamata API.</p>
        </div>

        <label className="grid gap-2 text-sm font-medium">
          Titolo
          <input className={fieldClass("title")} name="title" placeholder="Campagna teaser prodotto AI" required />
          {fieldErrors.title ? <span className="text-xs text-red-700">{fieldErrors.title}</span> : null}
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Prompt
          <textarea
            className={`${fieldClass("prompt")} min-h-32`}
            name="prompt"
            placeholder="Descrivi il video, il tono, il target e l'obiettivo narrativo"
            required
          />
          {fieldErrors.prompt ? <span className="text-xs text-red-700">{fieldErrors.prompt}</span> : null}
        </label>

        <div className="grid gap-5 md:grid-cols-3">
          <label className="grid gap-2 text-sm font-medium">
            Stile
            <input className="field" name="style" defaultValue="cinematic" required />
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Durata target
            <input className={fieldClass("duration_target")} name="duration_target" type="number" defaultValue={45} min={DURATION_MIN} max={DURATION_MAX} required />
            {fieldErrors.duration_target ? <span className="text-xs text-red-700">{fieldErrors.duration_target}</span> : null}
          </label>

          <label className="grid gap-2 text-sm font-medium">
            Formato
            <select className="field" name="aspect_ratio" defaultValue="16:9">
              <option value="16:9">16:9</option>
              <option value="9:16">9:16</option>
            </select>
          </label>
        </div>
      </section>

      <section className="grid gap-5 rounded-[28px] border border-ink/10 bg-paper/55 p-5">
        <div>
          <h2 className="text-lg font-semibold">Avatar / Personaggio</h2>
          <p className="mt-1 text-sm text-ink/60">
            Upload locale di una hero image opzionale e fino a otto reference per tenere coerente il personaggio.
          </p>
        </div>

        <label className="grid gap-2 text-sm font-medium">
          Immagine principale
          <input className="field file:mr-4 file:rounded-full file:border-0 file:bg-ink file:px-4 file:py-2 file:text-paper" name="primary_image" type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={handlePrimaryImageChange} />
          <span className="text-xs text-ink/55">{primaryImageLabel}</span>
          {fieldErrors.primary_image ? <span className="text-xs text-red-700">{fieldErrors.primary_image}</span> : null}
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Immagini reference
          <input className="field file:mr-4 file:rounded-full file:border-0 file:bg-ink file:px-4 file:py-2 file:text-paper" name="reference_images" type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple onChange={handleReferenceImagesChange} />
          <span className="text-xs text-ink/55">{referenceImagesLabel}</span>
          {fieldErrors.reference_images ? <span className="text-xs text-red-700">{fieldErrors.reference_images}</span> : null}
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Character bible / note personaggio
          <textarea className="field min-h-28" name="character_notes" placeholder="Tratti fisici, età percepita, mood, palette, vincoli di styling, dettagli da mantenere coerenti." />
        </label>

        <label className="flex items-center gap-3 rounded-[20px] border border-ink/10 bg-white/80 px-4 py-3 text-sm font-medium text-ink">
          <input className="h-4 w-4" name="lock_identity" type="checkbox" />
          Blocca identita' personaggio
        </label>
      </section>

      <div className="flex items-center justify-end gap-3">
        <button className="btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Creazione..." : "Crea progetto"}
        </button>
      </div>
    </form>
  );
}
