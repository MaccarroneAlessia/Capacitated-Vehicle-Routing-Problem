import json

with open('notebooks/CVRP.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        src = "".join(cell['source'])
        
        # Point 8: Name placeholder
        src = src.replace('[Tuo Nome e Cognome]', 'Alessia Maccarrone')
        
        # Point 5: Guardia O(1) clarification
        src = src.replace('Ogni operatore esegue un controllo predittivo a tempo costante:',
                          'Ogni operatore esegue un controllo predittivo a tempo costante. Ecco ad esempio la guardia per lo *Swap* (anche operatori come *Relocate* e *LNS* implementano difese rigorose analoghe sui propri domini di ricerca):')
        
        # Point 4: 84% statistic
        src = src.replace("nell'84% delle combinazioni", "nella stragrande maggioranza delle istanze testate")
        
        # Point 2: Link Section 9 to 4.1
        src = src.replace("Confronto finale sull'Outlier tra l'algoritmo baseline rigido e la variante *Adaptive Fuzzy Engine* con iper-mutazione dinamicamente rimodellata.",
                          "Come introdotto matematicamente nella **Sezione 4.1**, un semplice interruttore logico al superamento di una soglia di saturazione critica è troppo rigido. Per far fronte ai problemi visti nell'Outlier, ho implementato e testato la variante *Adaptive Fuzzy Engine* con iper-mutazione dinamicamente rimodellata, che agisce da \"freno morbido\" all'aumentare dello stress di capacità. Di seguito la validazione empirica di tale miglioramento architettonico rispetto alla baseline.")

        # Point 1: Narrative touch in Section 8
        if "L'istanza `A-n45-k6` presentava un'anomalia di comportamento" in src:
            src = src.replace("L'istanza `A-n45-k6` presentava un'anomalia di comportamento con un gap medio elevatissimo",
                              "Durante la fase di validazione, l'istanza `A-n45-k6` ha attirato la mia attenzione presentando un'anomalia di comportamento con un gap medio elevatissimo")

        cell['source'] = [line + '\n' for line in src.split('\n')]
        if cell['source'] and cell['source'][-1].endswith('\n\n'):
             cell['source'][-1] = cell['source'][-1][:-1]

    elif cell['cell_type'] == 'code':
        src = "".join(cell['source'])
        
        # Point 6: Legend in ablation study
        if "ax.legend(loc='upper right', fontsize=11, frameon=True, facecolor='#2d2d2d')" in src:
            src = src.replace(
                "    if i == 0:\n        ax.legend(loc='upper right', fontsize=11, frameon=True, facecolor='#2d2d2d')",
                ""
            )
            src = src.replace("plt.tight_layout()", "handles, labels_leg = ax.get_legend_handles_labels()\nfig.legend(handles, labels_leg, loc='upper center', ncol=4, fontsize=12, frameon=True, facecolor='#2d2d2d', bbox_to_anchor=(0.5, 1.05))\nplt.tight_layout()")

        # Point 3: Chart in Section 7
        if "plt.axvline(95" in src:
            src = src.replace(
                "plt.axvline(95, color='orange', linestyle=':', linewidth=2, label='Soglia Saturated Mode (95%)')",
                "plt.axvspan(80, 95, color='orange', alpha=0.15, label='Transizione Fuzzy Saturated Mode (80%→95%)')"
            )

        # Point 7: Parsing Saturazione
        if "capacity_match = re.search" in src and "capacity = int(capacity_match.group(1))" in src:
            src = src.replace(
                "capacity_match = re.search(r'CAPACITY\\s*[:=]?\\s*(\\d+)', text, re.IGNORECASE)\n        capacity = int(capacity_match.group(1))",
                "capacity_match = re.search(r'CAPACITY\\s*[:=]?\\s*(\\d+)', text, re.IGNORECASE)\n        if not capacity_match: return None\n        capacity = int(capacity_match.group(1))"
            )

        cell['source'] = [line + '\n' for line in src.split('\n')]
        if cell['source'] and cell['source'][-1].endswith('\n\n'):
             cell['source'][-1] = cell['source'][-1][:-1]

with open('notebooks/CVRP.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Updated CVRP.ipynb successfully')
