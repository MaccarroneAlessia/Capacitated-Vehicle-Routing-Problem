# Relazione Finale: Ottimizzazione del Capacitated Vehicle Routing Problem (CVRP)
**Corso:** Heuristics & Metaheuristics

---

## 1. Introduzione
Il *Capacitated Vehicle Routing Problem* (CVRP) è uno dei problemi di ottimizzazione combinatoria più studiati nella Ricerca Operativa. L'obiettivo è determinare un insieme di percorsi a costo minimo per una flotta di veicoli omogenei con capacità limitata ($Q$), partendo da un deposito centrale per servire un insieme di clienti con domande note.

Per risolvere questo problema NP-Hard, è stato sviluppato un **Algoritmo Memetico** fortemente ispirato agli *Artificial Immune Systems* (AIS), in particolare basato sul **Clonal Selection Algorithm (CSA)**.

---

## 2. Architettura dell'Algoritmo: Artificial Immune System
L'algoritmo modella il problema secondo l'analogia del sistema immunitario:
- **Antigene:** Il problema stesso (la rete dei clienti e le loro domande).
- **Anticorpo:** Una potenziale soluzione (un insieme di rotte).
- **Affinità:** Il valore di *fitness* dell'anticorpo. Poiché vogliamo minimizzare il costo (distanza percorsa), l'affinità è matematicamente definita come $1 / Costo$. Maggiore è il costo, minore è l'affinità.

L'algoritmo esegue ciclicamente 3 macro-fasi:
1. **Selezione ed Espansione Clonale:** Si selezionano gli anticorpi con la massima affinità (le rotte più brevi) e li si clona. Il numero di cloni è direttamente proporzionale al rango della soluzione (la migliore genera più cloni).
2. **Iper-Mutazione (Exploration):** I cloni subiscono mutazioni genetiche per esplorare lo spazio delle soluzioni.
3. **Ricerca Locale (Exploitation):** Le soluzioni promettenti vengono raffinate con euristiche locali.

Per rispettare i limiti computazionali richiesti, l'algoritmo impone uno **stop-criterion rigoroso a $3.5 \times 10^5$ Fitness Evaluations (valutazioni della funzione obiettivo)**.

---

## 3. Elementi di Originalità e Ottimizzazioni Custom
Il vero nucleo del progetto risiede nelle personalizzazioni avanzate ingegnerizzate per superare la stagnazione (minimi locali) tipica degli algoritmi genetici standard.

### 3.1 Smart Initialization (Costruzione Greedy)
Un algoritmo che parte da rotte generate in modo 100% puramente stocastico genera "gomitoli" inestricabili di percorsi, sprecando decine di migliaia di iterazioni solo per il *warm-up*.  
**La Soluzione:** Il 20% della popolazione iniziale è stato generato usando un'euristica costruttiva **Nearest Neighbor**. A partire dal deposito, il veicolo costruisce la rotta saltando al cliente più vicino non ancora servito, tenendo conto della capacità residua. Questo ha garantito al grafico di convergenza di partire da un costo iniziale già competitivo, lasciando il budget di calcolo per il *fine-tuning* della soluzione.

### 3.2 Iper-Mutazione LNS (Large Neighborhood Search)
Per mutare i cloni, l'algoritmo sceglie casualmente tra semplici *Swap*, *Inversioni*, ma soprattutto sfrutta un operatore custom di **Ruin & Recreate**.
- **Ruin:** Estrae un blocco di nodi consecutivi (spesso responsabili di sub-ottimalità) da una rotta.
- **Recreate:** Reinserisce iterativamente ogni nodo estratto nella posizione globalmente più economica all'interno dell'intero pool di veicoli.
L'LNS è fondamentale perché permette all'algoritmo di saltare ostacoli nello spazio di ricerca muovendo macro-blocchi di informazioni.

### 3.3 Ricerca Locale con Simulated Annealing (SA)
L'operatore **2-Opt** viene utilizzato per "sbrogliare" gli incroci dei percorsi. Tradizionalmente, la 2-Opt è una *hill-climbing*: accetta solo scambi che diminuiscono strettamente la distanza. Questo causa il blocco ai minimi locali.
**L'Innovazione:** Ho integrato il **Simulated Annealing** (SA) come criterio di accettazione della ricerca locale. Se una mossa locale è peggiorativa (costa di più), essa viene accettata con una probabilità $P = e^{-\frac{\Delta}{T}}$, dove $T$ è la "Temperatura" che decresce (Cooling Schedule) con il progredire delle valutazioni. Questa caratteristica ha eliminato i *plateau* nel grafico di convergenza.

---

## 4. Risultati e Visualizzazione
L'algoritmo è stato testato formalmente sulle istanze della **CVRPLIB** dei set A, B, E e P raccomandati. Per analizzare i dati scientificamente è stata costruita una **Dashboard in Python (Streamlit)** ed esportato un Notebook Jupyter.

🌐 **Demo Live e CI/CD:** L'applicazione Streamlit è integrata con una pipeline di **Continuous Integration (CI)** tramite GitHub Actions, che valida il codice Java e Python ad ogni aggiornamento. Inoltre, la dashboard è accessibile pubblicamente online a questo indirizzo:
🔗 **[App CVRP su Streamlit Cloud](https://capacitated-vehicle-routing-problem-jgnez4bsdkxthgvrgfs9mk.streamlit.app/)**

I grafici ottenuti (consultabili eseguendo lo script della demo o tramite la web app) mostrano:
1. **Convergenza Stabile:** Deviazione standard ridotta su 5 run indipendenti, prova della robustezza del framework.
2. **Saturazione della Capacità (Satisfability):** I grafici a barre attestano che nessun veicolo supera mai il 100% del carico, ottenendo un *Satisfability Rate* del 100% in tutte le istanze analizzate.
3. **Spazialità delle Rotte (Mappa 2D):** Le rotte ottimali disegnate confermano visivamente la totale assenza di incroci sovrapposti (i classici percorsi "a clessidra"), grazie all'azione chirurgica della 2-Opt con SA.

---
**Considerazioni Finali:**
L'introduzione della flessibilità del *Simulated Annealing* all'interno della rigidità della *Ricerca Locale*, bilanciata dal *Ruin & Recreate* a livello genetico, ha dimostrato che algoritmi ibridi superano abbondantemente la versione base del Clonal Selection Algorithm. L'utilizzo di uno stack tecnologico moderno (Java per il core-engine, Python per il dataviz interattivo) ha permesso uno studio ingegneristico profondo dei parametri.
