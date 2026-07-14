# 🚚 Capacitated Vehicle Routing Problem (CVRP) Optimizer
**Corso:** Heuristics & Metaheuristics

Questo progetto implementa un **Algoritmo Memetico Avanzato** basato sul paradigma degli *Artificial Immune Systems* (Clonal Selection Algorithm) per risolvere il problema del CVRP. L'algoritmo è scritto in Java per massimizzare le prestazioni computazionali, mentre l'analisi dei dati e la visualizzazione interattiva sono realizzate in Python (script Python, Jupyter Notebook & Streamlit).

## 🚀 Funzionalità Principali
- **Clonal Selection Algorithm (CSA):** Un algoritmo meta-euristico bio-ispirato.
- **Smart Initialization:** Il 20% della popolazione iniziale è generata usando l'euristica *Nearest Neighbor*, garantendo una convergenza molto più rapida rispetto a un'inizializzazione puramente casuale.
- **Large Neighborhood Search (LNS):** Un operatore di iper-mutazione (Ruin & Recreate) studiato per distruggere blocchi di percorsi sub-ottimi e reinserirli globalmente.
- **Simulated Annealing (SA) in Local Search:** La 2-Opt locale accetta mosse peggiorative con una probabilità basata sulla Temperatura per fuggire efficacemente dai minimi locali.
- **Dashboard Streamlit Interattiva:** Un simulatore visivo e analitico per esplorare le metriche di convergenza, il riempimento dei veicoli e la forma spaziale delle rotte.

## 📂 Struttura del Progetto
Di seguito l'architettura delle cartelle e dei file principali, con la spiegazione del loro ruolo nel flusso di lavoro:

```text
Capacitated-Vehicle-Routing-Problem/
│
├── data/                         # [INPUT] Contiene le istanze CVRPLIB originali in formato .vrp (Set A, B, E, P).
│
├── results/                      # [OUTPUT] Generata in automatico dal codice Java.
│   ├── global_summary.csv        # Tabella riassuntiva di tutte le metriche e statistiche.
│   ├── *_best_solution.json      # Coordinate delle rotte e carico veicoli (utilizzato per disegnare le mappe).
│   └── *_convergence.csv         # Dati grezzi per tracciare il grafico di convergenza.
│
├── src/                          # [CODICE SORGENTE]
│   ├── cvrp/algorithm/           
│   │   ├── Main.java             # Entry-point: itera sui file `data/`, avvia l'ottimizzazione e salva in `results/`.
│   │   └── ClonalSelection.java  # Cuore logico: implementa CSA, LNS, Smart Initialization e Simulated Annealing.
│   │
│   ├── demo/                     # Web App Interattiva
│   │   └── app.py                # Dashboard Streamlit
│   │
│   └── utils/                    # Script di utility e scaricamento automatico istanze.
│
├── doc/                          # [DOCUMENTAZIONE]
│   └── REPORT.md                 # Relazione accademica completa per il professore.
│
├── notebooks/                    # Notebook Jupyter
│
└── README.md                     # Questo file.
```

## 🛠️ Prerequisiti
- **Java 17+** (Per l'esecuzione dell'algoritmo di ottimizzazione).
- **Python 3.9+** (Per l'analisi dei dati e l'App Web).
- Librerie Python: `streamlit`, `pandas`, `matplotlib`, `numpy`.

## ⚙️ Esecuzione del Progetto

### 1. Esecuzione dell'Algoritmo (Java)
L'algoritmo elabora le istanze della CVRPLIB (Set A, B, E, P) presenti nella cartella `data/` e salva i risultati statistici in `results/`.
```bash
# Compilazione
javac -d bin -sourcepath src src/cvrp/algorithm/Main.java

# Esecuzione
java -cp bin cvrp.algorithm.Main
```

### 2. Dashboard Interattiva (Streamlit)

🌐 **Prova l'App Online!** La dashboard è supportata da una pipeline **CI/CD** (GitHub Actions) ed è ospitata gratuitamente qui:
👉 **[Clicca per accedere alla Demo Live](https://capacitated-vehicle-routing-problem-jgnez4bsdkxthgvrgfs9mk.streamlit.app/)**

In alternativa, per esplorare visivamente i risultati in locale, avviare l'App Streamlit:
```bash
pip install -r requirements.txt
streamlit run src/demo/app.py
```

### 3. Jupyter Notebook
È possibile utilizzare il notebook generato per la consultazione statica `notebooks/CVRP.ipynb`.
