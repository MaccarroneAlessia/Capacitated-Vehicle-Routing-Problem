import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

sns.set_theme(style="whitegrid")

instances = ['A-n45-k7', 'E-n101-k14', 'P-n101-k4']
folders = ['A', 'E', 'P']

output_dir = '../../results/infographics/convergence'
os.makedirs(output_dir, exist_ok=True)

for inst, folder in zip(instances, folders):
    # Cerca il file convergence della run_0
    file_path = f'../../results/{folder}/{inst}_run_0_convergence.csv'
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['Evaluations'], df['BestCost'], color='#2ca02c', linewidth=2.5)
        
        # Aggiungi un punto rosso all'inizio per evidenziare il costo iniziale
        plt.scatter(df['Evaluations'].iloc[0], df['BestCost'].iloc[0], color='red', zindex=5, label='Inizializzazione NN')
        
        plt.title(f'Convergence Plot - {inst}', fontsize=16, fontweight='bold')
        plt.xlabel('Fitness Evaluations', fontsize=12)
        plt.ylabel('Best Cost', fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        out_file = os.path.join(output_dir, f'{inst}_convergence.png')
        plt.savefig(out_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Salvato {out_file}")
    else:
        print(f"File non trovato: {file_path}")

print("Fatto!")
