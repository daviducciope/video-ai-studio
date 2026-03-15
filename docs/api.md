# API

## Endpoints principali

- `GET /health`
- `POST /projects`
- `GET /projects`
- `GET /projects/{id}`
- `GET /projects/{id}/assets`
- `POST /projects/{id}/assets`
- `POST /projects/{id}/storyboard`
- `POST /projects/{id}/previews`
- `POST /projects/{id}/scenes/{scene_id}/previews`
- `POST /projects/{id}/scenes/{scene_id}/select`
- `POST /projects/{id}/video`
- `POST /projects/{id}/scenes/{scene_id}/video`
- `POST /projects/{id}/render`
- `GET /projects/{id}/render-status`
- `GET /projects/{id}/outputs`

## Note comportamento

- I file locali sono serviti sotto `/files/...`
- `POST /projects/{id}/assets` accetta `multipart/form-data`
- `role=primary` richiede un solo file immagine
- `role=reference` accetta uno o piu' file immagine, fino a 8 reference totali
- Con `STORAGE_BACKEND=s3`, gli asset identity vengono salvati su bucket privato e la response include `resolved_url`
- `url` resta un riferimento stabile; il frontend deve preferire `resolved_url` quando presente

## Preview endpoints

### `POST /projects/{id}/previews`

Genera preview per tutte le scene.

Body:

```json
{
  "variants_per_scene": 3
}
```

### `POST /projects/{id}/scenes/{scene_id}/previews`

Rigenera solo la scena indicata:

- non tocca le altre scene
- incrementa `preview_revision`
- sostituisce in modo chiaro le preview precedenti di quella scena
- aggiorna `selected_preview_id` sulla nuova variante attiva

### `POST /projects/{id}/scenes/{scene_id}/select`

Seleziona esplicitamente una preview della scena.

## Metadata preview

Ogni `PreviewAsset` puo' includere:

- `configured_backend`
- `generation_backend`
- `generation_mode`
- `model_name`
- `seed`
- `retry_count`
- `fallback_reason`
- `prompt_signature`
- `generation_duration_ms`
- `positive_prompt`
- `negative_prompt`
- `consistency_notes`
- `camera_notes`
- `lighting_notes`
- `wardrobe_notes`
- `identity_strength_score`
- `identity_strength_label`
- `identity_strength_reason`

`generation_mode` distingue:

- `mock`
- `real`
- `mock_fallback`

## Backend preview HTTP

Il backend supporta tre modalita':

- `mock`
- `external_generic`
- `real_provider`

Alias supportati:

- `external`
- `real`

Il backend HTTP si aspetta sempre una response con:

- `image_base64` oppure `image_url`
- `mime_type`

Campi opzionali:

- `seed`
- `model_name`

Se la response e' malformata o il backend fallisce:

- con `PREVIEW_FALLBACK_TO_MOCK=true` la request degrada a mock
- con `PREVIEW_FALLBACK_TO_MOCK=false` l'API restituisce errore leggibile

## Render

Il render finale e' ancora mock.

- `RENDER_BACKEND=local` funziona davvero
- `RENDER_BACKEND=remote_stub` risponde `501` per dichiarare che il render remoto non e' ancora operativo

## Video endpoints

### `POST /projects/{id}/video`

Genera un clip video progetto e lo salva nel nostro storage.

Comportamento:

- `VIDEO_BACKEND=mock` produce un mp4 placeholder locale
- `VIDEO_BACKEND=xai` usa `grok-imagine-video`
- con `VIDEO_FALLBACK_TO_MOCK=true` eventuali errori xAI degradano a `mock_fallback`

### `POST /projects/{id}/scenes/{scene_id}/video`

Genera un clip video della scena indicata e lo salva nel nostro storage.

Se il progetto ha `identity_pack.primary_image`, la modalita' preferita e':

- `image_to_video`

Altrimenti:

- `text_to_video`

## Metadata video

`Project` puo' includere:

- `video_backend`
- `video_backend_effective`
- `video_generation_mode`
- `video_backend_message`
- `video_model_name`
- `video_last_generated_at`
- `video_job`
- `project_video`

Ogni clip video in `project_video` o `scene.generated_video` puo' includere:

- `video_backend`
- `video_generation_mode`
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

Nota importante:

- gli URL temporanei provider non sono la fonte di verita' finale
- il backend scarica subito il file e restituisce il riferimento al nostro storage
