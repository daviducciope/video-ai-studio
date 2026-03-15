# API

## Endpoints principali

- `GET /health`
- `POST /projects`
- `GET /projects`
- `GET /projects/{id}`
- `POST /projects/{id}/storyboard`
- `POST /projects/{id}/previews`
- `POST /projects/{id}/scenes/{scene_id}/select`
- `POST /projects/{id}/render`
- `GET /projects/{id}/render-status`
- `GET /projects/{id}/outputs`

## Note

- I file generati sono serviti sotto `/files/...`
- Le preview sono asset SVG
- Il render finale produce un manifest testuale e un file timeline dimostrabile
