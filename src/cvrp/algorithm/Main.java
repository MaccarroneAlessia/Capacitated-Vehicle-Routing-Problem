package cvrp.algorithm;

import cvrp.model.Antibody;
import cvrp.model.Instance;
import cvrp.model.Route;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Entry-point del programma Java e orchestratore principale.
 * Gestisce il caricamento delle istanze `.vrp`, inizializza l'algoritmo di selezione clonale
 * e gestisce le esecuzioni parallele/sequenziali per raccogliere statistiche.
 * Esporta infine i risultati aggregati in file CSV per la reportistica e 
 * genera output in formato JSON per la visualizzazione delle rotte in Python.
 */
public class Main {

    public static void main(String[] args) {
        String dataDir = "data";
        String resultsDir = "results";

        // Check if the application is running in "live mode" (for UI rendering in Python)
        boolean liveMode = false;
        String targetInstance = null;
        if (args.length >= 2 && args[0].equals("--live")) {
            liveMode = true;
            targetInstance = args[1];
        }

        File dataFolder = new File(dataDir);
        if (!dataFolder.exists() || !dataFolder.isDirectory()) {
            System.err.println("La cartella data/ non esiste. Scarica le istanze.");
            return;
        }

        // Standard benchmark set containing specific instances requested by the professor
        Set<String> requiredInstances = new HashSet<>(Arrays.asList(
                "A-n32-k5.vrp", "A-n45-k6.vrp", "A-n45-k7.vrp", "A-n60-k9.vrp", "A-n80-k10.vrp",
                "B-n56-k7.vrp", "B-n66-k9.vrp", "B-n78-k10.vrp",
                "E-n76-k8.vrp", "E-n101-k14.vrp",
                "P-n50-k10.vrp", "P-n101-k4.vrp"));

        if (liveMode) {
            requiredInstances.clear();
            requiredInstances.add(targetInstance + ".vrp");
        }

        // Recursively walk the data directory to find required .vrp files
        List<File> instanceFilesList = new ArrayList<>();
        try (Stream<Path> paths = Files.walk(Paths.get(dataDir))) {
            paths.filter(Files::isRegularFile)
                 .filter(p -> p.toString().endsWith(".vrp"))
                 //.filter(p -> requiredInstances.contains(p.getFileName().toString()))
                 .forEach(p -> instanceFilesList.add(p.toFile()));
        } catch (IOException e) {
            e.printStackTrace();
        }

        File[] instanceFiles = instanceFilesList.toArray(new File[0]);
        if (instanceFiles.length == 0) {
            System.err.println("Nessuna istanza trovata in data/ o nelle sue sottocartelle");
            return;
        }

        // Algorithm Hyperparameters
        int popSize = 100;
        int selectionSize = 20;
        double cloneFactor = 0.5;
        int maxEvaluations = 350000;
        // In standard mode we run 5 independent trials to compute statistical variance
        int numRuns = liveMode ? 1 : 5; 

        // Creazione cartella dei risultati globale se non esiste
        new File(resultsDir).mkdirs();

        // Inizializzazione file summary globali con percorsi robusti (NIO)
        Path globalSummaryPath = Paths.get(resultsDir, "global_summary.csv");
        Path topicSummaryPath = Paths.get(resultsDir, "topic_summary.csv");

        if (!liveMode) {
            // Write CSV Headers for aggregate summaries
            try (FileWriter w = new FileWriter(globalSummaryPath.toFile())) {
                w.write("Instance,BestCost,MeanCost,StdDevCost,MeanIterations,Satisfability\n");
            } catch (IOException e) {
                e.printStackTrace();
            }
            try (FileWriter w = new FileWriter(topicSummaryPath.toFile())) {
                w.write("Instance,BestCost,MeanCost,StdDevCost,MeanIterations,Satisfability\n");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        for (File instanceFile : instanceFiles) {
            if (instanceFile.getName().equals("A-n45-k6.vrp")) {
                System.out.println("=== CASO STUDIO: " + instanceFile.getName() + " ===");
            } else {
                System.out.println("Processing instance: " + instanceFile.getName());
            }
            try {
                // Parse the geometric and demand data from the TSPLIB formatted file
                Instance instance = new Instance(instanceFile.getAbsolutePath());

                // Group outputs by dataset family (A, B, E, P)
                String family = instance.name.substring(0, 1);
                Path familyDir = Paths.get(resultsDir, family);
                Files.createDirectories(familyDir);

                double[] bestCosts = new double[numRuns];
                int[] bestEvals = new int[numRuns];
                Antibody globalBest = null;

                // Execute independent runs for statistical robustness
                for (int run = 0; run < numRuns; run++) {
                    System.out.println("  Run " + (run + 1) + "/" + numRuns);
                    
                    // Generate a deterministic seed offset by the run index
                    long seed = System.currentTimeMillis() + run;
                    ClonalSelection clonalg = new ClonalSelection(instance, popSize, selectionSize, cloneFactor,
                            maxEvaluations, seed);

                    String csvFileName = familyDir.resolve(instance.name + "_run_" + run + "_convergence.csv").toString();
                    try (FileWriter csvWriter = new FileWriter(csvFileName)) {
                        csvWriter.write("Evaluations,BestCost\n");
                        final boolean isLive = liveMode;
                        List<String> frames = new ArrayList<>();
                        
                        // Callback lambda to track execution trace asynchronously without tight coupling
                        clonalg.setTracker((evaluations, cost, bestAb) -> {
                            try {
                                csvWriter.write(evaluations + "," + cost + "\n");
                                csvWriter.flush();
                                // In live mode, dump geometric frames to JSON for external visualization
                                if (isLive) {
                                    frames.add(generateFrameJson(bestAb, instance, evaluations));
                                }
                            } catch (IOException e) {
                                e.printStackTrace();
                            }
                        });

                        // Start execution block
                        Antibody best = clonalg.run();
                        bestCosts[run] = best.getFitness();
                        bestEvals[run] = clonalg.getBestEvaluations();
                        System.out.println("    Best Cost: " + best.getFitness() + " (at eval " + bestEvals[run] + ")");

                        if (isLive) {
                            Path liveFramesPath = Paths.get(resultsDir, "live_frames.json");
                            try (FileWriter w = new FileWriter(liveFramesPath.toFile())) {
                                w.write("[\n");
                                for (int i = 0; i < frames.size(); i++) {
                                    w.write(frames.get(i) + (i < frames.size() - 1 ? ",\n" : "\n"));
                                }
                                w.write("]\n");
                            }
                        }

                        // Maintain reference to the best solution across all independent runs
                        if (globalBest == null || best.getFitness() < globalBest.getFitness()) {
                            globalBest = new Antibody(best);
                        }
                    }
                }

                // Calcolo statistiche finali
                double sum = 0;
                double bestCost = Double.MAX_VALUE;
                for (double c : bestCosts) {
                    sum += c;
                    if (c < bestCost) {
                        bestCost = c;
                    }
                }
                double mean = sum / numRuns;
                
                // Deviazione standard campionaria corretta (N-1) per runs > 1
                // Corrected sample standard deviation (Bessel's correction)
                double stdDev = 0.0;
                if (numRuns > 1) {
                    double variance = 0;
                    for (double c : bestCosts) {
                        variance += Math.pow(c - mean, 2);
                    }
                    stdDev = Math.sqrt(variance / (numRuns - 1));
                }

                // Check satisfability per il best globale
                // Ensure no customers were left unvisited
                int visitedCustomers = 0;
                for (Route r : globalBest.routes) {
                    visitedCustomers += r.nodes.size();
                }
                String satisfability = visitedCustomers + "/" + instance.customers.size();

                double sumEvals = 0;
                for (int e : bestEvals) {
                    sumEvals += e;
                }
                double meanEvals = sumEvals / numRuns;

                // Scrittura file statistiche specifico per istanza
                String statsFileName = familyDir.resolve(instance.name + "_stats.txt").toString();
                try (FileWriter w = new FileWriter(statsFileName)) {
                    w.write("Instance: " + instance.name + "\n");
                    w.write("Best Cost: " + bestCost + "\n");
                    w.write("Mean Cost: " + mean + "\n");
                    w.write("StdDev Cost: " + stdDev + "\n");
                    w.write("Mean Iterations (Evaluations): " + meanEvals + "\n");
                    w.write("Satisfability: " + satisfability + "\n");
                }

                // Scrittura dei log globali e per famiglia
                if (!liveMode) {
                    String line = instance.name + "," + bestCost + "," + mean + "," + stdDev + "," + meanEvals + ","
                            + satisfability + "\n";
                    
                    try (FileWriter w = new FileWriter(globalSummaryPath.toFile(), true)) {
                        w.write(line);
                    }
                    
                    if (requiredInstances.contains(instance.name + ".vrp")) {
                        try (FileWriter w = new FileWriter(topicSummaryPath.toFile(), true)) {
                            w.write(line);
                        }
                    }

                    String familySummaryFileName = familyDir.resolve(family + "_summary.csv").toString();
                    File famFile = new File(familySummaryFileName);
                    boolean writeHeader = !famFile.exists();
                    try (FileWriter w = new FileWriter(famFile, true)) {
                        if (writeHeader) {
                            w.write("Instance,BestCost,MeanCost,StdDevCost,MeanIterations,Satisfability\n");
                        }
                        w.write(line);
                    }
                }

                // Export della soluzione ottima in formato JSON per il plotting in Python
                // Dumps spatial coordinates into a standard JSON array for downstream visualization scripts
                String bestFileName = familyDir.resolve(instance.name + "_best_solution.json").toString();
                try (FileWriter w = new FileWriter(bestFileName)) {
                    w.write("{\n");
                    w.write("  \"instance\": \"" + instance.name + "\",\n");
                    w.write("  \"cost\": " + globalBest.getFitness() + ",\n");
                    w.write("  \"capacity\": " + instance.capacity + ",\n");
                    w.write("  \"depot\": [" + instance.depot.x + ", " + instance.depot.y + "],\n");
                    w.write("  \"loads\": [\n");
                    for (int i = 0; i < globalBest.routes.size(); i++) {
                        w.write("    " + globalBest.routes.get(i).getLoad()
                                + (i < globalBest.routes.size() - 1 ? ",\n" : "\n"));
                    }
                    w.write("  ],\n");
                    w.write("  \"routes\": [\n");
                    for (int i = 0; i < globalBest.routes.size(); i++) {
                        Route r = globalBest.routes.get(i);
                        w.write("    [");
                        w.write(r.nodes.stream().map(n -> "[" + n.x + ", " + n.y + "]")
                                .collect(Collectors.joining(", ")));
                        w.write("]" + (i < globalBest.routes.size() - 1 ? ",\n" : "\n"));
                    }
                    w.write("  ]\n");
                    w.write("}\n");
                }

            } catch (Exception e) {
                System.err.println("Error processing instance " + instanceFile.getName() + ": " + e.getMessage());
                e.printStackTrace();
            }
        }
        System.out.println("Tutte le run sono terminate! I risultati sono in " + resultsDir + "/");
    }

    /**
     * Serializza lo stato di un anticorpo in JSON.
     * Utilizzato esclusivamente in 'liveMode' per animare la convergenza dell'algoritmo step-by-step.
     */
    private static String generateFrameJson(Antibody globalBest, Instance instance, int evaluations) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\n");
        sb.append("  \"instance\": \"").append(instance.name).append("\",\n");
        sb.append("  \"cost\": ").append(globalBest.getFitness()).append(",\n");
        sb.append("  \"evaluations\": ").append(evaluations).append(",\n");
        sb.append("  \"capacity\": ").append(instance.capacity).append(",\n");
        sb.append("  \"depot\": [").append(instance.depot.x).append(", ").append(instance.depot.y).append("],\n");
        sb.append("  \"loads\": [\n");
        for (int i = 0; i < globalBest.routes.size(); i++) {
            sb.append("    ").append(globalBest.routes.get(i).getLoad())
                    .append(i < globalBest.routes.size() - 1 ? ",\n" : "\n");
        }
        sb.append("  ],\n");
        sb.append("  \"routes\": [\n");
        for (int i = 0; i < globalBest.routes.size(); i++) {
            Route r = globalBest.routes.get(i);
            sb.append("    [");
            sb.append(r.nodes.stream().map(n -> "[" + n.x + ", " + n.y + "]").collect(Collectors.joining(", ")));
            sb.append("]").append(i < globalBest.routes.size() - 1 ? ",\n" : "\n");
        }
        sb.append("  ]\n");
        sb.append("}");
        return sb.toString();
    }
}
