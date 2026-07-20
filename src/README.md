# 💻 src/ (Codice Sorgente Principale)

Qui dentro si trova tutto il codice sorgente scritto per il progetto, diviso in moduli in base al linguaggio e alla loro funzione.

### Contenuto della cartella:

#### ☕ `cvrp/` (Java)
È il motore ad alte prestazioni che esegue i calcoli pesanti e implementa l'algoritmo immunitario.
- **`algorithm/`**: Logica del risolutore.
  - **`Main.java`**: Punto d'ingresso (entry-point) del programma Java. Si occupa di caricare i dati e avviare test globali sulle 10 istanze di protocollo con multi-run (5 run indipendenti). Include calcoli statistici avanzati (es. Deviazione Standard Campionaria con correzione di Bessel $N-1$), tracking delle Fitness Evaluations (FE) e delle Generazioni, e I/O cross-platform.
  - **`AblationRunner.java`**: Script per lo studio scientifico di ablazione su **85 istanze × 8 configurazioni** (680 run totali). Misura Costo, Tempo e FE per ogni combinazione di operatori (NN, SA, LNS) e salva i risultati in CSV per analisi statistica.
  - **`ClonalSelection.java`**: Motore meta-euristico immunitario dotato di Adaptive Saturated Mode (transizioni fuzzy), Ruin & Recreate (LNS), Smart Initialization (NN) e Simulated Annealing (SA). La configurazione di default è **NN_LNS**, eletta dallo studio d'ablazione.
- **`model/`**: Strutture dati base, ingegnerizzate per efficienza e sicurezza.
  - **`Instance.java`**: Parser robusto basato su espressioni regolari (Regex) e struttura dati con accessi in tempo costante O(1) alla matrice delle distanze spaziali. Supporta solo istanze EUC_2D con coordinate.
  - **`Antibody.java`**: Struttura della soluzione (Linfocita), blindata tramite tecniche di deep-copy pre-allocate per evitare *side effects*.
  - **`Route.java`**: Modello per singola rotta, caratterizzato da sincronizzazione deterministica del carico e isolamento in memoria.
  - **`Node.java`**: Elemento base spaziale, immutabile e *thread-safe*, ottimizzato per evitare colli di bottiglia (es. uso moltiplicazione algebrica al posto di `Math.pow`).

#### 🌐 `demo/` (Python)
Contiene l'applicazione web interattiva.
- 🚀 **[`app.py`](./demo/app.py)**: Lo script Streamlit che disegna la Dashboard, genera i grafici di convergenza e fa la simulazione live.

#### 🛠️ `utils/` (Python extra)
Script di supporto e validazione.
- 🐍 **[`download_instances.py`](./utils/download_instances.py)**: Script Python usato per scaricare in automatico i dataset ufficiali dalla CVRPLIB.
- 🐍 **[`plot_results.py`](./utils/plot_results.py)**: Script Python aggiuntivo per fare plotting statico da riga di comando.
- 🐍 **[`verify_solutions.py`](./utils/verify_solutions.py)**: Validazione automatica dei vincoli di capacità e correttezza delle soluzioni generate.
- 🐍 **[`generate_infographic.py`](./utils/generate_infographic.py)**: Generazione di infografiche PNG automatiche per ogni istanza risolta.
- 🐍 **[`check_demands.py`](./utils/check_demands.py)**: Analisi diagnostica delle domande/capacità per identificare istanze quasi sature.
