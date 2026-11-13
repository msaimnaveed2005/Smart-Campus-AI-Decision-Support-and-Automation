# Claude 2.0 — "Survey & Ledger" Design Plan

## Concept
The map is a surveyor's plan; the decision is a registrar's ledger. Six signature moves:

1. **Pipeline as Line Diagram** — Transit-map style horizontal rail with 6 stations
2. **Surveyor's Map** — Axis rulers, tick marks, glyphs by category (diamond/square/circle)
3. **Ownership Labels** — Every module header: "Decides:" / "Cannot decide:"
4. **Search Trace** — Optional overlay with expansion-order badges and frontier hatching
5. **Clearance Card as Pass** — Ledger rows, perforated stub, barcode, bordered stamp
6. **Real Computation** — A*, CSP evaluation, forward-chaining logic (not hard-coded)

## Screens
- **Screen 1 — Service Desk**: Pipeline rail, intake form (360px left), surveyor's map (right), execution log
- **Screen 2 — Decision Record**: Ledger strip, 4 evidence sections (ANN, Logic, CSP, Search), clearance card

## Scenarios
1. Ali, Full_Service_Request — all stations done (default)
2. Sara, Full_Service_Request — rejected at Logic (KB missing prerequisite)
3. Dr. Khan, Eligibility_Check — only Logic runs
4. Ali, Navigation_Only — only Search runs
5. Validation error at Ingestion

## Tokens
- canvas #F5F4F0, surface #FFFFFF, subtle #EDEBE5, border #DDDAD2
- accent #1F3A5F, success #2E7D5B, warning #A8650F, danger #B03A2E
- Fonts: IBM Plex Sans, IBM Plex Mono, Source Serif 4

## Implementation
Single-file React + inline Tailwind. Real algorithms: astar(), evaluateConstraints(), forwardChain().

