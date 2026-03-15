# AWS Plan

## Fase 1

- introdurre `StorageAdapter` con implementazione locale e futura S3
- introdurre `RenderExecutor` con implementazione locale e futura EC2 GPU
- mantenere le API stabili

## Fase 2

- bucket S3 per preview e output
- upload asincrono degli asset
- coda job remoti
- callback o polling per stato render

## Fase 3

- worker remoti su EC2 GPU
- ffmpeg e generatori video reali
- osservabilita' e retry policy
