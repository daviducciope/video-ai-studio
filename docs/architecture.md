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

- `data/assets/<project-id>` per avatar e reference images del personaggio
- `data/previews` per le preview mock di scena
- `data/renders` per gli output finali mock
- `data/temp` per file temporanei

Questa scelta mantiene il sistema semplice, leggibile e adatto alla fase MVP avanzata locale.

Quando `STORAGE_BACKEND=s3`, i JSON di progetto restano locali in `data/projects`, mentre gli asset dell'identity pack vengono salvati su S3.

## Workflow

1. Creazione progetto con brief e identity pack opzionale
2. Upload asset avatar/reference in storage locale o S3 privato
3. Generazione storyboard e scene
4. Generazione preview mock multi-variante per scena
5. Selezione esplicita della preview per scena
6. Render finale con output dimostrabile

## Storage adapter

Il backend usa una piccola astrazione `StorageAdapter`:

- `LocalStorageAdapter`: implementazione reale usata in questo step
- `S3StorageAdapter`: implementazione reale per upload asset identity pack

L'adapter salva file con nomi sicuri basati su UUID e non si fida del nome originale caricato dal browser.

Dettagli del backend S3:

- key normalizzate e prive di path traversal
- bucket previsto come privato
- lettura tramite URL presigned con TTL configurabile
- metadata minimi per `project-id`, `asset-role`, `asset-id`

Per evitare di salvare URL presigned scaduti nei JSON, il backend espone per ogni asset un `resolved_url` rigenerato a ogni risposta API.

## Delivery file

- Asset identity pack:
  - `local` -> `/files/...`
  - `s3` -> URL presigned `get_object`
- Preview mock di scena:
  - ancora generate e servite localmente
- Output render mock:
  - ancora generati e serviti localmente

Questa scelta limita rischio e costo: lo step cloud reale copre storage asset e accesso sicuro, senza spostare ancora la pipeline render.

## Render executor

Il punto di esecuzione del render e' stato isolato dietro `RenderExecutor`:

- `LocalRenderExecutor`: comportamento reale attuale del render mock
- `RemoteRenderExecutorStub`: stub esplicita che risponde in modo onesto e non avvia job remoti

Questo e' il punto dove agganciare nello step successivo EC2 GPU, ComfyUI e un job runner remoto.

## Estendibilita'

La pipeline mock passa da adapter condivisi (`video_ai_shared.mock_media`) cosi' da poter introdurre:

- client ComfyUI
- composizione ffmpeg
- storage S3 anche per preview e output
- job remoti su EC2 GPU
