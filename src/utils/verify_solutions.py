import os
import json
import glob
from collections import Counter

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
DATA_DIR = os.path.join(ROOT_DIR, "data")

json_files = glob.glob(os.path.join(RESULTS_DIR, "**", "*_best_solution.json"), recursive=True)
json_files.sort()

print("=== Verifica ID Duplicati/Mancanti ===")
for json_file in json_files:
    basename = os.path.basename(json_file).replace("_best_solution.json", "")
    vrp_files = glob.glob(os.path.join(DATA_DIR, "**", f"{basename}.vrp"), recursive=True)
    if not vrp_files: continue
    vrp_file = vrp_files[0]
    
    # Leggi mappa (x,y) -> node_id dal file VRP
    coord_to_id = {}
    dimension = 0
    with open(vrp_file, 'r') as f:
        in_coord_section = False
        for line in f:
            line = line.strip()
            if line.startswith("DIMENSION"):
                dimension = int(line.split(":")[1].strip())
            elif line.startswith("NODE_COORD_SECTION"):
                in_coord_section = True
            elif line.startswith("DEMAND_SECTION") or line.startswith("EOF") or line.startswith("DEPOT_SECTION"):
                in_coord_section = False
            elif in_coord_section and line:
                parts = line.split()
                node_id = int(parts[0])
                x = round(float(parts[1]), 4)
                y = round(float(parts[2]), 4)
                coord_to_id[(x, y)] = node_id
                
    with open(json_file, 'r') as f:
        sol = json.load(f)
        
    routes = sol.get("routes", [])
    
    # Raccogli ID dei nodi visitati
    visited_ids = []
    unmapped = []
    uses_legacy = False
    
    for r in routes:
        for node in r:
            if isinstance(node, dict) and "id" in node:
                visited_ids.append(node["id"])
            else:
                uses_legacy = True
                x, y = round(node[0], 4), round(node[1], 4)
                if (x, y) in coord_to_id:
                    visited_ids.append(coord_to_id[(x, y)])
                else:
                    # Fallback: cerca il nodo più vicino in caso di problemi di precisione
                    closest_id = None
                    min_dist = float('inf')
                    for (cx, cy), cid in coord_to_id.items():
                        dist = (cx-x)**2 + (cy-y)**2
                        if dist < min_dist:
                            min_dist = dist
                            closest_id = cid
                    if closest_id is not None and min_dist < 0.1:
                        visited_ids.append(closest_id)
                    else:
                        unmapped.append((x, y))

    expected_ids = set(range(2, dimension + 1))
    
    id_counts = Counter(visited_ids)
    duplicates = [nid for nid, count in id_counts.items() if count > 1]
    missing = sorted(list(expected_ids - set(visited_ids)))
    
    if duplicates or missing:
        format_str = "[LEGACY FALLBACK]" if uses_legacy else "[ID-BASED NATIVO]"
        print(f"\n[ERRORE] {basename} {format_str}:")
        if duplicates:
            print(f"  -> DUPLICATI: {duplicates}")
        if missing:
            print(f"  -> MANCANTI:  {missing}")
        if unmapped:
            print(f"  -> NON MAPPATI: {len(unmapped)} nodi (x,y non trovate nel .vrp)")
    else:
        format_str = "[LEGACY FALLBACK]" if uses_legacy else "[ID-BASED NATIVO]"
        print(f"\n[OK] {basename} {format_str}: 0 duplicati, 0 mancanti.")
