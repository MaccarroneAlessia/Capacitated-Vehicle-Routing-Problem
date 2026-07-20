import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches

# Configurazione percorsi
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
OUT_DIR = os.path.join(RESULTS_DIR, "infographics")

os.makedirs(OUT_DIR, exist_ok=True)

def find_file(directory, filename_pattern):
    matches = glob.glob(os.path.join(directory, "**", filename_pattern), recursive=True)
    return matches[0] if matches else None

def parse_vrp(vrp_path):
    nodes = []
    demands = {}
    depot_id = 1
    with open(vrp_path, 'r') as f:
        lines = f.readlines()
        
    in_node_section = False
    in_demand_section = False
    for line in lines:
        line = line.strip()
        if line.startswith("NODE_COORD_SECTION"):
            in_node_section = True
            in_demand_section = False
            continue
        if line.startswith("DEMAND_SECTION"):
            in_demand_section = True
            in_node_section = False
            continue
        if line.startswith("DEPOT_SECTION") or line.startswith("EOF"):
            in_node_section = False
            in_demand_section = False
            
        if in_node_section and line:
            parts = line.split()
            if len(parts) >= 3:
                nid, x, y = int(parts[0]), float(parts[1]), float(parts[2])
                nodes.append((x, y))
                
        if in_demand_section and line:
            parts = line.split()
            if len(parts) >= 2:
                nid, dem = int(parts[0]), int(parts[1])
                demands[nid] = dem
    
    # Cerchiamo il depot
    for line in lines:
        if line.startswith("DEPOT_SECTION"):
            idx = lines.index(line)
            depot_id = int(lines[idx+1].strip())
            break
            
    depot_coord = nodes[depot_id - 1] if 0 < depot_id <= len(nodes) else nodes[0]
    return np.array(nodes), depot_coord, demands, depot_id

def draw_network(ax, points, depot, depot_id, demands, routes=None, loads=None, capacity=1, show_demands=True):
    tri = Delaunay(points)
    ax.triplot(points[:,0], points[:,1], tri.simplices, color='gray', alpha=0.3, linewidth=1.5)
    
    # Stampa le domande (costi) sui nodi
    if show_demands:
        for i, p in enumerate(points):
            nid = i + 1
            if nid != depot_id:
                dem = demands.get(nid, 0)
                txt = ax.text(p[0], p[1]-1, f"{dem}", fontsize=9, color='#e11d48', ha='center', va='top', zorder=8, fontweight='bold')
                txt.set_path_effects([pe.withStroke(linewidth=2, foreground='white')])

    if routes is None:
        ax.scatter(points[:,0], points[:,1], c='#2d2d2d', s=80, zorder=3, edgecolors='white', linewidth=1)
    else:
        cmap = plt.get_cmap('tab10')
        legend_handles = []
        for i, route in enumerate(routes):
            if not route: continue
            
            xs = [depot[0]] + [(n["x"] if isinstance(n, dict) else n[0]) for n in route] + [depot[0]]
            ys = [depot[1]] + [(n["y"] if isinstance(n, dict) else n[1]) for n in route] + [depot[1]]
            
            ax.plot(xs, ys, color='#2d2d2d', linewidth=2.5, alpha=0.9, zorder=4)
            
            color = cmap(i % 10)
            rx = [(n["x"] if isinstance(n, dict) else n[0]) for n in route]
            ry = [(n["y"] if isinstance(n, dict) else n[1]) for n in route]
            ax.scatter(rx, ry, color=color, s=100, zorder=5, edgecolors='white', linewidth=1.5)
            
            if loads is not None and i < len(loads):
                sat = (loads[i] / capacity) * 100
                legend_handles.append(mpatches.Patch(color=color, label=f'Veicolo {i+1} (Sat: {sat:.1f}%)'))
                
        if legend_handles:
            ax.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=12, frameon=False)
            
    # Draw Depot
    ax.scatter(depot[0], depot[1], marker='*', color='#ffcc00', s=800, zorder=6, edgecolors='black', linewidth=1.5)
    txt = ax.text(depot[0], depot[1]+2, "Depot", fontsize=12, fontweight='bold', ha='center', va='bottom', zorder=7)
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground='white')])
    
    ax.axis('off')

def generate_infographic(instance_name):
    clean_name = instance_name.replace(".vrp", "")
    
    vrp_path = find_file(DATA_DIR, f"{clean_name}.vrp")
    json_path = find_file(RESULTS_DIR, f"{clean_name}_best_solution.json")
    
    if not vrp_path or not json_path:
        print(f"Error: Could not find VRP or JSON files for {clean_name}")
        return False
        
    points, depot, demands, depot_id = parse_vrp(vrp_path)
    with open(json_path, 'r') as f:
        sol_data = json.load(f)
        routes = sol_data.get('routes', [])
        
    # Creiamo una figura con altezza maggiorata per poter ospitare il testo in basso
    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor('white')
    
    # Aggiungiamo i subplot (occupando la parte superiore della figura)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.4])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax_text = fig.add_subplot(gs[1, :])
    ax_text.axis('off')
    
    capacity = sol_data.get('capacity', 1)
    loads = sol_data.get('loads', [])
    cost = sol_data.get('cost', 0)
    
    # Disegna plot di sinistra (con domande)
    draw_network(ax1, points, depot, depot_id, demands, routes=None, show_demands=True)
    ax1.set_title(f"VRP (Problem Graph)\nCapacità Singolo Veicolo: {capacity}", fontsize=24, fontweight='bold', pad=20, color='#2d3436')
    
    # Disegna plot di destra (SENZA domande)
    draw_network(ax2, points, depot, depot_id, demands, routes=routes, loads=loads, capacity=capacity, show_demands=False)
    ax2.set_title(f"Solved Routes\nCosto Totale: {cost:.1f}", fontsize=24, fontweight='bold', pad=20, color='#2d3436')
    
    # Freccia in alto, accanto ai titoli
    fig.text(0.5, 0.90, "➡", ha='center', va='center', fontsize=60, color='#0984e3')
    
    # Dettaglio percorso testuale in basso
    text_content = []
    for i, route in enumerate(routes):
        if not route: continue
        route_str = []
        for n in route:
            nid = n["id"] if isinstance(n, dict) else "?"
            route_str.append(f"{nid} ({demands.get(nid, 0)})")
        
        load = loads[i] if loads and i < len(loads) else 0
        free = capacity - load
        text_content.append(f"Veicolo {i+1}: [ " + " | ".join(route_str) + f" ]  --->  Somma Carico: {load}  |  Spazio Libero: {free}")
        
    ax_text.text(0.05, 0.95, "Dettaglio Clienti e Carichi per Veicolo:\n", fontsize=16, fontweight='bold', va='top')
    # wrap=True consente a matplotlib di mandare accapo il testo automaticamente entro i margini della figura
    ax_text.text(0.05, 0.85, "\n".join(text_content), fontsize=12, va='top', family='monospace', wrap=True)
    
    out_file = os.path.join(OUT_DIR, f"{clean_name}_infographic.png")
    plt.tight_layout()
    plt.subplots_adjust(top=0.88) # Lascia spazio in alto per i titoli e la freccia
    plt.savefig(out_file, dpi=300, facecolor='white')
    plt.close(fig)
    
    print(f"[OK] Infografica generata: {out_file}")
    return out_file

if __name__ == "__main__":
    instances = [
        "A-n45-k7", "A-n60-k9", "A-n80-k10",
        "B-n56-k7", "B-n66-k9", "B-n78-k10",
        "E-n76-k8", "E-n101-k14",
        "P-n50-k10", "P-n101-k4"
    ]
    for inst in instances:
        generate_infographic(inst)
