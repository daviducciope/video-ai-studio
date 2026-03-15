# Preview Pipeline

## Implementato davvero

- `PREVIEW_BACKEND=mock`
- `PREVIEW_BACKEND=external_generic`
- `PREVIEW_BACKEND=real_provider`
- alias retrocompatibili `external` e `real`
- prompt modulari piu' maturi
- identity strength score salvato per preview
- retry limitati e timeout configurabili
- fallback controllato a mock
- persistenza locale delle immagini preview e dei metadata

## Fallback reale disponibile

Se il backend HTTP non completa la richiesta e `PREVIEW_FALLBACK_TO_MOCK=true`:

- la preview viene comunque generata
- il file risultante e' mock
- `generation_mode=mock_fallback`
- `fallback_reason` e `retry_count` restano visibili nei metadata

## Predisposto ma non operativo

- backend ComfyUI verificato end-to-end
- render video remoto
- storage preview nativo su S3

## Variabili env

- `PREVIEW_BACKEND=mock|external_generic|real_provider`
- `PREVIEW_EXTERNAL_URL=<endpoint POST>`
- `PREVIEW_EXTERNAL_API_KEY=<opzionale>`
- `PREVIEW_EXTERNAL_MODEL_NAME=<opzionale>`
- `PREVIEW_EXTERNAL_TIMEOUT_SECONDS=30`
- `PREVIEW_EXTERNAL_MAX_RETRIES=1`
- `PREVIEW_FALLBACK_TO_MOCK=true`

## Contratto `external_generic`

Request:

- metadati progetto
- metadati scena
- prompt positivi e negativi
- note di coerenza, camera e lighting

Use case:

- provider HTTP semplice
- gateway immagini non ancora specializzato

## Contratto `real_provider`

Request:

- `creative_direction`
- `prompt.positive_prompt`
- `prompt.negative_prompt`
- `prompt.consistency_instructions`
- `prompt.camera_direction`
- `prompt.lens_direction`
- `prompt.lighting_direction`
- `prompt.wardrobe_direction`
- `prompt.mood_direction`
- `prompt.background_direction`
- `identity.primary_image`
- `identity.reference_images`

Le immagini identita' vengono inviate:

- come `image_base64` se il file e' disponibile localmente
- come `image_url` quando non e' leggibile dal filesystem locale ma e' risolvibile via storage adapter

## Response supportata

Formato minimo:

- `image_base64` oppure `image_url`
- `mime_type`

Campi opzionali:

- `seed`
- `model_name`

Il backend valida il MIME type, scarica l'immagine quando serve e la persiste in `data/previews/<project-id>/<scene-id>/`.
