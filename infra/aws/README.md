# AWS Readiness

Questa cartella documenta come evolvere il MVP locale verso un'architettura ibrida locale/cloud.

Obiettivi:

- separare storage locale e storage remoto;
- isolare i job di rendering dietro adapter;
- permettere upload asset su S3 senza cambiare il workflow della UI.

## Stato di questo step

Implementato davvero:

- bucket S3 privato come destinazione reale per gli asset dell'identity pack
- bootstrap bucket via AWS CLI con versioning, SSE-S3 e Block Public Access
- URL presigned in lettura per non rendere pubblico il bucket
- `RenderExecutor` con backend locale reale e stub remoto

Non implementato in questo step:

- EC2 GPU
- NAT Gateway, ALB, RDS, CloudFront
- render remoto reale
- storage S3 per preview e output render mock

Script AWS CLI:

- [scripts/aws_print_identity.sh](/home/davide/Sviluppo/Progetti/video-ai-studio/scripts/aws_print_identity.sh)
- [scripts/aws_check.sh](/home/davide/Sviluppo/Progetti/video-ai-studio/scripts/aws_check.sh)
- [scripts/aws_bootstrap_s3.sh](/home/davide/Sviluppo/Progetti/video-ai-studio/scripts/aws_bootstrap_s3.sh)
