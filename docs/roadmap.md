# Roadmap

## Completato davvero

### Foundation locale
- [x] Repo CLI-first con `make setup`, `make dev`, `make test`
- [x] Frontend Next.js + Tailwind
- [x] Backend FastAPI con persistenza file-based JSON
- [x] Worker Python mock separato
- [x] Workflow locale: create project -> storyboard -> preview -> render mock

### MVP avanzato locale
- [x] Fix della gestione errori frontend che mostrava `[object Object]`
- [x] Validazione frontend minima per titolo, prompt e durata
- [x] Supporto identity pack nel modello progetto
- [x] Upload locale immagine principale personaggio
- [x] Upload locale di fino a 8 reference images
- [x] Salvataggio metadati identity pack dentro il progetto JSON
- [x] Pagina "Nuovo progetto" con sezione Avatar / Personaggio
- [x] Pagina dettaglio progetto con identity pack, stati piu' leggibili e gallery preview complete
- [x] Selezione esplicita di una preview specifica per scena
- [x] Test aggiornati per nuovi campi, upload, metadati identity pack, selezione preview e render mock
- [x] `.python-version` fissato a `3.11`
- [x] Messaggio setup piu' chiaro se `python3.11` non e' disponibile

### AWS step minimo reale
- [x] Config env minima per `STORAGE_BACKEND`, `AWS_REGION`, `S3_BUCKET_NAME`, `S3_PREFIX`, `PRESIGNED_URL_TTL_SECONDS`, `RENDER_BACKEND`
- [x] `S3StorageAdapter` reale con upload via boto3, key normalizzate, metadata minimi e SSE-S3
- [x] Switch runtime `local|s3` per lo storage asset
- [x] Bucket previsto privato con delivery file tramite URL presigned
- [x] Frontend compatibile con `resolved_url` per asset/output/preview
- [x] `RenderExecutor` introdotto con `LocalRenderExecutor` reale e `RemoteRenderExecutorStub`
- [x] Script CLI prudenti per check/bootstrap bucket S3
- [x] Template EC2 GPU documentati ma non eseguiti
- [x] Test backend aggiuntivi senza dipendenza da AWS reale

## Predisposto ma non implementato davvero

- [x] Render remoto dietro `RemoteRenderExecutorStub`
- [x] Template EC2 GPU e IAM policy di esempio
- [ ] Upload di preview mock e render output su S3 reale
- [ ] Adapter cloud per job remoti o code asincrone reali
- [ ] Integrazione ComfyUI reale
- [ ] Pipeline ffmpeg reale
- [ ] Auth applicativa e permessi utente sugli asset

## Ancora da fare

- [ ] Polling o job queue reale per render asincroni
- [ ] Eliminazione o sostituzione asset immagine dal dettaglio progetto
- [ ] Compressione/resize lato backend per immagini caricate
- [ ] Test end-to-end browser della UI
- [ ] Filtri e ricerca nella dashboard
- [ ] Storage abstraction remota anche per preview e render, non solo per gli asset personaggio
- [ ] Strategia di migrazione da JSON locale a storage cloud senza downtime
