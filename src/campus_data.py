"""
Campus Data Module
==================
Contains all shared data structures for the Smart Campus AI system:
- Campus graph (13 nodes, 19 weighted edges)
- Node metadata (coordinates, categories)
- Room/lab definitions
- CSP constraint data
- Knowledge base facts and rules

This module is imported by all other modules that need campus information.
"""

# ─── CAMPUS GRAPH ──────────────────────────────────────────────────────
# Node coordinates and categories for the campus map.
# Categories: 'access' (gates, transport), 'academic' (blocks, labs), 'service' (admin, medical)

CAMPUS_NODES = {
    "Bus_Stop":         {"x": 0, "y": 1, "category": "access",   "description": "Bus Stop - Main Transport Hub"},
    "Main_Gate":        {"x": 0, "y": 4, "category": "access",   "description": "Main Gate - Campus Entrance"},
    "Medical_Center":   {"x": 1, "y": 1, "category": "service",  "description": "Medical Center - Health Services"},
    "Hostel":           {"x": 2, "y": 0, "category": "service",  "description": "Hostel - Student Residence"},
    "Parking":          {"x": 2, "y": 4, "category": "access",   "description": "Parking - Vehicle Area"},
    "Admin_Block":      {"x": 3, "y": 5, "category": "service",  "description": "Admin Block - Administrative Offices"},
    "Cafeteria":        {"x": 4, "y": 1, "category": "service",  "description": "Cafeteria - Dining Hall"},
    "Student_Services": {"x": 6, "y": 5, "category": "service",  "description": "Student Services - Support Center"},
    "Library":          {"x": 6, "y": 2, "category": "academic", "description": "Library - Learning Resource Center"},
    "Science_Block":    {"x": 7, "y": 1, "category": "academic", "description": "Science Block - Science & Computing Wing"},
    "Exam_Hall":        {"x": 8, "y": 5, "category": "academic", "description": "Exam Hall - Examination Center"},
    "AI_Lab":           {"x": 9, "y": 2, "category": "academic", "description": "AI Lab - Artificial Intelligence Laboratory"},
    "Seminar_Room":     {"x": 10, "y": 4, "category": "academic", "description": "Seminar Room - Presentation Hall"},
}

# Weighted undirected edges: (node_a, node_b, weight)
CAMPUS_EDGES = [
    ("Bus_Stop", "Main_Gate", 1),
    ("Bus_Stop", "Parking", 2),
    ("Bus_Stop", "Medical_Center", 2),
    ("Medical_Center", "Hostel", 3),
    ("Main_Gate", "Parking", 2),
    ("Main_Gate", "Hostel", 5),
    ("Main_Gate", "Admin_Block", 4),
    ("Hostel", "Cafeteria", 2),
    ("Cafeteria", "Library", 2),
    ("Cafeteria", "Science_Block", 3),
    ("Parking", "Science_Block", 3),
    ("Science_Block", "AI_Lab", 1),
    ("Science_Block", "Exam_Hall", 3),
    ("Science_Block", "Seminar_Room", 2),
    ("Library", "AI_Lab", 3),
    ("Library", "Student_Services", 2),
    ("Admin_Block", "Student_Services", 1),
    ("Admin_Block", "Exam_Hall", 2),
    ("Exam_Hall", "Seminar_Room", 1),
]


def build_adjacency_list():
    """
    Build and return an adjacency list from CAMPUS_EDGES.
    Returns a dict where each key is a node name and the value
    is a list of tuples (neighbor, weight).
    """
    adj = {node: [] for node in CAMPUS_NODES}
    for a, b, w in CAMPUS_EDGES:
        adj[a].append((b, w))
        adj[b].append((a, w))
    return adj


def get_node_names():
    """Return a sorted list of all campus node names."""
    return sorted(CAMPUS_NODES.keys())


# ─── ROOMS & LABS ──────────────────────────────────────────────────────

ROOMS = ["Lab 1", "Lab 2", "Lab 3"]

TIME_SLOTS = ["09:00", "10:00", "11:00", "12:00"]

# ─── CSP DATA ──────────────────────────────────────────────────────────
# Groups that need scheduling
GROUPS = ["G1", "G2", "G3", "G4", "G5", "G6"]

# Constraints: each constraint is a dict with type, involved groups, and description
CSP_CONSTRAINTS = [
    {"type": "room_clash",     "a": "G1", "b": "G2", "label": "G1≠G2", "description": "G1 and G2 cannot share the same room at the same time"},
    {"type": "room_clash",     "a": "G1", "b": "G4", "label": "G1≠G4", "description": "G1 and G4 cannot share the same room at the same time"},
    {"type": "room_clash",     "a": "G2", "b": "G4", "label": "G2≠G4", "description": "G2 and G4 cannot share the same room at the same time"},
    {"type": "room_clash",     "a": "G3", "b": "G5", "label": "G3≠G5", "description": "G3 and G5 cannot share the same room at the same time"},
    {"type": "room_clash",     "a": "G3", "b": "G6", "label": "G3≠G6", "description": "G3 and G6 cannot share the same room at the same time"},
    {"type": "room_clash",     "a": "G5", "b": "G6", "label": "G5≠G6", "description": "G5 and G6 cannot share the same room at the same time"},
    {"type": "examiner_clash", "a": "G1", "b": "G3", "label": "G1≠G3", "description": "G1 and G3 share an examiner and cannot overlap"},
    {"type": "supervisor_clash","a": "G2", "b": "G5", "label": "G2≠G5", "description": "G2 and G5 share a supervisor and cannot overlap"},
    {"type": "precedence",     "a": "G4", "b": "G3", "label": "G4<G3",  "description": "G4 must be scheduled before G3"},
]

# ─── ROUTING MATRIX ────────────────────────────────────────────────────
# Maps each canonical request type to the list of modules it activates.
# Ingestion, Router, and Final Response always run (not listed here).

ROUTING_MATRIX = {
    "Navigation_Only":         ["SEARCH"],
    "Eligibility_Check":       ["LOGIC"],
    "Booking_or_Scheduling":   ["LOGIC", "CSP"],
    "Urgent_Service_Request":  ["ANN", "LOGIC", "CSP"],
    "Full_Service_Request":    ["ANN", "LOGIC", "CSP", "SEARCH"],
}

VALID_REQUEST_TYPES = list(ROUTING_MATRIX.keys())

# ─── VALID ROLES ───────────────────────────────────────────────────────

VALID_ROLES = ["Student", "Instructor", "Staff"]


# ─── HELPER: PRINT GRAPH INFO ─────────────────────────────────────────

def print_campus_info():
    """Print campus graph information for debugging."""
    print(f"Campus Graph: {len(CAMPUS_NODES)} nodes, {len(CAMPUS_EDGES)} edges")
    print(f"\nNodes:")
    for name, data in CAMPUS_NODES.items():
        print(f"  {name:20s} ({data['x']},{data['y']}) [{data['category']}]")
    print(f"\nEdges:")
    for a, b, w in CAMPUS_EDGES:
        print(f"  {a:20s} <--{w}--> {b}")


if __name__ == "__main__":
    print_campus_info()
    adj = build_adjacency_list()
    print(f"\nAdjacency list built: {len(adj)} nodes")
    for node, neighbors in adj.items():
        neighbor_str = ", ".join(f"{n}({w})" for n, w in neighbors)
        print(f"  {node:20s} → {neighbor_str}")

