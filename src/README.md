# 💻 src/ (Codice Sorgente Principale)

Qui dentro si trova tutto il codice sorgente scritto per il progetto, diviso in moduli in base al linguaggio e alla loro funzione.

### Contenuto della cartella:

#### ☕ `cvrp/` (Java)
È il motore ad alte prestazioni che esegue i calcoli pesanti e implementa l'algoritmo immunitario.
- ⚙️ **`algorithm/`**: Logica del risolutore.
  - **[`Main.java`](./cvrp/algorithm/Main.java)**: Il punto d'ingresso (entry-point) del programma Java che si occupa di caricare i dati e avviare i test.
  - **[`ClonalSelection.java`](./cvrp/algorithm/ClonalSelection.java)**: Implementa la meta-euristica vera e propria (Selezione Clonale, Ruin & Recreate, Simulated Annealing).
- 🧩 **`model/`**: Strutture dati base.
  - **[`Instance.java`](./cvrp/model/Instance.java)**: Rappresenta il problema da risolvere (matrice delle distanze, nodi, capacità).
  - **[`Antibody.java`](./cvrp/model/Antibody.java)**: Un "anticorpo", ovvero una potenziale soluzione composta da più rotte.
  - **[`Route.java`](./cvrp/model/Route.java)**: Singola rotta di un veicolo.
  - **[`Node.java`](./cvrp/model/Node.java)**: Un singolo cliente o il deposito.

#### 🌐 `demo/` (Python)
Contiene l'applicazione web interattiva.
- 🚀 **[`app.py`](./demo/app.py)**: Lo script Streamlit che disegna la Dashboard, genera i grafici di convergenza e fa la simulazione live.

#### 🛠️ `utils/` (Python extra)
Piccoli script di supporto.
- 🐍 **[`download_instances.py`](./utils/download_instances.py)**: Script Python usato per scaricare in automatico i dataset ufficiali dalla CVRPLIB.
- 🐍 **[`plot_results.py`](./utils/plot_results.py)**: Script Python aggiuntivo per fare plotting statico da riga di comando.
