"""
Dashboard interattiva (Streamlit) per i risultati del CVRP.

Legge gli output prodotti dall'algoritmo Java (CSV di convergenza, JSON delle
soluzioni, statistiche) e li mostra in tre viste: esecuzione live, analisi
dettagliata di una singola istanza, walkthrough didattico dell'algoritmo.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import os
import glob
import subprocess
import time

# Root del progetto, indipendentemente da dove viene lanciato lo script
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(PROJECT_ROOT)

# Set page config
st.set_page_config(page_title="CVRP Optimizer Dashboard", page_icon="🚚", layout="wide", initial_sidebar_state="auto")

RESULTS_DIR = "results"

# ---------------------------------------------------------------------------
# Tema grafico condiviso da tutti i chart Plotly della dashboard
# ---------------------------------------------------------------------------
BG = "#0e1117"
GRID = "rgba(255,255,255,0.08)"
TEXT = "#e6e6e6"
ACCENT = "#2dd4bf"     # teal - colore principale
DEPOT_COLOR = "#f87171"  # rosso corallo per il deposito
HOVER_BG = "#1e1e1e"
ROUTE_LINE_COLOR = "#111"
HIGHLIGHT_COLOR = "#134e4a"
INACTIVE_TEXT = "#888888"
SUCCESS_COLOR = "#4ade80"
WARNING_COLOR = "orange"
YELLOW_WARNING = "#facc15"
WHITE = "white"
TRANSPARENT = "rgba(0,0,0,0)"
RANK_GRADIENT = ["#2dd4bf", "#25a693", "#1c7871", "#144a4f", "#0b1c2c"]

ROUTE_PALETTE = [
    ACCENT, "#60a5fa", "#f472b6", YELLOW_WARNING, "#a78bfa",
    SUCCESS_COLOR, "#fb923c", "#38bdf8", "#e879f9", "#fbbf24",
    "#94a3b8", DEPOT_COLOR,
]

def style_fig(fig, title=None, height=420):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, size=13),
        title=dict(text=title, font=dict(size=17, color=WHITE)) if title else None,
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        height=height,
        legend=dict(bgcolor=TRANSPARENT),
        hoverlabel=dict(bgcolor=HOVER_BG, font_size=12),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def route_map_figure(depot, routes, title, cost=None):
    fig = go.Figure()
    for i, route in enumerate(routes):
        if not route:
            continue
        xs = [depot[0]] + [n[0] for n in route] + [depot[0]]
        ys = [depot[1]] + [n[1] for n in route] + [depot[1]]
        color = ROUTE_PALETTE[i % len(ROUTE_PALETTE)]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers", name=f"Veicolo {i+1}",
            line=dict(color=color, width=2.5),
            marker=dict(size=7, color=color, line=dict(width=1, color=ROUTE_LINE_COLOR)),
            hovertemplate=f"Veicolo {i+1}<br>x=%{{x:.1f}}, y=%{{y:.1f}}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=[depot[0]], y=[depot[1]], mode="markers", name="Deposito",
        marker=dict(symbol="star", size=20, color=DEPOT_COLOR, line=dict(width=1, color=WHITE)),
        hovertemplate="Deposito<extra></extra>",
    ))
    full_title = title if cost is None else f"{title} — costo {cost:.2f}"
    fig = style_fig(fig, full_title, height=520)
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig


# ---------------------------------------------------------------------------
# Caricamento dati
# ---------------------------------------------------------------------------
def load_global_summary():
    summary_file = os.path.join(RESULTS_DIR, "global_summary.csv")
    if os.path.exists(summary_file):
        return pd.read_csv(summary_file)
    return None

def get_available_instances():
    json_files = glob.glob(os.path.join(RESULTS_DIR, "*_best_solution.json"))
    return [os.path.basename(f).replace("_best_solution.json", "") for f in json_files]


st.title("🚚 Capacitated Vehicle Routing Problem (CVRP)")
st.caption("Algoritmo memetico: selezione clonale + Large Neighborhood Search + Simulated Annealing")

instances = get_available_instances()
if not instances:
    st.error(f"Nessun risultato nella cartella '{RESULTS_DIR}'. Esegui prima l'algoritmo Java.")
    st.stop()

if "shared_instance" not in st.session_state:
    st.session_state.shared_instance = sorted(instances)[0]

def update_from_live():
    st.session_state.shared_instance = st.session_state.live_sel

def update_from_analysis():
    st.session_state.shared_instance = st.session_state.analysis_sel

st.sidebar.markdown("### 🔗 Istanze di riferimento")
st.sidebar.markdown("""
Dataset [CVRPLIB](http://vrp.galgos.inf.puc-rio.br/index.php/en/):
- **A**: A-n45-k7, A-n60-k9, A-n80-k10
- **B**: B-n56-k7, B-n66-k9, B-n78-k10
- **E**: E-n76-k8, E-n101-k14
- **P**: P-n50-k10, P-n101-k4
""")

# ---------------------------------------------------------------------------
# Introduzione all'algoritmo 
# ---------------------------------------------------------------------------
st.header("🧠 Come funziona l'algoritmo")
st.markdown("""
È un algoritmo memetico ispirato alla selezione clonale del sistema immunitario: le rotte sono
"anticorpi" che competono per adattarsi meglio al problema. L'obiettivo è minimizzare la distanza
totale percorsa senza mai superare la capacità dei veicoli.

Per evitare che restasse bloccato in soluzioni sub-ottime, sono stati aggiunti tre elementi:

- **Partenza intelligente** — il 20% della popolazione iniziale non è casuale ma costruita con il
  criterio del vicino più prossimo, così si parte già da un costo basso invece che da un groviglio.
- **Ruin & Recreate (LNS)** — invece di scambiare due nodi alla volta, l'algoritmo a volte smonta
  interi tratti di rotta e li ricolloca dove convengono davvero, anche su un altro veicolo.
- **Simulated Annealing nella 2-Opt** — durante la ricerca locale, accetta anche mosse che
  peggiorano temporaneamente il costo (con probabilità $P = e^{-\\Delta/T}$, decrescente nel
  tempo). È questo che permette di uscire dai minimi locali visibili come "gradini" nel grafico
  di convergenza.
""")

st.header("Riepilogo statistico")
df_global = load_global_summary()

if df_global is not None and not df_global.empty:
    st.dataframe(
        df_global.style.highlight_min(subset=['BestCost', 'MeanCost', 'StdDevCost', 'MeanIterations'], color=HIGHLIGHT_COLOR),
        use_container_width=True
    )
    st.caption(
        "La bassa deviazione standard tra run indipendenti indica un buon equilibrio tra "
        "sfruttamento (exploitation) ed esplorazione (exploration); la Satisfability al 100% "
        "conferma che il vincolo di capacità è sempre rispettato."
    )
else:
    st.warning("Riepilogo statistico globale vuoto o non trovato. Esegui l'algoritmo Java senza la modalità live per generarlo.")

st.divider()

tab1, tab2, tab3 = st.tabs([
    "▶️ Esecuzione Live",
    "📈 Analisi Dettagliata",
    "🎓 Walkthrough",
])

# ---------------------------------------------------------------------------
# TAB 1 — Live
# ---------------------------------------------------------------------------
with tab1:
    st.header("Replay dell'esecuzione")
    st.markdown("Scegli un'istanza, genera la simulazione, poi scorri i frame per vedere l'algoritmo evolvere.")

    col_sel, col_btn = st.columns([2, 1])
    with col_sel:
        st.selectbox(
            "Istanza", sorted(instances), key="live_sel",
            index=sorted(instances).index(st.session_state.shared_instance),
            on_change=update_from_live
        )
        live_instance = st.session_state.shared_instance
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🎬 Genera simulazione", type="primary", use_container_width=True):
            status_placeholder = st.empty()
            status_placeholder.info(f"⏳ Calcolo di {live_instance} in corso (circa 2 secondi)...")
            process = subprocess.Popen(["java", "-cp", "bin", "cvrp.algorithm.Main", "--live", live_instance])
            process.wait()

            live_json_path = os.path.join(RESULTS_DIR, "live_frames.json")
            if os.path.exists(live_json_path):
                with open(live_json_path, 'r') as f:
                    st.session_state.frames = json.load(f)
                st.session_state.current_frame = 0
                st.session_state.slider_frame = 0
                st.session_state.live_instance = live_instance
                status_placeholder.success("✅ Simulazione pronta.")
            else:
                status_placeholder.error("❌ Errore nella generazione dei frame.")

    if 'frames' in st.session_state and st.session_state.get('live_instance') == live_instance:
        frames = st.session_state.frames
        max_frame = len(frames) - 1

        if 'current_frame' not in st.session_state:
            st.session_state.current_frame = 0
        if 'auto_play' not in st.session_state:
            st.session_state.auto_play = False

        st.markdown("##### Controlli")
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

        selected_frame = st.slider("Timeline", 0, max_frame, value=st.session_state.current_frame)
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

            fig = route_map_figure(
                frame['depot'], frame.get('routes', []),
                f"Frame {f_idx + 1}/{max_frame + 1}", cost=current_cost
            )
            with plot_placeholder.container():
                st.plotly_chart(fig, use_container_width=True, key=f"live_frame_{f_idx}")

        render_frame(st.session_state.current_frame)

        if st.session_state.auto_play:
            if st.session_state.current_frame < max_frame:
                st.session_state.current_frame += 1
                time.sleep(0.3)
                st.rerun()
            else:
                st.session_state.auto_play = False
                st.rerun()

# ---------------------------------------------------------------------------
# TAB 2 — Analisi dettagliata
# ---------------------------------------------------------------------------
with tab2:
    st.header("Analisi dettagliata")

    col_sel_ana, _ = st.columns([2, 1])
    with col_sel_ana:
        st.selectbox(
            "Istanza", sorted(instances), key="analysis_sel",
            index=sorted(instances).index(st.session_state.shared_instance),
            on_change=update_from_analysis
        )
        selected_instance = st.session_state.shared_instance

    st.caption(f"Istanza corrente: **{selected_instance}**")

    json_file = os.path.join(RESULTS_DIR, f"{selected_instance}_best_solution.json")
    stats_file = os.path.join(RESULTS_DIR, f"{selected_instance}_stats.txt")

    col1, col2, col3, col4 = st.columns(4)
    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            stats = {}
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    stats[key.strip()] = val.strip()

        col1.metric("Best Cost", f"{float(stats.get('Best Cost', 0)):.2f}")
        col2.metric("Mean Cost", f"{float(stats.get('Mean Cost', 0)):.2f}")
        col3.metric("Iterazioni medie", f"{float(stats.get('Mean Iterations (Evaluations)', 0)):.0f}")
        col4.metric("Satisfability", stats.get('Satisfability', 'N/A'))

    st.divider()

    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)

        col_conv, col_cap = st.columns(2)

        # --- Convergenza ---
        with col_conv:
            fig_conv = go.Figure()
            for run in range(5):
                csv_file = os.path.join(RESULTS_DIR, f"{selected_instance}_run_{run}_convergence.csv")
                if os.path.exists(csv_file):
                    df = pd.read_csv(csv_file)
                    fig_conv.add_trace(go.Scatter(
                        x=df['Evaluations'], y=df['BestCost'], mode="lines",
                        name=f"Run {run + 1}", line=dict(width=2, color=ROUTE_PALETTE[run]),
                    ))
            fig_conv.update_xaxes(title_text="Valutazioni (FE)")
            fig_conv.update_yaxes(title_text="Miglior costo trovato")
            fig_conv = style_fig(fig_conv, "📉 Convergenza")
            st.plotly_chart(fig_conv, use_container_width=True)

        # --- Saturazione capacità ---
        with col_cap:
            loads = data.get('loads', [])
            capacity = data.get('capacity', 1)
            if loads:
                percentages = [(l / capacity) * 100 for l in loads]
                colors = [DEPOT_COLOR if p > 100 else ACCENT for p in percentages]
                fig_cap = go.Figure(go.Bar(
                    x=[f"V{i+1}" for i in range(len(loads))],
                    y=percentages,
                    marker_color=colors,
                    text=[f"{p:.0f}%" for p in percentages],
                    textposition="outside",
                    hovertemplate="%{x}: %{y:.1f}%%<extra></extra>",
                ))
                fig_cap.add_hline(y=100, line_dash="dash", line_color=DEPOT_COLOR,
                                   annotation_text="Capacità massima", annotation_font_color=DEPOT_COLOR)
                fig_cap.update_yaxes(title_text="Carico (%)", range=[0, max(110, max(percentages) + 10)])
                fig_cap = style_fig(fig_cap, "🚛 Saturazione veicoli")
                st.plotly_chart(fig_cap, use_container_width=True)

        # --- Mappa rotte ---
        fig_map = route_map_figure(data['depot'], data['routes'], "🗺️ Rotte ottimizzate", cost=data['cost'])
        st.plotly_chart(fig_map, use_container_width=True)

        with st.expander("📖 Come leggere i grafici"):
            st.markdown("""
            **Convergenza** — il costo scende all'aumentare delle valutazioni. Una discesa ripida
            all'inizio è merito della partenza intelligente (Nearest Neighbor); i "gradini" più
            avanti indicano che l'algoritmo era bloccato e LNS o Simulated Annealing lo hanno sbloccato.

            **Saturazione veicoli** — quanto ogni veicolo è riempito rispetto alla capacità massima
            (linea tratteggiata). Idealmente le barre stanno vicine al 100%: significa usare meno
            veicoli possibile, sfruttandoli al massimo.

            **Mappa rotte** — la disposizione geografica di clienti e deposito. Rotte che si
            incrociano a "clessidra" indicano margine di miglioramento; la 2-Opt le districa
            automaticamente in percorsi più circolari.
            """)

# ---------------------------------------------------------------------------
# TAB 3 — Walkthrough
# ---------------------------------------------------------------------------
with tab3:
    st.header("🎓 Come lavora l'algoritmo, passo per passo")

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

    steps_data = {
        1: {
            "title": "1. Partenza intelligente",
            "code": "1. Popolazione = 20% Nearest Neighbor + 80% random",
            "desc": "Una parte della popolazione iniziale non è casuale: si costruisce visitando ogni volta il cliente più vicino non ancora servito. Si parte già da un costo basso invece che da un groviglio di rotte."
        },
        2: {
            "title": "2. Valutazione",
            "code": "2. Ordina la popolazione per costo (affinità = 1 / costo)",
            "desc": "Ogni soluzione viene valutata e ordinata: le più economiche sono anche le più 'affini' al problema, e passano alla fase successiva con priorità."
        },
        3: {
            "title": "3. Selezione ed espansione clonale",
            "code": "3. Clona le soluzioni migliori, proporzionalmente al rango",
            "desc": "Le soluzioni migliori generano più cloni delle altre. È la fase di sfruttamento (exploitation): si concentra la ricerca vicino a ciò che già funziona."
        },
        4: {
            "title": "4. Ruin & Recreate (LNS)",
            "code": "4. Muta i cloni, incluso Ruin & Recreate",
            "desc": "Un tratto di rotta viene smontato ('ruin') e i nodi rimossi vengono ricollocati dove convengono davvero, anche su un altro veicolo ('recreate'). È una mutazione più drastica di un semplice scambio."
        },
        5: {
            "title": "5. Ricerca locale con Simulated Annealing",
            "code": "5. 2-Opt con accettazione simulated annealing sui cloni migliori",
            "desc": "La 2-Opt districa gli incroci nelle rotte. Grazie al Simulated Annealing, l'algoritmo accetta anche mosse temporaneamente peggiori, con probabilità che si riduce nel tempo — così evita di restare intrappolato in un minimo locale."
        },
        6: {
            "title": "6. Receptor editing",
            "code": "6. Sostituisci le soluzioni peggiori con nuove soluzioni random",
            "desc": "Per non perdere diversità, le soluzioni peggiori vengono buttate e rimpiazzate con soluzioni completamente nuove. È la fase di esplorazione (exploration)."
        },
        7: {
            "title": "7. Nuova generazione",
            "code": "7. Torna al punto 2",
            "desc": "Il ciclo ricomincia dalla valutazione, generazione dopo generazione, finché il budget di valutazioni non è esaurito."
        }
    }

    col_code, col_vis = st.columns([1, 1.5])

    with col_code:
        st.subheader("Pseudocodice")
        pseudocode = ""
        for i in range(1, 8):
            mark = "👉" if i == step else "  "
            color = ACCENT if i == step else INACTIVE_TEXT
            weight = "bold" if i == step else "normal"
            pseudocode += f"<div style='color:{color}; font-weight:{weight}; padding:4px; font-family:monospace'>{mark} {steps_data[i]['code']}</div>"
        st.markdown(f"<div style='background-color:{HOVER_BG}; padding:15px; border-radius:10px;'>{pseudocode}</div>", unsafe_allow_html=True)

        st.markdown(f"### {steps_data[step]['title']}")
        st.info(steps_data[step]['desc'])

    with col_vis:
        st.subheader("Visualizzazione")
        fig_edu = go.Figure()
        fig_edu.update_xaxes(visible=False, range=[0, 1])
        fig_edu.update_yaxes(visible=False, range=[0, 1])

        if step == 1:
            nx_, ny_ = [0.1, 0.4, 0.3], [0.1, 0.3, 0.6]
            fig_edu.add_trace(go.Scatter(x=nx_, y=ny_, mode="lines+markers",
                                          line=dict(color=ACCENT, width=2), marker=dict(size=12, color=ACCENT)))
            fig_edu.add_trace(go.Scatter(x=[0.1], y=[0.1], mode="markers", marker=dict(symbol="square", size=16, color=DEPOT_COLOR)))
            fig_edu = style_fig(fig_edu, "Costruzione greedy: salta al nodo più vicino", height=320)

        elif step == 2:
            fitness = [10, 8, 5, 2, 1]
            # Gradiente dal teal (rango 1, più affine) al grigio (rango 5, meno affine):
            # il colore da solo comunica l'ordinamento, non solo l'altezza della barra.
            fig_edu.add_trace(go.Bar(x=[f"Sol {i+1}" for i in range(5)], y=fitness,
                                      marker_color=RANK_GRADIENT,
                                      text=[f"rango {i+1}" for i in range(5)], textposition="outside"))
            fig_edu.update_xaxes(visible=True)
            fig_edu.update_yaxes(visible=True, title_text="Affinità (1 / costo)")
            fig_edu = style_fig(fig_edu, "Ordinamento per affinità (costo minore = migliore)", height=320)

        elif step == 3:
            fig_edu.add_trace(go.Scatter(x=[0.3, 0.5, 0.7], y=[0.7, 0.7, 0.7], mode="markers+text",
                                          marker=dict(size=18, color=ACCENT), text=["", "", ""]))
            fig_edu.add_trace(go.Scatter(x=[0.4, 0.6], y=[0.4, 0.4], mode="markers",
                                          marker=dict(size=14, color=ROUTE_PALETTE[1])))
            fig_edu.add_trace(go.Scatter(x=[0.5], y=[0.1], mode="markers",
                                          marker=dict(size=10, color=ROUTE_PALETTE[2])))
            fig_edu.add_annotation(x=0.1, y=0.8, text="Migliore → 3 cloni", showarrow=False, font=dict(color=ACCENT), xanchor="left")
            fig_edu.add_annotation(x=0.1, y=0.5, text="Seconda → 2 cloni", showarrow=False, font=dict(color=ROUTE_PALETTE[1]), xanchor="left")
            fig_edu.add_annotation(x=0.1, y=0.2, text="Terza → 1 clone", showarrow=False, font=dict(color=ROUTE_PALETTE[2]), xanchor="left")
            fig_edu = style_fig(fig_edu, "Espansione clonale", height=320)

        elif step == 4:
            # Rotta residua (i nodi non toccati dal ruin restano collegati)
            fig_edu.add_trace(go.Scatter(x=[0.1, 0.9], y=[0.5, 0.5],
                                          mode="lines+markers", name="Rotta residua",
                                          line=dict(color=WHITE, width=1.5, dash="dot"),
                                          marker=dict(size=10, color=WHITE)))
            # Ruin: il segmento centrale viene tolto dalla rotta
            fig_edu.add_trace(go.Scatter(x=[0.3, 0.5, 0.7], y=[0.6, 0.75, 0.6], mode="markers+lines",
                                          name="Ruin (rimossi)", marker=dict(size=12, color=DEPOT_COLOR),
                                          line=dict(color=DEPOT_COLOR, dash="dash")))
            # Recreate: gli stessi nodi vengono reinseriti nel punto di costo minimo
            # della rotta residua (anche su un altro veicolo) — qui collegati, non isolati.
            fig_edu.add_trace(go.Scatter(x=[0.1, 0.35, 0.9], y=[0.5, 0.25, 0.5], mode="markers+lines",
                                          name="Recreate (reinseriti)", marker=dict(size=12, color=SUCCESS_COLOR),
                                          line=dict(color=SUCCESS_COLOR, width=2)))
            fig_edu.add_annotation(x=0.5, y=0.75, text="rimossi", showarrow=False, font=dict(color=DEPOT_COLOR, size=11))
            fig_edu.add_annotation(x=0.35, y=0.2, text="reinseriti nel punto migliore", showarrow=False,
                                    font=dict(color=SUCCESS_COLOR, size=11))
            fig_edu = style_fig(fig_edu, "Large Neighborhood Search: Ruin & Recreate", height=320)

        elif step == 5:
            # Pannello sinistro: la 2-Opt classica, un incrocio che diventa migliorativo
            fig_edu.add_trace(go.Scatter(x=[0.02, 0.2], y=[0.75, 0.95], mode="lines",
                                          line=dict(color=DEPOT_COLOR, width=2, dash="dash"), name="Incrocio (Δ<0, migliora)"))
            fig_edu.add_trace(go.Scatter(x=[0.02, 0.2], y=[0.95, 0.75], mode="lines",
                                          line=dict(color=DEPOT_COLOR, width=2, dash="dash"), showlegend=False))
            fig_edu.add_trace(go.Scatter(x=[0.32, 0.5], y=[0.75, 0.75], mode="lines",
                                          line=dict(color=SUCCESS_COLOR, width=3), name="Accettata sempre"))
            fig_edu.add_trace(go.Scatter(x=[0.32, 0.5], y=[0.95, 0.95], mode="lines",
                                          line=dict(color=SUCCESS_COLOR, width=3), showlegend=False))
            fig_edu.add_annotation(x=0.11, y=1.03, text="prima", showarrow=False, font=dict(size=10, color=WHITE))
            fig_edu.add_annotation(x=0.41, y=1.03, text="dopo", showarrow=False, font=dict(size=10, color=WHITE))

            # Pannello destro: il caso specifico del Simulated Annealing — mossa che
            # PEGGIORA il costo ma viene accettata comunque con probabilità P = e^(-Δ/T)
            fig_edu.add_trace(go.Scatter(x=[0.65, 0.95], y=[0.75, 0.95], mode="lines",
                                          line=dict(color=YELLOW_WARNING, width=3, dash="dot"),
                                          name="Mossa peggiorativa (Δ>0)"))
            fig_edu.add_annotation(x=0.8, y=1.05, text="accettata con P = e^(−Δ/T)", showarrow=False,
                                    font=dict(size=11, color=YELLOW_WARNING))
            fig_edu.add_annotation(x=0.8, y=0.55, text="↳ evita di restare bloccati<br>in un minimo locale",
                                    showarrow=False, font=dict(size=10, color=INACTIVE_TEXT))

            fig_edu.update_yaxes(range=[0.4, 1.15])
            fig_edu = style_fig(fig_edu, "2-Opt: correzione standard vs accettazione Simulated Annealing", height=320)

        elif step == 6:
            fig_edu.add_trace(go.Scatter(x=[0.2, 0.3, 0.25], y=[0.8, 0.8, 0.7], mode="markers",
                                          name="Elite sopravvissuti", marker=dict(size=14, color=ACCENT)))
            fig_edu.add_trace(go.Scatter(x=[0.7, 0.8, 0.6, 0.9], y=[0.2, 0.3, 0.1, 0.4], mode="markers",
                                          name="Nuovi (random)", marker=dict(size=14, color=WARNING_COLOR, symbol="star")))
            fig_edu = style_fig(fig_edu, "Receptor editing: iniezione di diversità", height=320)

        elif step == 7:
            fig_edu.add_annotation(x=0.5, y=0.5, text="RIPETI<br>IL CICLO", showarrow=False,
                                    font=dict(size=22, color=ACCENT))
            # Due frecce curve che formano un anello, per comunicare visivamente il loop
            fig_edu.add_annotation(x=0.78, y=0.22, ax=0.22, ay=0.78, xref="x", yref="y", axref="x", ayref="y",
                                    showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2.5, arrowcolor=ACCENT,
                                    text="")
            fig_edu.add_annotation(x=0.22, y=0.78, ax=0.78, ay=0.22, xref="x", yref="y", axref="x", ayref="y",
                                    showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=2.5, arrowcolor=ACCENT,
                                    text="")
            fig_edu.add_annotation(x=0.5, y=0.85, text="torna allo step 2 (Valutazione)", showarrow=False,
                                    font=dict(size=11, color=INACTIVE_TEXT))
            fig_edu = style_fig(fig_edu, "Si torna alla fase di valutazione", height=320)

        st.plotly_chart(fig_edu, use_container_width=True)
