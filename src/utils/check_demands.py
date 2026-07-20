import os
import json
import glob

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
DATA_DIR = os.path.join(ROOT_DIR, "data")

json_files = glob.glob(os.path.join(RESULTS_DIR, "**", "*_best_solution.json"), recursive=True)
json_files.sort()

print("=== Verifica Domande e Sovrapposizioni Coordinate ===")
bug_count = 0
for json_file in json_files:
    basename = os.path.basename(json_file).replace("_best_solution.json", "")
    vrp_files = glob.glob(os.path.join(DATA_DIR, "**", f"{basename}.vrp"), recursive=True)
    if not vrp_files: continue
    vrp_file = vrp_files[0]
    
    total_expected_demand = 0
    coords = []
    
    with open(vrp_file, 'r') as f:
        in_demand = False
        in_coord = False
        for line in f:
            line = line.strip()
            if line.startswith("DEMAND_SECTION"):
                in_demand = True
                in_coord = False
                continue
            elif line.startswith("NODE_COORD_SECTION"):
                in_coord = True
                in_demand = False
                continue
            elif line.startswith("DEPOT_SECTION") or line.startswith("EOF") or line.startswith("EDGE_WEIGHT_TYPE") or line.startswith("CAPACITY"):
                in_demand = False
                in_coord = False
                
            if in_demand and line and line[0].isdigit():
                parts = line.split()
                if int(parts[0]) != 1:  # Ignora deposito
                    total_expected_demand += int(parts[1])
            elif in_coord and line and line[0].isdigit():
                parts = line.split()
                if int(parts[0]) != 1:  # Ignora deposito
                    coords.append((float(parts[1]), float(parts[2])))

    n_duplicati = len(coords) - len(set(coords))

    with open(json_file, 'r') as f:
        sol = json.load(f)
        
    total_served_demand = sum(sol.get("loads", []))
    
    if total_expected_demand != total_served_demand:
        bug_count += 1
        print(f"[BUG GRAVE] {basename}: Attesa {total_expected_demand}, Servita {total_served_demand}")
    else:
        if n_duplicati > 0:
            print(f"[OK] {basename}: Domanda {total_expected_demand} combacia. Coordinate sovrapposte nel raw: {n_duplicati}")

print(f"\nTOTALE BUG RILEVATI: {bug_count}")
