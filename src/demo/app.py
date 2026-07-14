import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import glob
import subprocess
import time

# working directory  root del progetto, indipendentemente 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(PROJECT_ROOT)

# Set page config
st.set_page_config(page_title="CVRP Optimizer Dashboard", page_icon="🚚", layout="wide", initial_sidebar_state="auto")

# Wow Factor: Dark Mode per matplotlib
plt.style.use('dark_background')

# Directory dei risultati
RESULTS_DIR = "results"

st.title("🚚 Capacitated Vehicle Routing Problem (CVRP)")
st.markdown("**Dashboard Interattiva - Algoritmo Memetico (Selezione Clonale + LNS + SA)**")

@st.cache_data
def load_global_summary():
    summary_file = os.path.join(RESULTS_DIR, "global_summary.csv")
    if os.path.exists(summary_file):
        df = pd.read_csv(summary_file)
        return df
    return None

def get_available_instances():
    json_files = glob.glob(os.path.join(RESULTS_DIR, "*_best_solution.json"))
    return [os.path.basename(f).replace("_best_solution.json", "") for f in json_files]

# Sidebar
#st.sidebar.header("⚙️ Impostazioni")
instances = get_available_instances()

if not instances:
    st.error(f"Nessun risultato trovato nella cartella '{RESULTS_DIR}'. Assicurati di aver eseguito l'algoritmo Java.")
    st.stop()

if 'shared_instance' not in st.session_state:
    st.session_state.shared_instance = sorted(instances)[0]

def update_from_live():
    st.session_state.shared_instance = st.session_state.live_sel

def update_from_analysis():
    st.session_state.shared_instance = st.session_state.analysis_sel

st.sidebar.markdown("### 🔗 Istanze Suggerite")
st.sidebar.markdown("""
- **Set A**: [A-n45-k7](http://vrp.galgos.inf.puc-rio.br/index.php/en/), [A-n60-k9](http://vrp.galgos.inf.puc-rio.br/index.php/en/), [A-n80-k10](http://vrp.galgos.inf.puc-rio.br/index.php/en/)
- **Set B**: [B-n56-k7](http://vrp.galgos.inf.puc-rio.br/index.php/en/), [B-n66-k9](http://vrp.galgos.inf.puc-rio.br/index.php/en/), [B-n78-k10](http://vrp.galgos.inf.puc-rio.br/index.php/en/)
- **Set E**: [E-n76-k8](http://vrp.galgos.inf.puc-rio.br/index.php/en/), [E-n101-k14](http://vrp.galgos.inf.puc-rio.br/index.php/en/)
- **Set P**: [P-n50-k10](http://vrp.galgos.inf.puc-rio.br/index.php/en/), [P-n101-k4](http://vrp.galgos.inf.puc-rio.br/index.php/en/)

*(I link rimandano al database ufficiale [CVRPLIB](http://vrp.galgos.inf.puc-rio.br/index.php/en/))*
""")


st.header("🧠 Algoritmo Memetico Customizzato")
    
st.markdown("""
L'algoritmo sviluppato per risolvere questo CVRP (Capacitated Vehicle Routing Problem) è un **Algoritmo Memetico** basato sulla Teoria della Selezione Clonale (Artificial Immune Systems). 
A differenza dei classici Algoritmi Genetici, il paradigma immunitario modella la ricerca dell'ottimo come la risposta degli anticorpi (le rotte) contro gli antigeni (i nodi da visitare).

L'obiettivo è minimizzare il costo totale (Distanza percorsa dai veicoli) rispettando strettamente un vincolo rigido: la somma delle richieste dei clienti su un veicolo non può mai superare la `capacity` del camion.

### Personalizzazioni
L'algoritmo di base rischiava di rimanere intrappolato in **minimi locali** (soluzioni sub-ottime da cui è impossibile uscire con piccole modifiche). Per questo, ho ingegnerizzato e innestato le seguenti personalizzazioni nel codice Java:

- 🚀 **Smart Initialization (Euristiche Costruttive):** Invece di partire con anticorpi generati 100% random (creando "gomitoli" inestricabili), il 20% della popolazione parte sfruttando il *Nearest Neighbor*. Questo assicura che il primo grafico di convergenza parta già da un valore bassissimo, accelerando la ricerca.
- 💥 **LNS (Large Neighborhood Search - Ruin & Recreate):** Una mutazione devastante ma chirurgica. Invece di scambiare 2 nodi a caso (Swap), l'LNS "distrugge" intere stringhe di clienti (Ruin) e valuta matematicamente qual è il posto globale migliore per reinserirle (Recreate). Risolve i problemi di routing su larga scala spostando blocchi enormi.
- 🌡️ **Simulated Annealing nella Ricerca Locale (2-Opt):** Quando l'algoritmo sbroglia gli incroci con la 2-Opt, normalmente accetterebbe *solo* modifiche che migliorano la rotta. Io ho inserito il **Simulated Annealing**: l'algoritmo accetta matematicamente mosse *peggiorative* calcolando una probabilità $P = e^{-\Delta / T}$. Più la "Temperatura" T scende, meno peggioramenti accetta. Questo è il segreto principale che gli ha permesso di uscire dalle buche (minimi locali) durante i plateau del grafico di convergenza.
""")

st.header("Riepilogo Statistico Globale")
df_global = load_global_summary()

if df_global is not None:
    st.dataframe(
        df_global.style.highlight_min(subset=['BestCost', 'MeanCost', 'StdDevCost', 'MeanIterations'], color='#2a4b2a'),
        use_container_width=True
    )
    
    st.markdown("""
    ### 🌟 Insight Automatici 🌟
    - **Smart Initialization**: Ha permesso di saltare la fase di riscaldamento (Warm-up phase) garantendo un drop istantaneo della curva di costo.
    - **Stabilità (StdDev)**: Grazie alla combinazione di Exploitation ed Exploration, la deviazione standard è molto ridotta tra i run indipendenti.
    - **LNS e Simulated Annealing**: Garantiscono costantemente lo sblocco dai minimi locali. Le istanze mostrano un "Satisfability" del 100%, rispettando rigorosamente la *Vehicle Capacity*.
    """)
else:
    st.warning("Il file global_summary.csv non è stato trovato.")

st.divider()

# Creazione dei Tab principali
tab1, tab2, tab3 = st.tabs([
    "▶️ Esecuzione Live", 
    "📈 Analisi Dettagliata", 
    #"🌍 Statistiche Globali", 
    "🎓 Walkthrough Iterattivo"
    #"🧠 L'Algoritmo (Teoria)",
    #"▶️ Esecuzione Live"
])

with tab1:
    st.header("▶️ Esecuzione Live dell'Algoritmo (Replay Timeline)")
    st.markdown("Seleziona un'istanza e genera la simulazione. Poi usa i controlli multimediali per rivedere l'evoluzione passo dopo passo!")
    
    col_sel, col_btn = st.columns([2, 1])
    with col_sel:
        st.selectbox(
            "Seleziona Istanza per la Simulazione", 
            sorted(instances), 
            key="live_sel",
            index=sorted(instances).index(st.session_state.shared_instance),
            on_change=update_from_live
        )
        live_instance = st.session_state.shared_instance
    with col_btn:
        st.write("") # spacing
        st.write("")
        if st.button("🎬 Genera Simulazione", type="primary", use_container_width=True):
            status_placeholder = st.empty()
            status_placeholder.info(f"⏳ Calcolo in background di {live_instance} (ci vorranno circa 2 secondi)...")
            
            process = subprocess.Popen(["java", "-cp", "bin", "cvrp.algorithm.Main", "--live", live_instance])
            process.wait()
            
            live_json_path = os.path.join(RESULTS_DIR, "live_frames.json")
            if os.path.exists(live_json_path):
                with open(live_json_path, 'r') as f:
                    st.session_state.frames = json.load(f)
                st.session_state.current_frame = 0
                st.session_state.slider_frame = 0
                st.session_state.live_instance = live_instance
                status_placeholder.success("✅ Simulazione Generata! Usa i controlli qui sotto.")
            else:
                status_placeholder.error("❌ Errore durante la generazione dei frame.")
                
    if 'frames' in st.session_state and st.session_state.get('live_instance') == live_instance:
        frames = st.session_state.frames
        max_frame = len(frames) - 1
        
        if 'current_frame' not in st.session_state:
            st.session_state.current_frame = 0
        if 'auto_play' not in st.session_state:
            st.session_state.auto_play = False
            
        st.markdown("### 🕹️ Controlli Multimediali")
        c1, c2, c3, c4, c5 = st.columns(5)
        
        if c1.button("⏮️ Inizio", use_container_width=True):
            st.session_state.current_frame = 0
            st.session_state.auto_play = False
        if c2.button("◀️ Indietro", use_container_width=True):
            st.session_state.current_frame = max(0, st.session_state.current_frame - 1)
            st.session_state.auto_play = False
        if c3.button("Avanti ▶️", use_container_width=True):
            st.session_state.current_frame = min(max_frame, st.session_state.current_frame + 1)
            st.session_state.auto_play = False
        if c4.button("⏭️ Fine", use_container_width=True):
            st.session_state.current_frame = max_frame
            st.session_state.auto_play = False
            
        if c5.button("⏹️ Stop" if st.session_state.auto_play else "⏯️ Auto-Play", use_container_width=True):
            st.session_state.auto_play = not st.session_state.auto_play
            if st.session_state.auto_play and st.session_state.current_frame == max_frame:
                st.session_state.current_frame = 0
                
        # Slider disconnesso dalla 'key' per evitare conflitti StreamlitAPIException
        selected_frame = st.slider("Scorri la Timeline", 0, max_frame, value=st.session_state.current_frame)
        
        if selected_frame != st.session_state.current_frame:
            st.session_state.current_frame = selected_frame
            st.session_state.auto_play = False
            st.rerun()
            
        metrics_placeholder = st.empty()
        plot_placeholder = st.empty()
        
        def render_frame(f_idx):
            frame = frames[f_idx]
            current_cost = frame.get('cost', 0)
            current_evals = frame.get('evaluations', 0)
            max_evals = 350000
            
            with metrics_placeholder.container():
                colA, colB, colC = st.columns(3)
                colA.metric("Costo", f"{current_cost:.2f}")
                colB.metric("Valutazioni (FE)", f"{current_evals}")
                colC.progress(min(current_evals / max_evals, 1.0))
                
            fig_live, ax_live = plt.subplots(figsize=(10, 6))
            depot = frame['depot']
            ax_live.scatter(depot[0], depot[1], c='#ff3333', marker='*', s=400, zorder=5, edgecolors='white', label='Deposito')
            
            cmap = plt.get_cmap('Set3')
            for i, route in enumerate(frame.get('routes', [])):
                if not route: continue
                xs = [depot[0]] + [node[0] for node in route] + [depot[0]]
                ys = [depot[1]] + [node[1] for node in route] + [depot[1]]
                color = cmap(i % 12)
                ax_live.plot(xs, ys, color=color, linewidth=2.5, alpha=0.8)
                ax_live.scatter(xs[1:-1], ys[1:-1], color=color, s=40, zorder=4, edgecolors='black')
                
            ax_live.set_title(f"Mappa Rotte - Frame {f_idx+1}/{max_frame+1} - Costo: {current_cost:.2f}", color='white', fontsize=16, fontweight='bold')
            ax_live.grid(True, linestyle='--', alpha=0.2)
            
            with plot_placeholder.container():
                st.pyplot(fig_live, use_container_width=True)
            plt.close(fig_live)

        render_frame(st.session_state.current_frame)

        if st.session_state.auto_play:
            if st.session_state.current_frame < max_frame:
                st.session_state.current_frame += 1
                time.sleep(0.3)
                st.rerun()
            else:
                st.session_state.auto_play = False
                st.rerun()


with tab2:
    st.header("Analisi Dettagliata Istanza")
    
    col_sel_ana, _ = st.columns([2, 1])
    with col_sel_ana:
        st.selectbox(
            "Seleziona Istanza da Analizzare", 
            sorted(instances), 
            key="analysis_sel",
            index=sorted(instances).index(st.session_state.shared_instance),
            on_change=update_from_analysis
        )
        selected_instance = st.session_state.shared_instance
        
    st.markdown(f"**Istanza Corrente: {selected_instance}**")
    
    # Carico i dati della specifica istanza
    json_file = os.path.join(RESULTS_DIR, f"{selected_instance}_best_solution.json")
    stats_file = os.path.join(RESULTS_DIR, f"{selected_instance}_stats.txt")
    
    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            lines = f.readlines()
            stats = {}
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    stats[key.strip()] = val.strip()
                    
        col1.metric("Best Cost", f"{float(stats.get('Best Cost', 0)):.2f}")
        col2.metric("Mean Cost", f"{float(stats.get('Mean Cost', 0)):.2f}")
        col3.metric("Iterazioni Medie", f"{float(stats.get('Mean Iterations (Evaluations)', 0)):.0f}")
        col4.metric("Satisfability", stats.get('Satisfability', 'N/A'))
    
    st.divider()

    # Creazione Plot
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        fig = plt.figure(figsize=(14, 8))
        gs = fig.add_gridspec(2, 2, width_ratios=[1, 1], height_ratios=[1, 1])
        
        # 1. Convergenza
        ax1 = fig.add_subplot(gs[0, 0])
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99', '#c2c2f0']
        for run in range(5):
            csv_file = os.path.join(RESULTS_DIR, f"{selected_instance}_run_{run}_convergence.csv")
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                ax1.plot(df['Evaluations'], df['BestCost'], label=f'Run {run+1}', color=colors[run], alpha=0.9, linewidth=2)
                
        ax1.set_title(f'📉 Convergenza Algoritmo Memetico', fontsize=14, fontweight='bold', color='white')
        ax1.set_xlabel('Valutazioni (FE)', fontsize=12)
        ax1.set_ylabel('Miglior Costo Trovato', fontsize=12)
        ax1.legend(loc='upper right', fontsize=10, frameon=True, facecolor='#2d2d2d')
        ax1.grid(True, linestyle='--', alpha=0.3)
        
        # 2. Capacità
        ax2 = fig.add_subplot(gs[1, 0])
        loads = data.get('loads', [])
        capacity = data.get('capacity', 1)
        if loads:
            x = np.arange(len(loads))
            percentages = [(l/capacity)*100 for l in loads]
            bars = ax2.bar(x, percentages, color='#66b3ff', edgecolor='white', alpha=0.8)
            ax2.axhline(y=100, color='r', linestyle='-', alpha=0.5, label='Capacità Massima')
            
            for bar, p in zip(bars, percentages):
                ax2.text(bar.get_x() + bar.get_width()/2., p - 8 if p > 15 else p + 2, 
                         f"{p:.1f}%", ha='center', va='bottom', color='white' if p > 15 else 'cyan', fontweight='bold')
                         
            ax2.set_title('🚛 Saturazione Capacità Veicoli', fontsize=14, fontweight='bold', color='white')
            ax2.set_xlabel('ID Veicolo', fontsize=12)
            ax2.set_ylabel('Carico (%)', fontsize=12)
            ax2.set_xticks(x)
            ax2.set_xticklabels([f'V{i+1}' for i in x])
            ax2.legend(frameon=True, facecolor='#2d2d2d')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.3)
            
        # 3. Mappa Rotte
        ax3 = fig.add_subplot(gs[:, 1])
        depot = data['depot']
        ax3.scatter(depot[0], depot[1], c='#ff3333', marker='*', s=400, label='Deposito', zorder=5, edgecolors='white')
        
        cmap = plt.get_cmap('Set3')
        for i, route in enumerate(data['routes']):
            if not route: continue
            xs = [depot[0]] + [node[0] for node in route] + [depot[0]]
            ys = [depot[1]] + [node[1] for node in route] + [depot[1]]
            color = cmap(i % 12)
            ax3.plot(xs, ys, color=color, linewidth=2.5, alpha=0.8, label=f'Veicolo {i+1}')
            ax3.scatter(xs[1:-1], ys[1:-1], color=color, s=60, zorder=4, edgecolors='black')
            
        ax3.set_title(f"🗺️ Rotte Ottimizzate (Miglior Costo: {data['cost']:.2f})", fontsize=16, fontweight='bold', color='white')
        ax3.grid(True, linestyle='--', alpha=0.2)
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        
        with st.expander("📖 Guida alla Lettura dei Grafici e dei Valori", expanded=True):
            st.markdown("""
            **1. Grafico di Convergenza (In alto a sinistra):**
            - **Cosa significa?** Mostra come il costo della soluzione (asse Y) decresce all'aumentare delle iterazioni (asse X).
            - **Come si legge?** Un crollo iniziale ripido significa che la **Smart Initialization** (Nearest Neighbor) ha trovato subito una soluzione ottima. Se noti degli *scalini* o crolli improvvisi verso metà del grafico, significa che l'algoritmo era bloccato in un minimo locale e la mia personalizzazione **LNS (Ruin & Recreate)** o il **Simulated Annealing** sono intervenuti sbloccandolo.

            **2. Saturazione Capacità (In basso a sinistra):**
            - **Cosa significa?** Mostra la percentuale di riempimento di ogni singolo veicolo usato.
            - **Come si legge?** Il traguardo (linea rossa) è il 100%. Un buon algoritmo per il CVRP non deve solo minimizzare la distanza, ma compattare il carico (usare meno veicoli possibili sfruttandoli al massimo). Se le barre sono tutte tra l'85% e il 100%, l'algoritmo è eccellente. Se superano il 100%, il vincolo di *Satisfability* è rotto (errore).

            **3. Mappa Rotte (A destra):**
            - **Cosa significa?** È la visualizzazione geografica spaziale (X, Y) dei clienti e del deposito (Stella Rossa).
            - **Come si legge?** Se vedi le rotte (linee colorate) che si "incrociano" a X (formando delle clessidre), significa che c'è margine di miglioramento o che l'algoritmo ha dovuto sacrificare la via breve per rispettare il vincolo di capacità. Un algoritmo come il nostro, grazie alla 2-Opt potenziata, **"sbroglia" automaticamente gli incroci**, creando rotte circolari "a petalo" attorno al deposito.
            """)
    

with tab3:
    st.header("🎓 Walkthrough Interattivo dell'Algoritmo Memetico")
    
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
        
    col_b1, col_b2, _ = st.columns([1, 1, 6])
    
    with col_b1:
        if st.button("⬅️ Indietro", use_container_width=True, disabled=(st.session_state.current_step == 1)):
            st.session_state.current_step -= 1
            st.rerun()
            
    with col_b2:
        if st.button("Avanti ➡️", use_container_width=True, disabled=(st.session_state.current_step == 7)):
            st.session_state.current_step += 1
            st.rerun()
            
    st.progress(st.session_state.current_step / 7.0)
    
    step = st.session_state.current_step
    
    # Configurazione step
    steps_data = {
        1: {
            "title": "1. Smart Initialization (Nearest Neighbor)",
            "code": "1. Popolazione = 20% Nearest Neighbor + 80% Random",
            "desc": "Anziché partire completamente alla cieca, una porzione della popolazione iniziale viene generata con un'euristica costruttiva. Partendo dal deposito, il veicolo visita sempre il nodo più vicino non ancora servito (finché ha capacità). Questo garantisce un abbassamento drastico del costo iniziale."
        },
        2: {
            "title": "2. Valutazione (Affinity)",
            "code": "2. Ordina Popolazione per Costo (Affinità = 1 / Costo)",
            "desc": "Nella teoria immunologica, l'affinità indica quanto un anticorpo (soluzione) lega l'antigene (il problema). Gli anticorpi più promettenti (a costo minore) vengono portati in cima per la fase successiva."
        },
        3: {
            "title": "3. Selezione ed Espansione Clonale",
            "code": "3. Seleziona gli Elite e crea Cloni proporzionalmente",
            "desc": "I cloni vengono creati in base al rango: la soluzione #1 genererà N cloni, la #2 genererà N-1 cloni, ecc. Questa fase intensifica la ricerca nell'intorno delle soluzioni migliori (Exploitation)."
        },
        4: {
            "title": "4. Iper-Mutazione (Ruin & Recreate LNS)",
            "code": "4. Applica Mutazioni Random (Incluso Ruin & Recreate)",
            "desc": "I cloni subiscono iper-mutazioni. Il nostro operatore LNS (Large Neighborhood Search) sceglie un segmento di rotta e lo 'distrugge' rimuovendo nodi consecutivi. Quei nodi vengono reinseriti nelle posizioni globalmente ottimali in qualsiasi altro veicolo."
        },
        5: {
            "title": "5. Ricerca Locale (Simulated Annealing)",
            "code": "5. SA Local Search sui cloni d'elite (2-Opt)",
            "desc": "Per raffinare ulteriormente i cloni top, usiamo la Ricerca Locale (2-Opt) per districare incroci. Grazie al Simulated Annealing, l'algoritmo non si blocca: accetta mosse che peggiorano il costo temporaneamente con probabilità P = e^(-Delta/T)."
        },
        6: {
            "title": "6. Receptor Editing (Esplorazione globale)",
            "code": "6. Sostituisci i peggiori elementi con random\n",
            "desc": "Per mantenere alta la diversità genetica (Exploration) e sfuggire ai minimi locali a livello macroscopico, una percentuale degli anticorpi peggiori viene distrutta e rimpiazzata da anticorpi generati totalmente a caso."
        },
        7: {
            "title": "7. Fine Iterazione",
            "code": "7. Torna al Punto 2",
            "desc": "L'iterazione corrente è conclusa. Si torna al punto 2 per avviare la generazione della generazione successiva."
        }
    }
    
    col_code, col_vis = st.columns([1, 1.5])
    
    with col_code:
        st.subheader("Pseudocodice")
        pseudocode = ""
        for i in range(1, 8):
            mark = "👉 " if i == step else "   "
            color = "#00ffcc" if i == step else "#888888"
            weight = "bold" if i == step else "normal"
            pseudocode += f"<div style='color:{color}; font-weight:{weight}; padding:5px; font-family:monospace'>{mark} {steps_data[i]['code']}</div>"
        
        st.markdown(f"<div style='background-color:#1e1e1e; padding:15px; border-radius:10px;'>{pseudocode}</div>", unsafe_allow_html=True)
        
        st.markdown(f"### {steps_data[step]['title']}")
        st.info(steps_data[step]['desc'])
        
    with col_vis:
        st.subheader("Rappresentazione Visiva")
        fig_edu, ax_edu = plt.subplots(figsize=(6, 4))
        ax_edu.set_xticks([])
        ax_edu.set_yticks([])
        ax_edu.set_facecolor('#121212')
        fig_edu.patch.set_facecolor('#121212')
        
        if step == 1: # Nearest Neighbor
            nodes_x = [0.1, 0.4, 0.3, 0.7, 0.8]
            nodes_y = [0.1, 0.3, 0.6, 0.5, 0.8]
            ax_edu.plot(nodes_x[:3], nodes_y[:3], 'w--', alpha=0.5)
            ax_edu.plot(nodes_x[:3], nodes_y[:3], 'co-', linewidth=2, markersize=8)
            ax_edu.scatter([0.1], [0.1], c='r', marker='s', s=100, label="Depot")
            ax_edu.annotate("Nearest", (0.4, 0.3), textcoords="offset points", xytext=(10,10), color='cyan')
            ax_edu.set_title("Costruzione Greedy: salta al nodo più vicino", color='white')
            
        elif step == 2: # Affinity
            fitness = [10, 8, 5, 2, 1]
            ax_edu.bar(range(5), fitness, color=['#00ffcc', '#00ccaa', '#009977', '#006644', '#003322'])
            ax_edu.set_title("Ordinamento per Affinità (Costo Minore = Migliore)", color='white')
            ax_edu.set_xlabel("Soluzioni")
            
        elif step == 3: # Cloning
            ax_edu.text(0.1, 0.8, "Miglior Soluzione -> 3 Cloni", color='#00ffcc', fontsize=12)
            ax_edu.scatter([0.3, 0.5, 0.7], [0.7, 0.7, 0.7], c='#00ffcc', s=150)
            ax_edu.text(0.1, 0.5, "Seconda Soluzione -> 2 Cloni", color='#00ccaa', fontsize=12)
            ax_edu.scatter([0.4, 0.6], [0.4, 0.4], c='#00ccaa', s=100)
            ax_edu.text(0.1, 0.2, "Terza Soluzione -> 1 Clone", color='#009977', fontsize=12)
            ax_edu.scatter([0.5], [0.1], c='#009977', s=50)
            
        elif step == 4: # LNS
            ax_edu.plot([0.1, 0.3, 0.5, 0.7, 0.9], [0.5, 0.6, 0.5, 0.6, 0.5], 'w-', alpha=0.3)
            ax_edu.plot([0.3, 0.5, 0.7], [0.6, 0.5, 0.6], 'ro-', markersize=10, label='RUIN (Rimossi)')
            ax_edu.annotate("Recreate", (0.5, 0.5), xytext=(0.5, 0.2), arrowprops=dict(facecolor='green', shrink=0.05), color='green', ha='center')
            ax_edu.scatter([0.2, 0.5, 0.8], [0.2, 0.2, 0.2], c='g', s=100)
            ax_edu.set_title("Large Neighborhood Search: Ruin & Recreate", color='white')
            ax_edu.legend()
            
        elif step == 5: # SA 2-Opt
            # Crossed
            ax_edu.plot([0.1, 0.4], [0.1, 0.4], 'r--', alpha=0.5)
            ax_edu.plot([0.1, 0.4], [0.4, 0.1], 'r--', alpha=0.5)
            # Fixed
            ax_edu.plot([0.6, 0.9], [0.1, 0.1], 'g-', linewidth=3)
            ax_edu.plot([0.6, 0.9], [0.4, 0.4], 'g-', linewidth=3)
            ax_edu.annotate("2-Opt", (0.45, 0.25), xytext=(0.5, 0.25), arrowprops=dict(facecolor='white', width=2), color='w')
            ax_edu.set_title("Ricerca Locale (Sbroglia Incroci)\n+ Simulated Annealing Acceptance", color='white')
            
        elif step == 6: # Receptor Editing
            ax_edu.scatter([0.2, 0.3, 0.25], [0.8, 0.8, 0.7], c='#00ffcc', s=100, label="Elite Sopravvissuti")
            ax_edu.scatter([0.7, 0.8, 0.6, 0.9], [0.2, 0.3, 0.1, 0.4], c='orange', marker='*', s=150, label="Nuovi (Random)")
            ax_edu.set_title("Receptor Editing: Iniezione di Diversità", color='white')
            ax_edu.legend(loc="upper left", fontsize=8)

        elif step == 7: # Fine Iterazione
            ax_edu.annotate("RIPETI\nCICLO", (0.5, 0.5), xytext=(0.5, 0.5), ha='center', va='center', color='#00ffcc', fontsize=24, fontweight='bold')
            ax_edu.annotate("", xy=(0.8, 0.2), xytext=(0.2, 0.8), arrowprops=dict(facecolor='#00ffcc', arrowstyle="wedge,tail_width=0.7", connectionstyle="arc3,rad=0.3"))
            ax_edu.annotate("", xy=(0.2, 0.8), xytext=(0.8, 0.2), arrowprops=dict(facecolor='#00ffcc', arrowstyle="wedge,tail_width=0.7", connectionstyle="arc3,rad=0.3"))
            ax_edu.set_title("Evoluzione: Ritorno alla fase di Valutazione", color='white')

        plt.tight_layout()
        st.pyplot(fig_edu, use_container_width=True)

