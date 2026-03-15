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
- [x] Layer `PreviewGenerator` con backend `mock`, `external_generic` e `real_provider`
- [x] `PromptBuilder` identity-aware con prompt modulari pro per identita', camera, lens, lighting, wardrobe, mood e background
- [x] Metadata preview estesi per backend configurato/effettivo, mode, prompt signature, retry, fallback, seed/model e timing
- [x] Rigenerazione preview di una singola scena senza rigenerare l'intero storyboard
- [x] UI progetto con badge backend preview, fallback, identity strength e pannello engine status
- [x] Layer `VideoGenerator` con backend `mock` e `xai`
- [x] `VideoPromptBuilder` identity-aware con modalita' `text_to_video` e `image_to_video`
- [x] Download immediato degli URL temporanei xAI e persistenza nel nostro storage
- [x] Endpoint `POST /projects/{id}/video` e `POST /projects/{id}/scenes/{scene_id}/video`
- [x] UI progetto con badge backend video, stato job, player clip progetto/scena e fallback esplicito
- [x] Caricamento locale opzionale di `XAI_API_KEY` da `aws_credential` solo a runtime
- [x] Test backend aggiuntivi per factory provider video, prompt builder, polling, timeout/expired e fallback
- [x] Test aggiornati per nuovi campi, upload, metadati identity pack, selezione preview e render mock
- [x] Script di avvio piu' robusti con gestione sicura delle porte occupate
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
- [x] Preview reali opzionali via servizio HTTP esterno compatibile, con fallback mock onesto

## Predisposto ma non implementato davvero

- [x] Render remoto dietro `RemoteRenderExecutorStub`
- [x] Template EC2 GPU e IAM policy di esempio
- [x] Editing video complesso predisposto a livello contratti/metadata ma non usato come flow principale
- [ ] Upload di preview e render output su S3 reale
- [ ] Adapter cloud per job remoti o code asincrone reali
- [ ] Contratto dedicato ComfyUI reale con workflow e mapping nodi verificati
- [ ] Pipeline ffmpeg reale
- [ ] Auth applicativa e permessi utente sugli asset

## Ancora da fare

- [ ] Polling o job queue reale per render asincroni
- [ ] Montaggio finale multi-clip con ffmpeg reale
- [ ] Editing video avanzato oltre il clip singolo
- [ ] Storage cloud nativo delle preview con URL signed e lifecycle policy
- [ ] Eliminazione o sostituzione asset immagine dal dettaglio progetto
- [ ] Compressione/resize lato backend per immagini caricate
- [ ] Test end-to-end browser della UI
- [ ] Filtri e ricerca nella dashboard
- [ ] Strategia di migrazione da JSON locale a storage cloud senza downtime
