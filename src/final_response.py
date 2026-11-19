"""
Final Response Layer
=====================
The output aggregation layer of the system. It:
- Collects results from all modules that ran
- Generates a coherent human-readable response
- Builds the complete audit trace (JSON)
- Produces the pipeline station statuses for the UI

This layer is what makes the platform understandable to the user.
It combines priority, eligibility, assignment, and route into one answer.

Owner: Yaeesh (Member 3)
"""

import time
import json
import hashlib


class FinalResponse:
    """
    Complete response combining all module outputs.
    This is what gets shown to the user and exported as the audit trace.
    """

    def __init__(self):
        self.request_id = None
        self.user = None
        self.request_type = None
        self.outcome = ""                 # One-sentence summary
        self.status = "PENDING"           # APPROVED, REJECTED, ERROR, COMPLETED
        self.pipeline_stages = []         # List of stage status dicts
        self.route_text = ""              # Pipeline route as text
        self.exec_log = []                # Execution log entries

        # Module results
        self.preprocessing_result = None
        self.router_result = None
        self.ann_result = None
        self.logic_result = None
        self.csp_result = None
        self.search_result = None

        # Timing
        self.total_exec_time = 0

    def __str__(self):
        return (f"Final Response [{self.status}]\n"
                f"  Request: {self.request_id}\n"
                f"  User: {self.user['name'] if self.user else 'Unknown'}\n"
                f"  Outcome: {self.outcome}")

    def generate_request_id(self):
        """Generate a deterministic request ID."""
        self.request_id = "SC-2026-000417"
        return self.request_id

    def build_outcome(self):
        """
        Build a one-sentence outcome summarizing all module results.
        This is the human-readable explanation shown to the user.
        """
        if self.preprocessing_result and not self.preprocessing_result.valid:
            self.status = "ERROR"
            errors = "; ".join(self.preprocessing_result.errors)
            self.outcome = f"Request could not be processed. {errors}"
            return

        user_name = self.user["name"] if self.user else "User"

        # Check Logic result
        if self.logic_result:
            if self.logic_result.verdict == "REJECTED":
                self.status = "REJECTED"
                self.outcome = (
                    f"Request halted at Logic / KB. {self.logic_result.reason} "
                    f"No slot was requested and no route was computed."
                )
                return

        # Build approval message
        parts = [f"{user_name} is authorized"]
        dest = self.preprocessing_result.request.get("destination", "") if self.preprocessing_result else ""

        if dest:
            parts.append(f"for {dest.replace('_', ' ')} access")

        if self.csp_result and self.csp_result.solved and self.csp_result.user_group:
            g = self.csp_result.assignment.get(self.csp_result.user_group, {})
            if g:
                parts.append(f"with {g['room']} at {g['slot']}")

        if self.search_result and self.search_result.path:
            route_names = [n.replace("_", " ") for n in self.search_result.path[1:-1]]
            if route_names:
                parts.append(f"Route via {' and '.join(route_names)}")

        self.status = "APPROVED"
        self.outcome = f"Request approved. {'. '.join(parts)}."

    def build_pipeline_stages(self, router_result):
        """
        Build the pipeline stage statuses based on which modules ran and their results.
        Each stage gets: done, skipped, blocked, or current status.
        """
        stages = []
        pipeline = router_result.pipeline if router_result else []

        # Stage 01: Ingestion
        if self.preprocessing_result and not self.preprocessing_result.valid:
            stages.append({"num": "01", "name": "Ingestion", "status": "blocked",
                          "result": "Validation failed"})
        else:
            stages.append({"num": "01", "name": "Ingestion", "status": "done",
                          "result": "Validated"})

        # Stage 02: Router
        if self.preprocessing_result and not self.preprocessing_result.valid:
            stages.append({"num": "02", "name": "Router", "status": "skipped",
                          "result": "Not executed"})
        else:
            req_label = self.request_type.replace("_Request", "").replace("_", " ") if self.request_type else "Unknown"
            stages.append({"num": "02", "name": "Router", "status": "done",
                          "result": req_label})

        # Stage 03: ANN
        if "ANN" in pipeline:
            if self.ann_result:
                stages.append({"num": "03", "name": "ANN", "status": "done",
                              "result": f"{self.ann_result.mlp_class} {list(self.ann_result.mlp_probs.values())[0]}%"})
            else:
                stages.append({"num": "03", "name": "ANN", "status": "skipped",
                              "result": "Not executed"})
        else:
            stages.append({"num": "03", "name": "ANN", "status": "skipped",
                          "result": "Not routed"})

        # Stage 04: Logic/KB
        if "LOGIC" in pipeline:
            if self.logic_result:
                if self.logic_result.verdict == "AUTHORIZED":
                    rules = ", ".join(self.logic_result.rules_fired)
                    stages.append({"num": "04", "name": "Logic/KB", "status": "done",
                                  "result": f"Authorized · {rules}"})
                else:
                    stages.append({"num": "04", "name": "Logic/KB", "status": "blocked",
                                  "result": "Rejected"})
            else:
                stages.append({"num": "04", "name": "Logic/KB", "status": "skipped",
                              "result": "Not executed"})
        else:
            stages.append({"num": "04", "name": "Logic/KB", "status": "skipped",
                          "result": "Not routed"})

        # Stage 05: CSP
        if "CSP" in pipeline:
            if self.logic_result and self.logic_result.verdict == "REJECTED":
                stages.append({"num": "05", "name": "CSP", "status": "skipped",
                              "result": "Not executed"})
            elif self.csp_result and self.csp_result.solved:
                g = self.csp_result.assignment.get(self.csp_result.user_group, {})
                stages.append({"num": "05", "name": "CSP", "status": "done",
                              "result": f"{g.get('room', '?')} · {g.get('slot', '?')}"})
            else:
                stages.append({"num": "05", "name": "CSP", "status": "skipped",
                              "result": "Not executed"})
        else:
            stages.append({"num": "05", "name": "CSP", "status": "skipped",
                          "result": "Not routed"})

        # Stage 06: Navigation
        if "SEARCH" in pipeline:
            if self.logic_result and self.logic_result.verdict == "REJECTED":
                stages.append({"num": "06", "name": "Navigation", "status": "skipped",
                              "result": "Not executed"})
            elif self.search_result and self.search_result.path:
                stages.append({"num": "06", "name": "Navigation", "status": "done",
                              "result": f"A* · cost {self.search_result.cost:.1f}"})
            else:
                stages.append({"num": "06", "name": "Navigation", "status": "skipped",
                              "result": "Not executed"})
        else:
            stages.append({"num": "06", "name": "Navigation", "status": "skipped",
                          "result": "Not routed"})

        self.pipeline_stages = stages

    def build_exec_log(self):
        """Build the execution log with timing for each stage."""
        log = []

        if self.preprocessing_result:
            detail = (f"{len(self.preprocessing_result.request or {})} fields validated"
                     if self.preprocessing_result.valid
                     else f"VALIDATION FAILED: {'; '.join(self.preprocessing_result.errors)}")
            log.append({
                "stage": "01 INGEST",
                "time": f"{self.preprocessing_result.exec_time:.2f} ms",
                "detail": detail,
            })

        if self.router_result:
            path = " → ".join([self.request_type] + self.router_result.pipeline)
            log.append({
                "stage": "02 ROUTER",
                "time": f"{self.router_result.exec_time:.2f} ms",
                "detail": path,
            })

        if self.ann_result:
            top_prob = list(self.ann_result.mlp_probs.values())[0] / 100
            log.append({
                "stage": "03 ANN",
                "time": f"{self.ann_result.exec_time:.2f} ms",
                "detail": f"MLP 7-4-3-4 · {self.ann_result.mlp_class} {top_prob:.3f}",
            })

        if self.logic_result:
            if self.logic_result.verdict == "AUTHORIZED":
                rules = " · ".join(f"{r} ok" for r in self.logic_result.rules_fired)
                detail = f"{rules} · AUTHORIZED"
            else:
                detail = f"R1 FAILED · REJECTED · pipeline halted"
            log.append({
                "stage": "04 LOGIC",
                "time": f"{self.logic_result.exec_time:.2f} ms",
                "detail": detail,
            })

        if self.csp_result:
            satisfied = sum(1 for c in self.csp_result.constraint_results if c["satisfied"])
            total = len(self.csp_result.constraint_results)
            g = self.csp_result.assignment.get(self.csp_result.user_group, {})
            detail = (f"{satisfied}/{total} constraints satisfied · "
                     f"{self.csp_result.user_group} → {g.get('room', '?')} @ {g.get('slot', '?')}")
            log.append({
                "stage": "05 CSP",
                "time": f"{self.csp_result.exec_time:.2f} ms",
                "detail": detail,
            })

        if self.search_result:
            log.append({
                "stage": "06 SEARCH",
                "time": f"{self.search_result.exec_time:.2f} ms",
                "detail": f"A* · expanded {len(self.search_result.expanded)} · cost {self.search_result.cost:.1f}",
            })

        self.exec_log = log

    def build_audit_trace(self):
        """
        Build the complete JSON audit trace for export.
        Includes all module inputs and outputs for full auditability.
        """
        trace = {
            "request_id": self.request_id,
            "request": {
                "role": self.user["role"] if self.user else None,
                "type": self.request_type,
                "severity": self.preprocessing_result.request.get("severity") if self.preprocessing_result and self.preprocessing_result.valid else None,
                "destination": self.preprocessing_result.request.get("destination") if self.preprocessing_result and self.preprocessing_result.valid else None,
            },
            "router": self.router_result.to_dict() if self.router_result else None,
        }

        if self.ann_result:
            trace["ann"] = self.ann_result.to_dict()
        if self.logic_result:
            trace["logic"] = self.logic_result.to_dict()
        if self.csp_result:
            trace["csp"] = self.csp_result.to_dict()
        if self.search_result:
            trace["search"] = self.search_result.to_dict()

        return trace

    def get_trace_json(self, indent=2):
        """Return the audit trace as a formatted JSON string."""
        trace = self.build_audit_trace()
        return json.dumps(trace, indent=indent, default=str)

    def get_trace_hash(self):
        """Compute a SHA-256 hash of the audit trace for integrity verification."""
        trace_str = self.get_trace_json(indent=None)
        return hashlib.sha256(trace_str.encode()).hexdigest()[:8]

    def build_ledger(self):
        """
        Build the 5-cell ledger strip for the Decision Record.
        Maps: Priority→ANN, Permission→Logic, Allocation→CSP, Route→Search, Communication→Final
        """
        ledger = []

        # Priority (ANN)
        if self.ann_result:
            ledger.append({"topic": "Priority", "module": "ANN",
                          "value": self.ann_result.mlp_class.upper(),
                          "status": "warning" if self.ann_result.mlp_class == "Urgent" else "neutral"})
        else:
            ledger.append({"topic": "Priority", "module": "ANN",
                          "value": "Not routed", "status": "neutral"})

        # Permission (Logic/KB)
        if self.logic_result:
            ledger.append({"topic": "Permission", "module": "Logic/KB",
                          "value": self.logic_result.verdict,
                          "status": "success" if self.logic_result.verdict == "AUTHORIZED" else "danger"})
        else:
            ledger.append({"topic": "Permission", "module": "Logic/KB",
                          "value": "Not routed", "status": "neutral"})

        # Allocation (CSP)
        if self.csp_result and self.csp_result.solved:
            g = self.csp_result.assignment.get(self.csp_result.user_group, {})
            ledger.append({"topic": "Allocation", "module": "CSP",
                          "value": f"{g.get('room', '?')} · {g.get('slot', '?')}",
                          "status": "neutral"})
        else:
            val = "Not executed" if (self.logic_result and self.logic_result.verdict == "REJECTED") else "Not routed"
            ledger.append({"topic": "Allocation", "module": "CSP",
                          "value": val, "status": "neutral"})

        # Route (Search)
        if self.search_result and self.search_result.path:
            ledger.append({"topic": "Route", "module": "Search",
                          "value": f"{self.search_result.cost:.1f} units",
                          "status": "neutral"})
        else:
            val = "Not executed" if (self.logic_result and self.logic_result.verdict == "REJECTED") else "Not routed"
            ledger.append({"topic": "Route", "module": "Search",
                          "value": val, "status": "neutral"})

        # Communication (Final Response)
        if self.status == "APPROVED":
            ledger.append({"topic": "Communication", "module": "Final Response",
                          "value": "Ready", "status": "success"})
        elif self.status == "REJECTED":
            ledger.append({"topic": "Communication", "module": "Final Response",
                          "value": "Denied", "status": "danger"})
        else:
            ledger.append({"topic": "Communication", "module": "Final Response",
                          "value": self.status, "status": "neutral"})

        return ledger

    def print_summary(self):
        """Print a formatted summary of the complete response."""
        print("\n" + "=" * 70)
        print(f"  FINAL RESPONSE — {self.status}")
        print("=" * 70)
        print(f"  Request ID:  {self.request_id}")
        print(f"  User:        {self.user['name']} ({self.user['roll']}) · {self.user['role']}")
        print(f"  Type:        {self.request_type}")
        print(f"  Outcome:     {self.outcome}")

        # Ledger
        print("\n  ┌─────────────┬──────────────┬─────────────────────┐")
        print(f"  │ {'Topic':^11s} │ {'Module':^12s} │ {'Result':^19s} │")
        print("  ├─────────────┼──────────────┼─────────────────────┤")
        for cell in self.build_ledger():
            print(f"  │ {cell['topic']:^11s} │ {cell['module']:^12s} │ {cell['value']:^19s} │")
        print("  └─────────────┴──────────────┴─────────────────────┘")

        # Pipeline stages
        print("\n  Pipeline:")
        for stage in self.pipeline_stages:
            icon = {"done": "●", "skipped": "○", "blocked": "✗"}.get(stage["status"], "?")
            print(f"    {icon} {stage['num']} {stage['name']:<12s} {stage['result']}")

        # Exec log
        if self.exec_log:
            print("\n  Execution log:")
            for entry in self.exec_log:
                print(f"    {entry['stage']:<12s} {entry['time']:>8s}  {entry['detail']}")

        print("\n" + "=" * 70)

