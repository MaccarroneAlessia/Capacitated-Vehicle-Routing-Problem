package cvrp.algorithm;

import cvrp.model.Antibody;
import cvrp.model.Instance;
import cvrp.model.Node;
import cvrp.model.Route;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Entry-point del programma Java. 
 * 
 * Gestisce il caricamento dei file `.vrp`, 
 * l'esecuzione dei test statistici e l'esportazione dei risultati in formato 
 * CSV e JSON.
 */

public class Main {

    public static void main(String[] args) {
        String dataDir = "data";
        String resultsDir = "results";

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

        java.util.Set<String> requiredInstances = new java.util.HashSet<>(java.util.Arrays.asList(
            "A-n45-k7.vrp", "A-n60-k9.vrp", "A-n80-k10.vrp",
            "B-n56-k7.vrp", "B-n66-k9.vrp", "B-n78-k10.vrp",
            "E-n76-k8.vrp", "E-n101-k14.vrp",
            "P-n50-k10.vrp", "P-n101-k4.vrp"
        ));

        if (liveMode) {
            requiredInstances.clear();
            requiredInstances.add(targetInstance + ".vrp");
        }

        List<File> instanceFilesList = new ArrayList<>();
        try {
            java.nio.file.Files.walk(java.nio.file.Paths.get(dataDir))
                .filter(p -> java.nio.file.Files.isRegularFile(p))
                .filter(p -> p.toString().endsWith(".vrp"))
                .filter(p -> requiredInstances.contains(p.getFileName().toString()))
                .forEach(p -> instanceFilesList.add(p.toFile()));
        } catch (IOException e) {
            e.printStackTrace();
        }

        File[] instanceFiles = instanceFilesList.toArray(new File[0]);
        if (instanceFiles.length == 0) {
            System.err.println("Nessuna istanza trovata in data/ o nelle sue sottocartelle");
            return;
        }

        int popSize = 100;
        int selectionSize = 20;
        double cloneFactor = 0.5;
        int maxEvaluations = 350000;
        int numRuns = liveMode ? 1 : 5;

        // Initialize global summary file
        String globalSummaryFileName = resultsDir + "/global_summary.csv";
        try (FileWriter w = new FileWriter(globalSummaryFileName)) {
            w.write("Instance,BestCost,MeanCost,StdDevCost,MeanIterations,Satisfability\n");
        } catch (IOException e) {
            e.printStackTrace();
        }

        for (File instanceFile : instanceFiles) {
            System.out.println("Processing instance: " + instanceFile.getName());
            try {
                Instance instance = new Instance(instanceFile.getAbsolutePath());
                double[] bestCosts = new double[numRuns];
                int[] bestEvals = new int[numRuns];
                Antibody globalBest = null;

                for (int run = 0; run < numRuns; run++) {
                    System.out.println("  Run " + (run + 1) + "/" + numRuns);
                    long seed = System.currentTimeMillis() + run;
                    ClonalSelection clonalg = new ClonalSelection(instance, popSize, selectionSize, cloneFactor, maxEvaluations, seed);
                    
                    final int currentRun = run;
                    String csvFileName = resultsDir + "/" + instance.name + "_run_" + run + "_convergence.csv";
                    try (FileWriter csvWriter = new FileWriter(csvFileName)) {
                        csvWriter.write("Evaluations,BestCost\n");
                        final boolean isLive = liveMode;
                        List<String> frames = new ArrayList<>();
                        clonalg.setTracker((evaluations, cost, bestAb) -> {
                            try {
                                csvWriter.write(evaluations + "," + cost + "\n");
                                csvWriter.flush();
                                if (isLive) {
                                    frames.add(generateFrameJson(bestAb, instance, evaluations));
                                }
                            } catch (IOException e) {
                                e.printStackTrace();
                            }
                        });
                        
                        Antibody best = clonalg.run();
                        bestCosts[run] = best.getFitness();
                        bestEvals[run] = clonalg.getBestEvaluations();
                        System.out.println("    Best Cost: " + best.getFitness() + " (at eval " + bestEvals[run] + ")");
                        
                        if (isLive) {
                            try (FileWriter w = new FileWriter(resultsDir + "/live_frames.json")) {
                                w.write("[\n");
                                for (int i = 0; i < frames.size(); i++) {
                                    w.write(frames.get(i) + (i < frames.size() - 1 ? ",\n" : "\n"));
                                }
                                w.write("]\n");
                            }
                        }
                        
                        if (globalBest == null || best.getFitness() < globalBest.getFitness()) {
                            globalBest = new Antibody(best);
                        }
                    }
                }

                // Calculate stats
                double sum = 0;
                double bestCost = Double.MAX_VALUE;
                for (double c : bestCosts) {
                    sum += c;
                    if (c < bestCost) bestCost = c;
                }
                double mean = sum / numRuns;
                double variance = 0;
                for (double c : bestCosts) {
                    variance += Math.pow(c - mean, 2);
                }
                double stdDev = Math.sqrt(variance / numRuns);

                // Check satisfability for global best
                int visitedCustomers = 0;
                for (Route r : globalBest.routes) visitedCustomers += r.nodes.size();
                String satisfability = visitedCustomers + "/" + instance.customers.size();

                double sumEvals = 0;
                for (int e : bestEvals) sumEvals += e;
                double meanEvals = sumEvals / numRuns;

                // Write stats
                String statsFileName = resultsDir + "/" + instance.name + "_stats.txt";
                try (FileWriter w = new FileWriter(statsFileName)) {
                    w.write("Instance: " + instance.name + "\n");
                    w.write("Best Cost: " + bestCost + "\n");
                    w.write("Mean Cost: " + mean + "\n");
                    w.write("StdDev Cost: " + stdDev + "\n");
                    w.write("Mean Iterations (Evaluations): " + meanEvals + "\n");
                    w.write("Satisfability: " + satisfability + "\n");
                }

                // Append to global summary
                if (!liveMode) {
                    try (FileWriter w = new FileWriter(globalSummaryFileName, true)) {
                        w.write(instance.name + "," + bestCost + "," + mean + "," + stdDev + "," + meanEvals + "," + satisfability + "\n");
                    }
                }
                
                // Write best solution for plotting
                String bestFileName = resultsDir + "/" + instance.name + "_best_solution.json";
                try (FileWriter w = new FileWriter(bestFileName)) {
                    w.write("{\n");
                    w.write("  \"instance\": \"" + instance.name + "\",\n");
                    w.write("  \"cost\": " + globalBest.getFitness() + ",\n");
                    w.write("  \"capacity\": " + instance.capacity + ",\n");
                    w.write("  \"depot\": [" + instance.depot.x + ", " + instance.depot.y + "],\n");
                    w.write("  \"loads\": [\n");
                    for (int i = 0; i < globalBest.routes.size(); i++) {
                        w.write("    " + globalBest.routes.get(i).getLoad() + (i < globalBest.routes.size() - 1 ? ",\n" : "\n"));
                    }
                    w.write("  ],\n");
                    w.write("  \"routes\": [\n");
                    for (int i = 0; i < globalBest.routes.size(); i++) {
                        Route r = globalBest.routes.get(i);
                        w.write("    [");
                        w.write(r.nodes.stream().map(n -> "[" + n.x + ", " + n.y + "]").collect(Collectors.joining(", ")));
                        w.write("]" + (i < globalBest.routes.size() - 1 ? ",\n" : "\n"));
                    }
                    w.write("  ]\n");
                    w.write("}\n");
                }

            } catch (Exception e) {
                System.err.println("Error processing instance " + instanceFile.getName() + ": " + e.getMessage());
            }
        }
        System.out.println("Tutte le run sono terminate! I risultati sono in results/");
    }

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
            sb.append("    ").append(globalBest.routes.get(i).getLoad()).append(i < globalBest.routes.size() - 1 ? ",\n" : "\n");
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
