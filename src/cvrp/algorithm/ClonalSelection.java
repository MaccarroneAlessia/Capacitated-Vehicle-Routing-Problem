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
 * Ho implementato il motore di ottimizzazione principale, integrando la struttura
 * base dell'algoritmo immunologico con alcune personalizzazioni per migliorarne la convergenza:
 * 
 * 1. Smart Initialization: Invece di partire da una popolazione totalmente casuale, ho scelto di 
 *    inizializzare il 20% degli "anticorpi" usando un'euristica costruttiva greedy (Nearest Neighbor).
 *    Questo accelera notevolmente il warm-up iniziale.
 * 
 * 2. Large Neighborhood Search (LNS): Per l'operatore di iper-mutazione, ho sviluppato una logica 
 *    di Ruin & Recreate. Piuttosto che fare un semplice swap, distruggo blocchi di nodi sub-ottimi 
 *    e li reinserisco nella posizione globalmente più economica, compiendo salti più ampi nello 
 *    spazio di ricerca.
 * 
 * 3. Simulated Annealing (SA) in Local Search: Ho sostituito l'accettazione 
 *    deterministica della 2-Opt (Hill Climbing) con un criterio stocastico basato sulla Temperatura. 
 *    Accettando mosse peggiorative con una certa probabilità, l'algoritmo riesce a fuggire efficacemente
 *    dai minimi locali, garantendo rotte pulite e prive di incroci.
 * 
 * L'algoritmo termina al raggiungimento del limite massimo di Fitness Evaluations (FE).
 */

public class ClonalSelection {
    private final Instance instance;
    private final int popSize;
    private final int selectionSize;
    private final double cloneFactor;
    private final Random random;
    private final int maxEvaluations;

    private int currentEvaluations;
    private Antibody bestAntibody;
    private int bestEvaluations;

    public int getBestEvaluations() {
        return bestEvaluations;
    }

    // Callbacks for tracking
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

    public Antibody run() {
        currentEvaluations = 0;
        List<Antibody> population = initializePopulation();
        
        if (tracker != null && !population.isEmpty()) {
            // Expose the unoptimized random solution (end of population before sort)
            // to the tracker as the initial baseline frame.
            Antibody messyStart = population.get(population.size() - 1);
            tracker.onNewBest(0, messyStart.getFitness(), messyStart);
        }
        
        while (currentEvaluations < maxEvaluations) {
            // Sort population by fitness
            Collections.sort(population);

            if (bestAntibody == null || population.get(0).getFitness() < bestAntibody.getFitness()) {
                bestAntibody = new Antibody(population.get(0));
                bestEvaluations = currentEvaluations;
                if (tracker != null) {
                    tracker.onNewBest(currentEvaluations, bestAntibody.getFitness(), bestAntibody);
                }
            }

            // Select best 'selectionSize' antibodies
            List<Antibody> selected = new ArrayList<>(population.subList(0, selectionSize));

            // Clone and mutate
            List<Antibody> clones = new ArrayList<>();
            for (int i = 0; i < selected.size(); i++) {
                Antibody parent = selected.get(i);
                int numClones = (int) Math.round(cloneFactor * popSize / (i + 1.0)); // Better ones get more clones
                if (numClones < 1) numClones = 1;

                for (int c = 0; c < numClones; c++) {
                    if (currentEvaluations >= maxEvaluations) break;
                    Antibody clone = new Antibody(parent);
                    
                    // Mutation rate inversely proportional to rank
                    int numMutations = 1 + i; 
                    hyperMutate(clone, numMutations);
                    
                    // MEMETIC STEP: Apply SA Local Search only to elite clones (i=0) for intensification
                    if (i == 0 && random.nextDouble() < 0.2) {
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

            // Receptor Editing (replace worst 10% with random new solutions)
            int replaceCount = (int) (0.1 * popSize);
            for (int i = 0; i < replaceCount; i++) {
                if (currentEvaluations >= maxEvaluations) break;
                Antibody fresh = generateRandomSolution();
                fresh.recalculateFitness();
                currentEvaluations++;
                population.set(popSize - 1 - i, fresh);
            }
        }
        
        // Final check
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

    private List<Antibody> initializePopulation() {
        List<Antibody> pop = new ArrayList<>();
        int smartCount = (int) (popSize * 0.20); // 20% greedy initialization
        
        for (int i = 0; i < popSize; i++) {
            Antibody sol;
            if (i < smartCount) {
                sol = generateSmartSolution(); // Nearest-Neighbor (Greedy)
            } else {
                sol = generateRandomSolution(); // Random
            }
            sol.recalculateFitness();
            currentEvaluations++;
            pop.add(sol);
        }
        return pop;
    }

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
            
            // Introduce a small randomness factor (e.g. 10% chance to pick random feasible)
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

    private void hyperMutate(Antibody ab, int numMutations) {
        for (int m = 0; m < numMutations; m++) {
            int op = random.nextInt(5);
            switch (op) {
                case 0: intraRouteSwap(ab); break;
                case 1: intraRoute2Opt(ab); break;
                case 2: interRouteRelocate(ab); break;
                case 3: interRouteSwapNodes(ab); break;
                case 4: largeNeighborhoodRuinRecreate(ab); break;
            }
        }
        // Cleanup empty routes
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
        
        // Reverse sublist from i to j
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

    // Memetic Algorithm: 2-Opt Local Search with Simulated Annealing Acceptance
    private void saLocalSearch(Antibody ab, int currentEval, int maxEval) {
        // Linearly decrease temperature based on evaluation progress
        double initialTemp = 100.0;
        double currentTemp = initialTemp * (1.0 - ((double) currentEval / maxEval));
        if (currentTemp < 0.1) currentTemp = 0.1;

        boolean improvement = true;
        int maxIter = 50; // Iteration limit to prevent infinite loops
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
                        
                        double currentDist = a.distanceTo(b) + c.distanceTo(d);
                        double newDist = a.distanceTo(c) + b.distanceTo(d);
                        double delta = newDist - currentDist;
                        
                        boolean accept = false;
                        if (delta < -1e-4) {
                            accept = true; // Strict improvement
                            improvement = true;
                        } else {
                            // SA acceptance probability for worsening moves
                            double p = Math.exp(-delta / currentTemp);
                            if (random.nextDouble() < p) {
                                accept = true;
                            }
                        }
                        
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

    // Large Neighborhood Search (LNS) - Ruin & Recreate Mutation
    private void largeNeighborhoodRuinRecreate(Antibody ab) {
        if (ab.routes.isEmpty()) return;
        
        // RUIN phase: randomly select a route and remove a sequence of N nodes
        Route ruinedRoute = ab.routes.get(random.nextInt(ab.routes.size()));
        if (ruinedRoute.nodes.size() < 3) return; // Route too short for LNS
        
        int ruinSize = 2 + random.nextInt(Math.min(4, ruinedRoute.nodes.size() - 1));
        int startIndex = random.nextInt(ruinedRoute.nodes.size() - ruinSize + 1);
        
        List<Node> removedNodes = new ArrayList<>();
        for (int i = 0; i < ruinSize; i++) {
            removedNodes.add(ruinedRoute.removeNodeAt(startIndex));
        }
        
        // RECREATE phase: reinsert removed nodes using greedy global insertion
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
                // Create a new route if no existing vehicle has sufficient capacity
                Route newRoute = new Route(instance);
                newRoute.addNode(n);
                ab.routes.add(newRoute);
            }
        }
    }
}
