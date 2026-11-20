# Smart Campus AI — Decision Support & Automation System

**AL2002 — Artificial Intelligence Lab · Fall 2026**
**FAST-NUCES**

## Overview

A unified AI platform that receives structured campus requests, routes them through the correct AI pipeline, and produces one final response. The system demonstrates integration of classical AI (Search, Logic/KB, CSP) with modern AI (ANN) through structured request routing.

## Architecture

```
User Request → Input & Preprocessing → Request Router → [AI Modules] → Final Response
```

### Modules

| Module | Responsibility | Marks |
|---|---|:---:|
| Input & Preprocessing | Validate, normalize, build feature vector | 10 |
| ANN Priority Prediction | Predict urgency class (Perceptron + MLP) | 20 |
| Logic / Knowledge Base | Forward chaining, eligibility, gatekeeper | 20 |
| CSP Scheduler | Backtracking room/slot assignment | 15 |
| Search Navigation | A*, BFS, UCS with policy selection | 15 |
| Final Response | Aggregate all module outputs | 10 |

### Request Types & Pipelines

| Request Type | Modules Activated |
|---|---|
| Navigation_Only | Search |
| Eligibility_Check | Logic/KB |
| Booking_or_Scheduling | Logic/KB → CSP |
| Urgent_Service_Request | ANN → Logic/KB → CSP |
| Full_Service_Request | ANN → Logic/KB → CSP → Search |

Ingestion, Router, and Final Response always run.

## Project Structure

```
src/
├── main.py                 # CLI entry point, 5 predefined scenarios
├── campus_data.py          # Shared data (graph, rooms, constraints)
├── preprocessing.py        # Input validation and normalization
├── ann_module.py           # Perceptron + MLP neural networks (numpy)
├── logic_kb.py             # FOL forward chaining with unification
├── csp_scheduler.py        # Backtracking constraint solver
├── search_navigation.py    # A*, BFS, UCS with policy
├── router.py               # Request type → pipeline routing
└── final_response.py       # Output aggregation and audit trace
models/
└── mlp_model.json          # Trained MLP weights (7→4→3→4)
Claude design v2/
└── claude2_app.html        # Interactive UI (Survey & Ledger design)
```

## How to Run

### Requirements
- Python 3.10+
- numpy (`pip install numpy`)

### Run Scenarios

```bash
cd src
python main.py 1    # Ali · Full Service · Approved (all modules)
python main.py 2    # Sara · Full Service · Rejected at Logic/KB
python main.py 3    # Dr. Khan · Eligibility Check (Logic only)
python main.py 4    # Ali · Navigation Only (Search only)
python main.py 5    # Validation Error (halts at Ingestion)
```

### Run Individual Module Tests

```bash
cd src
python preprocessing.py
python ann_module.py
python logic_kb.py
python csp_scheduler.py
python search_navigation.py
python router.py
```

### Run Desktop GUI (Python Tkinter)

Launch the native Python desktop interface (zero external dependencies, runs directly on Python standard library):

```bash
python run_gui.py
# or from inside src:
python src/gui.py
```

Features included in the Desktop GUI:
- **Tab 1: Service Desk & Campus Map** — Intake form, real-time pipeline strip, interactive 13-node spatial campus graph on Canvas (clickable node selection and route highlighting).
- **Tab 2: Decision Record & Clearance** — Multi-paradigm breakdown for ANN (softmax bars), Logic/KB (derivation steps), CSP (timetable matrix), and Search with official digital clearance card.
- **Tab 3: Execution Log & Audit Trace** — Millisecond stage latencies, full formatted JSON trace viewer, and SHA-256 provenance hash.
- **Preset Scenario Switcher** — Quick one-click execution for all 5 canonical project scenarios.

### View Web UI (HTML Fallback)

Open `Claude design v2/claude2_app.html` in any browser.

## Key Design Decisions

1. **ANN predicts priority only.** It does not grant permission or replace logic-based validation.
2. **Logic/KB is the gatekeeper.** If rejected, the pipeline halts. CSP and Search do not execute.
3. **Not every request uses all modules.** The request type decides the pipeline.
4. **Real computation.** A* runs over the actual edge list, CSP evaluates constraints against the assignment, and forward chaining derives new facts from rules.

## Campus Graph

- 13 nodes, 19 weighted edges
- Node categories: access (diamond), academic (square), service (circle)
- Heuristic: Euclidean distance / 3 (admissible, consistent)

## Team

| Member | Role | Modules |
|---|---|---|
| Saim | Leader | Preprocessing, ANN, UI, Integration |
| Mohsin | Member | Logic/KB, CSP Scheduler |
| Yaeesh | Member | Search, Router, Final Response |
