"""
Search & Navigation Module
===========================
Implements three search algorithms for campus navigation:
- A* Search: For weighted graphs with an admissible heuristic (primary)
- BFS: For unweighted graph traversal
- UCS (Uniform Cost Search): Fallback for weighted graphs without a heuristic

Policy: A* is used for weighted graphs when a heuristic is available.
        BFS is used for unweighted route problems.
        UCS is used as a fallback for weighted problems without a suitable heuristic.

Each algorithm returns a SearchResult with the path, cost, expansion trace,
and frontier information for visualization and auditing.
"""

import math
import heapq
import time
from campus_data import CAMPUS_NODES, build_adjacency_list


class SearchResult:
    """
    Container for search algorithm results.
    Stores the path, total cost, expansion trace, frontier nodes,
    algorithm name, and execution time.
    """

    def __init__(self, algorithm, path, cost, trace, expanded, frontier, exec_time):
        """Initialize SearchResult with algorithm name, path, cost, expansion trace, frontier, and timing."""
        self.algorithm = algorithm        # Name of the algorithm used
        self.path = path                  # List of node names in order
        self.cost = cost                  # Total path cost
        self.trace = trace                # List of dicts: {node, g, h, f} in expansion order
        self.expanded = expanded          # Set of expanded node names
        self.frontier = frontier          # Nodes generated but never expanded
        self.edges = len(path) - 1 if path else 0  # Number of edges in path
        self.exec_time = exec_time        # Execution time in milliseconds

    def __str__(self):
        """Return a formatted string showing the algorithm, path, cost, expansion count, and execution time."""
        if not self.path:
            return f"{self.algorithm}: No path found"
        path_str = " → ".join(self.path)
        return (f"{self.algorithm}: {path_str}\n"
                f"  Cost: {self.cost:.1f} ({self.edges} edges)\n"
                f"  Expanded: {len(self.expanded)} nodes\n"
                f"  Time: {self.exec_time:.2f} ms")

    def to_dict(self):
        """Convert the search result to a dictionary for JSON serialization."""
        return {
            "algorithm": self.algorithm,
            "path": self.path,
            "cost": self.cost,
            "edges": self.edges,
            "expanded_count": len(self.expanded),
            "expanded_nodes": list(self.expanded),
            "frontier_nodes": list(self.frontier),
            "trace": self.trace,
            "exec_time_ms": round(self.exec_time, 2),
        }

    def get_directions(self):
        """
        Return step-by-step directions with cumulative cost.
        Returns a list of dicts: {from, to, edge_cost, cumulative_cost}
        """
        if not self.path or len(self.path) < 2:
            return []

        adj = build_adjacency_list()
        directions = []
        cumulative = 0

        for i in range(len(self.path) - 1):
            from_node = self.path[i]
            to_node = self.path[i + 1]
            # Find edge weight
            edge_cost = 0
            for neighbor, weight in adj[from_node]:
                if neighbor == to_node:
                    edge_cost = weight
                    break
            cumulative += edge_cost
            directions.append({
                "from": from_node,
                "to": to_node,
                "edge_cost": edge_cost,
                "cumulative_cost": cumulative,
            })

        return directions


def euclidean_heuristic(node_a, node_b, divisor=3):
    """
    Compute the Euclidean distance between two campus nodes divided by a divisor.
    This heuristic is admissible and consistent for A* search.

    Args:
        node_a: Name of the first node
        node_b: Name of the second node
        divisor: Division factor to ensure admissibility (default 3)

    Returns:
        Heuristic estimate of the cost from node_a to node_b
    """
    a = CAMPUS_NODES[node_a]
    b = CAMPUS_NODES[node_b]
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    return math.sqrt(dx * dx + dy * dy) / divisor


def astar(start, goal, heuristic_fn=None):
    """
    A* Search Algorithm for weighted graphs with a heuristic.
    Uses a priority queue ordered by f(n) = g(n) + h(n).

    Args:
        start: Starting node name
        goal: Goal node name
        heuristic_fn: Function(node, goal) -> float. Defaults to euclidean_heuristic.

    Returns:
        SearchResult object with path, cost, trace, and timing.
    """
    if heuristic_fn is None:
        heuristic_fn = lambda n, g: euclidean_heuristic(n, g)

    start_time = time.perf_counter()
    adj = build_adjacency_list()

    # Priority queue: (f_score, counter, node)
    # counter breaks ties deterministically
    counter = 0
    open_set = [(heuristic_fn(start, goal), counter, start)]
    counter += 1

    g_score = {start: 0}
    came_from = {}
    closed_set = set()
    generated = {start}
    trace = []

    while open_set:
        f, _, current = heapq.heappop(open_set)

        if current in closed_set:
            continue

        closed_set.add(current)
        g = g_score[current]
        h = heuristic_fn(current, goal)
        trace.append({
            "node": current,
            "g": round(g, 2),
            "h": round(h, 2),
            "f": round(g + h, 2),
        })

        # Goal reached
        if current == goal:
            break

        # Expand neighbors
        for neighbor, weight in adj[current]:
            if neighbor in closed_set:
                continue

            tentative_g = g + weight
            if tentative_g < g_score.get(neighbor, math.inf):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                h_neighbor = heuristic_fn(neighbor, goal)
                f_neighbor = tentative_g + h_neighbor
                heapq.heappush(open_set, (f_neighbor, counter, neighbor))
                counter += 1
                generated.add(neighbor)

    # Reconstruct path
    path = _reconstruct_path(came_from, start, goal)
    total_cost = g_score.get(goal, math.inf)
    frontier = generated - closed_set

    exec_time = (time.perf_counter() - start_time) * 1000

    return SearchResult(
        algorithm="A*",
        path=path,
        cost=total_cost if path else math.inf,
        trace=trace,
        expanded=closed_set,
        frontier=frontier,
        exec_time=exec_time,
    )


def bfs(start, goal):
    """
    Breadth-First Search for unweighted graphs.
    Finds the shortest path by number of edges (all edges have equal weight).

    Args:
        start: Starting node name
        goal: Goal node name

    Returns:
        SearchResult object with path (cost = number of edges), trace, and timing.
    """
    start_time = time.perf_counter()
    adj = build_adjacency_list()

    from collections import deque
    queue = deque([start])
    came_from = {start: None}
    expanded = set()
    trace = []

    while queue:
        current = queue.popleft()
        if current in expanded:
            continue

        expanded.add(current)
        depth = _path_length(came_from, start, current)
        trace.append({
            "node": current,
            "g": depth,
            "h": 0,
            "f": depth,
        })

        if current == goal:
            break

        for neighbor, _ in adj[current]:
            if neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)

    # Reconstruct path
    path = _reconstruct_path_bfs(came_from, start, goal)
    cost = len(path) - 1 if path else math.inf
    frontier = set(came_from.keys()) - expanded

    exec_time = (time.perf_counter() - start_time) * 1000

    return SearchResult(
        algorithm="BFS",
        path=path,
        cost=cost,
        trace=trace,
        expanded=expanded,
        frontier=frontier,
        exec_time=exec_time,
    )


def ucs(start, goal):
    """
    Uniform Cost Search for weighted graphs without a heuristic.
    This is equivalent to A* with h(n) = 0 for all nodes.
    Guarantees optimal path by expanding lowest-cost node first.

    Args:
        start: Starting node name
        goal: Goal node name

    Returns:
        SearchResult object with path, cost, trace, and timing.
    """
    # UCS is A* with zero heuristic
    result = astar(start, goal, heuristic_fn=lambda n, g: 0)
    result.algorithm = "UCS"
    return result


def select_algorithm(start, goal, weighted=True, heuristic_available=True):
    """
    Select the appropriate search algorithm based on graph properties.
    Policy (from project manual):
      - A* for weighted graphs with a heuristic
      - BFS for unweighted graphs
      - UCS for weighted graphs without a heuristic

    Args:
        start: Starting node name
        goal: Goal node name
        weighted: Whether the graph is weighted (default True)
        heuristic_available: Whether a heuristic is available (default True)

    Returns:
        SearchResult from the selected algorithm
    """
    try:
        if not weighted:
            return bfs(start, goal)
        elif heuristic_available:
            return astar(start, goal)
        else:
            return ucs(start, goal)
    except Exception as e:
        return SearchResult(
            algorithm="Error",
            path=[],
            cost=math.inf,
            trace=[],
            expanded=set(),
            frontier=set(),
            exec_time=0,
        )


def _reconstruct_path(came_from, start, goal):
    """
    Reconstruct the path from start to goal using the came_from dictionary.
    Returns an empty list if no path exists.
    """
    if goal not in came_from and goal != start:
        # Check if goal was reached (it's in came_from or is the start)
        # For A*/UCS, goal might not be in came_from if start == goal
        if start == goal:
            return [start]
        return []

    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    path.reverse()

    if path and path[0] == start:
        return path
    return []


def _reconstruct_path_bfs(came_from, start, goal):
    """Reconstruct path for BFS where came_from maps node -> parent."""
    if goal not in came_from:
        return []

    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def _path_length(came_from, start, node):
    """Count the number of edges from start to node using came_from."""
    length = 0
    current = node
    while current != start and current is not None:
        current = came_from.get(current)
        length += 1
    return length


# ─── TESTING ───────────────────────────────────────────────────────────

def test_search():
    """
    Run test cases for all search algorithms.
    Verifies correctness of routes and costs against known values.
    """
    print("=" * 60)
    print("SEARCH & NAVIGATION MODULE — TEST SUITE")
    print("=" * 60)

    # Test 1: A* — Main_Gate to AI_Lab (Scenario 1)
    print("\n--- Test 1: A* Main_Gate → AI_Lab ---")
    result = astar("Main_Gate", "AI_Lab")
    print(result)
    print(f"Path: {' → '.join(result.path)}")
    print(f"Expected cost: 6.0, Got: {result.cost}")
    assert result.cost == 6.0, f"Expected cost 6.0, got {result.cost}"
    assert result.path == ["Main_Gate", "Parking", "Science_Block", "AI_Lab"], \
        f"Unexpected path: {result.path}"
    print("✓ PASSED\n")

    # Test 2: A* — Main_Gate to Library (Scenario 4)
    print("--- Test 2: A* Main_Gate → Library ---")
    result2 = astar("Main_Gate", "Library")
    print(result2)
    print(f"Path: {' → '.join(result2.path)}")
    print(f"Expected cost: 7.0, Got: {result2.cost}")
    assert result2.cost == 7.0, f"Expected cost 7.0, got {result2.cost}"
    print("✓ PASSED\n")

    # Test 3: BFS — Main_Gate to AI_Lab
    print("--- Test 3: BFS Main_Gate → AI_Lab ---")
    result3 = bfs("Main_Gate", "AI_Lab")
    print(result3)
    print(f"Shortest by edges: {result3.cost} edges")
    print("✓ PASSED\n")

    # Test 4: UCS — Main_Gate to AI_Lab
    print("--- Test 4: UCS Main_Gate → AI_Lab ---")
    result4 = ucs("Main_Gate", "AI_Lab")
    print(result4)
    print(f"UCS cost: {result4.cost} (should match A*: {result.cost})")
    assert result4.cost == result.cost, "UCS and A* should find the same optimal cost"
    print("✓ PASSED\n")

    # Test 5: Policy selection
    print("--- Test 5: Algorithm selection policy ---")
    r_weighted_heuristic = select_algorithm("Main_Gate", "AI_Lab", weighted=True, heuristic_available=True)
    assert r_weighted_heuristic.algorithm == "A*", "Should select A*"
    print(f"Weighted + heuristic → {r_weighted_heuristic.algorithm} ✓")

    r_unweighted = select_algorithm("Main_Gate", "AI_Lab", weighted=False, heuristic_available=False)
    assert r_unweighted.algorithm == "BFS", "Should select BFS"
    print(f"Unweighted → {r_unweighted.algorithm} ✓")

    r_weighted_no_h = select_algorithm("Main_Gate", "AI_Lab", weighted=True, heuristic_available=False)
    assert r_weighted_no_h.algorithm == "UCS", "Should select UCS"
    print(f"Weighted, no heuristic → {r_weighted_no_h.algorithm} ✓")
    print("\n✓ ALL POLICY TESTS PASSED\n")

    # Test 6: Expansion trace for A*
    print("--- Test 6: A* Expansion Trace (Main_Gate → AI_Lab) ---")
    result_trace = astar("Main_Gate", "AI_Lab")
    print(f"{'#':<4} {'Node':<20} {'g':>6} {'h':>6} {'f':>6}")
    print("-" * 46)
    for i, t in enumerate(result_trace.trace):
        label = "goal" if t["node"] == "AI_Lab" else str(i + 1)
        print(f"{label:<4} {t['node']:<20} {t['g']:>6.2f} {t['h']:>6.2f} {t['f']:>6.2f}")
    print(f"\nFrontier (generated, never expanded): {sorted(result_trace.frontier)}")

    # Test 7: Directions
    print("\n--- Test 7: Step-by-step directions ---")
    directions = result_trace.get_directions()
    for d in directions:
        print(f"  {d['from']} → {d['to']} (cost {d['edge_cost']}) → cumulative {d['cumulative_cost']}")

    print("\n" + "=" * 60)
    print("ALL SEARCH TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_search()

