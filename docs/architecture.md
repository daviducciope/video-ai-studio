# Architecture

## Overview

Il progetto resta separato in quattro blocchi:

- `apps/web`: dashboard Next.js
- `services/api`: FastAPI con persistenza JSON e orchestrazione workflow
- `services/worker`: worker Python mock
- `packages/shared`: utility condivise per media mock

## Persistence

Ogni progetto vive in `data/projects/<project-id>.json`.

Gli artefatti vengono salvati in:

- `data/assets/<project-id>/` per primary image e reference images
- `data/previews/<project-id>/<scene-id>/` per preview scena
- `data/renders/` per output render mock e clip video persistiti dopo il download provider
- `data/temp/` per file temporanei

Anche quando il backend preview o video e' esterno, i file vengono riscaricati e persistiti nel nostro storage. Il JSON non salva URL temporanei provider come fonte di verita'.

## Workflow

1. Creazione progetto con brief e identity pack opzionale
2. Upload asset identity in storage locale o S3 privato
3. Generazione storyboard
4. Costruzione prompt preview identity-aware
5. Generazione preview multi-variante per scena
6. Selezione esplicita della preview scena
7. Generazione clip video progetto o scena via provider selezionato
8. Render finale mock

## Preview engine

La generazione preview passa da `PreviewGenerator` con factory semplice:

- `MockPreviewGenerator`
- `ExternalGenericPreviewGenerator`
- `RealProviderPreviewGenerator`

Alias compatibili:

- `PREVIEW_BACKEND=external` -> `external_generic`
- `PREVIEW_BACKEND=real` -> `real_provider`

### `external_generic`

Backend HTTP minimale:

- payload leggero
- utile per provider generici o gateway legacy
- salva comunque metadata consistenti nel progetto

### `real_provider`

Backend HTTP piu' strutturato:

- request con sezioni `creative_direction`, `prompt`, `identity`
- invio di `primary_image` e `reference_images` come `image_base64` se leggibili localmente
- fallback automatico a `image_url` quando necessario
- retry e timeout controllati da env

### Fallback e hardening

- retry prudenti su timeout, connessioni fallite e 5xx
- validazione MIME reale
- errori leggibili
- nessun crash su response malformate
- fallback a mock solo se abilitato da env

## Prompt builder

`PromptBuilder` produce prompt modulari con:

- identity consistency
- face and hairstyle consistency
- wardrobe continuity
- age/body coherence
- camera framing
- lens feel
- lighting style
- scene mood
- background discipline
- premium commercial finish
- negative prompt forte

Lo stesso layer stima anche `identity_strength` con score, livello e spiegazione breve.

## Video engine

La generazione video passa da `VideoGenerator`:

- `MockVideoGenerator`
- `XaiVideoGenerator`

`XaiVideoGenerator` usa il modello `grok-imagine-video` e segue il flow asincrono provider:

1. `POST /v1/videos/generations`
2. polling `GET /v1/videos/{request_id}`
3. download immediato dell'URL temporaneo
4. salvataggio nel nostro storage tramite `StorageAdapter`

Quando il progetto ha una `primary_image`, il prompt builder forza la modalita' preferita `image_to_video`; altrimenti usa `text_to_video`. Le `reference_images` restano nel contratto interno per rinforzare coerenza e metadata, senza inventare parametri xAI non documentati.

## Project metadata

Il progetto salva:

- backend preview configurato
- backend preview effettivo
- generation mode complessivo
- ultimo modello usato
- timestamp ultima generazione
- backend video configurato
- backend video effettivo
- job video con stato `pending|processing|done|failed|expired|fallback`
- clip progetto persistita

Ogni `PreviewAsset` salva inoltre:

- backend configurato
- backend effettivo
- mode
- model name
- seed
- retry count
- fallback reason
- prompt signature
- generation duration
- identity strength score/label/reason

Ogni `OutputAsset` video puo' salvare inoltre:

- `provider_request_id`
- `provider_status`
- `provider_model_name`
- `source_mode`
- `duration_seconds`
- `aspect_ratio`
- `resolution`
- `prompt_used`
- `identity_mode`
- `fallback_message`

## UI

La pagina dettaglio progetto mostra:

- badge backend configurato/effettivo
- differenza visiva tra real, mock e mock fallback
- pannello `preview engine status`
- metadata preview leggibili
- badge backend video e stato job video
- player per clip progetto e clip scena
- metadata video essenziali e fallback esplicito
- note di coerenza e regia
- rigenerazione singola scena con feedback esplicito

## Local startup reliability

`scripts/common.sh` centralizza:

- caricamento `.env` senza sovrascrivere variabili gia' presenti
- caricamento locale opzionale di `XAI_API_KEY` da `aws_credential` senza persisterla
- rilevazione porta occupata
- terminazione sicura solo di processi chiaramente legati al repo
- `kill -9` solo sulle porte di dev locali del repo se il processo non si arresta
- scelta di porta alternativa se la porta non e' liberabile in sicurezza

## Non implementato davvero

- render video remoto reale
- pipeline ffmpeg reale
- ComfyUI verificato end-to-end
- GPU EC2 o job remoti attivi
