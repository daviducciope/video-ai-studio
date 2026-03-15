# Video Pipeline

## Stato reale dello step

Implementato davvero:

- provider video `mock`
- provider video `xai` per `grok-imagine-video`
- flow asincrono submit + polling
- download dell'asset finale e persistenza nel nostro storage
- trigger API per clip progetto e clip scena
- UI con stato backend, job e player

Fallback/mock onesto:

- se xAI non e' configurato o fallisce, il sistema puo' degradare a `mock_fallback`
- il fallback resta visibile nei metadata e in UI

Predisposto ma non operativo:

- editing video complesso
- montaggio finale multi-clip
- render GPU remoto

## Flow xAI

1. Il backend costruisce il prompt con `VideoPromptBuilder`
2. Se esiste `identity_pack.primary_image`, il clip preferisce `image_to_video`
3. Il provider invia `POST /v1/videos/generations`
4. Il provider esegue polling su `GET /v1/videos/{request_id}`
5. Quando lo stato e' `done`, il backend scarica subito l'URL temporaneo
6. Il file viene salvato con `StorageAdapter`
7. Il progetto JSON salva metadata leggibili e il path interno del file

## Contract

Il progetto salva:

- `video_backend`
- `video_backend_effective`
- `video_generation_mode`
- `video_backend_message`
- `video_model_name`
- `video_last_generated_at`
- `video_job`
- `project_video`

Ogni scena puo' salvare:

- `generated_video`

Ogni clip salva:

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

## Storage

Il frontend non deve dipendere da URL xAI temporanei.

- con `STORAGE_BACKEND=local` il file finisce sotto `data/renders/<project-id>/videos/`
- con `STORAGE_BACKEND=s3` il file viene caricato nel bucket configurato

## Secret handling

- `XAI_API_KEY` resta una env runtime
- `scripts/run_api.sh` e `scripts/dev.sh` possono leggerla da `aws_credential` solo localmente
- il file `aws_credential` e' ignorato da git
