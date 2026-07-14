package cvrp.model;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Classe per il caricamento e la memorizzazione delle istanze CVRPLIB.
 * 
 * Legge i file `.vrp` e memorizza il numero di nodi, la capacità del veicolo,
 * la lista dei clienti e il deposito.
 * Pre-calcola la matrice delle distanze per ottimizzare i tempi di calcolo 
 * della fitness durante l'esecuzione dell'algoritmo.
 */

public class Instance {
    public final String name;
    public final int dimension;
    public final int capacity;
    public final Node depot;
    public final List<Node> customers;
    public final double[][] distanceMatrix;

    public Instance(String filePath) throws IOException {
        String name = "";
        int dimension = 0;
        int capacity = 0;
        
        List<Double> xCoords = new ArrayList<>();
        List<Double> yCoords = new ArrayList<>();
        List<Integer> demands = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line;
            String section = "";
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.equals("EOF")) continue;

                if (line.startsWith("NAME")) {
                    name = line.split(":")[1].trim();
                } else if (line.startsWith("DIMENSION")) {
                    dimension = Integer.parseInt(line.split(":")[1].trim());
                } else if (line.startsWith("CAPACITY")) {
                    capacity = Integer.parseInt(line.split(":")[1].trim());
                } else if (line.startsWith("NODE_COORD_SECTION")) {
                    section = "COORD";
                    continue;
                } else if (line.startsWith("DEMAND_SECTION")) {
                    section = "DEMAND";
                    continue;
                } else if (line.startsWith("DEPOT_SECTION")) {
                    section = "DEPOT";
                    continue;
                }

                if (section.equals("COORD")) {
                    String[] parts = line.split("\\s+");
                    // parts[0] is id, parts[1] is x, parts[2] is y
                    xCoords.add(Double.parseDouble(parts[1]));
                    yCoords.add(Double.parseDouble(parts[2]));
                } else if (section.equals("DEMAND")) {
                    String[] parts = line.split("\\s+");
                    demands.add(Integer.parseInt(parts[1]));
                } else if (section.equals("DEPOT")) {
                    // Usually 1, then -1. We don't really need to parse it if we assume 1 is depot.
                }
            }
        }

        if (xCoords.isEmpty()) {
            throw new IllegalArgumentException("Formato non supportato (es. EXPLICIT matrix). Sono supportate solo istanze EUC_2D con coordinate.");
        }

        this.name = name;
        this.dimension = dimension;
        this.capacity = capacity;
        
        // Node 1 is depot
        this.depot = new Node(1, xCoords.get(0), yCoords.get(0), demands.get(0));
        this.customers = new ArrayList<>();
        
        for (int i = 2; i <= dimension; i++) {
            this.customers.add(new Node(i, xCoords.get(i-1), yCoords.get(i-1), demands.get(i-1)));
        }

        // Precompute distance matrix
        List<Node> allNodes = new ArrayList<>();
        allNodes.add(depot);
        allNodes.addAll(customers);
        
        // Dimension can be used as max id. IDs are 1-indexed. We make matrix size dimension + 1
        this.distanceMatrix = new double[dimension + 1][dimension + 1];
        for (Node n1 : allNodes) {
            for (Node n2 : allNodes) {
                distanceMatrix[n1.id][n2.id] = n1.distanceTo(n2);
            }
        }
    }

    public double getDistance(Node n1, Node n2) {
        return distanceMatrix[n1.id][n2.id];
    }
}
