# Video AI Studio

MVP locale avanzato per creare progetti video AI con workflow completo: progetto, identity pack locale, storyboard, preview mock multi-variante, selezione esplicita preview e render finale dimostrabile.

## Stack

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic
- Worker: Python separato con pipeline mock sostituibile
- Persistenza: file JSON strutturati in `data/`
- Storage asset: adapter locale reale o S3 privato con URL presigned

## Struttura

```text
apps/web          Frontend dashboard
services/api      API FastAPI e CLI
services/worker   Worker mock per preview/render
packages/shared   Utility condivise per pipeline media mock
data/             Progetti, asset personaggio, preview, render e file temporanei
docs/             Architettura, API e roadmap
infra/aws         Piano di predisposizione cloud
scripts/          Script operativi per setup e run
```

## Avvio rapido

Prerequisito: `python3.11` deve essere disponibile nel `PATH`.

1. Copia `.env.example` in `.env`
2. Esegui `make setup`
3. Avvia tutto con `make dev`

Default sicuri:

- `STORAGE_BACKEND=local`
- `RENDER_BACKEND=local`
- nessuna dipendenza da AWS per far girare setup, dev e test locali

Servizi attesi:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Docs API: `http://localhost:8000/docs`

## Comandi utili

```bash
make setup
make dev
make web
make api
make worker
make test
```

## CLI backend

```bash
PYTHONPATH=services/api:packages/shared python -m app.cli create-project --title "Demo" --prompt "Un lancio prodotto cinematografico"
PYTHONPATH=services/api:packages/shared python -m app.cli generate-storyboard <project-id>
PYTHONPATH=services/api:packages/shared python -m app.cli generate-previews <project-id>
PYTHONPATH=services/api:packages/shared python -m app.cli render-project <project-id>
```

## Note MVP

- Le preview sono SVG mock leggibili e sostituibili con generatori reali.
- Il render finale produce un artefatto dimostrabile con manifest e timeline testuale.
- Gli asset avatar/reference vengono salvati localmente in `data/assets/<project-id>/`.
- L'identity pack del personaggio salva immagine principale, reference images, note e `lock_identity`.
- La UI dettaglio progetto mostra tutte le preview disponibili per scena e permette di selezionare esplicitamente la variante attiva.
- Se `STORAGE_BACKEND=s3`, gli asset dell'identity pack vengono caricati in un bucket S3 privato e letti tramite URL presigned a tempo.
- Preview e render output restano mock locali in questo step, anche quando lo storage asset e' S3.
- La pipeline e' predisposta per render remoti futuri verso EC2 GPU, ComfyUI e ffmpeg, ma in questo step `RENDER_BACKEND=remote_stub` e' solo una stub onesta.

## Configurazione ambiente

Variabili principali:

- `DATA_ROOT=./data`
- `STORAGE_BACKEND=local|s3`
- `AWS_REGION=<regione bucket>`
- `S3_BUCKET_NAME=<bucket privato>`
- `S3_PREFIX=video-ai-studio`
- `PRESIGNED_URL_TTL_SECONDS=900`
- `RENDER_BACKEND=local|remote_stub`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

`AWS_PROFILE` e' supportata lato shell e script AWS CLI, ma non e' hardcodata nella logica del backend.

## AWS bootstrap minimo

Script disponibili:

```bash
./scripts/aws_print_identity.sh
./scripts/aws_check.sh
./scripts/aws_bootstrap_s3.sh
```

Gli script:

- verificano l'identita' corrente con `sts get-caller-identity`
- controllano bucket/regione correnti
- creano il bucket solo se non esiste
- attivano `Block Public Access`, versioning e SSE-S3 (`AES256`)
- non creano risorse costose o ricorrenti
