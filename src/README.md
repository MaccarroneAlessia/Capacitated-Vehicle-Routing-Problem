# 💻 src/ (Codice Sorgente Principale)

Qui dentro si trova tutto il codice sorgente scritto per il progetto, diviso in moduli in base al linguaggio e alla loro funzione.

### Contenuto della cartella:

#### ☕ `cvrp/` (Java)
È il motore ad alte prestazioni che esegue i calcoli pesanti e implementa l'algoritmo immunitario.
- **`algorithm/`**: Logica del risolutore.
  - **`Main.java`**: Punto d'ingresso (entry-point) del programma Java. Si occupa di caricare i dati e avviare test globali su multi-run. Include calcoli statistici avanzati (es. Deviazione Standard Campionaria con correzione di Bessel $N-1$) e I/O cross-platform.
  - **`AblationRunner.java`**: Script per lo studio scientifico di ablazione, permettendo di misurare l'efficacia di NN, SA e LNS su set diversificati di istanze.
  - **`ClonalSelection.java`**: Motore meta-euristico immunitario dotato di Adaptive Saturated Mode (transizioni fuzzy), Ruin & Recreate e Simulated Annealing.
- **`model/`**: Strutture dati base, ingegnerizzate per efficienza e sicurezza.
  - **`Instance.java`**: Parser robusto basato su espressioni regolari (Regex) e struttura dati con accessi in tempo costante O(1) alla matrice delle distanze spaziali.
  - **`Antibody.java`**: Struttura della soluzione (Linfocita), blindata tramite tecniche di deep-copy pre-allocate per evitare *side effects*.
  - **`Route.java`**: Modello per singola rotta, caratterizzato da sincronizzazione deterministica del carico e isolamento in memoria.
  - **`Node.java`**: Elemento base spaziale, immutabile e *thread-safe*, ottimizzato per evitare colli di bottiglia (es. uso moltiplicazione algebrica al posto di `Math.pow`).

#### 🌐 `demo/` (Python)
Contiene l'applicazione web interattiva.
- 🚀 **[`app.py`](./demo/app.py)**: Lo script Streamlit che disegna la Dashboard, genera i grafici di convergenza e fa la simulazione live.

#### 🛠️ `utils/` (Python extra)
Piccoli script di supporto.
- 🐍 **[`download_instances.py`](./utils/download_instances.py)**: Script Python usato per scaricare in automatico i dataset ufficiali dalla CVRPLIB.
- 🐍 **[`plot_results.py`](./utils/plot_results.py)**: Script Python aggiuntivo per fare plotting statico da riga di comando.
