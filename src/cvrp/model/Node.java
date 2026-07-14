package cvrp.model;

public class Node {
    public final int id;
    public final double x;
    public final double y;
    public final int demand;

    public Node(int id, double x, double y, int demand) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.demand = demand;
    }

    public double distanceTo(Node other) {
        return Math.sqrt(Math.pow(this.x - other.x, 2) + Math.pow(this.y - other.y, 2));
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Node node = (Node) o;
        return id == node.id;
    }

    @Override
    public int hashCode() {
        return id;
    }

    @Override
    public String toString() {
        return "N" + id;
    }
}
