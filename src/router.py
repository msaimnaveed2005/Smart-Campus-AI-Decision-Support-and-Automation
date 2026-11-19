"""
Request Router Module
======================
The control-flow brain of the platform. It reads the request_type
and decides which modules should run and in what order.

The router does NOT solve the request itself. It directs the request
to the correct parts of the system. This is what makes the project
feel unified rather than a set of isolated algorithm demonstrations.

Owner: Yaeesh (Member 3)

Pipeline rules:
  Navigation_Only:         Search only
  Eligibility_Check:       Logic/KB only
  Booking_or_Scheduling:   Logic/KB → CSP
  Urgent_Service_Request:  ANN → Logic/KB → CSP
  Full_Service_Request:    ANN → Logic/KB → CSP → Search

Ingestion, Router, and Final Response always run.
If Logic/KB rejects, the pipeline HALTS — CSP and Search do not execute.
"""

import time
from campus_data import ROUTING_MATRIX, VALID_REQUEST_TYPES


class RouterResult:
    """
    Container for router decisions.
    Stores which modules to activate and the routing path.
    """

    def __init__(self, request_type, pipeline, exec_time=0):
        """Initialize RouterResult with request type, pipeline module list, and execution time."""
        self.request_type = request_type   # The canonical request type
        self.pipeline = pipeline           # List of module names to run
        self.exec_time = exec_time         # Execution time in ms

    def __str__(self):
        """Return a formatted string showing the routing decision: request type and pipeline path."""
        path = " → ".join(self.pipeline)
        return f"Router: {self.request_type} → {path}"

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "request_type": self.request_type,
            "pipeline": self.pipeline,
            "path": [self.request_type] + self.pipeline,
            "exec_time_ms": round(self.exec_time, 2),
        }

    def uses_module(self, module_name):
        """Check if a specific module is in the pipeline."""
        return module_name.upper() in [m.upper() for m in self.pipeline]


def route_request(request_type):
    """
    Determine the pipeline for a given request type.
    This is the main entry point for the Router module.

    Args:
        request_type: One of the 5 canonical request types

    Returns:
        RouterResult with the list of modules to activate

    Raises:
        ValueError: If request_type is not recognized
    """
    start = time.perf_counter()

    if request_type not in VALID_REQUEST_TYPES:
        raise ValueError(
            f"Unknown request type: '{request_type}'. "
            f"Valid types: {', '.join(VALID_REQUEST_TYPES)}"
        )

    pipeline = ROUTING_MATRIX[request_type]
    exec_time = (time.perf_counter() - start) * 1000

    return RouterResult(
        request_type=request_type,
        pipeline=list(pipeline),
        exec_time=exec_time,
    )


def get_routing_matrix():
    """
    Return the full routing matrix for display (e.g., in the UI popover).
    Returns a list of dicts with request type and which modules it uses.
    """
    matrix = []
    all_modules = ["ANN", "LOGIC", "CSP", "SEARCH"]

    for req_type in VALID_REQUEST_TYPES:
        modules = ROUTING_MATRIX[req_type]
        row = {
            "request_type": req_type,
            "modules": {m: (m in modules) for m in all_modules},
            "pipeline": modules,
        }
        matrix.append(row)

    return matrix


def get_full_pipeline_stages():
    """
    Return the 6 pipeline stages (including always-run stages).
    Used for the pipeline rail visualization.
    """
    return [
        {"num": "01", "name": "Ingestion", "always_runs": True},
        {"num": "02", "name": "Router", "always_runs": True},
        {"num": "03", "name": "ANN", "always_runs": False},
        {"num": "04", "name": "Logic/KB", "always_runs": False},
        {"num": "05", "name": "CSP", "always_runs": False},
        {"num": "06", "name": "Navigation", "always_runs": False},
    ]


# ─── TESTING ───────────────────────────────────────────────────────────

def test_router():
    """Test the router module with all request types."""
    print("=" * 60)
    print("REQUEST ROUTER MODULE — TEST SUITE")
    print("=" * 60)

    # Test all 5 request types
    for req_type in VALID_REQUEST_TYPES:
        result = route_request(req_type)
        print(f"\n  {result}")

    # Test routing matrix display
    print("\n--- Routing Matrix ---")
    matrix = get_routing_matrix()
    header = f"{'Request Type':<30} {'ANN':>5} {'LOGIC':>7} {'CSP':>5} {'SEARCH':>8}"
    print(header)
    print("-" * len(header))
    for row in matrix:
        modules = row["modules"]
        print(f"{row['request_type']:<30} "
              f"{'●' if modules['ANN'] else '–':>5} "
              f"{'●' if modules['LOGIC'] else '–':>7} "
              f"{'●' if modules['CSP'] else '–':>5} "
              f"{'●' if modules['SEARCH'] else '–':>8}")

    # Test invalid type
    print("\n--- Invalid request type ---")
    try:
        route_request("Invalid_Type")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  Correctly raised: {e}")

    print("\n" + "=" * 60)
    print("ALL ROUTER TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_router()

