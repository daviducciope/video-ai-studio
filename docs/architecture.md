# Architecture

## Overview

Il progetto e' organizzato in quattro blocchi:

- `apps/web`: dashboard Next.js che consuma le API e guida il workflow.
- `services/api`: FastAPI con persistenza file-based, orchestrazione workflow e CLI.
- `services/worker`: worker Python separato per elaborazioni mock e future code asincrone.
- `packages/shared`: logica condivisa per la generazione di preview e output dimostrabili.

## Persistence

Ogni progetto vive in `data/projects/<project-id>.json`.

I file generati vengono salvati in:

- `data/previews`
- `data/renders`
- `data/temp`

Questa scelta mantiene il sistema semplice, leggibile e adatto alla fase MVP.

## Workflow

1. Creazione progetto
2. Generazione storyboard e scene
3. Generazione preview mock per scena
4. Selezione scene
5. Render finale con output dimostrabile

## Estendibilita'

La pipeline mock passa da adapter condivisi (`video_ai_shared.mock_media`) cosi' da poter introdurre:

- client ComfyUI
- composizione ffmpeg
- storage S3
- job remoti su EC2 GPU
