# Video AI Studio

MVP locale per creare progetti video AI con workflow completo: progetto, storyboard, preview mock, selezione scene e render finale dimostrabile.

## Stack

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic
- Worker: Python separato con pipeline mock sostituibile
- Persistenza: file JSON strutturati in `data/`

## Struttura

```text
apps/web          Frontend dashboard
services/api      API FastAPI e CLI
services/worker   Worker mock per preview/render
packages/shared   Utility condivise per pipeline media mock
data/             Progetti, preview, render e file temporanei
docs/             Architettura, API e roadmap
infra/aws         Piano di predisposizione cloud
scripts/          Script operativi per setup e run
```

## Avvio rapido

1. Copia `.env.example` in `.env`
2. Esegui `make setup`
3. Avvia tutto con `make dev`

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
- La pipeline e' pronta per adapter futuri verso ComfyUI, ffmpeg, S3 ed EC2 GPU.
