package cvrp.algorithm;

import cvrp.model.Antibody;
import cvrp.model.Instance;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Stream;

public class AblationRunner {

    public static void main(String[] args) {
        String dataDir = "data";
        String resultsDir = "results/ablations";
        
        // Istanze di cui esportiamo anche l'andamento completo per i grafici nel Notebook
        // Più piccola	P-n16-k8
        // Più grande	E-n101-k14
        // Meno satura	E-n23-k3	
        // Più satura	B-n57-k7
        // "A-n32-k5"
        // "A-n45-k6"
        // "B-n56-k7"
        Set<String> detailInstances = new HashSet<>(Arrays.asList("P-n16-k8", "E-n101-k14", "E-n23-k3", "B-n57-k7", "A-n32-k5", "A-n45-k6", "B-n56-k7"));

        List<File> instanceFilesList = new ArrayList<>();
        try (Stream<Path> paths = Files.walk(Paths.get(dataDir))) {
            paths.filter(Files::isRegularFile)
                 .filter(p -> p.toString().endsWith(".vrp"))
                 .forEach(p -> instanceFilesList.add(p.toFile()));
        } catch (IOException e) {
            e.printStackTrace();
        }

        File[] instanceFiles = instanceFilesList.toArray(new File[0]);
        if (instanceFiles.length == 0) {
            System.err.println("Nessuna istanza trovata in data/");
            return;
        }

        String[] configs = {"baseline", "nn", "sa", "lns", "nn_sa", "nn_lns", "sa_lns", "all"};
        Map<String, Integer> winCounts = new HashMap<>();
        for (String c : configs) winCounts.put(c, 0);

        int totalInstancesProcessed = 0;

        long globalStartTime = System.currentTimeMillis();
        
        Path metricsPath = Paths.get(resultsDir, "ablation_global_metrics.csv");
        new File(resultsDir).mkdirs();
        try (FileWriter w = new FileWriter(metricsPath.toFile())) {
            w.write("Instance,Configuration,Cost,TimeMs,BestEval\n");
        } catch (IOException e) {
            e.printStackTrace();
        }

        for (File instanceFile : instanceFiles) {
            String instanceName = instanceFile.getName().replace(".vrp", "");
            System.out.println("=== ABLATION STUDY: " + instanceName + " ===");
            long startInstanceTime = System.currentTimeMillis();

            Instance instance = null;
            try {
                instance = new Instance(instanceFile.getAbsolutePath());
            } catch (Exception e) {
                e.printStackTrace();
                continue;
            }

            boolean isDetail = detailInstances.contains(instanceName);
            String targetDir = resultsDir + "/" + instanceName;
            if (isDetail) {
                new java.io.File(targetDir).mkdirs();
            }

            int popSize = 100;
            int selectionSize = 20;
            double cloneFactor = 0.5;
            int maxEvaluations = 350000;
            long seed = 42;

            Map<String, Double> costs = new HashMap<>();

            try (FileWriter metricsWriter = new FileWriter(metricsPath.toFile(), true)) {
                for (String c : configs) {
                    boolean nn = c.contains("nn") || c.equals("all");
                    boolean sa = c.contains("sa") || c.equals("all");
                    boolean lns = c.contains("lns") || c.equals("all");
                    if (c.equals("baseline")) { nn = false; sa = false; lns = false; }
                    
                    double[] result = runAblation(instance, c, nn, sa, lns, popSize, selectionSize, cloneFactor, maxEvaluations, seed, isDetail ? targetDir : null);
                    costs.put(c, result[0]);
                    
                    metricsWriter.write(instanceName + "," + c + "," + result[0] + "," + (long)result[1] + "," + (int)result[2] + "\n");
                }
            } catch (IOException e) {
                e.printStackTrace();
            }

            // Trova il vincitore
            double minCost = Double.MAX_VALUE;
            String winner = "";
            for (Map.Entry<String, Double> entry : costs.entrySet()) {
                if (entry.getValue() < minCost) {
                    minCost = entry.getValue();
                    winner = entry.getKey();
                }
            }
            
            winCounts.put(winner, winCounts.get(winner) + 1);
            totalInstancesProcessed++;
            long endInstanceTime = System.currentTimeMillis();
            System.out.println("  -> WINNER per " + instanceName + ": " + winner.toUpperCase() + " (Time: " + (endInstanceTime - startInstanceTime) + " ms)\n");
        }

        long globalEndTime = System.currentTimeMillis();
        System.out.println("=====================================================");
        System.out.println("  RISULTATI FINALI ABLATION SU " + totalInstancesProcessed + " ISTANZE (Total time: " + (globalEndTime - globalStartTime) + " ms)");
        System.out.println("=====================================================");
        
        String bestConfig = "";
        int maxWins = -1;

        for (String c : configs) {
            int wins = winCounts.get(c);
            double pct = (wins / (double) totalInstancesProcessed) * 100.0;
            System.out.printf(" - Configurazione %-8s: %3d vittorie (%.1f%%)\n", c.toUpperCase(), wins, pct);
            
            if (wins > maxWins) {
                maxWins = wins;
                bestConfig = c;
            }
        }
        
        System.out.println("\n🏆 Configurazione statisticamente migliore: " + bestConfig.toUpperCase() + " con il " + String.format("%.1f", (maxWins / (double) totalInstancesProcessed) * 100.0) + "% di dominanza.");
    }

    private static double[] runAblation(Instance instance, String name, boolean useNN, boolean useSA, boolean useLNS,
                                    int popSize, int selectionSize, double cloneFactor, int maxEvaluations, long seed, String targetDir) {
        System.out.println("Running config: " + name);
        
        ClonalSelection clonalg = new ClonalSelection(instance, popSize, selectionSize, cloneFactor, maxEvaluations, seed);
        clonalg.setAblations(useNN, useSA, useLNS);
        clonalg.setAdaptiveMode(false);

        FileWriter csvWriter = null;
        if (targetDir != null) {
            java.nio.file.Path csvPath = java.nio.file.Paths.get(targetDir, instance.name + "_ablation_" + name + "_convergence.csv");
            try {
                csvWriter = new FileWriter(csvPath.toFile());
                csvWriter.write("Evaluations,BestCost\n");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

        final FileWriter finalCsvWriter = csvWriter;

        if (finalCsvWriter != null) {
            clonalg.setTracker((evaluations, cost, bestAb) -> {
                try {
                    finalCsvWriter.write(evaluations + "," + cost + "\n");
                } catch (IOException e) {
                    e.printStackTrace();
                }
            });
        }

        long startRunTime = System.currentTimeMillis();
        Antibody best = clonalg.run();
        long endRunTime = System.currentTimeMillis();
        System.out.println("    -> Cost: " + best.getFitness() + " (Time: " + (endRunTime - startRunTime) + " ms)");
        
        if (finalCsvWriter != null) {
            try {
                finalCsvWriter.flush();
                finalCsvWriter.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        
        return new double[] { best.getFitness(), (endRunTime - startRunTime), clonalg.getBestEvaluations() };
    }
}
