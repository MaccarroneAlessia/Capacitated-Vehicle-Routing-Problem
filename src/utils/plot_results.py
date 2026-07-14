"""
Script di supporto per la generazione statica di grafici.
"""
import os
import json
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = "../results"

def plot_convergence(instance_name):
    print(f"Plotting convergence for {instance_name}...")
    plt.figure(figsize=(10, 6))
    
    # Ci aspettiamo 5 run
    colors = ['b', 'g', 'r', 'c', 'm']
    for run in range(5):
        csv_file = os.path.join(RESULTS_DIR, f"{instance_name}_run_{run}_convergence.csv")
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            plt.plot(df['Evaluations'], df['BestCost'], label=f'Run {run+1}', color=colors[run], alpha=0.7)
            
    plt.title(f'Convergence Graph - {instance_name}')
    plt.xlabel('Fitness Evaluations')
    plt.ylabel('Best Cost')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    out_file = os.path.join(RESULTS_DIR, f"{instance_name}_convergence.png")
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {out_file}")

def plot_solution(instance_name):
    json_file = os.path.join(RESULTS_DIR, f"{instance_name}_best_solution.json")
    if not os.path.exists(json_file):
        print(f"No solution file found for {instance_name}")
        return
        
    print(f"Plotting best solution for {instance_name}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
        
    plt.figure(figsize=(10, 10))
    depot = data['depot']
    
    # Plot depot
    plt.scatter(depot[0], depot[1], c='black', marker='s', s=100, label='Depot', zorder=5)
    
    # Plot routes
    routes = data['routes']
    cmap = plt.get_cmap('tab20')
    
    for i, route in enumerate(routes):
        if not route: continue
        
        # Extract x and y coordinates
        xs = [depot[0]] + [node[0] for node in route] + [depot[0]]
        ys = [depot[1]] + [node[1] for node in route] + [depot[1]]
        
        color = cmap(i % 20)
        
        # Plot lines
        plt.plot(xs, ys, color=color, linewidth=2, alpha=0.7, label=f'Route {i+1}')
        # Plot customers
        plt.scatter(xs[1:-1], ys[1:-1], color=color, s=30, zorder=4)
        
    plt.title(f"Best Routing Solution - {instance_name} (Cost: {data['cost']:.2f})")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    # Adjust layout to fit legend
    plt.tight_layout()
    
    out_file = os.path.join(RESULTS_DIR, f"{instance_name}_best_solution.png")
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {out_file}")

if __name__ == "__main__":
    if not os.path.exists(RESULTS_DIR):
        print(f"Results directory {RESULTS_DIR} not found.")
        exit(1)
        
    # Find all unique instance names from convergence files
    instances = set()
    for file in os.listdir(RESULTS_DIR):
        if file.endswith("_convergence.csv"):
            parts = file.split("_run_")
            if len(parts) == 2:
                instances.add(parts[0])
                
    if not instances:
        print("No CSV results found to plot.")
    else:
        for instance in instances:
            plot_convergence(instance)
            plot_solution(instance)
        print("All plots generated successfully.")
