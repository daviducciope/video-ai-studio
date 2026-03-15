# AWS Plan

## Fase 1: completata in questo step

- `StorageAdapter` reale con backend `local|s3`
- `S3StorageAdapter` operativo per gli asset dell'identity pack
- bucket S3 privato con presigned URL in lettura
- `RenderExecutor` con implementazione locale e stub remota
- API stabili e flusso locale preservato

## Fase 2: predisposta, non ancora operativa

- portare anche preview e output mock su S3
- introdurre upload asincrono e cleanup asset
- definire contratto job per render remoto
- aggiungere polling o callback di stato

## Fase 3: ancora da fare

- worker remoti su EC2 GPU
- ComfyUI e ffmpeg reali
- osservabilita', retry policy e cost controls
