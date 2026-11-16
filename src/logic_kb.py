"""
Logic / Knowledge Base Module
==============================
The project's rule-based reasoning engine. This module:
- Checks whether a request is logically supported
- Verifies user eligibility and authorization
- Forward-chains rules over a knowledge base of facts
- Acts as a GATEKEEPER before CSP — if rejected, the pipeline halts

Owner: Mohsin (Member 2)

Key concepts:
- Ground facts: known truths (e.g., Student(Ali), Completed(Ali, PF))
- Rules: IF premise THEN conclusion, with variable substitution
- Forward chaining: iteratively derive new facts until no more rules fire
- Unification: matching variables to constants (e.g., {x → Ali})
"""

import time
import re


class LogicResult:
    """
    Container for Logic/KB module output.
    Stores verdict, fired rules, derivation trace, and reason for rejection.
    """

    def __init__(self, verdict, facts, rules_fired, derivation, reason=None, exec_time=0):
        self.verdict = verdict           # "AUTHORIZED" or "REJECTED"
        self.facts = facts               # Ground facts used
        self.rules_fired = rules_fired   # List of rule IDs that fired
        self.derivation = derivation     # Step-by-step derivation trace
        self.reason = reason             # Rejection reason (if rejected)
        self.exec_time = exec_time       # Execution time in ms
        self.derived_facts = []          # New facts derived by forward chaining

    def __str__(self):
        status = f"Logic/KB: {self.verdict}"
        if self.rules_fired:
            status += f" (rules: {', '.join(self.rules_fired)})"
        if self.reason:
            status += f"\n  Reason: {self.reason}"
        return status

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = {
            "verdict": self.verdict,
            "facts": self.facts,
            "rules_fired": self.rules_fired,
            "derivation": self.derivation,
            "derived_facts": self.derived_facts,
            "exec_time_ms": round(self.exec_time, 2),
        }
        if self.reason:
            result["reason"] = self.reason
        return result


# ─── KNOWLEDGE BASE ───────────────────────────────────────────────────
# Facts and rules for the campus system.
# In production, these would be loaded from a JSON file.

# Known facts about users and the campus
KNOWLEDGE_BASE = {
    # Student facts
    "Ali": [
        "Student(Ali)",
        "Completed(Ali, ProgrammingFundamentals)",
        "Enrolled(Ali, AI)",
    ],
    "Sara": [
        "Student(Sara)",
        # NOTE: Sara has NOT completed ProgrammingFundamentals
        # This is intentional — demonstrates the gatekeeper halting the pipeline
    ],
    "DrKhan": [
        "Instructor(DrKhan)",
        "Teaches(DrKhan, AI)",
        "HasPhD(DrKhan)",
    ],
}

# Inference rules with variable substitution
# Each rule: if all premises match known facts, derive the conclusion
RULES = [
    {
        "id": "R1",
        "description": "Students who completed ProgrammingFundamentals are eligible for AI",
        "premises": ["Student(x)", "Completed(x, ProgrammingFundamentals)"],
        "conclusion": "Eligible(x, AI)",
    },
    {
        "id": "R2",
        "description": "Anyone who teaches AI is an instructor for AI",
        "premises": ["Teaches(x, AI)"],
        "conclusion": "Instructor(x, AI)",
    },
    {
        "id": "R3",
        "description": "Students enrolled in AI use Lab1",
        "premises": ["Enrolled(x, AI)"],
        "conclusion": "UsesLab(x, Lab1)",
    },
    {
        "id": "R4",
        "description": "Instructors for AI use Lab1",
        "premises": ["Instructor(x, AI)"],
        "conclusion": "UsesLab(x, Lab1)",
    },
]


def parse_predicate(pred_str):
    """
    Parse a predicate string into (name, args) tuple.
    Example: "Student(Ali)" → ("Student", ["Ali"])
             "Completed(x, PF)" → ("Completed", ["x", "PF"])

    Args:
        pred_str: Predicate string in FOL-like notation

    Returns:
        Tuple of (predicate_name, list_of_arguments)
    """
    match = re.match(r'(\w+)\(([^)]+)\)', pred_str.strip())
    if not match:
        return pred_str, []
    name = match.group(1)
    args = [a.strip() for a in match.group(2).split(',')]
    return name, args


def unify(pattern, fact, variable='x'):
    """
    Attempt to unify a pattern with a fact by substituting the variable.
    Returns the substitution dict if successful, None if not.

    Args:
        pattern: Pattern predicate string (may contain variable 'x')
        fact: Ground fact predicate string (no variables)
        variable: The variable name to substitute (default 'x')

    Returns:
        Dict {variable: value} if unification succeeds, None otherwise
    """
    p_name, p_args = parse_predicate(pattern)
    f_name, f_args = parse_predicate(fact)

    if p_name != f_name or len(p_args) != len(f_args):
        return None

    substitution = {}
    for p_arg, f_arg in zip(p_args, f_args):
        if p_arg == variable:
            if variable in substitution:
                if substitution[variable] != f_arg:
                    return None  # Inconsistent binding
            substitution[variable] = f_arg
        elif p_arg != f_arg:
            return None  # Constant mismatch

    return substitution


def apply_substitution(pred_str, substitution, variable='x'):
    """
    Apply a variable substitution to a predicate string.
    Example: apply_substitution("Eligible(x, AI)", {"x": "Ali"}) → "Eligible(Ali, AI)"

    Args:
        pred_str: Predicate string with variables
        substitution: Dict mapping variable names to values
        variable: The variable name (default 'x')

    Returns:
        New predicate string with variables replaced
    """
    name, args = parse_predicate(pred_str)
    new_args = []
    for arg in args:
        if arg == variable and variable in substitution:
            new_args.append(substitution[variable])
        else:
            new_args.append(arg)
    return f"{name}({', '.join(new_args)})"


def forward_chain(facts, rules, max_iterations=10):
    """
    Forward chaining inference engine.
    Iteratively applies rules to derive new facts until no more rules can fire.

    Args:
        facts: List of ground fact strings
        rules: List of rule dicts with 'id', 'premises', 'conclusion'
        max_iterations: Safety limit to prevent infinite loops

    Returns:
        Tuple of (all_facts, fired_rules, derivation_steps)
        - all_facts: Set of all known facts (original + derived)
        - fired_rules: List of rule IDs that fired
        - derivation_steps: List of dicts describing each derivation step
    """
    known_facts = set(facts)
    fired_rules = []
    derivation = []

    # Add initial facts to derivation
    for i, fact in enumerate(facts):
        derivation.append({
            "step": i + 1,
            "formula": fact,
            "justification": "Fact",
        })

    step_counter = len(facts)

    for iteration in range(max_iterations):
        new_fact_added = False

        for rule in rules:
            # Try to find a consistent substitution that satisfies all premises
            possible_subs = _find_substitutions(rule["premises"], known_facts)

            for sub in possible_subs:
                # Apply substitution to the conclusion
                new_fact = apply_substitution(rule["conclusion"], sub)

                if new_fact not in known_facts:
                    known_facts.add(new_fact)
                    new_fact_added = True

                    if rule["id"] not in fired_rules:
                        fired_rules.append(rule["id"])

                    step_counter += 1
                    sub_str = ", ".join(f"{k}/{v}" for k, v in sub.items())
                    derivation.append({
                        "step": step_counter,
                        "formula": new_fact,
                        "justification": f"{rule['id']}, modus ponens, {{{sub_str}}}",
                    })

        if not new_fact_added:
            break  # Fixed point reached

    return known_facts, fired_rules, derivation


def _find_substitutions(premises, known_facts, variable='x'):
    """
    Find all consistent variable substitutions that satisfy all premises
    against the set of known facts.

    Args:
        premises: List of premise predicate strings
        known_facts: Set of known fact strings
        variable: Variable name to bind

    Returns:
        List of substitution dicts that satisfy all premises
    """
    if not premises:
        return [{}]

    # Get all possible substitutions from the first premise
    first_premise = premises[0]
    candidates = []

    for fact in known_facts:
        sub = unify(first_premise, fact, variable)
        if sub is not None:
            candidates.append(sub)

    if not candidates:
        return []

    # If only one premise, return the candidates
    if len(premises) == 1:
        return candidates

    # For multiple premises, check consistency
    valid_subs = []
    for sub in candidates:
        # Apply this substitution to remaining premises and check
        all_satisfied = True
        for premise in premises[1:]:
            ground_premise = apply_substitution(premise, sub, variable)
            if ground_premise not in known_facts:
                all_satisfied = False
                break
        if all_satisfied:
            valid_subs.append(sub)

    return valid_subs


def check_authorization(user_name, destination, request_type):
    """
    Main entry point for the Logic/KB module.
    Checks whether a user is authorized for a given request.

    This function:
    1. Looks up the user's facts in the knowledge base
    2. Forward-chains the rules to derive new facts
    3. Checks for eligibility and authorization
    4. Returns AUTHORIZED or REJECTED with full derivation trace

    Args:
        user_name: Name of the user (e.g., "Ali", "Sara", "DrKhan")
        destination: Destination node name
        request_type: Type of request being made

    Returns:
        LogicResult with verdict, derivation, and timing
    """
    start = time.perf_counter()

    # Get user's facts from KB
    user_facts = KNOWLEDGE_BASE.get(user_name, [])
    if not user_facts:
        exec_time = (time.perf_counter() - start) * 1000
        return LogicResult(
            verdict="REJECTED",
            facts=[],
            rules_fired=[],
            derivation=[],
            reason=f"User '{user_name}' not found in the knowledge base.",
            exec_time=exec_time,
        )

    # Forward chain to derive new facts
    all_facts, fired_rules, derivation = forward_chain(user_facts, RULES)

    # Check authorization based on derived facts
    verdict = "REJECTED"
    reason = None
    derived_facts = all_facts - set(user_facts)

    # Determine what to check based on user role
    is_student = f"Student({user_name})" in all_facts
    is_instructor = f"Instructor({user_name})" in all_facts or f"Instructor({user_name}, AI)" in all_facts

    if is_student:
        # Students need Eligible(user, AI) to be derived
        eligible_fact = f"Eligible({user_name}, AI)"
        if eligible_fact in all_facts:
            verdict = "AUTHORIZED"
        else:
            # Find which rule failed and why
            reason = _find_rejection_reason(user_name, user_facts, RULES)
    elif is_instructor:
        # Instructors are authorized if they teach the relevant course
        if f"Teaches({user_name}, AI)" in all_facts or f"Instructor({user_name}, AI)" in all_facts:
            verdict = "AUTHORIZED"
        else:
            reason = f"Instructor {user_name} is not associated with the requested course."
    else:
        # Staff or unknown role
        verdict = "AUTHORIZED"  # Staff have general access

    exec_time = (time.perf_counter() - start) * 1000

    result = LogicResult(
        verdict=verdict,
        facts=user_facts,
        rules_fired=fired_rules,
        derivation=derivation,
        reason=reason,
        exec_time=exec_time,
    )
    result.derived_facts = list(derived_facts)

    return result


def _find_rejection_reason(user_name, user_facts, rules):
    """
    Analyze why authorization failed by checking which rule premises are unmet.
    Returns a human-readable rejection reason.
    """
    for rule in rules:
        if rule["id"] == "R1":  # Eligibility rule for students
            # Check each premise
            for premise in rule["premises"]:
                ground = apply_substitution(premise, {"x": user_name})
                if ground not in user_facts:
                    # Convert shorthand back to full name
                    display = ground.replace("ProgrammingFundamentals", "ProgrammingFundamentals")
                    return (f"Rule {rule['id']} could not be satisfied: "
                            f"{display} is not in the knowledge base.")
    return "Authorization could not be established from the available facts."


# ─── TESTING ───────────────────────────────────────────────────────────

def test_logic_kb():
    """Test the Logic/KB module with all three user scenarios."""
    print("=" * 60)
    print("LOGIC / KNOWLEDGE BASE MODULE — TEST SUITE")
    print("=" * 60)

    # Test 1: Ali — should be AUTHORIZED (R1, R3 fire)
    print("\n--- Test 1: Ali — Full Service Request ---")
    result = check_authorization("Ali", "AI_Lab", "Full_Service_Request")
    print(result)
    print(f"Derivation:")
    for step in result.derivation:
        marker = "  ✓" if "Fact" in step["justification"] else "  →"
        print(f"  {step['step']}. {step['formula']:40s} [{step['justification']}]")
    print(f"Derived: {result.derived_facts}")
    assert result.verdict == "AUTHORIZED", f"Ali should be AUTHORIZED, got {result.verdict}"
    assert "R1" in result.rules_fired, "R1 should fire for Ali"
    assert "R3" in result.rules_fired, "R3 should fire for Ali"
    print("✓ PASSED\n")

    # Test 2: Sara — should be REJECTED (R1 cannot fire)
    print("--- Test 2: Sara — Full Service Request (should REJECT) ---")
    result2 = check_authorization("Sara", "AI_Lab", "Full_Service_Request")
    print(result2)
    print(f"Derivation:")
    for step in result2.derivation:
        print(f"  {step['step']}. {step['formula']:40s} [{step['justification']}]")
    assert result2.verdict == "REJECTED", f"Sara should be REJECTED, got {result2.verdict}"
    assert "ProgrammingFundamentals" in result2.reason, "Reason should mention missing prerequisite"
    print("✓ PASSED\n")

    # Test 3: Dr. Khan — should be AUTHORIZED (R2, R4 fire)
    print("--- Test 3: Dr. Khan — Eligibility Check ---")
    result3 = check_authorization("DrKhan", "AI_Lab", "Eligibility_Check")
    print(result3)
    print(f"Derivation:")
    for step in result3.derivation:
        print(f"  {step['step']}. {step['formula']:40s} [{step['justification']}]")
    print(f"Derived: {result3.derived_facts}")
    assert result3.verdict == "AUTHORIZED", f"DrKhan should be AUTHORIZED, got {result3.verdict}"
    assert "R2" in result3.rules_fired, "R2 should fire for DrKhan"
    print("✓ PASSED\n")

    # Test 4: Unknown user
    print("--- Test 4: Unknown user ---")
    result4 = check_authorization("UnknownUser", "AI_Lab", "Full_Service_Request")
    print(result4)
    assert result4.verdict == "REJECTED"
    print("✓ PASSED\n")

    # Test 5: Unification
    print("--- Test 5: Unification tests ---")
    sub = unify("Student(x)", "Student(Ali)")
    assert sub == {"x": "Ali"}, f"Expected {{x: Ali}}, got {sub}"
    print(f"  unify('Student(x)', 'Student(Ali)') = {sub} ✓")

    sub2 = unify("Completed(x, ProgrammingFundamentals)", "Completed(Ali, ProgrammingFundamentals)")
    assert sub2 == {"x": "Ali"}, f"Expected {{x: Ali}}, got {sub2}"
    print(f"  unify with 2 args = {sub2} ✓")

    sub3 = unify("Student(x)", "Instructor(Ali)")
    assert sub3 is None, "Different predicates should not unify"
    print(f"  unify('Student(x)', 'Instructor(Ali)') = {sub3} ✓")
    print("✓ ALL UNIFICATION TESTS PASSED")

    print("\n" + "=" * 60)
    print("ALL LOGIC/KB TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    test_logic_kb()
