"""
Smart Campus AI — Decision Support & Automation System
=======================================================
Main entry point for the project.

This file orchestrates the full pipeline:
  1. Input & Preprocessing → validate and normalize the request
  2. Request Router → select the module pipeline
  3. ANN Priority → predict urgency (if routed)
  4. Logic / KB → check eligibility and authorization (if routed)
  5. CSP Scheduler → assign slot and room (if routed, and Logic approved)
  6. Search Navigation → compute optimal route (if routed, and Logic approved)
  7. Final Response → combine all outputs into one coherent answer

Course: AL2002 – Artificial Intelligence Lab, Fall 2026
Institution: FAST-NUCES

Team:
  Member 1 (Leader): Saim     — ANN Priority, Input & Preprocessing
  Member 2:          Mohsin   — Logic/KB, CSP Scheduler
  Member 3:          Yaeesh   — Search Navigation, Router, Final Response, UI
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from campus_data import VALID_REQUEST_TYPES, VALID_ROLES, get_node_names
from preprocessing import preprocess_request
from router import route_request, get_routing_matrix
from ann_module import predict_priority
from logic_kb import check_authorization
from csp_scheduler import schedule_for_user
from search_navigation import astar, select_algorithm
from final_response import FinalResponse


def run_pipeline(request):
    """
    Execute the complete Smart Campus AI pipeline for a given request.
    This is the core function that processes a request end-to-end.

    Args:
        request: Dict with user request data:
            {
                "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
                "request_type": "Full_Service_Request",
                "severity": 8.5,
                "time_sensitivity": 0.92,
                "origin": "Main_Gate",
                "destination": "AI_Lab",
            }

    Returns:
        FinalResponse object with complete results from all modules
    """
    total_start = time.perf_counter()
    response = FinalResponse()
    response.user = request.get("user", {})
    response.request_type = request.get("request_type", "Unknown")
    response.generate_request_id()

    try:
        # ── STAGE 1: INPUT & PREPROCESSING ──────────────────────────────────
        print("\n[01] Input & Preprocessing...")
        prep_result = preprocess_request(request)
        response.preprocessing_result = prep_result

        if not prep_result.valid:
            print(f"     ✗ Validation failed: {prep_result.errors}")
            response.router_result = None
            response.build_pipeline_stages(None)
            response.build_outcome()
            response.build_exec_log()
            response.total_exec_time = (time.perf_counter() - total_start) * 1000
            return response

        print(f"     ✓ Validated. Feature vector: {prep_result.feature_vector}")

        # ── STAGE 2: REQUEST ROUTER ─────────────────────────────────────────
        print("\n[02] Request Router...")
        router_result = route_request(request["request_type"])
        response.router_result = router_result
        print(f"     ✓ {router_result}")

        # ── STAGE 3: ANN PRIORITY (if routed) ───────────────────────────────
        if router_result.uses_module("ANN"):
            print("\n[03] ANN Priority Prediction...")
            ann_result = predict_priority(prep_result.feature_vector)
            response.ann_result = ann_result
            print(f"     ✓ {ann_result}")
        else:
            print("\n[03] ANN: Not routed for this request type")

        # ── STAGE 4: LOGIC / KB (if routed) ─────────────────────────────────
        if router_result.uses_module("LOGIC"):
            print("\n[04] Logic / Knowledge Base...")
            user_name = _extract_user_key(request["user"]["name"])
            logic_result = check_authorization(
                user_name,
                request["destination"],
                request["request_type"]
            )
            response.logic_result = logic_result
            print(f"     {'✓' if logic_result.verdict == 'AUTHORIZED' else '✗'} {logic_result}")

            # GATEKEEPER: If rejected, halt the pipeline
            if logic_result.verdict == "REJECTED":
                print(f"     ⚠ Pipeline HALTED at Logic/KB. CSP and Search will NOT execute.")
                response.build_pipeline_stages(router_result)
                response.build_outcome()
                response.build_exec_log()
                response.total_exec_time = (time.perf_counter() - total_start) * 1000
                return response
        else:
            print("\n[04] Logic/KB: Not routed for this request type")

        # ── STAGE 5: CSP SCHEDULER (if routed) ──────────────────────────────
        if router_result.uses_module("CSP"):
            print("\n[05] CSP Scheduler...")
            csp_result = schedule_for_user(user_group="G3")
            response.csp_result = csp_result
            print(f"     ✓ {csp_result}")
        else:
            print("\n[05] CSP: Not routed for this request type")

        # ── STAGE 6: SEARCH / NAVIGATION (if routed) ───────────────────────
        if router_result.uses_module("SEARCH"):
            origin = request.get("origin")
            destination = request.get("destination")
            if origin and destination:
                print(f"\n[06] Search Navigation ({origin} → {destination})...")
                search_result = select_algorithm(origin, destination,
                                                weighted=True, heuristic_available=True)
                response.search_result = search_result
                print(f"     ✓ {search_result}")
            else:
                print("\n[06] Search: Missing origin or destination")
        else:
            print("\n[06] Navigation: Not routed for this request type")

        # ── STAGE 7: FINAL RESPONSE ─────────────────────────────────────────
        print("\n[07] Building final response...")
        response.build_pipeline_stages(router_result)
        response.build_outcome()
        response.build_exec_log()
        response.total_exec_time = (time.perf_counter() - total_start) * 1000

        return response

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {str(e)}")
        response.status = "ERROR"
        response.outcome = f"Pipeline error: {str(e)}"
        response.total_exec_time = (time.perf_counter() - total_start) * 1000
        response.build_pipeline_stages(response.router_result)
        response.build_exec_log()
        return response


def _extract_user_key(full_name):
    """
    Extract the KB lookup key from a user's full name.
    Maps 'Ali Muhammad' → 'Ali', 'Sara Ahmed' → 'Sara', 'Dr. Khan' → 'DrKhan'
    """
    name_map = {
        "Ali Muhammad": "Ali",
        "Ali": "Ali",
        "Sara Ahmed": "Sara",
        "Sara": "Sara",
        "Dr. Khan": "DrKhan",
        "DrKhan": "DrKhan",
        "Dr Khan": "DrKhan",
    }
    return name_map.get(full_name, full_name.split()[0])


# ─── PREDEFINED SCENARIOS ─────────────────────────────────────────────

SCENARIOS = {
    1: {
        "name": "Ali · Full Service · Approved",
        "request": {
            "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
            "request_type": "Full_Service_Request",
            "severity": 8.5,
            "time_sensitivity": 0.92,
            "crowd_level": 0.40,
            "distance": 0.32,
            "eligibility_flag": 1.0,
            "origin": "Main_Gate",
            "destination": "AI_Lab",
        },
    },
    2: {
        "name": "Sara · Full Service · Rejected at Logic",
        "request": {
            "user": {"name": "Sara Ahmed", "roll": "24F-1301", "role": "Student"},
            "request_type": "Full_Service_Request",
            "severity": 8.0,
            "time_sensitivity": 0.88,
            "crowd_level": 0.45,
            "distance": 0.38,
            "eligibility_flag": 1.0,
            "origin": "Main_Gate",
            "destination": "AI_Lab",
        },
    },
    3: {
        "name": "Dr. Khan · Eligibility Check",
        "request": {
            "user": {"name": "Dr. Khan", "roll": "FAC-0042", "role": "Instructor"},
            "request_type": "Eligibility_Check",
            "severity": 3.0,
            "time_sensitivity": 0.30,
            "crowd_level": 0.20,
            "distance": 0.0,
            "origin": None,
            "destination": "AI_Lab",
        },
    },
    4: {
        "name": "Ali · Navigation Only",
        "request": {
            "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
            "request_type": "Navigation_Only",
            "severity": 2.0,
            "time_sensitivity": 0.10,
            "crowd_level": 0.30,
            "distance": 0.50,
            "origin": "Main_Gate",
            "destination": "Library",
        },
    },
    5: {
        "name": "Validation Error (invalid severity)",
        "request": {
            "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
            "request_type": "Full_Service_Request",
            "severity": -1,
            "time_sensitivity": 0.50,
            "origin": "Main_Gate",
            "destination": "AI_Lab",
        },
    },
    6: {
        "name": "Ali · Booking & Scheduling · Logic + CSP",
        "request": {
            "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
            "request_type": "Booking_or_Scheduling",
            "severity": 5.0,
            "time_sensitivity": 0.50,
            "crowd_level": 0.35,
            "distance": 0.20,
            "eligibility_flag": 1.0,
            "origin": "Main_Gate",
            "destination": "AI_Lab",
        },
    },
    7: {
        "name": "Ali · Urgent Service · ANN + Logic + CSP",
        "request": {
            "user": {"name": "Ali Muhammad", "roll": "24F-1234", "role": "Student"},
            "request_type": "Urgent_Service_Request",
            "severity": 9.5,
            "time_sensitivity": 0.98,
            "crowd_level": 0.60,
            "distance": 0.40,
            "eligibility_flag": 1.0,
            "origin": "Main_Gate",
            "destination": "AI_Lab",
        },
    },
}


def run_scenario(scenario_id):
    """Run a predefined scenario by ID."""
    if scenario_id not in SCENARIOS:
        print(f"Invalid scenario ID. Choose from: {list(SCENARIOS.keys())}")
        return None

    scenario = SCENARIOS[scenario_id]
    print(f"\n{'='*70}")
    print(f"  SCENARIO {scenario_id}: {scenario['name']}")
    print(f"{'='*70}")

    response = run_pipeline(scenario["request"])
    response.print_summary()

    return response


def interactive_menu():
    """
    Interactive command-line menu for the Smart Campus AI system.
    Allows running predefined scenarios or custom requests.
    """
    print("\n" + "="*70)
    print("  Smart Campus AI — Decision Support & Automation System")
    print("  AL2002 · Artificial Intelligence Lab · Fall 2026 · FAST-NUCES")
    print("="*70)
    print("\n  Team: Saim (Leader) · Mohsin · Yaeesh")
    print()

    while True:
        print("\n┌──────────────────────────────────────┐")
        print("│  Main Menu                           │")
        print("├──────────────────────────────────────┤")
        print("│  1. Scenario 1 (Full Service)        │")
        print("│  2. Scenario 2 (Sara Rejected)       │")
        print("│  3. Scenario 3 (Eligibility Check)   │")
        print("│  4. Scenario 4 (Navigation Only)     │")
        print("│  5. Scenario 5 (Validation Error)    │")
        print("│  6. Scenario 6 (Booking/Scheduling)  │")
        print("│  7. Scenario 7 (Urgent Service)      │")
        print("│  8. Custom Request                   │")
        print("│  9. Run All Scenarios                │")
        print("│  R. Show Routing Matrix              │")
        print("│  T. Run Module Tests                 │")
        print("│  0. Exit                             │")
        print("└──────────────────────────────────────┘")

        choice = input("\n  Enter choice: ").strip()

        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            response = run_scenario(int(choice))
            if response and input("\n  Export trace JSON? (y/n): ").strip().lower() == 'y':
                print(f"\n{response.get_trace_json()}")
                print(f"\nTrace hash: sha256 {response.get_trace_hash()}")

        elif choice == '8':
            response = custom_request_flow()
            if response:
                response.print_summary()

        elif choice == '9':
            for sid in [1, 2, 3, 4, 5, 6, 7]:
                run_scenario(sid)
                print()

        elif choice.upper() == 'R':
            print("\n  Routing Matrix:")
            matrix = get_routing_matrix()
            print(f"  {'Request Type':<30s} {'ANN':>5} {'LOGIC':>7} {'CSP':>5} {'SEARCH':>8}")
            print("  " + "-" * 55)
            for row in matrix:
                m = row["modules"]
                print(f"  {row['request_type']:<30s} "
                      f"{'●' if m['ANN'] else '–':>5} "
                      f"{'●' if m['LOGIC'] else '–':>7} "
                      f"{'●' if m['CSP'] else '–':>5} "
                      f"{'●' if m['SEARCH'] else '–':>8}")

        elif choice.upper() == 'T':
            run_all_tests()

        elif choice == '0':
            print("\n  Goodbye.\n")
            break

        else:
            print("  Invalid choice. Please try again.")


def custom_request_flow():
    """Guide the user through building a custom request interactively."""
    print("\n--- Custom Request ---")

    name = input("  Name: ").strip() or "Ali Muhammad"
    roll = input("  Roll number: ").strip() or "24F-1234"

    print(f"  Roles: {', '.join(VALID_ROLES)}")
    role = input("  Role: ").strip() or "Student"

    print(f"  Request types: {', '.join(VALID_REQUEST_TYPES)}")
    req_type = input("  Request type: ").strip() or "Full_Service_Request"

    severity = float(input("  Severity (0-10): ").strip() or "5.0")
    time_sens = float(input("  Time sensitivity (0-1): ").strip() or "0.5")

    nodes = get_node_names()
    print(f"  Nodes: {', '.join(nodes)}")
    origin = input("  Origin: ").strip() or "Main_Gate"
    destination = input("  Destination: ").strip() or "AI_Lab"

    request = {
        "user": {"name": name, "roll": roll, "role": role},
        "request_type": req_type,
        "severity": severity,
        "time_sensitivity": time_sens,
        "origin": origin if origin else None,
        "destination": destination,
    }

    return run_pipeline(request)


def run_all_tests():
    """Run all module test suites."""
    print("\n" + "="*70)
    print("  RUNNING ALL MODULE TESTS")
    print("="*70)

    from search_navigation import test_search
    from preprocessing import test_preprocessing
    from logic_kb import test_logic_kb
    from csp_scheduler import test_csp
    from ann_module import test_ann
    from router import test_router

    test_search()
    print()
    test_preprocessing()
    print()
    test_router()
    print()
    test_logic_kb()
    print()
    test_csp()
    print()
    test_ann()

    print("\n" + "="*70)
    print("  ALL MODULE TESTS COMPLETED")
    print("="*70)


# ─── ENTRY POINT ───────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command-line argument: run specific scenario
        arg = sys.argv[1]
        if arg == "test":
            run_all_tests()
        elif arg == "all":
            for sid in [1, 2, 3, 4, 5]:
                run_scenario(sid)
        elif arg.isdigit() and int(arg) in SCENARIOS:
            run_scenario(int(arg))
        else:
            print(f"Usage: python main.py [1-5|all|test]")
    else:
        interactive_menu()

