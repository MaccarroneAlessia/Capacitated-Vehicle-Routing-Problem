import urllib.request
import os

instances = [
    "A-n45-k7", "A-n60-k9", "A-n80-k10",
    "B-n56-k7", "B-n66-k9", "B-n78-k10",
    "E-n76-k8", "E-n101-k14",
    "P-n50-k10", "P-n101-k4"
]

DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

for inst in instances:
    prefix = inst[0]
    url = f"http://vrp.galgos.inf.puc-rio.br/media/com_vrp/instances/{prefix}/{inst}.vrp"
    out_path = os.path.join(DATA_DIR, f"{inst}.vrp")
    
    if os.path.exists(out_path):
        print(f"Skipping {inst}, already downloaded.")
        continue
        
    print(f"Downloading {inst}...")
    try:
        urllib.request.urlretrieve(url, out_path)
        print(f"  -> Saved to {out_path}")
    except Exception as e:
        print(f"  -> Failed to download {inst}: {e}")

print("Download complete.")
