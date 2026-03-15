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
- `POST /projects/{id}/scenes/{scene_id}/select`
- `POST /projects/{id}/render`
- `GET /projects/{id}/render-status`
- `GET /projects/{id}/outputs`

## Note

- I file locali generati sono serviti sotto `/files/...`
- `POST /projects/{id}/assets` accetta `multipart/form-data` con:
  - `role=primary` e un solo file immagine
  - `role=reference` e uno o piu' file immagine, fino a 8 reference totali
- Se `STORAGE_BACKEND=s3`, gli asset dell'identity pack vengono salvati in un bucket privato e le risposte includono `resolved_url` con URL presigned temporaneo
- `url` resta un riferimento stabile compatibile con il flusso locale; il frontend deve preferire `resolved_url` quando presente
- Le preview sono asset SVG
- Il render finale produce un manifest testuale e un file timeline dimostrabile
- `RENDER_BACKEND=remote_stub` restituisce errore `501` per dichiarare apertamente che il render remoto non e' ancora operativo
