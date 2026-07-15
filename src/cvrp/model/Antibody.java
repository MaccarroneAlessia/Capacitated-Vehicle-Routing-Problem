package cvrp.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Rappresentazione di una potenziale soluzione (Anticorpo) nell'Algoritmo Immunologico.
 * Mantiene la collezione delle rotte assegnate all'intera flotta di veicoli.
 * Incapsula il calcolo aggregato della fitness (distanza euclidea totale) e provvede
 * alla traduzione in "Affinità", dove costi minori generano affinità maggiori per la selezione clonale.
 */
public class Antibody implements Comparable<Antibody> {
    // Collection of routes representing the entire vehicle fleet delivery plan
    public final List<Route> routes;
    
    // Total geometric cost across all routes (lower is better)
    private double fitness; 
    
    // Reference to the problem instance for geometric constraints
    private final Instance instance;

    public Antibody(Instance instance) {
        this.instance = instance;
        this.routes = new ArrayList<>();
        this.fitness = 0.0;
    }

    /**
     * Costruttore di clonazione profonda (Deep Copy).
     * Alloca nuove rotte clonate per garantire l'indipendenza strutturale assoluta
     * e prevenire effetti collaterali durante le mutazioni dell'algoritmo genetico.
     */
    public Antibody(Antibody other) {
        this.instance = other.instance;
        this.routes = new ArrayList<>(other.routes.size());
        for (Route r : other.routes) {
            // Perform deep copy of each individual route
            this.routes.add(new Route(r)); 
        }
        // Copy the primitive fitness value to maintain state coherence
        this.fitness = other.fitness; 
    }

    /**
     * Ricalcola la fitness aggregando i costi aggiornati di tutte le rotte attive.
     * Viene chiamato obbligatoriamente dopo ogni operazione di iper-mutazione.
     */
    public void recalculateFitness() {
        double cost = 0.0;
        for (Route r : routes) {
            r.recalculateCost(); // Enforce cost recalculation for each route
            cost += r.getCost();
        }
        this.fitness = cost;
    }

    public double getFitness() {
        return fitness;
    }

    /**
     * Calcola l'affinità biologica dell'anticorpo.
     * L'affinità è calcolata come l'inverso della fitness: (1 / (1 + cost)).
     * Serve ad attrarre probabilisticamente i cloni verso i minimi di costo.
     */
    public double getAffinity() {
        // Prevent division by zero and normalize the affinity profile
        return 1.0 / (1.0 + fitness);
    }

    @Override
    public int compareTo(Antibody o) {
        // Ordinamento naturale crescente in base alla fitness (i costi minori hanno la precedenza)
        // Ascending natural ordering: smaller distance means higher priority in sorting
        return Double.compare(this.fitness, o.fitness);
    }
    
    public Instance getInstance() {
        return instance;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("Total Cost: ").append(String.format("%.2f", fitness)).append("\n");
        for (int i = 0; i < routes.size(); i++) {
            sb.append("  Route ").append(i + 1).append(": ").append(routes.get(i).toString()).append("\n");
        }
        return sb.toString();
    }
}
