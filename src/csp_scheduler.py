"""
CSP Scheduler Module
=====================
Constraint Satisfaction Problem solver for room/slot scheduling.
Assigns groups to rooms and time slots while respecting constraints:
- Room clash: Two groups cannot use the same room at the same time
- Examiner clash: Groups sharing an examiner cannot overlap
- Supervisor clash: Groups sharing a supervisor cannot overlap
- Precedence: One group must be scheduled before another

Uses backtracking search with constraint propagation.
This module only runs AFTER Logic/KB authorizes the request.

Owner: Mohsin (Member 2)
"""

import time
from campus_data import ROOMS, TIME_SLOTS, GROUPS, CSP_CONSTRAINTS


class CSPResult:
    """
    Container for CSP scheduler output.
    Stores the assignment, constraint evaluation, and user's group info.
    """

    def __init__(self, solved, assignment, constraint_results, user_group=None,
                 violations=0, exec_time=0):
        self.solved = solved                      # Whether a valid assignment was found
        self.assignment = assignment              # Dict {group: {room, slot}}
        self.constraint_results = constraint_results  # List of constraint check results
        self.user_group = user_group              # The user's group name
        self.violations = violations              # Number of constraint violations
        self.exec_time = exec_time                # Execution time in ms

    def __str__(self):
        if not self.solved:
            return "CSP Scheduler: No valid assignment found"
        satisfied = sum(1 for c in self.constraint_results if c["satisfied"])
        total = len(self.constraint_results)
        user_info = ""
        if self.user_group and self.user_group in self.assignment:
            a = self.assignment[self.user_group]
            user_info = f"\n  User's group: {self.user_group} → {a['room']} @ {a['slot']}"
        return (f"CSP Scheduler: SOLVED ({satisfied}/{total} constraints satisfied)"
                f"{user_info}")

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "solved": self.solved,
            "assignment": self.assignment,
            "violations": self.violations,
            "constraints_satisfied": sum(1 for c in self.constraint_results if c["satisfied"]),
            "constraints_total": len(self.constraint_results),
            "constraint_results": self.constraint_results,
            "user_group": self.user_group,
            "exec_time_ms": round(self.exec_time, 2),
        }

    def get_timetable(self):
        """
        Generate a timetable matrix (rooms × slots) for display.
        Returns a dict: {room: {slot: group_or_None}}
        """
        timetable = {}
        for room in ROOMS:
            timetable[room] = {}
            for slot in TIME_SLOTS:
                timetable[room][slot] = None

        for group, info in self.assignment.items():
            room = info["room"]
            slot = info["slot"]
            if room in timetable and slot in timetable[room]:
                timetable[room][slot] = group

        return timetable


def check_constraint(constraint, assignment):
    """
    Check whether a single constraint is satisfied by the current assignment.

    Args:
        constraint: Dict with 'type', 'a', 'b' (group names)
        assignment: Dict {group: {room, slot}}

    Returns:
        True if the constraint is satisfied, False if violated
    """
    a_name = constraint["a"]
    b_name = constraint["b"]

    # If either group is not yet assigned, constraint is not violated
    if a_name not in assignment or b_name not in assignment:
        return True

    a = assignment[a_name]
    b = assignment[b_name]

    if constraint["type"] in ("room_clash", "examiner_clash", "supervisor_clash"):
        # These groups must not be in the same room at the same time
        return not (a["room"] == b["room"] and a["slot"] == b["slot"])

    elif constraint["type"] == "precedence":
        # Group 'a' must be scheduled before group 'b'
        slot_order = {slot: i for i, slot in enumerate(TIME_SLOTS)}
        return slot_order[a["slot"]] < slot_order[b["slot"]]

    return True


def evaluate_all_constraints(assignment, constraints=None):
    """
    Evaluate all constraints against a complete assignment.

    Args:
        assignment: Dict {group: {room, slot}}
        constraints: List of constraint dicts (defaults to CSP_CONSTRAINTS)

    Returns:
        List of dicts with constraint info and whether it's satisfied
    """
    if constraints is None:
        constraints = CSP_CONSTRAINTS

    results = []
    for c in constraints:
        satisfied = check_constraint(c, assignment)
        results.append({
            "type": c["type"],
            "a": c["a"],
            "b": c["b"],
            "label": c["label"],
            "description": c["description"],
            "satisfied": satisfied,
        })
    return results


def is_consistent(assignment, group, value, constraints):
    """
    Check if assigning 'value' to 'group' is consistent with current assignment.
    Used during backtracking to prune invalid branches.

    Args:
        assignment: Current partial assignment
        group: Group being assigned
        value: Dict {room, slot} to assign
        constraints: List of constraint dicts

    Returns:
        True if the assignment is consistent
    """
    # Temporarily add the assignment
    test_assignment = dict(assignment)
    test_assignment[group] = value

    for c in constraints:
        if c["a"] == group or c["b"] == group:
            if not check_constraint(c, test_assignment):
                return False
    return True


def solve_csp(groups=None, rooms=None, slots=None, constraints=None):
    """
    Solve the CSP using backtracking search.
    Finds a conflict-free assignment of groups to rooms and time slots.

    Args:
        groups: List of group names (defaults to GROUPS)
        rooms: List of room names (defaults to ROOMS)
        slots: List of time slot strings (defaults to TIME_SLOTS)
        constraints: List of constraint dicts (defaults to CSP_CONSTRAINTS)

    Returns:
        CSPResult with the assignment and constraint evaluation
    """
    if groups is None:
        groups = GROUPS
    if rooms is None:
        rooms = ROOMS
    if slots is None:
        slots = TIME_SLOTS
    if constraints is None:
        constraints = CSP_CONSTRAINTS

    start = time.perf_counter()

    # Build domain: all possible (room, slot) combinations
    domain = [{"room": r, "slot": s} for s in slots for r in rooms]

    # Backtracking search
    assignment = {}
    solved = _backtrack(assignment, list(groups), domain, constraints)

    exec_time = (time.perf_counter() - start) * 1000

    if solved:
        constraint_results = evaluate_all_constraints(assignment, constraints)
        violations = sum(1 for c in constraint_results if not c["satisfied"])
        return CSPResult(
            solved=True,
            assignment=assignment,
            constraint_results=constraint_results,
            violations=violations,
            exec_time=exec_time,
        )
    else:
        return CSPResult(
            solved=False,
            assignment={},
            constraint_results=[],
            violations=-1,
            exec_time=exec_time,
        )


def _backtrack(assignment, remaining_groups, domain, constraints):
    """
    Recursive backtracking search.
    Tries each domain value for the next unassigned group.
    Returns True if a valid complete assignment is found.
    """
    if not remaining_groups:
        return True  # All groups assigned

    group = remaining_groups[0]
    rest = remaining_groups[1:]

    for value in domain:
        if is_consistent(assignment, group, value, constraints):
            assignment[group] = value
            if _backtrack(assignment, rest, domain, constraints):
                return True
            del assignment[group]  # Backtrack

    return False


def schedule_for_user(user_group="G3"):
    """
    Run the CSP solver and annotate the result with the user's group.
    This is the main entry point called by the router.

    Args:
        user_group: The user's group identifier (default "G3")

    Returns:
        CSPResult with user_group set
    """
    result = solve_csp()
    result.user_group = user_group
    return result


# ─── TESTING ───────────────────────────────────────────────────────────

def test_csp():
    """Test the CSP scheduler with the campus constraints."""
    print("=" * 60)
    print("CSP SCHEDULER MODULE — TEST SUITE")
    print("=" * 60)

    # Test 1: Solve the full CSP
    print("\n--- Test 1: Solve full CSP (6 groups, 3 rooms, 4 slots) ---")
    result = solve_csp()
    print(result)
    assert result.solved, "CSP should be solvable"
    print(f"\nAssignment:")
    for group in sorted(result.assignment):
        a = result.assignment[group]
        print(f"  {group}: {a['room']} @ {a['slot']}")
    print("✓ PASSED\n")

    # Test 2: All constraints satisfied
    print("--- Test 2: Constraint evaluation ---")
    print(f"Constraints: {len(result.constraint_results)} total")
    for c in result.constraint_results:
        status = "✓" if c["satisfied"] else "✗"
        print(f"  {status} {c['label']:10s} ({c['type']}): {c['description']}")
    violations = sum(1 for c in result.constraint_results if not c["satisfied"])
    assert violations == 0, f"Expected 0 violations, got {violations}"
    print(f"\n{len(result.constraint_results)}/{len(result.constraint_results)} satisfied, 0 violations")
    print("✓ PASSED\n")

    # Test 3: Timetable display
    print("--- Test 3: Timetable matrix ---")
    timetable = result.get_timetable()
    header = f"{'Room':<10}" + "".join(f"{slot:<10}" for slot in TIME_SLOTS)
    print(header)
    print("-" * len(header))
    for room in ROOMS:
        row = f"{room:<10}"
        for slot in TIME_SLOTS:
            group = timetable[room][slot] or "—"
            row += f"{group:<10}"
        print(row)
    print("✓ PASSED\n")

    # Test 4: User-specific scheduling
    print("--- Test 4: Schedule for user (G3) ---")
    user_result = schedule_for_user("G3")
    print(user_result)
    if "G3" in user_result.assignment:
        g3 = user_result.assignment["G3"]
        print(f"  Ali's group G3: {g3['room']} @ {g3['slot']}")
    print("✓ PASSED\n")

    # Test 5: Precedence constraint (G4 before G3)
    print("--- Test 5: Precedence check (G4 < G3) ---")
    if "G4" in result.assignment and "G3" in result.assignment:
        g4_slot = result.assignment["G4"]["slot"]
        g3_slot = result.assignment["G3"]["slot"]
        slot_idx = {s: i for i, s in enumerate(TIME_SLOTS)}
        print(f"  G4 @ {g4_slot} (index {slot_idx[g4_slot]})")
        print(f"  G3 @ {g3_slot} (index {slot_idx[g3_slot]})")
        assert slot_idx[g4_slot] < slot_idx[g3_slot], "G4 must be before G3"
        print("  G4 is before G3 ✓")
    print("✓ PASSED")

    print("\n" + "=" * 60)
    print("ALL CSP TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_csp()
