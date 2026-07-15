package cvrp.algorithm;

import cvrp.model.Antibody;
import cvrp.model.Instance;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

/**
 * Orchestratore sperimentale per lo studio di ablazione (Ablation Study).
 * Questo script isola, disattiva e riattiva selettivamente le varie componenti algoritmiche
 * (Greedy Initialization, Simulated Annealing, Large Neighborhood Search)
 * per valutare scientificamente l'impatto matematico e prestazionale di ogni singola
 * componente sulla fitness finale della meta-euristica.
 */
public class AblationRunner {

    public static void main(String[] args) {
        String dataDir = "data";
        String resultsDir = "results/ablations";
        
        // Define target instances of varying sizes and complexities for a rigorous benchmark
        String[] targetInstances = {"A-n32-k5", "A-n45-k6", "B-n56-k7", "E-n101-k14"};

        for (String targetInstance : targetInstances) {
            // Flexible path resolution supporting both flat and nested 'data' directories
            File instanceFile = new File(dataDir, targetInstance.substring(0, 1) + "/" + targetInstance + ".vrp");
            if (!instanceFile.exists()) {
                instanceFile = new File(dataDir, targetInstance + ".vrp");
            }
            if (!instanceFile.exists()) {
                 System.err.println("File istanza non trovato: " + targetInstance);
                 continue;
            }

            System.out.println("=== ABLATION STUDY: " + targetInstance + " ===");

            Instance instance = null;
            try {
                // Parse instance file into immutable geometric data structure
                instance = new Instance(instanceFile.getAbsolutePath());
            } catch (Exception e) {
                e.printStackTrace();
                continue;
            }

            // Create target output directory for this specific instance
            String targetDir = resultsDir + "/" + targetInstance;
            new java.io.File(targetDir).mkdirs();

            // Hyperparameter baseline configuration
            int popSize = 100;
            int selectionSize = 20;
            double cloneFactor = 0.5;
            int maxEvaluations = 350000;
            long seed = 42; // Fixed seed for reproducible stochastic benchmarking

            // Execute the full cartesian product of algorithmic components
            runAblation(instance, "baseline", false, false, false, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "nn", true, false, false, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "sa", false, true, false, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "lns", false, false, true, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "nn_sa", true, true, false, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "nn_lns", true, false, true, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "sa_lns", false, true, true, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
            runAblation(instance, "all", true, true, true, popSize, selectionSize, cloneFactor, maxEvaluations, seed, targetDir);
        }
        System.out.println("Ablation study completato per tutte le istanze.");
    }

    /**
     * Innesca un'esecuzione isolata dell'algoritmo genetico disabilitando/abilitando componenti selettive.
     * Utilizza un'interfaccia funzionale (lambda) per intercettare il tracker
     * ed esportare dinamicamente i dati di convergenza (Evaluations vs Cost) in formato CSV.
     */
    private static void runAblation(Instance instance, String name, boolean useNN, boolean useSA, boolean useLNS,
                                    int popSize, int selectionSize, double cloneFactor, int maxEvaluations, long seed, String targetDir) {
        System.out.println("Running config: " + name + " (NN=" + useNN + ", SA=" + useSA + ", LNS=" + useLNS + ")");
        
        // Initialize the algorithmic engine with defined hyper-parameters
        ClonalSelection clonalg = new ClonalSelection(instance, popSize, selectionSize, cloneFactor, maxEvaluations, seed);
        
        // Force structural ablations according to the study matrix
        clonalg.setAblations(useNN, useSA, useLNS);
        clonalg.setAdaptiveMode(false); // Disabilita la Saturated Mode per un test di ablazione "puro"

        // Platform-agnostic path resolution for output CSVs
        java.nio.file.Path csvPath = java.nio.file.Paths.get(targetDir, instance.name + "_ablation_" + name + "_convergence.csv");
        
        try (FileWriter csvWriter = new FileWriter(csvPath.toFile())) {
            // Write standard CSV header
            csvWriter.write("Evaluations,BestCost\n");
            
            // Attach lambda callback to track fitness convergence asynchronously
            clonalg.setTracker((evaluations, cost, bestAb) -> {
                try {
                    csvWriter.write(evaluations + "," + cost + "\n");
                    // Avoid calling flush at each iteration to prevent massive I/O bottlenecks
                } catch (IOException e) {
                    e.printStackTrace();
                }
            });

            // Trigger the execution
            Antibody best = clonalg.run();
            
            // Force write persistence after completion
            csvWriter.flush(); // Garantisce la persistenza dei dati prima della chiusura
            System.out.println("  -> Best Cost: " + best.getFitness());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
