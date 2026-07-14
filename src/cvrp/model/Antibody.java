package cvrp.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Rappresentazione di una potenziale soluzione (Anticorpo) nell'Algoritmo Immunologico.
 * 
 * Ho strutturato l'anticorpo come una collezione di oggetti Route (i veicoli).
 * Questa classe calcola e mantiene il costo totale (la distanza) e il grado di 
 * "Affinità" (fitness), che nel CVRP è l'inverso del costo: vogliamo minimizzare la distanza.
 */

public class Antibody implements Comparable<Antibody> {
    public final List<Route> routes;
    private double fitness; // Total cost
    private final Instance instance;

    public Antibody(Instance instance) {
        this.instance = instance;
        this.routes = new ArrayList<>();
        this.fitness = 0.0;
    }

    // Clone constructor
    public Antibody(Antibody other) {
        this.instance = other.instance;
        this.routes = new ArrayList<>();
        for (Route r : other.routes) {
            this.routes.add(new Route(r));
        }
        this.fitness = other.fitness;
    }

    public void recalculateFitness() {
        double cost = 0;
        for (Route r : routes) {
            r.recalculateCost();
            cost += r.getCost();
        }
        this.fitness = cost;
    }

    public double getFitness() {
        return fitness;
    }

    // Affinity is inverse of fitness (lower cost = higher affinity)
    public double getAffinity() {
        return 1.0 / (1.0 + fitness);
    }

    @Override
    public int compareTo(Antibody o) {
        // Ascending order of fitness (lower cost is better)
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
            sb.append("Route ").append(i + 1).append(": ").append(routes.get(i).toString()).append("\n");
        }
        return sb.toString();
    }
}
