# SOURCE OF TRUTH — Video AI Studio

> Questo file è la fonte di verità del progetto.
> Codex deve attenersi a questo documento per creare, organizzare e portare avanti il progetto.
> In caso di dubbio tra idee implicite e questo file, **vince questo file**.

---

## 1) Visione del progetto

Stiamo costruendo una **piattaforma semplice ma professionale** per creare video AI di qualità, con workflow guidato e controllabile.

L'obiettivo non è partire subito con una piattaforma gigante, ma con un **MVP realmente funzionante**, ben strutturato e pronto a crescere.

L'utente deve poter:

1. inserire un prompt testuale;
2. farlo elaborare dal sistema;
3. ottenere una proposta di **script + storyboard + scene**;
4. generare **preview** delle scene;
5. scegliere le preview migliori;
6. lanciare il **render finale**;
7. unire le scene in un video finale pronto per pubblicazione.

Il sistema deve essere pensato per lavorare bene in locale e, successivamente, poter usare AWS come boost per i render più pesanti.

---

## 2) Contesto tecnico reale dell'utente

Questa parte è fondamentale e va rispettata.

### Ambiente di lavoro dell'utente
- Sistema principale: **Fedora Linux**
- Disco esterno MSI 2TB ad alte prestazioni
- Partizione di sviluppo: **`/home/davide/Sviluppo`** (ext4)
- Tutti i progetti devono vivere qui: **`/home/davide/Sviluppo/Progetti`**
- Il progetto corrente deve essere creato qui:
  - **`/home/davide/Sviluppo/Progetti/video-ai-studio`**

### Regole pratiche
- Non usare percorsi casuali fuori da `/home/davide/Sviluppo/Progetti`
- Non scrivere asset pesanti sull'SSD interno se evitabile
- Tutte le cartelle di output, cache, render, preview e asset devono essere pensate per stare sul disco di sviluppo
- Nessun secret reale deve essere hardcodato nel codice
- Usare file `.env` e `.env.example`

---

## 3) Filosofia del progetto

Il progetto deve essere:

- **CLI-first**: tutto deve poter essere lanciato anche via terminale
- **UI-friendly**: deve avere una interfaccia grafica semplice ma funzionante
- **modulare**: frontend, backend, worker e infrastruttura separati
- **production-minded**: struttura seria, non prototipo disordinato
- **scalabile**: pronto a supportare render locali o remoti
- **facile da capire**: codice ben commentato, file chiari, README utile

---

## 4) Cosa stiamo costruendo davvero

Stiamo creando un sistema con questi macro-blocchi:

### A. Frontend / Dashboard
Una UI essenziale per:
- creare un progetto video;
- inserire prompt, stile, durata, formato;
- visualizzare storyboard e scene;
- vedere preview;
- selezionare le scene migliori;
- avviare render finale;
- vedere lo stato dei job;
- scaricare o visualizzare il risultato finale.

### B. Backend API
Una API che gestisce:
- creazione progetti;
- salvataggio configurazioni;
- generazione storyboard;
- generazione prompt per scena;
- gestione preview;
- lancio render finale;
- stato dei job;
- elenco asset, scene e output.

### C. Worker di generazione
Un worker separato che:
- genera asset mock o reali;
- dialoga in futuro con ComfyUI / modelli video / ffmpeg;
- salva file di output;
- aggiorna lo stato del job.

### D. Infrastruttura / CLI / AWS-ready
Una base pronta per:
- esecuzione locale;
- futura integrazione con S3;
- futura integrazione con EC2 GPU;
- comandi CLI per sviluppare, buildare e testare;
- possibilità di integrare n8n in futuro come orchestratore.

---

## 5) Non obiettivi iniziali

Per evitare dispersione, **NON** sono prioritari nella prima versione:

- autenticazione complessa multiutente;
- billing / Stripe;
- rendering video finale avanzatissimo già perfetto;
- n8n obbligatorio nella v1;
- deploy completo AWS nella prima ora;
- avatar fotorealistici già perfetti al primo commit;
- architettura enterprise esagerata.

Prima vogliamo un MVP pulito, funzionante, leggibile e collegabile.

---

## 6) Stack consigliato

Codex deve usare questo stack, salvo impossibilità tecnica forte.

### Frontend
- **Next.js**
- **TypeScript**
- **Tailwind CSS**
- componenti semplici, puliti, moderni

### Backend
- **Python 3.11+**
- **FastAPI**
- **Pydantic**

### Worker / Media pipeline
- **Python**
- struttura già pronta per integrare:
  - ComfyUI API
  - ffmpeg
  - AWS S3
  - AWS EC2 GPU

### Tooling
- Git
- Makefile oppure script CLI
- `.env` / `.env.example`
- Docker facoltativo ma non obbligatorio nella prima iterazione

### Testing
- frontend: test minimi
- backend: test minimi
- almeno smoke test o test base per gli endpoint principali

---

## 7) Architettura richiesta

Codex deve creare una struttura simile a questa:

```text
video-ai-studio/
├── README.md
├── SOURCE_OF_TRUTH.md
├── AGENTS.md
├── .gitignore
├── .env.example
├── Makefile
├── apps/
│   └── web/
│       ├── package.json
│       ├── next.config.*
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   ├── lib/
│       │   └── types/
│       └── public/
├── services/
│   ├── api/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   ├── requirements.txt
│   │   └── tests/
│   └── worker/
│       ├── app/
│       ├── requirements.txt
│       └── tests/
├── packages/
│   └── shared/
├── scripts/
│   ├── dev.sh
│   ├── setup.sh
│   ├── run_api.sh
│   ├── run_web.sh
│   └── run_worker.sh
├── infra/
│   └── aws/
│       ├── README.md
│       └── plan.md
├── data/
│   ├── projects/
│   ├── previews/
│   ├── renders/
│   └── temp/
└── docs/
    ├── architecture.md
    ├── api.md
    └── roadmap.md
```

La struttura può essere migliorata, ma non deve essere confusionaria.

---

## 8) Workflow prodotto richiesto

Questo è il workflow che il sistema deve supportare.

### Step 1 — Creazione progetto
L'utente crea un progetto con:
- titolo
- prompt
- stile
- durata target
- formato (9:16 / 16:9)
- eventuali note sul personaggio/avatar

### Step 2 — Elaborazione creativa
Il sistema genera:
- titolo video raffinato
- breve script
- storyboard testuale
- elenco scene
- prompt tecnici per ogni scena
- eventuali prompt negativi

### Step 3 — Preview scene
Il sistema genera preview di scena.
Nella v1 può andare bene anche un mock controllato o placeholder realistico, purché il flusso sia pronto.

### Step 4 — Selezione utente
L'utente seleziona le scene migliori o le versioni preferite.

### Step 5 — Render finale
Il sistema lancia un render finale.
Nella v1 può essere mockato o semplificato, ma il flusso deve esistere davvero, non solo a parole.

### Step 6 — Assemblaggio
Il sistema prepara un output finale.
Nella v1 può essere:
- un video placeholder assemblato;
- oppure una simulazione realistica con stato completo e file output generato.

---

## 9) Stato richiesto della v1

La v1 deve essere **funzionante** e dimostrabile.

Significa che Codex deve produrre un progetto che permetta davvero di:

- avviare frontend e backend;
- creare un progetto;
- salvare dati;
- visualizzare storyboard;
- vedere scene;
- simulare o generare preview;
- cambiare stato di job;
- lanciare il render finale;
- ottenere un output visibile o scaricabile;
- essere pronto per agganciare motori reali dopo.

Non vogliamo una demo vuota. Vogliamo un MVP funzionante con flussi reali, anche se alcune parti nella prima versione sono mock controllati.

---

## 10) Integrazioni future già previste

Codex deve preparare il codice per queste integrazioni future:

### Rendering / media
- ComfyUI API
- ffmpeg
- generatori immagini/video
- avatar coherence pipeline

### Cloud
- AWS S3 per asset e output
- AWS EC2 GPU per render pesanti
- eventuale coda job futura

### Automazione
- n8n come orchestratore secondario
- webhook per notifiche e step approval

### LLM
- prompt planner
- scene planner
- future integrazioni OpenAI / Ollama / altri provider

Il codice deve essere scritto per permettere adapter o service layer, non accoppiando tutto male.

---

## 11) n8n: posizione ufficiale del progetto

n8n **non è il motore principale** del progetto.

n8n potrà essere usato in futuro per:
- orchestrazione;
- notifiche;
- approvazioni;
- publishing;
- automazioni tra servizi.

Ma la logica principale deve stare nel nostro codice.

---

## 12) AWS: posizione ufficiale del progetto

AWS è un target reale del progetto, ma nella prima fase deve essere trattato così:

### Fase iniziale
- progetto funzionante in locale
- struttura pronta per cloud
- file `infra/aws/plan.md`
- eventuali client wrapper già predisposti

### Fase successiva
- bucket S3
- upload asset
- job remoti
- render su EC2 GPU

Codex non deve bloccare la consegna del MVP perché mancano credenziali AWS reali.

---

## 13) UX minima richiesta

La UI deve essere semplice ma bella e chiara.

### Pagine minime richieste
1. **Dashboard / Home**
   - elenco progetti
   - bottone nuovo progetto

2. **Create Project**
   - form con prompt e parametri

3. **Project Detail**
   - dati progetto
   - script
   - storyboard
   - lista scene
   - preview scene
   - pulsanti per generate/select/render

4. **Render Status / Output**
   - stato job
   - log essenziali
   - output finale o placeholder scaricabile

### Principi UX
- niente interfaccia confusionaria
- tutto leggibile
- pulsanti con nomi chiari
- errori chiari
- loading state chiari
- stato del progetto comprensibile a colpo d'occhio

---

## 14) API minima richiesta

Codex deve creare almeno endpoint coerenti con questo schema.

### Project
- `POST /projects`
- `GET /projects`
- `GET /projects/{id}`

### Storyboard
- `POST /projects/{id}/storyboard`

### Preview
- `POST /projects/{id}/previews`
- `POST /projects/{id}/scenes/{scene_id}/select`

### Render
- `POST /projects/{id}/render`
- `GET /projects/{id}/render-status`

### Assets / outputs
- `GET /projects/{id}/outputs`

Gli endpoint possono essere raffinati, ma il flusso deve essere coerente.

---

## 15) Data model minimo

Codex deve modellare almeno questi concetti:

- **Project**
- **Storyboard**
- **Scene**
- **PreviewAsset**
- **RenderJob**
- **OutputAsset**

Non serve un database enterprise iniziale.
Anche un file-based store o SQLite può andare bene nella v1, purché sia ordinato.

### Preferenza
- **SQLite** oppure file JSON strutturati
- semplice, leggibile, locale
- facile da evolvere

---

## 16) CLI richiesta

Il progetto deve essere usabile anche da terminale.

### Comandi minimi desiderati
Codex deve predisporre comandi o script equivalenti a:

```bash
make setup
make dev
make web
make api
make worker
make test
```

Facoltativo ma molto utile:

```bash
python -m app.cli create-project
python -m app.cli generate-storyboard
python -m app.cli generate-previews
python -m app.cli render-project
```

L'obiettivo è poter controllare il sistema anche senza UI.

---

## 17) Checklist di avanzamento da spuntare

Codex deve usare questa checklist come riferimento e aggiornarla nel file `docs/roadmap.md` o in un file TODO dedicato.

## Fase 0 — Bootstrap repo
- [ ] Creare la cartella progetto `video-ai-studio`
- [ ] Inizializzare Git
- [ ] Creare `.gitignore`
- [ ] Creare `README.md`
- [ ] Copiare questo file come `SOURCE_OF_TRUTH.md`
- [ ] Creare `AGENTS.md`
- [ ] Creare `.env.example`
- [ ] Creare struttura cartelle iniziale

## Fase 1 — Frontend base
- [ ] Inizializzare app Next.js con TypeScript
- [ ] Configurare Tailwind
- [ ] Creare layout base
- [ ] Creare Dashboard
- [ ] Creare pagina Nuovo Progetto
- [ ] Creare pagina dettaglio progetto
- [ ] Creare componenti per storyboard, scene e stato render

## Fase 2 — Backend base
- [ ] Inizializzare FastAPI
- [ ] Creare struttura app backend ordinata
- [ ] Creare modelli e schemi principali
- [ ] Implementare endpoint Project
- [ ] Implementare endpoint Storyboard
- [ ] Implementare endpoint Preview
- [ ] Implementare endpoint Render
- [ ] Aggiungere validazione dati e gestione errori

## Fase 3 — Persistenza e dati
- [ ] Scegliere persistenza iniziale (SQLite o JSON strutturati)
- [ ] Salvare progetti
- [ ] Salvare storyboard
- [ ] Salvare scene
- [ ] Salvare stato render
- [ ] Salvare output e preview

## Fase 4 — Worker e pipeline mock reale
- [ ] Creare worker Python separato
- [ ] Implementare job preview mock ma realistici
- [ ] Implementare job render mock ma realistici
- [ ] Aggiornare stati job
- [ ] Generare file output dimostrabili

## Fase 5 — Collegamento frontend-backend
- [ ] Collegare il form progetto alle API
- [ ] Collegare generazione storyboard
- [ ] Collegare preview scene
- [ ] Collegare selezione scene
- [ ] Collegare render finale
- [ ] Mostrare stato e output nella UI

## Fase 6 — CLI e developer experience
- [ ] Creare `Makefile` o script equivalenti
- [ ] Creare script di bootstrap
- [ ] Creare script run frontend/backend/worker
- [ ] Scrivere README con istruzioni reali
- [ ] Aggiungere comandi test

## Fase 7 — Preparazione cloud
- [ ] Creare `infra/aws/README.md`
- [ ] Creare `infra/aws/plan.md`
- [ ] Preparare struttura per S3 client wrapper
- [ ] Preparare struttura per future EC2 GPU jobs
- [ ] Non hardcodare nessuna credenziale

## Fase 8 — Stabilizzazione
- [ ] Testare l'intero flusso end-to-end
- [ ] Correggere bug evidenti
- [ ] Ripulire codice duplicato
- [ ] Migliorare messaggi di errore
- [ ] Verificare che il progetto sia facile da avviare

## Fase 9 — Done definition
- [ ] Da terminale il progetto si installa
- [ ] Frontend parte senza errori
- [ ] Backend parte senza errori
- [ ] Si può creare un progetto
- [ ] Si può generare storyboard
- [ ] Si possono vedere le scene
- [ ] Si può lanciare un render
- [ ] Si ottiene un output finale
- [ ] README e docs sono sufficienti per ripartire da zero

---

## 18) Regole di implementazione per Codex

Codex deve seguire queste regole.

### Regola 1
Non creare codice inutile o troppo sofisticato se non serve al MVP.

### Regola 2
Meglio un flusso semplice ma funzionante che un'architettura finta.

### Regola 3
Il codice deve essere commentato in modo utile, soprattutto nelle parti chiave.

### Regola 4
Ogni parte importante deve essere in file separati e nominati bene.

### Regola 5
Non hardcodare path assoluti se evitabile, ma rispettare la convenzione del progetto.

### Regola 6
Preparare hook/adapter/service layer per future integrazioni media e cloud.

### Regola 7
Se una parte reale non è ancora disponibile, creare un mock chiaro e sostituibile.

### Regola 8
Non rompere il repo con dipendenze esotiche se una soluzione standard basta.

### Regola 9
Documentare le decisioni importanti.

### Regola 10
Ogni milestone deve lasciare il progetto in stato eseguibile.

---

## 19) Criteri di successo

Il progetto è considerato sulla buona strada se:

- la struttura è pulita;
- si capisce subito dove mettere mano;
- il workflow principale è reale;
- esistono endpoint e UI collegati;
- esiste uno stato job leggibile;
- il render può essere simulato o reale ma il flusso è vero;
- il progetto è pronto per evolvere in pipeline video AI seria.

---

## 20) Prima istruzione operativa per Codex

Codex deve partire così:

1. creare il repo in `video-ai-studio`;
2. bootstrapparne la struttura;
3. creare frontend, backend e worker;
4. creare un MVP end-to-end locale;
5. aggiornare roadmap/checklist;
6. lasciare il progetto avviabile da terminale.

---

## 21) Ordine di priorità ufficiale

In caso di dubbio, la priorità è questa:

1. progetto avviabile;
2. flusso end-to-end funzionante;
3. codice ordinato;
4. UI semplice ma chiara;
5. CLI e docs;
6. predisposizione AWS;
7. integrazioni avanzate future.

---

## 22) Istruzione finale diretta a Codex

Codex, devi trattare questo documento come la fonte di verità del progetto.

Il tuo compito è realizzare il progetto seguendo il piano sopra, partendo da un MVP realmente funzionante e non da una demo finta.

Devi:
- costruire una base solida;
- lasciare il progetto eseguibile ad ogni milestone;
- usare mock chiari dove il motore finale non è ancora integrato;
- preparare il codice per integrazioni future reali;
- mantenere ordine, leggibilità e documentazione.

L'obiettivo non è impressionare con complessità inutile.
L'obiettivo è consegnare una piattaforma semplice, modulare, seria e pronta a crescere.

