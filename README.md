# Video AI Studio

MVP avanzato per creare progetti video AI con workflow completo: progetto, identity pack, storyboard, preview immagini multi-variante, selezione preview per scena e render finale ancora mock ma separato dalla pipeline preview.

## Stack

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + Pydantic
- Worker: Python separato con pipeline mock sostituibile
- Persistenza: file JSON in `data/`
- Storage asset: locale o S3 privato con URL presigned
- Preview engine: `PreviewGenerator` con backend `mock`, `external_generic` o `real_provider`
- Video engine: `VideoGenerator` con backend `mock` o `xai`

## Avvio rapido

Prerequisito: `python3.11` nel `PATH`.

1. Copia `.env.example` in `.env`
2. Esegui `make setup`
3. Avvia tutto con `make dev`

Default sicuri:

- `STORAGE_BACKEND=local`
- `PREVIEW_BACKEND=mock`
- `VIDEO_BACKEND=mock`
- `RENDER_BACKEND=local`
- nessuna dipendenza da AWS per far girare setup, dev e test locali

Servizi attesi:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Docs API: `http://localhost:8000/docs`

Se una porta e' occupata, `scripts/dev.sh`, `scripts/run_api.sh` e `scripts/run_web.sh`:

- identificano il processo sulla porta
- lo terminano solo se e' chiaramente una vecchia istanza locale del repo
- usano `kill -9` solo sulle porte locali di dev del repo (`3000`, `8000`, `3010`, `8010`) se il processo non si ferma
- altrimenti scelgono una porta alternativa e lo loggano

## Comandi utili

```bash
make setup
make dev
make web
make api
make worker
make test
cd apps/web && npm run build
```

## Preview pipeline

Implementato davvero:

- `PREVIEW_BACKEND=mock` genera SVG locali stabili e leggibili
- `PREVIEW_BACKEND=external_generic` invia una richiesta HTTP minimale ma reale a un servizio immagini
- `PREVIEW_BACKEND=real_provider` invia un payload piu' strutturato con prompt modulari, metadata e identity assets
- alias retrocompatibili: `external -> external_generic`, `real -> real_provider`
- supporto risposta `image_base64` oppure `image_url`
- timeout e retry limitati tramite env
- fallback automatico a mock solo se `PREVIEW_FALLBACK_TO_MOCK=true`
- salvataggio locale delle preview sotto `data/previews/`

Implementato come fallback onesto:

- se il backend HTTP fallisce, il flusso resta operativo con `mock_fallback`
- la UI mostra badge, warning e metadata di fallback

Predisposto ma non operativo in questo step:

- render video remoto reale
- job queue cloud
- ComfyUI verificato end-to-end
- GPU EC2

## Video pipeline xAI

Implementato davvero:

- `VIDEO_BACKEND=mock|xai` con default sicuro `mock`
- provider `XaiVideoGenerator` per `grok-imagine-video`
- flow asincrono xAI: submit `POST /v1/videos/generations` e polling `GET /v1/videos/{request_id}`
- supporto `text-to-video`
- supporto `image-to-video` quando l'identity pack ha una `primary_image`
- prompt builder video identity-aware con brief, scena, style, durata, aspect ratio, note personaggio e lock identity
- download immediato dell'URL temporaneo xAI e salvataggio nel nostro storage locale o S3
- endpoint `POST /projects/{id}/video`
- endpoint `POST /projects/{id}/scenes/{scene_id}/video`
- UI progetto con badge backend video, stato job, player e metadata essenziali

Implementato come fallback onesto:

- se `VIDEO_BACKEND=xai` ma manca config o la request fallisce, il sistema puo' degradare a `mock_fallback`
- il fallback resta esplicito nei metadata e nella UI

Predisposto ma non operativo in questo step:

- editing video complesso
- timeline cinematica finale multi-clip
- montaggio ffmpeg reale
- render remoto GPU

## Prompt builder pro

Il layer `PromptBuilder` ora costruisce prompt modulari con:

- subject identity consistency
- face, hairstyle, age e body type coherence
- wardrobe continuity
- camera framing e lens feel
- lighting style e scene mood
- background discipline
- premium commercial look e cinematic polish
- negative prompt piu' forte e meno rumoroso

Ogni preview salva metadata utili davvero, inclusi:

- backend configurato ed effettivo
- generation mode `mock|real|mock_fallback`
- model name, seed, retry count e durata
- prompt signature
- reason di fallback
- identity strength score, label e spiegazione breve

## Variabili env principali

- `DATA_ROOT=./data`
- `STORAGE_BACKEND=local|s3`
- `AWS_REGION=<regione bucket>`
- `S3_BUCKET_NAME=<bucket privato>`
- `S3_PREFIX=video-ai-studio`
- `PRESIGNED_URL_TTL_SECONDS=900`
- `PREVIEW_BACKEND=mock|external_generic|real_provider`
- `PREVIEW_EXTERNAL_URL=https://preview-backend.example/generate`
- `PREVIEW_EXTERNAL_API_KEY=<opzionale>`
- `PREVIEW_EXTERNAL_MODEL_NAME=<opzionale>`
- `PREVIEW_EXTERNAL_TIMEOUT_SECONDS=30`
- `PREVIEW_EXTERNAL_MAX_RETRIES=1`
- `PREVIEW_FALLBACK_TO_MOCK=true`
- `VIDEO_BACKEND=mock|xai`
- `XAI_VIDEO_MODEL=grok-imagine-video`
- `XAI_API_BASE_URL=https://api.x.ai/v1`
- `XAI_POLL_INTERVAL_SECONDS=5`
- `XAI_POLL_TIMEOUT_SECONDS=600`
- `XAI_VIDEO_DEFAULT_DURATION=5`
- `XAI_VIDEO_DEFAULT_RESOLUTION=720p`
- `XAI_VIDEO_DEFAULT_ASPECT_RATIO=16:9`
- `XAI_DOWNLOAD_TO_STORAGE=true`
- `VIDEO_FALLBACK_TO_MOCK=true`
- `RENDER_BACKEND=local|remote_stub`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

Nota locale sui segreti:

- `scripts/run_api.sh` e `scripts/dev.sh` possono leggere `XAI_API_KEY` da `aws_credential` solo in memoria runtime
- la chiave non va copiata in repo, README, docs o `.env.example`

## Contratti preview HTTP

`external_generic`:

- payload minimale con progetto, scena, prompt positivi/negativi e note camera/luci
- utile per provider HTTP semplici o gateway legacy

`real_provider`:

- payload piu' strutturato con `creative_direction`, sezioni prompt separate e `identity.primary_image/reference_images`
- gli asset identita' vengono inviati come `image_base64` quando disponibili localmente, altrimenti come `image_url`

Risposta attesa per entrambi:

- `image_base64` oppure `image_url`
- `mime_type`
- `seed` opzionale
- `model_name` opzionale

## Stato del render

Implementato davvero:

- render mock locale con output dimostrabili

Predisposto ma non operativo:

- `RENDER_BACKEND=remote_stub`
- template EC2 GPU e documentazione cloud

Nessuna GPU EC2 viene creata o usata in questo step.
