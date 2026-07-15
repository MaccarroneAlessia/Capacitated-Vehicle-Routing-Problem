# 📈 results/ (Output dell'Algoritmo)

È la cartella di destinazione di tutti i dati sfornati dall'algoritmo Java quando finisce di elaborare. Funge da "ponte" tra l'elaborazione (fatta in Java) e la visualizzazione sulla dashboard (fatta in Python).

### Contenuto della cartella:
- 📊 **`global_summary.csv`**: La tabella riassuntiva che confronta i risultati di tutti i test eseguiti. La **Deviazione Standard** dei costi su multi-run è calcolata rigorosamente utilizzando la correzione di Bessel ($N-1$) per varianza campionaria.
- 🎞️ **`live_frames.json`** e **`live_state.json`**: I "fotogrammi" e lo stato letti dalla dashboard Streamlit per fare la riproduzione live dell'algoritmo.
- 🗺️ **`*_best_solution.json`**: Contengono le coordinate esatte delle rotte finali per una specifica istanza, fondamentali per la ricostruzione visiva delle mappe 2D.
- 📉 **`*_convergence.csv`**: Tabelle che tracciano l'andamento del costo iterazione per iterazione per ogni run, necessarie per i grafici di convergenza.
- 📝 **`*_stats.txt`**: Piccoli file testuali con metriche isolate (Best Cost, Mean Cost, Deviazione Standard campionaria, ecc) per singola istanza.
- 🔬 **`ablations/`**: Sotto-cartelle contenenti le combinazioni dello **Studio di Ablazione**. Lo studio incrociato è stato esteso per coprire le 8 configurazioni algoritmiche possibili su 4 dataset geometricamente molto diversi tra loro (es. A-n32-k5, E-n101-k14), garantendo valenza scientifica all'impatto degli operatori LNS, SA e NN.
