package cvrp.model;

import java.util.ArrayList;
import java.util.List;

public class Route {
    public final List<Node> nodes; // exclude depot from start and end, just customers
    private int currentLoad;
    private double currentCost;
    private final Instance instance;

    public Route(Instance instance) {
        this.instance = instance;
        this.nodes = new ArrayList<>();
        this.currentLoad = 0;
        this.currentCost = 0.0;
    }

    public Route(Route other) {
        this.instance = other.instance;
        this.nodes = new ArrayList<>(other.nodes);
        this.currentLoad = other.currentLoad;
        this.currentCost = other.currentCost;
    }

    public boolean canAdd(Node n) {
        return currentLoad + n.demand <= instance.capacity;
    }

    public void addNode(Node n) {
        nodes.add(n);
        currentLoad += n.demand;
        recalculateCost();
    }
    
    public void addNodeAt(int index, Node n) {
        nodes.add(index, n);
        currentLoad += n.demand;
        recalculateCost();
    }

    public Node removeNodeAt(int index) {
        Node n = nodes.remove(index);
        currentLoad -= n.demand;
        recalculateCost();
        return n;
    }

    public void recalculateCost() {
        if (nodes.isEmpty()) {
            currentCost = 0.0;
            currentLoad = 0;
            return;
        }
        
        int load = 0;
        double cost = instance.getDistance(instance.depot, nodes.get(0));
        load += nodes.get(0).demand;
        
        for (int i = 0; i < nodes.size() - 1; i++) {
            cost += instance.getDistance(nodes.get(i), nodes.get(i + 1));
            load += nodes.get(i + 1).demand;
        }
        
        cost += instance.getDistance(nodes.get(nodes.size() - 1), instance.depot);
        this.currentCost = cost;
        this.currentLoad = load;
    }

    public double getCost() {
        return currentCost;
    }

    public int getLoad() {
        return currentLoad;
    }

    public boolean isEmpty() {
        return nodes.isEmpty();
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("Depot -> ");
        for (Node n : nodes) {
            sb.append(n.id).append(" -> ");
        }
        sb.append("Depot | Load: ").append(currentLoad).append("/").append(instance.capacity).append(" | Cost: ").append(String.format("%.2f", currentCost));
        return sb.toString();
    }
}
