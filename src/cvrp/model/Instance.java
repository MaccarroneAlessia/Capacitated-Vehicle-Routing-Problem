package cvrp.model;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Classe per il caricamento e la memorizzazione delle istanze CVRPLIB.
 * Analizza i file di test `.vrp` estraendo dimensione, capacità, coordinate e domande.
 * Pre-calcola la matrice delle distanze geometriche in modo da garantire
 * accessi in tempo costante O(1) durante l'intensiva fase di fitness evaluation.
 */
public class Instance {
    // Unique name of the instance (e.g. A-n45-k6)
    public final String name;
    
    // Total number of nodes (customers + 1 depot)
    public final int dimension;
    
    // Maximum capacity limit for each homogeneous vehicle in the fleet
    public final int capacity;
    
    // The central depot where all routes must start and end
    public final Node depot;
    
    // List of customers requiring delivery
    public final List<Node> customers;
    
    // Pre-computed lookup table for Euclidean distances between any two nodes
    public final double[][] distanceMatrix;
    
    // Campi diagnostici per la saturazione della flotta
    public final int totalDemand;
    public final int maxVehicles;

    public Instance(String filePath) throws IOException {
        String parsedName = "";
        int parsedDimension = 0;
        int parsedCapacity = 0;
        int parsedMaxVehicles = -1;
        
        List<Double> xCoords = new ArrayList<>();
        List<Double> yCoords = new ArrayList<>();
        List<Integer> demands = new ArrayList<>();

        // Pattern regex flessibile per catturare KEY : VALUE oppure KEY VALUE (anche con tab o spazi multipli)
        // Flexible Regex pattern to capture metadata pairs robustly across different TSPLIB variations
        Pattern headerPattern = Pattern.compile("^([A-Z_]+)\\s*[:\\s]\\s*(.+)$", Pattern.CASE_INSENSITIVE);

        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line;
            String section = "";
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty() || line.equalsIgnoreCase("EOF")) continue;

                // Match header metadata lines
                Matcher matcher = headerPattern.matcher(line);
                if (matcher.matches()) {
                    String key = matcher.group(1).toUpperCase();
                    String value = matcher.group(2).trim();

                    switch (key) {
                        case "NAME":
                            parsedName = value;
                            // Estrazione robusta di k (numero veicoli) dal nome dell'istanza
                            // Robust extraction of the optimal vehicle count 'k' embedded in standard instance names
                            if (parsedName.contains("-k")) {
                                try {
                                    String kPart = parsedName.substring(parsedName.lastIndexOf("-k") + 2);
                                    if (kPart.contains(".")) {
                                        kPart = kPart.substring(0, kPart.indexOf("."));
                                    }
                                    parsedMaxVehicles = Integer.parseInt(kPart);
                                } catch (NumberFormatException e) {
                                    // Fallback silenzioso se il parsing del k finale fallisce
                                    // Silent fallback if parsing the trailing k value fails
                                }
                            }
                            break;
                        case "DIMENSION":
                            parsedDimension = Integer.parseInt(value);
                            break;
                        case "CAPACITY":
                            parsedCapacity = Integer.parseInt(value);
                            break;
                    }
                }

                // Gestione delle sezioni dati del file .vrp
                // Track current parsing section
                if (line.startsWith("NODE_COORD_SECTION")) {
                    section = "COORD";
                    continue;
                } else if (line.startsWith("DEMAND_SECTION")) {
                    section = "DEMAND";
                    continue;
                } else if (line.startsWith("DEPOT_SECTION")) {
                    section = "DEPOT";
                    continue;
                }

                // Parse tabular data based on the active section
                if (section.equals("COORD")) {
                    String[] parts = line.split("\\s+");
                    // parts[0] è l'ID del nodo, parts[1] è la coordinata X, parts[2] è la coordinata Y
                    xCoords.add(Double.parseDouble(parts[1]));
                    yCoords.add(Double.parseDouble(parts[2]));
                } else if (section.equals("DEMAND")) {
                    String[] parts = line.split("\\s+");
                    demands.add(Integer.parseInt(parts[1]));
                }
            }
        }

        // Safety check to ensure geometric data was correctly loaded
        if (xCoords.isEmpty()) {
            throw new IllegalArgumentException("Formato non supportato. Sono supportate solo istanze EUC_2D con coordinate.");
        }

        this.name = parsedName;
        this.dimension = parsedDimension;
        this.capacity = parsedCapacity;
        
        // Per convenzione standard CVRPLIB, il nodo 1 rappresenta sempre il deposito centrale
        // By CVRPLIB standard convention, node ID 1 is always the central depot
        this.depot = new Node(1, xCoords.get(0), yCoords.get(0), demands.get(0));
        this.customers = new ArrayList<>(dimension - 1);
        
        // Populate the remaining nodes as deliverable customers
        for (int i = 2; i <= dimension; i++) {
            this.customers.add(new Node(i, xCoords.get(i-1), yCoords.get(i-1), demands.get(i-1)));
        }

        // Calcolo della domanda aggregata complessiva dell'istanza
        // Calculate the aggregate demand required by all customers
        int sumDemands = 0;
        for (Node c : this.customers) {
            sumDemands += c.demand;
        }
        this.totalDemand = sumDemands;
        this.maxVehicles = parsedMaxVehicles;

        // Inizializzazione della matrice simmetrica pre-calcolata delle distanze
        // Initialize the symmetric distance lookup matrix to avoid runtime Math.pow calculations
        List<Node> allNodes = new ArrayList<>(dimension);
        allNodes.add(depot);
        allNodes.addAll(customers);
        
        this.distanceMatrix = new double[dimension + 1][dimension + 1];
        for (Node n1 : allNodes) {
            for (Node n2 : allNodes) {
                this.distanceMatrix[n1.id][n2.id] = n1.distanceTo(n2);
            }
        }
    }

    /**
     * Calcola la saturazione teorica della flotta per l'istanza.
     * Rapporto tra la domanda totale richiesta e la capacità di trasporto massima teorica.
     *
     * @param estimatedK fallback vehicle count if instance name parsing failed
     * @return ratio of total demand vs total fleet capacity (0.0 to 1.0+)
     */
    public double getSaturation(int estimatedK) {
        // Prefer the actual max vehicles parsed from the instance filename, else use the algorithmic estimate
        int kToUse = maxVehicles > 0 ? maxVehicles : estimatedK;
        if (kToUse <= 0 || capacity <= 0) return 0.0;
        return (double) totalDemand / (kToUse * capacity);
    }

    /**
     * Restituisce la distanza euclidea pre-calcolata tra due nodi in O(1).
     * 
     * @param n1 Source node
     * @param n2 Destination node
     * @return Pre-calculated geometric distance
     */
    public double getDistance(Node n1, Node n2) {
        return distanceMatrix[n1.id][n2.id];
    }
}
