package cvrp.model;

/**
 * Struttura dati per un singolo Nodo (Cliente o Deposito).
 * Rappresenta l'entità minima del problema spaziale.
 * Memorizza le coordinate spaziali (x, y) e la propria domanda di merce.
 * Fornisce un'implementazione immutabile e thread-safe, con calcolo
 * della distanza ottimizzato.
 */
public class Node {
    // Unique identifier for the node (1 is usually the depot)
    public final int id;
    
    // Spatial coordinates
    public final double x;
    public final double y;
    
    // Capacity demand for this specific node
    public final int demand;

    public Node(int id, double x, double y, int demand) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.demand = demand;
    }

    /**
     * Calcola la distanza euclidea verso un altro nodo.
     * Utilizza la moltiplicazione algebrica diretta invece di Math.pow
     * per massimizzare le performance durante i calcoli geometrici ripetitivi.
     */
    public double distanceTo(Node other) {
        // Calculate coordinate deltas
        double dx = this.x - other.x;
        double dy = this.y - other.y;
        
        // Return Euclidean distance using fast multiplication
        return Math.sqrt(dx * dx + dy * dy);
    }

    @Override
    public boolean equals(Object o) {
        // Fast reference check
        if (this == o) return true;
        // Null and type check
        if (o == null || getClass() != o.getClass()) return false;
        
        // Logical equality is strictly based on the unique ID
        Node node = (Node) o;
        return id == node.id;
    }

    @Override
    public int hashCode() {
        // ID is unique and immutable, making it a perfect hash code
        return id;
    }

    @Override
    public String toString() {
        return "N" + id;
    }
}
