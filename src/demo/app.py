"""
Dashboard interattiva (Streamlit) per i risultati del CVRP.
LINK: https://capacitated-vehicle-routing-problem-jgnez4bsdkxthgvrgfs9mk.streamlit.app/

pip install -r requirements.txt
streamlit run src/demo/app.py
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
import scipy.stats as stats

# Root del progetto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(PROJECT_ROOT)

# Set page config
st.set_page_config(page_title="CVRP Optimizer Dashboard", page_icon="🚚", layout="wide", initial_sidebar_state="auto")

RESULTS_DIR = "results"
DATA_DIR = "data"

PROTOCOL_INSTANCES = [
    "A-n45-k7", "A-n60-k9", "A-n80-k10",
    "B-n56-k7", "B-n66-k9", "B-n78-k10",
    "E-n76-k8", "E-n101-k14",
    "P-n50-k10", "P-n101-k4"
]

HIGHLIGHT_GREEN = "#4ade80"  # Verde per i minimi
HIGHLIGHT_RED = "#991b1b"    # Bordeaux per i massimi

ROUTE_PALETTE = [
    "#2dd4bf", "#60a5fa", "#f472b6", "#facc15", "#a78bfa",
    "#4ade80", "#fb923c", "#38bdf8", "#e879f9", "#fbbf24",
    "#94a3b8", "#f87171",
]

def style_fig(fig, title=None, height=420):
    fig.update_layout(
        title=dict(text=title, font=dict(size=17)) if title else None,
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        height=height,
    )
    return fig

def route_map_figure(depot, routes, title, cost=None, demands=None):
    fig = go.Figure()
    for i, route in enumerate(routes):
        if not route: continue
        xs = [depot[0]] + [(n["x"] if isinstance(n, dict) else n[0]) for n in route] + [depot[0]]
        ys = [depot[1]] + [(n["y"] if isinstance(n, dict) else n[1]) for n in route] + [depot[1]]
        n_ids = ["-"] + [(str(n["id"]) if isinstance(n, dict) else "?") for n in route] + ["-"]
        
        if demands:
            n_costs = ["Dep"] + [str(demands.get(int(nid), 0)) if str(nid).isdigit() else "?" for nid in n_ids[1:-1]] + ["Dep"]
        else:
            n_costs = [""] * len(xs)

        color = ROUTE_PALETTE[i % len(ROUTE_PALETTE)]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines+markers+text", name=f"Veicolo {i+1}",
            customdata=n_ids, text=n_costs, textposition="top center", textfont=dict(size=10, color=color),
            line=dict(color=color, width=2.5),
            marker=dict(size=7, color=color, line=dict(width=1, color="black")),
            hovertemplate=f"Veicolo {i+1}<br>Cliente ID: %{{customdata}}<br>x=%{{x:.1f}}, y=%{{y:.1f}}<br>Domanda: %{{text}}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=[depot[0]], y=[depot[1]], mode="markers", name="Deposito",
        marker=dict(symbol="star", size=20, color="#f87171", line=dict(width=1, color="white")),
        hovertemplate="Deposito<extra></extra>",
    ))
    full_title = title if cost is None else f"{title} — costo {cost:.2f}"
    fig = style_fig(fig, full_title, height=520)
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig

# --- Dati ---
@st.cache_data
def load_global_summary():
    sf = os.path.join(RESULTS_DIR, "global_summary.csv")
    return pd.read_csv(sf) if os.path.exists(sf) else None

@st.cache_data
def get_available_instances():
    jf = glob.glob(os.path.join(RESULTS_DIR, "*", "*_best_solution.json"))
    if not jf: jf = glob.glob(os.path.join(RESULTS_DIR, "*_best_solution.json"))
    return [os.path.basename(f).replace("_best_solution.json", "") for f in jf]

@st.cache_data
def load_family_summary():
    sf = os.path.join(RESULTS_DIR, "global_summary.csv")
    if os.path.exists(sf):
        df = pd.read_csv(sf)
        df['Family'] = df['Instance'].str[0]
        df['Gap%'] = ((df['MeanCost'] - df['BestCost']) / df['BestCost']) * 100
        df['CV%'] = (df['StdDevCost'] / df['MeanCost']) * 100
        return df
    return None

@st.cache_data
def load_saturation_data():
    sf = os.path.join(RESULTS_DIR, "global_summary.csv")
    if not os.path.exists(sf): return None
    df = pd.read_csv(sf)
    rows = []
    for _, r in df.iterrows():
        i = r['Instance']
        f = i[0]
        jp = os.path.join(RESULTS_DIR, f, f"{i}_best_solution.json")
        if os.path.exists(jp):
            with open(jp, 'r') as file:
                d = json.load(file)
                loads = d.get('loads', [])
                cap = d.get('capacity', 1)
                nv = len(loads) if len(loads)>0 else 1
                sat = (sum(loads)/(cap*nv))*100 if cap*nv>0 else 0
                gap = ((r['MeanCost']-r['BestCost'])/r['BestCost'])*100
                rows.append({'Instance': i, 'Saturation%': sat, 'Gap%': gap, 'Family': f})
    return pd.DataFrame(rows)

@st.cache_data
def load_vrp_demands(instance_name):
    vp = os.path.join(DATA_DIR, instance_name[0], f"{instance_name}.vrp")
    demands = {}
    cap = 0
    if os.path.exists(vp):
        with open(vp, 'r') as f:
            in_d = False
            for line in f:
                if line.strip().startswith("CAPACITY"):
                    parts = line.strip().split(":")
                    if len(parts)>=2: cap = int(parts[1].strip())
                if line.startswith("DEMAND_SECTION"): in_d=True; continue
                if line.startswith("DEPOT_SECTION") or line.startswith("EOF"): in_d=False
                if in_d:
                    p = line.strip().split()
                    if len(p)>=2: demands[int(p[0])] = int(p[1])
    return demands, cap

# --- UI TOP ---
st.title("🚚 Capacitated Vehicle Routing Problem (CVRP)")

instances = get_available_instances()
if not instances:
    st.error(f"Nessun risultato in '{RESULTS_DIR}'.")
    st.stop()

if "shared_instance" not in st.session_state: st.session_state.shared_instance = sorted(instances)[0]
def update_from_live(): st.session_state.shared_instance = st.session_state.live_sel
def update_from_analysis(): st.session_state.shared_instance = st.session_state.analysis_sel

st.header("1. Il Problema CVRP")
st.markdown(r"""
Il **CVRP** è una sfida di ottimizzazione logistica (NP-Hard).
**Obiettivo:** Minimizzare la distanza totale $\min \sum d_{ij} x_{ijk}$
**Vincolo:** Nessun veicolo supera la capacità $\sum q_i y_{ik} \le C$
""")

st.header("2. La Soluzione (Algoritmo NN_LNS)")
st.markdown("""
Il motore risolutivo è un **Algoritmo Immunologico** basato sulla Selezione Clonale, potenziato da due operatori euristici chiave:
- **Nearest Neighbor (NN)**: Costruzione iniziale intelligente per il 20% della popolazione, accelerando la convergenza.
- **Large Neighborhood Search (LNS)**: Operatore distruttivo ("Ruin & Recreate") per le ipermutazioni dei cloni.
""")

st.header("3. Studio di Ablazione")
ablation_csv = os.path.join(RESULTS_DIR, "ablations", "ablation_global_metrics.csv")
if os.path.exists(ablation_csv):
    df_abl_full = pd.read_csv(ablation_csv)
    cA, cB = st.columns(2)
    with cA:
        st.subheader("Globali (85 Istanze)")
        bc = df_abl_full.groupby('Instance')['Cost'].min()
        df_abl_full['Gap%'] = df_abl_full.apply(lambda r: (r['Cost']-bc[r['Instance']])/bc[r['Instance']]*100, axis=1)
        st85 = df_abl_full.groupby('Configuration').agg({'Gap%':'mean','TimeMs':'mean'}).sort_values('Gap%')
        st.dataframe(st85.style.format({'Gap%':'{:.2f}%','TimeMs':'{:.0f} ms'}).highlight_min(subset=['Gap%','TimeMs'],color=HIGHLIGHT_GREEN).highlight_max(subset=['Gap%','TimeMs'],color=HIGHLIGHT_RED), use_container_width=True)
    with cB:
        st.subheader("Protocollo (10 Istanze)")
        df_p = df_abl_full[df_abl_full['Instance'].isin(PROTOCOL_INSTANCES)].copy()
        pb = df_p.groupby('Instance')['Cost'].min()
        df_p['Gap%'] = df_p.apply(lambda r: (r['Cost']-pb[r['Instance']])/pb[r['Instance']]*100, axis=1)
        st10 = df_p.groupby('Configuration').agg({'Gap%':'mean','TimeMs':'mean'}).sort_values('Gap%')
        w = df_p.loc[df_p.groupby('Instance')['Cost'].idxmin()]['Configuration'].value_counts()
        st.dataframe(st10.style.format({'Gap%':'{:.2f}%','TimeMs':'{:.0f} ms'}).highlight_min(subset=['Gap%','TimeMs'],color=HIGHLIGHT_GREEN).highlight_max(subset=['Gap%','TimeMs'],color=HIGHLIGHT_RED), use_container_width=True)
        st.caption(f"🏆 Vittorie assolute nel set protocollo: **NN_LNS ({w.get('nn_lns',0)}/10)**")

st.header("4. Analisi Aggregata e Strutturale")
df_all = load_family_summary()
if df_all is not None:
    cF1, cF2 = st.columns([1, 2])
    with cF1:
        fsum = df_all.groupby('Family').agg({'Instance':'count','Gap%':'mean','CV%':'mean'})
        st.dataframe(fsum.style.format({'Gap%':'{:.2f}%','CV%':'{:.2f}%'}), use_container_width=True)
    with cF2:
        ds = load_saturation_data()
        if ds is not None and not ds.empty:
            r, p_val = stats.pearsonr(ds['Saturation%'], ds['Gap%'])
            f_sat = go.Figure()
            for fam in ds['Family'].unique():
                df_f = ds[ds['Family']==fam]
                f_sat.add_trace(go.Scatter(x=df_f['Saturation%'], y=df_f['Gap%'], mode='markers', name=f"Famiglia {fam}"))
            m, b = np.polyfit(ds['Saturation%'], ds['Gap%'], 1)
            xr = np.linspace(ds['Saturation%'].min(), ds['Saturation%'].max(), 100)
            f_sat.add_trace(go.Scatter(x=xr, y=m*xr+b, mode='lines', name="Trendline", line=dict(color='red',dash='dash')))
            f_sat.update_layout(title=f"Saturazione vs Gap (Pearson r={r:.3f})", height=350, margin=dict(l=20,r=20,t=40,b=20))
            st.plotly_chart(f_sat, use_container_width=True)

st.header("5. Risultati Istanze Protocollo")
tc = os.path.join(RESULTS_DIR, "topic_summary.csv")
if os.path.exists(tc):
    dt = pd.read_csv(tc)
    st.dataframe(dt.style.format({'BestCost':'{:.2f}','MeanCost':'{:.2f}','StdDevCost':'{:.2f}','MeanFE':'{:.0f}'}), use_container_width=True)

st.divider()

# --- TABS ---
tab_walk, tab_analysis, tab_proto, tab_abl = st.tabs([
    "🎓 Walkthrough (Codice & Demo)",
    "📈 Analisi Dettagliata",
    "📋 Istanze di Protocollo",
    "⚖️ Ablation Visivo"
])

# ----------------- TAB: WALKTHROUGH (CODICE + LIVE) -----------------
with tab_walk:
    st.header("🎓 Walkthrough: Architettura, Pseudocodice e Demo")
    st.markdown("""
### Architettura
```text
+------------------------------------------------------------------------+
|                           CORE JAVA ENGINE                             |
+------------------------------------------------------------------------+
|                                                                        |
| [ClonalSelection] --(Real-Time Fitness Loop)--> Scrittura Tabulare     |
|                                                  (*_convergence.csv)   |
|         |                                                              |
|         v                                                              |
| [JSON Exporter] ----(Dettaglio Topologico)----> Rotte Ottime           |
|                                                  (*_best_solution.json)|
+------------------------------------------------------------------------+
```

### Pseudocodice 
```text
1. Population = InitializePopulation(20% NearestNeighbor, 80% Random Feasible)
2. WHILE (FitnessEvaluations < 350,000):
3.     Ordina Population per Costo crescente (Affinità descrescente)
4.     Selected = Seleziona i top N anticorpi
5.     Clones = []
6.     FOR EACH parent in Selected:
7.         NumClones = Proporzionale al Rank(parent)
8.         FOR c = 1 to NumClones:
9.             clone = DeepCopy(parent)
10.            NumMutations = Proporzionale Inverso al Rank(parent)
11.            HyperMutate(clone, NumMutations)
                   --> Seleziona operatore: [Swap, 2-Opt, Relocate, LNS]
12.            RicalcolaFitness(clone)
13.            Aggiungi clone a Clones
14.    
15.    Population.AddAll(Clones)
16.    Ordina Population, tieni i top N
17.    
18.    ReceptorEditing: Rimpiazza peggiori con random feasible
19. RETURN Best Antibody
```
    """)
    
    st.divider()
    st.subheader("▶️ Demo Visualizzazione (Esecuzione Live)")
    
    c_sel, c_btn = st.columns([2, 1])
    with c_sel:
        st.selectbox("Istanza", sorted(instances), key="live_sel", index=sorted(instances).index(st.session_state.shared_instance), on_change=update_from_live)
        live_instance = st.session_state.shared_instance
    with c_btn:
        st.write(""); st.write("")
        if st.button("🎬 Genera simulazione", type="primary", use_container_width=True):
            status = st.empty()
            status.info(f"⏳ Calcolo di {live_instance} in corso...")
            p = subprocess.Popen(["java", "-cp", "bin", "cvrp.algorithm.Main", "--live", live_instance])
            p.wait()
            lj = os.path.join(RESULTS_DIR, "live_frames.json")
            if os.path.exists(lj):
                with open(lj, 'r') as f: st.session_state.frames = json.load(f)
                st.session_state.current_frame = 0
                st.session_state.auto_play = False
                st.session_state.live_instance = live_instance
                status.success("✅ Simulazione pronta.")
            else:
                status.error("❌ Errore nella generazione.")

    if 'frames' in st.session_state and st.session_state.get('live_instance') == live_instance:
        frs = st.session_state.frames
        mf = len(frs) - 1
        if 'current_frame' not in st.session_state: st.session_state.current_frame = 0
        if 'auto_play' not in st.session_state: st.session_state.auto_play = False

        c1, c2, c3, c4, c5 = st.columns(5)
        if c1.button("⏮️ Inizio", use_container_width=True): st.session_state.current_frame = 0; st.session_state.auto_play = False
        if c2.button("◀️ Indietro", use_container_width=True): st.session_state.current_frame = max(0, st.session_state.current_frame - 1); st.session_state.auto_play = False
        if c3.button("Avanti ▶️", use_container_width=True): st.session_state.current_frame = min(mf, st.session_state.current_frame + 1); st.session_state.auto_play = False
        if c4.button("⏭️ Fine", use_container_width=True): st.session_state.current_frame = mf; st.session_state.auto_play = False
        if c5.button("⏹️ Stop" if st.session_state.auto_play else "⏯️ Auto-Play", use_container_width=True):
            st.session_state.auto_play = not st.session_state.auto_play
            if st.session_state.auto_play and st.session_state.current_frame == mf: st.session_state.current_frame = 0

        sf = st.slider("Timeline", 0, mf, value=st.session_state.current_frame)
        if sf != st.session_state.current_frame:
            st.session_state.current_frame = sf; st.session_state.auto_play = False; st.rerun()

        m_ph = st.empty()
        p_ph = st.empty()

        def render_frame(f_idx):
            fr = frs[f_idx]
            dems, _ = load_vrp_demands(live_instance)
            with m_ph.container():
                cA, cB, cC = st.columns(3)
                cA.metric("Costo", f"{fr.get('cost', 0):.2f}")
                cB.metric("Valutazioni (FE)", f"{fr.get('evaluations', 0)}")
                cC.progress(min(fr.get('evaluations', 0) / 350000, 1.0))
            fig = route_map_figure(fr['depot'], fr.get('routes', []), f"Frame {f_idx + 1}", cost=fr.get('cost', 0), demands=dems)
            with p_ph.container():
                st.plotly_chart(fig, use_container_width=True, key=f"lf_{f_idx}")

        render_frame(st.session_state.current_frame)
        if st.session_state.auto_play:
            if st.session_state.current_frame < mf:
                st.session_state.current_frame += 1; time.sleep(0.3); st.rerun()
            else:
                st.session_state.auto_play = False; st.rerun()

# ----------------- TAB: ANALISI DETTAGLIATA -----------------
with tab_analysis:
    st.header("Analisi dettagliata")
    c_s, _ = st.columns([2, 1])
    with c_s:
        st.selectbox("Istanza", sorted(instances), key="analysis_sel", index=sorted(instances).index(st.session_state.shared_instance), on_change=update_from_analysis)
        si = st.session_state.shared_instance

    fam = si[0]
    jf = os.path.join(RESULTS_DIR, fam, f"{si}_best_solution.json")
    stf = os.path.join(RESULTS_DIR, fam, f"{si}_stats.txt")
    if not os.path.exists(jf): jf = os.path.join(RESULTS_DIR, f"{si}_best_solution.json"); stf = os.path.join(RESULTS_DIR, f"{si}_stats.txt")

    if os.path.exists(stf):
        with open(stf, 'r') as f:
            sd = {k.strip(): v.strip() for line in f if ":" in line for k, v in [line.split(":", 1)]}
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best Cost", f"{float(sd.get('Best Cost', 0)):.2f}")
        c2.metric("Mean Cost", f"{float(sd.get('Mean Cost', 0)):.2f}")
        c3.metric("Iterazioni medie", f"{float(sd.get('Mean Iterations (Evaluations)', 0)):.0f}")
        c4.metric("Satisfability", sd.get('Satisfability', 'N/A'))

    if os.path.exists(jf):
        with open(jf, 'r') as f: d = json.load(f)
        dems, _ = load_vrp_demands(si)
        fm = route_map_figure(d['depot'], d['routes'], f"Miglior soluzione trovata per {si}", cost=d['cost'], demands=dems)
        st.plotly_chart(fm, use_container_width=True)

        lds = d.get('loads', [])
        cap = d.get('capacity', 1)
        if lds:
            pl = [(l / cap) * 100 for l in lds]
            fb = go.Figure(data=[go.Bar(x=[f"V{i+1}" for i in range(len(lds))], y=pl, text=[f"{l}/{cap}" for l in lds], textposition='auto', marker_color=["#ef4444" if p > 95 else "#2dd4bf" for p in pl])])
            fb.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Capacità Massima")
            fb = style_fig(fb, "Saturazione Capacità", height=350)
            fb.update_yaxes(range=[0, max(110, max(pl) + 10)])
            st.plotly_chart(fb, use_container_width=True)

# ----------------- TAB: PROTOCOLLO -----------------
with tab_proto:
    st.header("Infografiche Istanze di Protocollo")
    sp = st.selectbox("Scegli l'istanza da visualizzare", PROTOCOL_INSTANCES)
    pp = os.path.join(RESULTS_DIR, "infographics", f"{sp}_infographic.png")
    if os.path.exists(pp): st.image(pp, use_container_width=True)
    else: st.warning("Infografica non generata. Esegui utils/generate_infographic.py")

# ----------------- TAB: ABLATION VISUAL -----------------
with tab_abl:
    st.header("Studio di Ablazione Dettagliato")
    tg = ['P-n16-k8', 'E-n101-k14', 'E-n23-k3', 'B-n57-k7']
    cf = ['baseline', 'nn', 'sa', 'lns', 'nn_sa', 'nn_lns', 'sa_lns', 'all']
    lb = ['Baseline', 'Solo NN', 'Solo SA', 'Solo LNS', 'NN+SA', 'NN+LNS', 'SA+LNS', 'Full']
    sa = st.selectbox("Seleziona Istanza Ablation", tg)
    fc = go.Figure()
    fa = False
    for c, l in zip(cf, lb):
        csv = os.path.join(RESULTS_DIR, 'ablations', sa, f'{sa}_ablation_{c}_convergence.csv')
        if os.path.exists(csv):
            fa = True
            dc = pd.read_csv(csv)
            fc.add_trace(go.Scatter(x=dc['Evaluations'], y=dc['BestCost'], mode='lines', name=l))
    if fa:
        fc.update_layout(title=f"Convergenza Ablation: {sa}", height=500)
        st.plotly_chart(fc, use_container_width=True)
    else: st.warning("Dati di convergenza non trovati.")

# --- FOOTER ---
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Progetto per il corso di <strong>Heuristics & Metaheuristics for Optimization & Learning</strong></p>
        <p>🔗 <a href='https://github.com/MaccarroneAlessia/Capacitated-Vehicle-Routing-Problem' target='_blank' style='text-decoration: none; color: #0984e3; font-weight: bold;'>Visualizza il Codice Sorgente su GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
