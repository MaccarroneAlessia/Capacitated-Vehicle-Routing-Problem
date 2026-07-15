package cvrp.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Modello di un singolo percorso (Rotta) di un veicolo.
 * Tiene traccia della sequenza di clienti visitati da un singolo mezzo.
 * Incapsula la logica per calcolare il carico corrente (evitando
 * di superare la capacità massima) e il costo della rotta (distanza percorsa).
 */
public class Route {
    // Contiene unicamente i clienti visitati, escludendo il deposito da testa e coda
    // Contains only the visited customers, excluding the depot from head and tail
    public final List<Node> nodes; 
    private int currentLoad;
    private double currentCost;
    private final Instance instance;

    public Route(Instance instance) {
        this.instance = instance;
        this.nodes = new ArrayList<>();
        this.currentLoad = 0;
        this.currentCost = 0.0;
    }

    /**
     * Costruttore di clonazione profonda.
     * Alloca una nuova lista indipendente per garantire l'integrità delle mutazioni.
     */
    public Route(Route other) {
        this.instance = other.instance;
        // Deep copy the node list structure to prevent mutation side-effects
        this.nodes = new ArrayList<>(other.nodes.size());
        this.nodes.addAll(other.nodes);
        this.currentLoad = other.currentLoad;
        this.currentCost = other.currentCost;
    }

    /**
     * Verifica l'ammissibilità del vincolo di capacità per un nodo.
     */
    public boolean canAdd(Node n) {
        // Check if adding the node exceeds the maximum vehicle capacity
        return currentLoad + n.demand <= instance.capacity;
    }

    public void addNode(Node n) {
        nodes.add(n);
        currentLoad += n.demand; // Incremental load update (O(1))
        recalculateCost();
    }
    
    public void addNodeAt(int index, Node n) {
        nodes.add(index, n);
        currentLoad += n.demand; // Incremental load update (O(1))
        recalculateCost();
    }

    public Node removeNodeAt(int index) {
        Node n = nodes.remove(index);
        currentLoad -= n.demand; // Incremental load update (O(1))
        recalculateCost();
        return n;
    }

    /**
     * Calcola la distanza geometrica complessiva della rotta includendo la partenza
     * e il rientro finale obbligatorio al deposito centrale.
     */
    public void recalculateCost() {
        if (nodes.isEmpty()) {
            currentCost = 0.0;
            currentLoad = 0;
            return;
        }
        
        int load = 0;
        
        // Costo di uscita dal deposito verso il primo nodo
        // Cost from depot to the first customer
        double cost = instance.getDistance(instance.depot, nodes.get(0));
        load += nodes.get(0).demand;
        
        // Costo del transito tra clienti consecutivi
        // Transit cost between consecutive customers
        for (int i = 0; i < nodes.size() - 1; i++) {
            cost += instance.getDistance(nodes.get(i), nodes.get(i + 1));
            load += nodes.get(i + 1).demand;
        }
        
        // Costo di rientro al deposito centrale dall'ultimo nodo
        // Return cost from the last customer back to the depot
        cost += instance.getDistance(nodes.get(nodes.size() - 1), instance.depot);
        
        this.currentCost = cost;
        this.currentLoad = load; // Sincronizzazione deterministica di sicurezza
    }

    public double getCost() {
        return currentCost;
    }

    public int getLoad() {
        return currentLoad;
    }

    public boolean isEmpty() {
        return nodes.isEmpty();
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("Depot -> ");
        for (Node n : nodes) {
            sb.append(n.id).append(" -> ");
        }
        sb.append("Depot | Load: ").append(currentLoad).append("/")
          .append(instance.capacity).append(" | Cost: ").append(String.format("%.2f", currentCost));
        return sb.toString();
    }
}
