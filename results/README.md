# 📈 results/ (Output dell'Algoritmo)

È la cartella di destinazione di tutti i dati sfornati dall'algoritmo Java quando finisce di elaborare. Funge da "ponte" tra l'elaborazione (fatta in Java) e la visualizzazione sulla dashboard (fatta in Python).

### Contenuto della cartella:
- 📊 **[`global_summary.csv`](./global_summary.csv)**: La tabella riassuntiva che confronta i risultati (costi, iterazioni, valutazioni) di tutti i test eseguiti sulle varie istanze.
- 🎬 **[`live_frames.json`](./live_frames.json)** e **[`live_state.json`](./live_state.json)**: I "fotogrammi" e lo stato che vengono letti dalla dashboard Streamlit per fare la riproduzione live dell'algoritmo in esecuzione.
- 🗺️ **`*_best_solution.json`**: (es. `A-n32-k5_best_solution.json`) Contengono le coordinate esatte delle rotte finali per una specifica istanza, fondamentali per permettere a Python di disegnare la mappa 2D.
- 📉 **`*_convergence.csv`**: Tabelle che tracciano l'andamento del costo iterazione per iterazione per ogni run, necessarie per plottare i grafici di convergenza.
- 📋 **`*_stats.txt`**: Piccoli file testuali con le metriche isolate di una singola istanza (Best Cost, Mean Cost, ecc).
