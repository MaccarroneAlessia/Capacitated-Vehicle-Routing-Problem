package cvrp.algorithm;

import cvrp.model.Antibody;
import cvrp.model.Instance;
import cvrp.model.Node;
import cvrp.model.Route;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Implementazione dell'Algoritmo Memetico basato su Clonal Selection (Artificial Immune System) per il CVRP.
 * 
 * Motore di ottimizzazione principale che integra la selezione clonale con operatori euristici avanzati:
 * 
 * 1. Smart Initialization: Inizializza una frazione della popolazione usando un'euristica costruttiva greedy (Nearest Neighbor), accelerando la convergenza iniziale.
 * 2. Large Neighborhood Search (LNS): Un operatore di Ruin & Recreate distrugge porzioni di rotte sub-ottime e le reinserisce nella posizione globalmente più economica, evitando trappole di minimo locale.
 * 3. Simulated Annealing (SA) in Local Search: Sostituisce l'accettazione deterministica della 2-Opt con un criterio stocastico basato sulla Temperatura, permettendo all'algoritmo di fuggire efficacemente dai minimi locali.
 * 4. Saturated Mode (Receptor Editing): Meccanismo adattivo fuzzy che modula il tasso di rimpiazzo della popolazione e l'intensità delle mutazioni in base al livello di saturazione della flotta (domanda vs capacità).
 */
public class ClonalSelection {
    // Geometrical and logic properties of the problem instance
    private final Instance instance;
    
    // Core parameters of the Clonal Selection Algorithm
    private final int popSize;
    private final int selectionSize;
    private final double cloneFactor;
    private final Random random;
    private final int maxEvaluations;

    // Tracking variables for progress and optimal solution
    private int currentEvaluations;
    private Antibody bestAntibody;
    private int bestEvaluations;
    private int totalIterations;
    private int bestIteration;
    
    // Algorithmic estimation for total necessary vehicles
    private int estimatedK = -1;

    // ABLATION FLAGS (for experimental toggle of algorithmic features)
    // Default: NN_LNS — eletta configurazione migliore dallo studio d'ablazione su 85 istanze
    // NN_LNS raggiunge il 92.99% del costo baseline con solo il 174% del tempo (vs ALL al 1193%)
    private boolean useNN = true;
    private boolean useSA = false;
    private boolean useLNS = true;
    private boolean useAdaptiveMode = true;

    public void setAblations(boolean useNN, boolean useSA, boolean useLNS) {
        this.useNN = useNN;
        this.useSA = useSA;
        this.useLNS = useLNS;
    }

    public void setAdaptiveMode(boolean useAdaptiveMode) {
        this.useAdaptiveMode = useAdaptiveMode;
    }

    public int getBestEvaluations() {
        return bestEvaluations;
    }

    public int getTotalIterations() {
        return totalIterations;
    }

    public int getBestIteration() {
        return bestIteration;
    }

    // Callbacks for tracking algorithm convergence and telemetry
    public interface Tracker {
        void onNewBest(int evaluations, double cost, Antibody bestAntibody);
    }
    private Tracker tracker;

    public ClonalSelection(Instance instance, int popSize, int selectionSize, double cloneFactor, int maxEvaluations, long seed) {
        this.instance = instance;
        this.popSize = popSize;
        this.selectionSize = selectionSize;
        this.cloneFactor = cloneFactor;
        this.maxEvaluations = maxEvaluations;
        this.random = new Random(seed);
    }

    public void setTracker(Tracker tracker) {
        this.tracker = tracker;
    }

    /**
     * Esegue il ciclo principale dell'algoritmo genetico-immunitario.
     * Itera le fasi di clonazione, mutazione, selezione e editing dei recettori 
     * fino all'esaurimento del budget computazionale (Fitness Evaluations).
     */
    public Antibody run() {
        currentEvaluations = 0;
        totalIterations = 0;
        bestIteration = 0;
        
        // Fallback se l'inizializzazione Greedy (NN) è disattivata dall'ablation
        // Fallback constraint logic to establish minimum fleet size if Greedy heuristic is bypassed
        if (!useNN || estimatedK == -1) {
            double totalDemand = instance.customers.stream().mapToDouble(n -> n.demand).sum();
            // Calcolo teorico del numero minimo di veicoli (Bin Packing Lower Bound)
            // Theoretical lower bound of required vehicles based on aggregate demand vs capacity
            estimatedK = (int) Math.ceil(totalDemand / instance.capacity);
            if (estimatedK < 1) estimatedK = 1;
        }

        List<Antibody> population = initializePopulation();
        
        if (tracker != null && !population.isEmpty()) {
            // Expose the unoptimized random solution (end of population before sort)
            // to the tracker as the initial baseline frame for live visualization.
            Antibody messyStart = population.get(population.size() - 1);
            tracker.onNewBest(0, messyStart.getFitness(), messyStart);
        }
        
        // Main Evolutionary Loop bounded by Fitness Evaluation budget
        while (currentEvaluations < maxEvaluations) {
            totalIterations++;
            // Sort population by fitness (lower cost is prioritized)
            Collections.sort(population);

            // Update global best if a new optimum is found
            if (bestAntibody == null || population.get(0).getFitness() < bestAntibody.getFitness()) {
                bestAntibody = new Antibody(population.get(0));
                bestEvaluations = currentEvaluations;
                bestIteration = totalIterations;
                if (tracker != null) {
                    tracker.onNewBest(currentEvaluations, bestAntibody.getFitness(), bestAntibody);
                }
            }

            // Select best 'selectionSize' antibodies for cloning
            List<Antibody> selected = new ArrayList<>(population.subList(0, selectionSize));

            // Proliferation stage: Clone and mutate
            List<Antibody> clones = new ArrayList<>();
            for (int i = 0; i < selected.size(); i++) {
                Antibody parent = selected.get(i);
                
                // Affinity Proportionate Cloning: Better ranked antibodies (lower 'i') produce more clones
                int numClones = (int) Math.round(cloneFactor * popSize / (i + 1.0));
                if (numClones < 1) numClones = 1;

                for (int c = 0; c < numClones; c++) {
                    // Preemptive execution guard
                    if (currentEvaluations >= maxEvaluations) break;
                    
                    Antibody clone = new Antibody(parent);
                    
                    // Hypermutation phase: Mutation rate is inversely proportional to rank (worse clones mutate more)
                    int numMutations = 1 + i; 
                    hyperMutate(clone, numMutations);
                    
                    // MEMETIC STEP: Apply SA Local Search only to elite clones (i=0) for intense local exploitation
                    if (useSA && i == 0 && random.nextDouble() < 0.2) {
                        saLocalSearch(clone, currentEvaluations, maxEvaluations);
                    }

                    clone.recalculateFitness();
                    currentEvaluations++;
                    clones.add(clone);
                }
            }

            // Combine and select next generation
            population.addAll(clones);
            Collections.sort(population);
            population = new ArrayList<>(population.subList(0, popSize)); // Keep top popSize

            // Receptor Editing: transizione morbida dal 10% (sat <= 80%) al 20% (sat >= 95%)
            // Fuzzy Adaptive Receptor Editing to inject diversity based on instance difficulty (saturation)
            double sat = instance.getSaturation(estimatedK);
            double alpha = 0.0;
            if (useAdaptiveMode) {
                // Linear fuzzy membership function [0.0, 1.0] over [80%, 95%] saturation range
                alpha = Math.max(0.0, Math.min(1.0, (sat - 0.8) / 0.15));
            }
            double editingRate = 0.1 + alpha * 0.1;
            int replaceCount = (int) (editingRate * popSize);
            
            for (int i = 0; i < replaceCount; i++) {
                // Guardia preventiva: se abbiamo esaurito le valutazioni, fermiamo immediatamente l'editing
                // Hard guard against surpassing the evaluation budget during diversity injection
                if (currentEvaluations >= maxEvaluations) {
                    break;
                }
                Antibody fresh = generateRandomSolution();
                fresh.recalculateFitness();
                currentEvaluations++;
                population.set(popSize - 1 - i, fresh);
            }
        }
        
        // Final check and sort post-evaluation loop
        Collections.sort(population);
        if (population.get(0).getFitness() < bestAntibody.getFitness()) {
            bestAntibody = new Antibody(population.get(0));
            bestEvaluations = currentEvaluations;
            if (tracker != null) {
                tracker.onNewBest(currentEvaluations, bestAntibody.getFitness(), bestAntibody);
            }
        }

        return bestAntibody;
    }

    /**
     * Inizializza la popolazione miscelando algoritmi costruttivi deterministici (Greedy/NN)
     * e puramente casuali per massimizzare la copertura spaziale garantendo al contempo convergenza veloce.
     */
    private List<Antibody> initializePopulation() {
        List<Antibody> pop = new ArrayList<>();
        // Inject up to 20% heuristically sound solutions to accelerate convergence
        int smartCount = useNN ? (int) (popSize * 0.20) : 0; 
        
        for (int i = 0; i < popSize; i++) {
            Antibody sol;
            if (i < smartCount) {
                sol = generateSmartSolution(); // Nearest-Neighbor (Greedy)
                if (estimatedK == -1 && !sol.routes.isEmpty()) {
                    estimatedK = sol.routes.size(); // Set estimated K heuristically
                }
            } else {
                sol = generateRandomSolution(); // Purely random construction
            }
            sol.recalculateFitness();
            currentEvaluations++;
            pop.add(sol);
        }
        return pop;
    }

    /**
     * Genera una soluzione costruttiva tramite l'euristica Nearest-Neighbor (Greedy)
     * stocasticizzata per creare varietà all'interno del sub-pool di élite.
     */
    private Antibody generateSmartSolution() {
        Antibody ab = new Antibody(instance);
        List<Node> unvisited = new ArrayList<>(instance.customers);
        
        // Shuffle unvisited nodes to introduce stochasticity into the greedy heuristic
        Collections.shuffle(unvisited, random);

        Route currentRoute = new Route(instance);
        Node currentNode = instance.depot;

        while (!unvisited.isEmpty()) {
            // Find the nearest feasible neighbor
            Node bestNext = null;
            double minDistance = Double.MAX_VALUE;
            
            // Introduce a small randomness factor (e.g. 10% chance to pick random feasible node instead of nearest)
            if (random.nextDouble() < 0.1) {
                for (Node n : unvisited) {
                    if (currentRoute.canAdd(n)) {
                        bestNext = n;
                        break;
                    }
                }
            } else {
                for (Node n : unvisited) {
                    if (currentRoute.canAdd(n)) {
                        double dist = currentNode.distanceTo(n);
                        if (dist < minDistance) {
                            minDistance = dist;
                            bestNext = n;
                        }
                    }
                }
            }

            if (bestNext != null) {
                currentRoute.addNode(bestNext);
                unvisited.remove(bestNext);
                currentNode = bestNext;
            } else {
                // Vehicle capacity reached: close current route and return to depot
                ab.routes.add(currentRoute);
                currentRoute = new Route(instance);
                currentNode = instance.depot;
            }
        }
        if (!currentRoute.isEmpty()) {
            ab.routes.add(currentRoute);
        }
        return ab;
    }

    /**
     * Genera un anticorpo completamente stocastico (random) rispettando il vincolo di capacità.
     */
    private Antibody generateRandomSolution() {
        Antibody ab = new Antibody(instance);
        List<Node> unvisited = new ArrayList<>(instance.customers);
        Collections.shuffle(unvisited, random);

        Route currentRoute = new Route(instance);
        for (Node n : unvisited) {
            if (currentRoute.canAdd(n)) {
                currentRoute.addNode(n);
            } else {
                ab.routes.add(currentRoute);
                currentRoute = new Route(instance);
                currentRoute.addNode(n);
            }
        }
        if (!currentRoute.isEmpty()) {
            ab.routes.add(currentRoute);
        }
        return ab;
    }

    /**
     * Modula l'intensità delle mutazioni (Intra-Route, Inter-Route, LNS)
     * e le applica in maniera stocastica bilanciata dall'Alpha parametro della Saturated Mode.
     */
    private void hyperMutate(Antibody ab, int numMutations) {
        // Transizione lineare delle probabilità di mutazione tra baseline e saturated
        double sat = instance.getSaturation(estimatedK);
        double alpha = 0.0;
        if (useAdaptiveMode) {
            alpha = Math.max(0.0, Math.min(1.0, (sat - 0.8) / 0.15));
        }
        
        // Probability distribution of specific permutation operators modulated by fuzzy logic
        double p0 = 0.2 + alpha * 0.1; // intraSwap: 20% -> 30%
        double p1 = 0.2 + alpha * 0.1; // intra2Opt: 20% -> 30%
        double p2 = 0.2 - alpha * 0.2; // interRelocate: 20% -> 0%
        double p3 = 0.2 + alpha * 0.1; // interSwapNodes: 20% -> 30%
        // p4 (LNS) is implicitly the remaining probability: 20% -> 10%

        if (!useLNS) {
            // Normalize probabilities if LNS is completely deactivated for ablation study
            double scale = 1.0 / (p0 + p1 + p2 + p3);
            p0 *= scale;
            p1 *= scale;
            p2 *= scale;
            p3 *= scale;
        }
        
        for (int m = 0; m < numMutations; m++) {
            int op = -1;
            double r = random.nextDouble();
            
            // Roulette wheel selection for the specific mutation operator
            if (r < p0) op = 0;
            else if (r < p0 + p1) op = 1;
            else if (r < p0 + p1 + p2) op = 2;
            else if (r < p0 + p1 + p2 + p3) op = 3;
            else op = useLNS ? 4 : random.nextInt(4);
            
            switch (op) {
                case 0: intraRouteSwap(ab); break;
                case 1: intraRoute2Opt(ab); break;
                case 2: interRouteRelocate(ab); break;
                case 3: interRouteSwapNodes(ab); break;
                case 4: if(useLNS) largeNeighborhoodRuinRecreate(ab); break;
            }
        }
        // Cleanup empty routes that might have been drained by relocations
        ab.routes.removeIf(Route::isEmpty);
    }

    private void intraRouteSwap(Antibody ab) {
        if (ab.routes.isEmpty()) return;
        Route r = ab.routes.get(random.nextInt(ab.routes.size()));
        if (r.nodes.size() < 2) return;
        int i = random.nextInt(r.nodes.size());
        int j = random.nextInt(r.nodes.size());
        
        Node temp = r.nodes.get(i);
        r.nodes.set(i, r.nodes.get(j));
        r.nodes.set(j, temp);
    }

    private void intraRoute2Opt(Antibody ab) {
        if (ab.routes.isEmpty()) return;
        Route r = ab.routes.get(random.nextInt(ab.routes.size()));
        if (r.nodes.size() < 4) return;
        
        int i = random.nextInt(r.nodes.size() - 2);
        int j = i + 2 + random.nextInt(r.nodes.size() - i - 2);
        
        // Reverse sublist from i to j (destroys crossing edges in a planar graph)
        int left = i, right = j;
        while (left < right) {
            Node temp = r.nodes.get(left);
            r.nodes.set(left, r.nodes.get(right));
            r.nodes.set(right, temp);
            left++;
            right--;
        }
    }

    private void interRouteRelocate(Antibody ab) {
        if (ab.routes.size() < 2) return;
        int r1Idx = random.nextInt(ab.routes.size());
        int r2Idx = random.nextInt(ab.routes.size());
        while (r1Idx == r2Idx) r2Idx = random.nextInt(ab.routes.size());
        
        Route r1 = ab.routes.get(r1Idx);
        Route r2 = ab.routes.get(r2Idx);
        
        if (r1.nodes.isEmpty()) return;
        int nodeIdx = random.nextInt(r1.nodes.size());
        Node n = r1.nodes.get(nodeIdx);
        
        // Try inserting the node from route 1 into route 2 respecting capacity constraint
        if (r2.canAdd(n)) {
            r1.removeNodeAt(nodeIdx);
            int insertIdx = r2.nodes.isEmpty() ? 0 : random.nextInt(r2.nodes.size() + 1);
            r2.addNodeAt(insertIdx, n);
        }
    }

    private void interRouteSwapNodes(Antibody ab) {
        if (ab.routes.size() < 2) return;
        int r1Idx = random.nextInt(ab.routes.size());
        int r2Idx = random.nextInt(ab.routes.size());
        while (r1Idx == r2Idx) r2Idx = random.nextInt(ab.routes.size());
        
        Route r1 = ab.routes.get(r1Idx);
        Route r2 = ab.routes.get(r2Idx);
        
        if (r1.nodes.isEmpty() || r2.nodes.isEmpty()) return;
        int idx1 = random.nextInt(r1.nodes.size());
        int idx2 = random.nextInt(r2.nodes.size());
        
        Node n1 = r1.nodes.get(idx1);
        Node n2 = r2.nodes.get(idx2);
        
        // Check capacity constraints before swapping nodes between routes
        int newLoad1 = r1.getLoad() - n1.demand + n2.demand;
        int newLoad2 = r2.getLoad() - n2.demand + n1.demand;
        
        if (newLoad1 <= instance.capacity && newLoad2 <= instance.capacity) {
            r1.nodes.set(idx1, n2);
            r2.nodes.set(idx2, n1);
            r1.recalculateCost();
            r2.recalculateCost();
        }
    }

    /**
     * Memetic Algorithm Component: 2-Opt Local Search con accettazione Simulated Annealing (SA).
     * Invece di accettare rigorosamente solo le mosse migliorative (Hill Climbing), il 
     * Simulated Annealing accetta occasionalmente peggioramenti per fuggire dai minimi locali.
     */
    private void saLocalSearch(Antibody ab, int currentEval, int maxEval) {
        // Linearly decrease temperature based on evaluation progress (exploration to exploitation)
        double initialTemp = 100.0;
        double currentTemp = initialTemp * (1.0 - ((double) currentEval / maxEval));
        if (currentTemp < 0.1) currentTemp = 0.1; // Freeze boundary

        boolean improvement = true;
        int maxIter = 50; // Iteration limit to prevent infinite loops on flat plateaus
        int iter = 0;
        
        while (improvement && iter < maxIter) {
            improvement = false;
            iter++;
            for (Route r : ab.routes) {
                if (r.nodes.size() < 4) continue;
                for (int i = 0; i < r.nodes.size() - 2; i++) {
                    for (int j = i + 2; j < r.nodes.size() - 1; j++) {
                        Node a = (i == 0) ? instance.depot : r.nodes.get(i - 1);
                        Node b = r.nodes.get(i);
                        Node c = r.nodes.get(j);
                        Node d = (j == r.nodes.size() - 1) ? instance.depot : r.nodes.get(j + 1);
                        
                        // Delta calculation: Geometric cost of new connections minus old connections
                        double currentDist = a.distanceTo(b) + c.distanceTo(d);
                        double newDist = a.distanceTo(c) + b.distanceTo(d);
                        double delta = newDist - currentDist;
                        
                        boolean accept = false;
                        if (delta < -1e-4) {
                            // Strict improvement: ALWAYS accept
                            accept = true; 
                            improvement = true;
                        } else {
                            // SA stochastic acceptance probability for worsening moves
                            double p = Math.exp(-delta / currentTemp);
                            if (random.nextDouble() < p) {
                                accept = true;
                            }
                        }
                        
                        // Execute the topological 2-Opt swap in the data structure
                        if (accept) {
                            int left = i, right = j;
                            while (left < right) {
                                Node temp = r.nodes.get(left);
                                r.nodes.set(left, r.nodes.get(right));
                                r.nodes.set(right, temp);
                                left++;
                                right--;
                            }
                        }
                    }
                }
                r.recalculateCost();
            }
        }
    }

    /**
     * Large Neighborhood Search (LNS) - Ruin & Recreate Operator.
     * Operatore distruttivo e costruttivo. A differenza delle piccole mutazioni (swap, relocate),
     * LNS estirpa catene contigue e le ricuce globalmente nel miglior veicolo disponibile.
     */
    private void largeNeighborhoodRuinRecreate(Antibody ab) {
        if (ab.routes.isEmpty()) return;
        
        // RUIN phase: randomly select a route and completely extract a sequence of N contiguous nodes
        Route ruinedRoute = ab.routes.get(random.nextInt(ab.routes.size()));
        if (ruinedRoute.nodes.size() < 3) return; // Route too short for meaningful LNS
        
        int ruinSize = 2 + random.nextInt(Math.min(4, ruinedRoute.nodes.size() - 1));
        int startIndex = random.nextInt(ruinedRoute.nodes.size() - ruinSize + 1);
        
        List<Node> removedNodes = new ArrayList<>();
        for (int i = 0; i < ruinSize; i++) {
            removedNodes.add(ruinedRoute.removeNodeAt(startIndex));
        }
        
        // RECREATE phase: sequentially reinsert removed nodes using greedy global insertion 
        // into any vehicle across the entire fleet prioritizing the minimum geometric delta
        for (Node n : removedNodes) {
            double bestIncrease = Double.MAX_VALUE;
            Route bestRoute = null;
            int bestIndex = -1;
            
            for (Route r : ab.routes) {
                if (r.canAdd(n)) {
                    for (int i = 0; i <= r.nodes.size(); i++) {
                        Node prev = (i == 0) ? instance.depot : r.nodes.get(i - 1);
                        Node next = (i == r.nodes.size()) ? instance.depot : r.nodes.get(i);
                        
                        double increase = prev.distanceTo(n) + n.distanceTo(next) - prev.distanceTo(next);
                        if (increase < bestIncrease) {
                            bestIncrease = increase;
                            bestRoute = r;
                            bestIndex = i;
                        }
                    }
                }
            }
            
            if (bestRoute != null) {
                bestRoute.addNodeAt(bestIndex, n);
            } else {
                // Failsafe: Create a brand new route if no existing vehicle has sufficient capacity
                Route newRoute = new Route(instance);
                newRoute.addNode(n);
                ab.routes.add(newRoute);
            }
        }
    }
}
