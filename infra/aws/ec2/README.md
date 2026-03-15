# EC2 GPU Templates

Questa directory contiene solo template per lo step successivo.

In questo step:

- nessuna istanza GPU viene creata;
- nessuno script in questa cartella viene eseguito;
- il backend continua a usare `RENDER_BACKEND=local` per default.

Scopo dei template:

- definire il punto di aggancio per un futuro renderer remoto;
- preparare bootstrap di una singola EC2 GPU on-demand, senza introdurre ancora orchestrazione o code reali;
- documentare permessi minimi e lifecycle manuale.

Prima di usare questi template nello step successivo:

1. rivedere costi e limiti AWS dell'account;
2. creare un IAM role dedicato;
3. collegare `RemoteRenderExecutor` a una coda o a un job runner reale;
4. aggiungere cleanup e tagging obbligatori.
