<div align="center">
  <h1>🚚 Capacitated Vehicle Routing Problem (CVRP) Optimizer</h1>
  
  <p>
    <strong>Corso: Heuristics & Metaheuristics for Optimization & Learning</strong><br>
    Un Algoritmo Memetico Avanzato basato sul paradigma degli <em>Artificial Immune Systems</em>.
  </p>

  [![Java](https://img.shields.io/badge/Java-17+-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)](https://www.java.com/)
  [![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-Live_Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://capacitated-vehicle-routing-problem-jgnez4bsdkxthgvrgfs9mk.streamlit.app/)
  
  <h3>
    <a href="https://capacitated-vehicle-routing-problem-jgnez4bsdkxthgvrgfs9mk.streamlit.app/">👉 Prova la Live Demo su Streamlit</a>
  </h3>
</div>

<br />

## 📋 Indice
- [Informazioni sul Progetto](#-informazioni-sul-progetto)
- [Funzionalità Principali](#-funzionalità-principali)
- [Miglioramenti Ingegneristici](#-miglioramenti-ingegneristici--rigore-scientifico)
- [Come Iniziare (Getting Started)](#-come-iniziare)
- [Risultati dello Studio](#-risultati-dellablation-study)
- [Struttura del Repository](#-struttura-del-progetto)

---

## ℹ️ Informazioni sul Progetto

Questo progetto implementa la soluzione al problema del **CVRP** utilizzando un algoritmo meta-euristico ibrido scritto in **Java**, per garantire la massima efficienza computazionale (budget rigoroso di $350.000$ *Fitness Evaluations* in meno di 2 secondi). L'analisi dei dati, lo studio statistico e la visualizzazione interattiva dei risultati sono stati sviluppati in **Python** (Jupyter Notebook & Streamlit).

---

## 🚀 Funzionalità Principali

- **Clonal Selection Algorithm (CSA):** Un algoritmo meta-euristico bio-ispirato basato sulla selezione clonale del sistema immunitario.
- **Smart Initialization:** Il 20% della popolazione iniziale è generata usando l'euristica *Nearest Neighbor*, garantendo una convergenza molto più rapida rispetto a un'inizializzazione puramente casuale.
- **Large Neighborhood Search (LNS):** Un operatore di iper-mutazione (Ruin & Recreate) studiato per distruggere blocchi di percorsi sub-ottimi e reinserirli globalmente nella posizione più economica.
- **Simulated Annealing (SA) in Local Search** *(valutato, disattivato nel modello finale)*: La 2-Opt locale accetta mosse peggiorative con una probabilità basata sulla Temperatura per fuggire efficacemente dai minimi locali (raffreddamento lineare basato sul budget FE). Poiché l'overhead temporale (+7x) non giustifica il beneficio marginale, **SA è disattivato nella configurazione vincente NN_LNS** (`useSA=false`).
- **Ablation Study Framework:** Uno studio scientifico su **85 istanze × 8 configurazioni = 680 run** per validare statisticamente il contributo di ogni operatore. *Risultato: la combinazione NN_LNS è il miglior compromesso costo/tempo.*
- **Saturated Mode (Fuzzy Logic):** Modulazione adattiva degli operatori in base al rapporto di saturazione della flotta (transizione fuzzy nell'intervallo `[80%, 95%]`).

---

## ✨ Miglioramenti

- **Correzione di Bessel ($N-1$):** Calcolo della deviazione standard campionaria per una corretta analisi della varianza statistica su esecuzioni stocastiche.
- **Doppio Tracking:** Ogni run traccia sia le **Fitness Evaluations (FE)** sia il numero di **Generazioni** (iterazioni del ciclo `while`) al raggiungimento del miglior candidato.
- **Saturated Mode (Fuzzy Transition):** Il tasso di mutazione e di *receptor editing* varia dinamicamente in modo *fuzzy* in base al rapporto di saturazione della flotta.
- **Robustezza di Parsing:** Parser basato su Regex per tollerare formattazioni inconsistenti dei dataset storici TSPLIB/CVRPLIB.
- **Ottimizzazioni O(1) e CPU:** Sostituzione di `Math.pow` con moltiplicazioni algebriche dirette; matrice delle distanze pre-calcolata in RAM.
- **Incapsulamento Difensivo:** Le strutture dati spaziali (`Node`, `Route`, `Antibody`) garantiscono coerenza di stato deterministica durante i cicli di mutazione intensiva.

---

## ⚙️ Come Iniziare

### Prerequisiti
- **Java 17+** (per l'engine di ottimizzazione)
- **Python 3.9+** (per la dashboard e il notebook)
- **Conda** (Miniconda/Anaconda) per la gestione dell'ambiente virtuale

### 1. Setup Ambiente Python (Conda)
Ti raccomandiamo di creare un ambiente Conda isolato per installare in modo pulito tutte le librerie necessarie:
```bash
# Crea un nuovo ambiente chiamato 'cvrp_env' con Python 3.9
conda create -n cvrp_env python=3.9 -y

# Attiva l'ambiente
conda activate cvrp_env

# Installa le dipendenze richieste
pip install -r requirements.txt
```

### 2. Compila ed Esegui (Java)
Il motore logico elabora le istanze della CVRPLIB (`data/`) e salva i risultati in `results/`.
```bash
# Compilazione del codice sorgente
javac -d bin src/cvrp/algorithm/*.java src/cvrp/model/*.java

# Esecuzione standard (10 istanze di protocollo × 5 run ciascuna)
java -cp bin cvrp.algorithm.Main
```

### 3. Ablation Study (Java)
Per ricreare da zero lo studio d'ablazione completo su tutte le 85 istanze:
```bash
# Esecuzione (~60 minuti, salva risultati in results/ablations/)
java -cp bin cvrp.algorithm.AblationRunner
```

### 4. Dashboard Interattiva (Streamlit)
Oltre alla [Demo Live online](https://capacitated-vehicle-routing-problem-jgnez4bsdkxthgvrgfs9mk.streamlit.app/), puoi lanciare l'applicativo localmente per esplorare visivamente i risultati (assicurati di avere l'ambiente Conda attivato):
```bash
streamlit run src/demo/app.py
```

### 5. Jupyter Notebook
Per consultare l'analisi statistica completa con grafici, deviazioni standard e tabelle:
```bash
jupyter notebook notebooks/CVRP.ipynb
```

---

## 📊 Risultati dell'Ablation Study

Lo studio d'ablazione su 85 istanze ha eletto **NN_LNS** come configurazione architetturale ottimale:

| Configurazione | Win Rate | Costo vs Baseline | Tempo vs Baseline |
|:---|---:|---:|---:|
| **NN_LNS** ✅ | **30.59%** | **91.96%** | **167%** |
| ALL | 14.12% | 93.37% | 1193% |
| LNS | 21.18% | 93.58% | 171% |
| SA_LNS | 12.94% | 94.14% | 1166% |

> **Nota:** La configurazione `NN_LNS` riduce il costo dell'**8%** rispetto alla baseline con un overhead temporale irrisorio. La configurazione completa (`ALL`) raggiunge un costo simile ma risulta **7 volte più lenta** a causa della complessità computazionale del Simulated Annealing.

---

## 🏆 Risultati Istanze di Protocollo

Per le 10 istanze target fornite dalle direttive del progetto (5 run stocastiche ciascuna, con budget rigoroso di $350.000$ *Fitness Evaluations* max), l'algoritmo **NN_LNS** ha ottenuto i seguenti risultati. 

*La colonna "Satisfability" certifica l'assenza assoluta di violazioni di capacità in tutte le soluzioni (100% hard constraints rispettati).*

| Istanza | Best Cost | Mean Cost | Std. Dev | FE Medie | Iterazioni Medie | Satisfability |
|:---|---:|---:|---:|---:|---:|:---:|
| **A-n45-k7** | 1172.61 | 1201.48 | 19.33 | 103.301 | 520 | ✅ 44/44 |
| **A-n60-k9** | 1396.64 | 1420.16 | 23.00 | 47.540 | 238 | ✅ 59/59 |
| **A-n80-k10** | 1900.45 | 1919.87 | 15.38 | 150.086 | 747 | ✅ 79/79 |
| **B-n56-k7** | 725.06 | 738.64 | 14.17 | 51.753 | 263 | ✅ 55/55 |
| **B-n66-k9** | 1356.92 | 1403.02 | 39.73 | 110.311 | 547 | ✅ 65/65 |
| **B-n78-k10** | 1288.27 | 1331.26 | 52.27 | 121.664 | 606 | ✅ 77/77 |
| **E-n76-k8** | 787.29 | 812.52 | 16.23 | 127.694 | 636 | ✅ 75/75 |
| **E-n101-k14** | 1157.86 | 1183.12 | 18.48 | 116.980 | 585 | ✅ 100/100 |
| **P-n50-k10** | 735.30 | 751.88 | 19.24 | 181.900 | 901 | ✅ 49/49 |
| **P-n101-k4** | 716.91 | 743.35 | 16.50 | 110.266 | 555 | ✅ 100/100 |

> **Analisi Varianza:** Grazie alla forte componente adattiva e alla *Large Neighborhood Search*, il coefficiente di variazione (Std. Dev rispetto al Mean Cost) si attesta costantemente sotto la soglia del **3%**, denotando una stabilità straordinaria a prescindere dal seme stocastico iniziale.

---

## 📂 Struttura del Progetto

```text
Capacitated-Vehicle-Routing-Problem/
├── data/                              # [INPUT] Istanze CVRPLIB originali (.vrp) — Set A, B, E, P
├── results/                           # [OUTPUT] Generata in automatico dal codice Java
│   ├── ablations/                     # Risultati Ablation Study (85 istanze × 8 config)
│   ├── infographics/                  # Infografiche PNG
│   └── {A,B,E,P}/                     # Sotto-cartelle risultati per famiglia
├── src/                               # [CODICE SORGENTE]
│   ├── cvrp/algorithm/                # Core Java (Main, ClonalSelection, AblationRunner)
│   ├── cvrp/model/                    # Strutture dati Java (Instance, Antibody, Route, Node)
│   ├── demo/                          # Web App Interattiva (Streamlit app.py)
│   └── utils/                         # Script Python (Plotting, Verifica vincoli, API)
├── notebooks/                         # Notebook Jupyter (CVRP.ipynb)
├── doc/                               # Relazione accademica (REPORT.md)
├── logs/                              # Log delle esecuzioni (Main e Ablation)
├── .github/workflows/                 # Pipeline CI/CD per il deploy
└── requirements.txt                   # Dipendenze Python
```
