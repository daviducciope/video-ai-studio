# Roadmap

## Fase 0 — Bootstrap repo
- [x] Creare la cartella progetto `video-ai-studio`
- [x] Inizializzare Git
- [x] Creare `.gitignore`
- [x] Creare `README.md`
- [x] Copiare questo file come `SOURCE_OF_TRUTH.md`
- [x] Creare `AGENTS.md`
- [x] Creare `.env.example`
- [x] Creare struttura cartelle iniziale

## Fase 1 — Frontend base
- [x] Inizializzare app Next.js con TypeScript
- [x] Configurare Tailwind
- [x] Creare layout base
- [x] Creare Dashboard
- [x] Creare pagina Nuovo Progetto
- [x] Creare pagina dettaglio progetto
- [x] Creare componenti per storyboard, scene e stato render

## Fase 2 — Backend base
- [x] Inizializzare FastAPI
- [x] Creare struttura app backend ordinata
- [x] Creare modelli e schemi principali
- [x] Implementare endpoint Project
- [x] Implementare endpoint Storyboard
- [x] Implementare endpoint Preview
- [x] Implementare endpoint Render
- [x] Aggiungere validazione dati e gestione errori

## Fase 3 — Persistenza e dati
- [x] Scegliere persistenza iniziale (SQLite o JSON strutturati)
- [x] Salvare progetti
- [x] Salvare storyboard
- [x] Salvare scene
- [x] Salvare stato render
- [x] Salvare output e preview

## Fase 4 — Worker e pipeline mock reale
- [x] Creare worker Python separato
- [x] Implementare job preview mock ma realistici
- [x] Implementare job render mock ma realistici
- [x] Aggiornare stati job
- [x] Generare file output dimostrabili

## Fase 5 — Collegamento frontend-backend
- [x] Collegare il form progetto alle API
- [x] Collegare generazione storyboard
- [x] Collegare preview scene
- [x] Collegare selezione scene
- [x] Collegare render finale
- [x] Mostrare stato e output nella UI

## Fase 6 — CLI e developer experience
- [x] Creare `Makefile` o script equivalenti
- [x] Creare script di bootstrap
- [x] Creare script run frontend/backend/worker
- [x] Scrivere README con istruzioni reali
- [x] Aggiungere comandi test

## Fase 7 — Preparazione cloud
- [x] Creare `infra/aws/README.md`
- [x] Creare `infra/aws/plan.md`
- [x] Preparare struttura per S3 client wrapper
- [x] Preparare struttura per future EC2 GPU jobs
- [x] Non hardcodare nessuna credenziale

## Fase 8 — Stabilizzazione
- [x] Testare l'intero flusso end-to-end
- [x] Correggere bug evidenti
- [x] Ripulire codice duplicato
- [x] Migliorare messaggi di errore
- [x] Verificare che il progetto sia facile da avviare

## Fase 9 — Done definition
- [x] Da terminale il progetto si installa
- [x] Frontend parte senza errori
- [x] Backend parte senza errori
- [x] Si puo' creare un progetto
- [x] Si puo' generare storyboard
- [x] Si possono vedere le scene
- [x] Si puo' lanciare un render
- [x] Si ottiene un output finale
- [x] README e docs sono sufficienti per ripartire da zero
