"""
Report Generator for Smart Campus AI Project
=============================================
Generates the Microsoft Word report with:
- Project overview and architecture
- AI concepts used (per module)
- Code snippets from each module
- Screenshots
- Module descriptions and sequence to run

Uses python-docx to build the report.
"""

import os
import sys
import json
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# ─── CONFIG ────────────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
REPORT_DIR = os.path.join(PROJECT_ROOT, "report")
UI_DIR = os.path.join(PROJECT_ROOT, "Claude design v2")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

OUTPUT_PATH = os.path.join(REPORT_DIR, "report.docx")

# Colors
ACCENT = RGBColor(0x1F, 0x3A, 0x5F)   # #1F3A5F
TEXT_2 = RGBColor(0x5E, 0x5B, 0x53)    # #5E5B53
SUCCESS = RGBColor(0x2E, 0x7D, 0x5B)   # #2E7D5B
DANGER = RGBColor(0xB0, 0x3A, 0x2E)    # #B03A2E
BLACK = RGBColor(0x1B, 0x1A, 0x17)     # #1B1A17


def set_cell_shading(cell, color_hex):
    """Set background shading on a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_heading_styled(doc, text, level=1):
    """Add a heading with consistent styling."""
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = ACCENT
    return heading


def add_code_block(doc, code, max_lines=30):
    """Add a formatted code block to the document."""
    lines = code.strip().split('\n')
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"    # ... ({len(code.strip().split(chr(10))) - max_lines} more lines)"]
    
    code_text = '\n'.join(lines)
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.left_indent = Cm(0.5)
    run = para.add_run(code_text)
    run.font.name = 'Consolas'
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


def add_screenshot(doc, path, caption, width=Inches(6)):
    """Add a screenshot image with caption."""
    if os.path.exists(path):
        doc.add_picture(path, width=width)
        last_para = doc.paragraphs[-1]
        last_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        run.font.size = Pt(9)
        run.font.italic = True
        run.font.color.rgb = TEXT_2
    else:
        doc.add_paragraph(f"[Screenshot not found: {os.path.basename(path)}]")


def read_source(filename, start_line=None, end_line=None):
    """Read source code from a file, optionally a specific line range."""
    path = os.path.join(SRC_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if start_line and end_line:
        lines = lines[start_line-1:end_line]
    
    return ''.join(lines)


def extract_function(filename, func_name):
    """Extract a specific function from a source file."""
    path = os.path.join(SRC_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find function start
    import re
    pattern = rf'((?:class |def ){func_name}[\s\S]*?)(?=\n(?:class |def |\Z))'
    match = re.search(pattern, content)
    if match:
        return match.group(1).rstrip()
    return f"# Function {func_name} not found in {filename}"


def build_report():
    """Build the complete Word report."""
    doc = Document()
    
    # ─── STYLES ─────────────────────────────────────────────────────
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.font.color.rgb = BLACK
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15
    
    # ─── TITLE PAGE ─────────────────────────────────────────────────
    for _ in range(4):
        doc.add_paragraph()
    
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Smart Campus AI\nDecision Support & Automation System")
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = ACCENT
    
    doc.add_paragraph()
    
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("AL2002 — Artificial Intelligence Lab\nFall 2026")
    run.font.size = Pt(14)
    run.font.color.rgb = TEXT_2
    
    doc.add_paragraph()
    
    inst = doc.add_paragraph()
    inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = inst.add_run("National University of Computing & Emerging Sciences\nFAST-NUCES")
    run.font.size = Pt(12)
    run.font.color.rgb = TEXT_2
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    team = doc.add_paragraph()
    team.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = team.add_run("Team Members")
    run.font.size = Pt(14)
    run.font.bold = True
    
    members = doc.add_paragraph()
    members.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = members.add_run(
        "Saim (Leader) — Preprocessing, ANN, UI\n"
        "Mohsin — Logic/KB, CSP Scheduler\n"
        "Yaeesh — Search, Router, Final Response"
    )
    run.font.size = Pt(11)
    
    doc.add_page_break()
    
    # ─── TABLE OF CONTENTS ──────────────────────────────────────────
    add_heading_styled(doc, "Table of Contents", 1)
    
    toc_items = [
        ("1.", "Project Overview"),
        ("2.", "System Architecture"),
        ("3.", "Module 1: Input & Preprocessing"),
        ("4.", "Module 2: ANN Priority Prediction"),
        ("5.", "Module 3: Logic / Knowledge Base"),
        ("6.", "Module 4: CSP Scheduler"),
        ("7.", "Module 5: Search & Navigation"),
        ("8.", "Module 6: Request Router"),
        ("9.", "Module 7: Final Response & Integration"),
        ("10.", "User Interface"),
        ("11.", "End-to-End Scenarios"),
        ("12.", "How to Run the Program"),
    ]
    
    for num, title_text in toc_items:
        p = doc.add_paragraph()
        run = p.add_run(f"{num}  {title_text}")
        run.font.size = Pt(11)
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: PROJECT OVERVIEW
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "1. Project Overview", 1)
    
    doc.add_paragraph(
        "This project implements an intelligent campus decision support platform. "
        "The system receives structured requests from university users (students, "
        "instructors, staff), validates and normalizes the input, routes the request "
        "through the appropriate AI pipeline, and produces one unified final response."
    )
    
    doc.add_paragraph(
        "The platform integrates four AI paradigms:"
    )
    
    ai_items = [
        ("Artificial Neural Networks (ANN)", "Perceptron (binary baseline) and Multi-Layer Perceptron (multiclass operational model) for urgency/priority prediction."),
        ("Logic / Knowledge Base", "First-Order Logic with forward chaining inference and unification for eligibility verification and authorization."),
        ("Constraint Satisfaction (CSP)", "Backtracking search for conflict-free room and time slot scheduling under 9 constraints."),
        ("Graph Search", "A*, BFS, and UCS algorithms with policy-based selection for campus navigation."),
    ]
    
    for title_text, desc in ai_items:
        p = doc.add_paragraph()
        run = p.add_run(f"{title_text}: ")
        run.font.bold = True
        p.add_run(desc)
    
    doc.add_paragraph(
        "The key design principle is intelligence separation: each module has a single "
        "responsibility. ANN predicts priority only — it does not grant permission. "
        "Logic/KB is the gatekeeper — if it rejects, the pipeline halts. Not every "
        "request uses all modules; the request type determines the pipeline."
    )
    
    add_heading_styled(doc, "1.1 Canonical Request Types", 2)
    
    # Request types table
    table = doc.add_table(rows=6, cols=3)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers = ["Request Type", "Modules Activated", "Example Use Case"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    data = [
        ("Navigation_Only", "Search", "Find route to Library"),
        ("Eligibility_Check", "Logic/KB", "Check course prerequisites"),
        ("Booking_or_Scheduling", "Logic/KB, CSP", "Book a lab session"),
        ("Urgent_Service_Request", "ANN, Logic/KB, CSP", "Emergency resource allocation"),
        ("Full_Service_Request", "ANN, Logic/KB, CSP, Search", "Complete lab access with route"),
    ]
    
    for row_idx, (rtype, modules, example) in enumerate(data, 1):
        table.rows[row_idx].cells[0].text = rtype
        table.rows[row_idx].cells[0].paragraphs[0].runs[0].font.name = 'Consolas'
        table.rows[row_idx].cells[0].paragraphs[0].runs[0].font.size = Pt(9)
        table.rows[row_idx].cells[1].text = modules
        table.rows[row_idx].cells[2].text = example
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: SYSTEM ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "2. System Architecture", 1)
    
    doc.add_paragraph(
        "The system follows a pipeline architecture where each module processes "
        "the request in sequence. The Request Router determines which modules to "
        "activate based on the request type."
    )
    
    add_heading_styled(doc, "2.1 Pipeline Flow", 2)
    
    doc.add_paragraph(
        "User Request → Input & Preprocessing → Request Router → "
        "[ANN → Logic/KB → CSP → Search] → Final Response"
    )
    
    doc.add_paragraph(
        "Ingestion, Router, and Final Response always run. The modules in brackets "
        "are activated selectively based on the request type."
    )
    
    add_heading_styled(doc, "2.2 Intelligence Separation Table", 2)
    
    table = doc.add_table(rows=7, cols=2)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    sep_headers = ["Responsibility", "Module"]
    for i, h in enumerate(sep_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    sep_data = [
        ("User intent", "User input"),
        ("Control flow", "Request Router"),
        ("Priority estimation", "ANN"),
        ("Permission & rules", "Logic / KB"),
        ("Allocation", "CSP"),
        ("Navigation", "Search"),
    ]
    
    for i, (resp, mod) in enumerate(sep_data, 1):
        table.rows[i].cells[0].text = resp
        table.rows[i].cells[1].text = mod
    
    add_heading_styled(doc, "2.3 Project File Structure", 2)
    
    structure = """src/
├── main.py                 # CLI entry point, 5 predefined scenarios
├── campus_data.py          # Shared data (graph, rooms, constraints)
├── preprocessing.py        # Input validation and normalization
├── ann_module.py           # Perceptron + MLP neural networks
├── logic_kb.py             # FOL forward chaining with unification
├── csp_scheduler.py        # Backtracking constraint solver
├── search_navigation.py    # A*, BFS, UCS with policy
├── router.py               # Request type to pipeline routing
└── final_response.py       # Output aggregation and audit trace
models/
└── mlp_model.json          # Trained MLP weights"""
    
    add_code_block(doc, structure)
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: INPUT & PREPROCESSING (10 marks)
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "3. Module 1: Input & Preprocessing", 1)
    
    doc.add_paragraph(
        "This is the first module of the system. It receives the user's structured "
        "request, validates all required fields, normalizes values, and builds the "
        "7-element feature vector used by the ANN module."
    )
    
    add_heading_styled(doc, "3.1 AI Concepts Used", 2)
    
    doc.add_paragraph(
        "Feature Engineering: The module transforms raw request data into a "
        "standardized 7-element numeric vector suitable for neural network input. "
        "Each feature is normalized to the [0, 1] range."
    )
    
    # Feature vector table
    table = doc.add_table(rows=8, cols=4)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    fv_headers = ["Feature", "Variable", "Description", "Example Value"]
    for i, h in enumerate(fv_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    fv_data = [
        ("x1", "Role", "Student=0, Instructor=0.5, Staff=1", "0.0"),
        ("x2", "RequestType", "Nav=0, Elig=0.25, Book=0.5, Urgent=0.75, Full=1", "1.0"),
        ("x3", "Severity", "Normalized severity/10", "0.85"),
        ("x4", "TimeSensitivity", "Time urgency factor", "0.92"),
        ("x5", "CrowdLevel", "Derived from time of day", "0.40"),
        ("x6", "Distance", "Euclidean distance (normalized)", "0.32"),
        ("x7", "Eligibility", "Pre-check flag", "1.0"),
    ]
    
    for i, (feat, var, desc, val) in enumerate(fv_data, 1):
        table.rows[i].cells[0].text = feat
        table.rows[i].cells[0].paragraphs[0].runs[0].font.name = 'Consolas'
        table.rows[i].cells[1].text = var
        table.rows[i].cells[2].text = desc
        table.rows[i].cells[3].text = val
    
    add_heading_styled(doc, "3.2 Code Snippet — Validation", 2)
    add_code_block(doc, extract_function("preprocessing.py", "validate_request"))
    
    add_heading_styled(doc, "3.3 Code Snippet — Feature Vector Construction", 2)
    add_code_block(doc, extract_function("preprocessing.py", "preprocess_request"))
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: ANN PRIORITY PREDICTION (20 marks)
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "4. Module 2: ANN Priority Prediction", 1)
    
    p = doc.add_paragraph()
    run = p.add_run("Critical Rule: ")
    run.font.bold = True
    run.font.color.rgb = DANGER
    p.add_run("ANN predicts priority only. It does not grant permission, check "
              "eligibility, or replace logic-based validation.")
    
    add_heading_styled(doc, "4.1 AI Concepts Used", 2)
    
    doc.add_paragraph(
        "The module implements two neural network architectures from scratch using "
        "only NumPy (no PyTorch, TensorFlow, or sklearn neural networks):"
    )
    
    p = doc.add_paragraph()
    run = p.add_run("Perceptron (Binary Baseline): ")
    run.font.bold = True
    p.add_run(
        "A single-layer neural network with 7 inputs and 1 sigmoid output. "
        "Classifies requests as Urgent or Not-Urgent. Trained with gradient "
        "descent on binary cross-entropy loss."
    )
    
    p = doc.add_paragraph()
    run = p.add_run("MLP (Operational Model): ")
    run.font.bold = True
    p.add_run(
        "A multi-layer perceptron with architecture 7 → 4 → 3 → 4. "
        "Hidden layers use ReLU activation. Output layer uses softmax for "
        "4-class probability distribution (Urgent, High, Normal, Low). "
        "Trained with backpropagation and cross-entropy loss. "
        "Uses Xavier initialization for stable training."
    )
    
    add_heading_styled(doc, "4.2 Network Architecture", 2)
    
    doc.add_paragraph(
        "Input Layer (7 neurons): x1=Role, x2=RequestType, x3=Severity, "
        "x4=TimeSensitivity, x5=CrowdLevel, x6=Distance, x7=Eligibility\n"
        "Hidden Layer 1 (4 neurons): ReLU activation\n"
        "Hidden Layer 2 (3 neurons): ReLU activation\n"
        "Output Layer (4 neurons): Softmax → P(Urgent), P(High), P(Normal), P(Low)"
    )
    
    add_heading_styled(doc, "4.3 Code Snippet — MLP Forward Pass", 2)
    add_code_block(doc, extract_function("ann_module.py", "forward"))
    
    add_heading_styled(doc, "4.4 Code Snippet — Backpropagation Training", 2)
    add_code_block(doc, extract_function("ann_module.py", "train"))
    
    add_heading_styled(doc, "4.5 Code Snippet — Prediction Entry Point", 2)
    add_code_block(doc, extract_function("ann_module.py", "predict_priority"))
    
    add_heading_styled(doc, "4.6 Training Data Generation", 2)
    doc.add_paragraph(
        "100 synthetic training samples are generated with rule-based labeling. "
        "The urgency score formula weights severity (0.35), time sensitivity (0.30), "
        "request type (0.15), crowd level (0.10), and distance (0.10). "
        "This produces a realistic distribution across the four priority classes."
    )
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: LOGIC / KNOWLEDGE BASE (20 marks)
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "5. Module 3: Logic / Knowledge Base", 1)
    
    doc.add_paragraph(
        "This module is the project's rule-based reasoning engine. It checks whether "
        "a request is logically supported, verifies user eligibility and authorization, "
        "and acts as a gatekeeper before CSP. If the request is not allowed, the "
        "pipeline halts and the system explains the rejection."
    )
    
    add_heading_styled(doc, "5.1 AI Concepts Used", 2)
    
    concepts = [
        ("First-Order Logic (FOL)", "Predicates with variables represent facts and rules. Example: Student(x), Completed(x, ProgrammingFundamentals)."),
        ("Forward Chaining", "An iterative inference engine that applies rules to derive new facts until no more rules can fire (fixed-point reached)."),
        ("Unification", "Pattern matching with variable substitution. Example: unify(Student(x), Student(Ali)) produces {x/Ali}."),
        ("Modus Ponens", "If all premises of a rule are satisfied, the conclusion is derived as a new fact."),
    ]
    
    for title_text, desc in concepts:
        p = doc.add_paragraph()
        run = p.add_run(f"{title_text}: ")
        run.font.bold = True
        p.add_run(desc)
    
    add_heading_styled(doc, "5.2 Knowledge Base", 2)
    
    doc.add_paragraph("Ground Facts:")
    
    facts_code = """# Ali's facts
Student(Ali)
Completed(Ali, ProgrammingFundamentals)
Enrolled(Ali, AI)

# Sara's facts (missing prerequisite)
Student(Sara)
# NOTE: No Completed(Sara, ProgrammingFundamentals)

# Dr. Khan's facts
Instructor(DrKhan)
Teaches(DrKhan, AI)
HasPhD(DrKhan)"""
    add_code_block(doc, facts_code)
    
    doc.add_paragraph("Inference Rules:")
    
    rules_code = """R1: Student(x) AND Completed(x, ProgrammingFundamentals) => Eligible(x, AI)
R2: Teaches(x, AI) => Instructor(x, AI)
R3: Enrolled(x, AI) => UsesLab(x, Lab1)
R4: Instructor(x, AI) => UsesLab(x, Lab1)"""
    add_code_block(doc, rules_code)
    
    add_heading_styled(doc, "5.3 Derivation Example — Ali (Authorized)", 2)
    
    table = doc.add_table(rows=7, cols=3)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    deriv_headers = ["Step", "Formula", "Justification"]
    for i, h in enumerate(deriv_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    deriv_data = [
        ("1", "Student(Ali)", "Fact"),
        ("2", "Completed(Ali, ProgrammingFundamentals)", "Fact"),
        ("3", "Enrolled(Ali, AI)", "Fact"),
        ("4", "Eligible(Ali, AI)", "R1, modus ponens, {x/Ali}"),
        ("5", "UsesLab(Ali, Lab1)", "R3, modus ponens, {x/Ali}"),
        ("", "Verdict: AUTHORIZED", "R1, R3 fired"),
    ]
    
    for i, (step, formula, just) in enumerate(deriv_data, 1):
        table.rows[i].cells[0].text = step
        table.rows[i].cells[1].text = formula
        table.rows[i].cells[1].paragraphs[0].runs[0].font.name = 'Consolas'
        table.rows[i].cells[1].paragraphs[0].runs[0].font.size = Pt(9)
        table.rows[i].cells[2].text = just
    
    add_heading_styled(doc, "5.4 Rejection Example — Sara", 2)
    
    doc.add_paragraph(
        "Sara is a Student but has not completed ProgrammingFundamentals. "
        "Rule R1 requires both Student(x) AND Completed(x, ProgrammingFundamentals). "
        "Since Completed(Sara, ProgrammingFundamentals) is not in the knowledge base, "
        "R1 cannot fire. The verdict is REJECTED, and the pipeline halts. "
        "CSP and Search do not execute."
    )
    
    p = doc.add_paragraph()
    run = p.add_run("Note: ")
    run.font.bold = True
    p.add_run("ANN still predicts Sara's request as Urgent (98.7%). This demonstrates "
              "intelligence separation — ANN predicts priority, Logic/KB decides permission.")
    
    add_heading_styled(doc, "5.5 Code Snippet — Forward Chaining", 2)
    add_code_block(doc, extract_function("logic_kb.py", "forward_chain"))
    
    add_heading_styled(doc, "5.6 Code Snippet — Unification", 2)
    add_code_block(doc, extract_function("logic_kb.py", "unify"))
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: CSP SCHEDULER (15 marks)
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "6. Module 4: CSP Scheduler", 1)
    
    doc.add_paragraph(
        "The CSP (Constraint Satisfaction Problem) scheduler assigns groups to rooms "
        "and time slots while respecting a set of constraints. It uses backtracking "
        "search to find a conflict-free assignment. This module only runs after "
        "Logic/KB authorizes the request."
    )
    
    add_heading_styled(doc, "6.1 AI Concepts Used", 2)
    
    csp_concepts = [
        ("Variables", "6 groups: G1, G2, G3, G4, G5, G6"),
        ("Domains", "3 rooms (Lab 1, Lab 2, Lab 3) x 4 time slots (09:00, 10:00, 11:00, 12:00) = 12 possible values per group"),
        ("Constraints (9 total)", "Room clash (6), Examiner clash (1), Supervisor clash (1), Precedence (1)"),
        ("Backtracking Search", "Tries each domain value for each variable. If a constraint is violated, it backtracks and tries another value."),
    ]
    
    for title_text, desc in csp_concepts:
        p = doc.add_paragraph()
        run = p.add_run(f"{title_text}: ")
        run.font.bold = True
        p.add_run(desc)
    
    add_heading_styled(doc, "6.2 Constraint List", 2)
    
    table = doc.add_table(rows=10, cols=4)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    csp_headers = ["#", "Label", "Type", "Description"]
    for i, h in enumerate(csp_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    from campus_data import CSP_CONSTRAINTS
    for i, c in enumerate(CSP_CONSTRAINTS, 1):
        table.rows[i].cells[0].text = str(i)
        table.rows[i].cells[1].text = c["label"]
        table.rows[i].cells[1].paragraphs[0].runs[0].font.name = 'Consolas'
        table.rows[i].cells[2].text = c["type"]
        table.rows[i].cells[3].text = c["description"]
    
    add_heading_styled(doc, "6.3 Code Snippet — Backtracking Solver", 2)
    add_code_block(doc, extract_function("csp_scheduler.py", "solve_csp"))
    
    add_heading_styled(doc, "6.4 Code Snippet — Constraint Checking", 2)
    add_code_block(doc, extract_function("csp_scheduler.py", "check_constraint"))
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: SEARCH & NAVIGATION (15 marks)
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "7. Module 5: Search & Navigation", 1)
    
    doc.add_paragraph(
        "This module implements three search algorithms for campus navigation. "
        "A policy function selects the appropriate algorithm based on graph properties."
    )
    
    add_heading_styled(doc, "7.1 AI Concepts Used", 2)
    
    search_algs = [
        ("A* Search", "Optimal path finding for weighted graphs using f(n) = g(n) + h(n). Uses a Euclidean/3 heuristic that is admissible and consistent."),
        ("BFS (Breadth-First Search)", "Finds shortest path by number of edges in unweighted graphs. Expands nodes level by level."),
        ("UCS (Uniform Cost Search)", "Optimal search for weighted graphs without a heuristic. Equivalent to A* with h(n) = 0."),
    ]
    
    for title_text, desc in search_algs:
        p = doc.add_paragraph()
        run = p.add_run(f"{title_text}: ")
        run.font.bold = True
        p.add_run(desc)
    
    add_heading_styled(doc, "7.2 Algorithm Selection Policy", 2)
    
    doc.add_paragraph(
        "Weighted graph + heuristic available: A* (primary)\n"
        "Unweighted graph: BFS\n"
        "Weighted graph + no heuristic: UCS (fallback)"
    )
    
    add_heading_styled(doc, "7.3 Campus Graph", 2)
    
    doc.add_paragraph(
        "The campus graph has 13 nodes and 19 weighted edges. "
        "Nodes are categorized as access (gates, transport), academic (labs, blocks), "
        "or service (admin, medical, cafeteria)."
    )
    
    from campus_data import CAMPUS_EDGES
    
    table = doc.add_table(rows=len(CAMPUS_EDGES) + 1, cols=3)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    edge_headers = ["Node A", "Node B", "Weight"]
    for i, h in enumerate(edge_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    for i, (a, b, w) in enumerate(CAMPUS_EDGES, 1):
        table.rows[i].cells[0].text = a
        table.rows[i].cells[1].text = b
        table.rows[i].cells[2].text = str(w)
    
    add_heading_styled(doc, "7.4 A* Trace — Main_Gate to AI_Lab", 2)
    
    doc.add_paragraph(
        "The A* algorithm expands nodes in order of f(n) = g(n) + h(n). "
        "The heuristic h(n) is the Euclidean distance divided by 3 (admissible, consistent)."
    )
    
    # Run A* to get actual trace
    sys.path.insert(0, SRC_DIR)
    from search_navigation import astar
    a_result = astar("Main_Gate", "AI_Lab")
    
    table = doc.add_table(rows=len(a_result.trace) + 1, cols=4)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    trace_headers = ["#", "Node", "g(n)", "f(n)"]
    for i, h in enumerate(trace_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    for i, t in enumerate(a_result.trace, 1):
        table.rows[i].cells[0].text = str(i)
        table.rows[i].cells[1].text = t["node"]
        table.rows[i].cells[2].text = str(t["g"])
        table.rows[i].cells[3].text = str(t["f"])
    
    p = doc.add_paragraph()
    run = p.add_run(f"\nOptimal Path: {' -> '.join(a_result.path)}")
    run.font.bold = True
    doc.add_paragraph(f"Total Cost: {a_result.cost:.1f} ({a_result.edges} edges)")
    doc.add_paragraph(f"Nodes Expanded: {len(a_result.expanded)}")
    
    add_heading_styled(doc, "7.5 Code Snippet — A* Algorithm", 2)
    add_code_block(doc, extract_function("search_navigation.py", "astar"))
    
    add_heading_styled(doc, "7.6 Code Snippet — Heuristic Function", 2)
    add_code_block(doc, extract_function("search_navigation.py", "euclidean_heuristic"))
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 8: REQUEST ROUTER
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "8. Module 6: Request Router", 1)
    
    doc.add_paragraph(
        "The Request Router is the control-flow brain of the platform. It reads "
        "the request_type and decides which modules should run and in what order. "
        "The router does not solve the request itself — it directs the request to "
        "the correct parts of the system."
    )
    
    add_heading_styled(doc, "8.1 Routing Matrix", 2)
    
    table = doc.add_table(rows=6, cols=5)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    rm_headers = ["Request Type", "ANN", "Logic", "CSP", "Search"]
    for i, h in enumerate(rm_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    from campus_data import ROUTING_MATRIX
    for row_idx, (rtype, modules) in enumerate(ROUTING_MATRIX.items(), 1):
        table.rows[row_idx].cells[0].text = rtype
        table.rows[row_idx].cells[0].paragraphs[0].runs[0].font.name = 'Consolas'
        table.rows[row_idx].cells[0].paragraphs[0].runs[0].font.size = Pt(9)
        for col_idx, mod in enumerate(["ANN", "LOGIC", "CSP", "SEARCH"], 1):
            table.rows[row_idx].cells[col_idx].text = "●" if mod in modules else "—"
            table.rows[row_idx].cells[col_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    add_heading_styled(doc, "8.2 Code Snippet — Route Request", 2)
    add_code_block(doc, extract_function("router.py", "route_request"))
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 9: FINAL RESPONSE & INTEGRATION
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "9. Module 7: Final Response & Integration", 1)
    
    doc.add_paragraph(
        "The Final Response layer collects the relevant results from all modules "
        "that were used and presents them as one coherent answer. It includes "
        "the priority summary, eligibility result, assignment, route, and explanation."
    )
    
    add_heading_styled(doc, "9.1 Output Components", 2)
    
    components = [
        ("Outcome", "A one-sentence human-readable summary of the decision."),
        ("Ledger", "A 5-cell summary: Priority, Permission, Allocation, Route, Communication."),
        ("Pipeline Stages", "Status of each pipeline stage (done, skipped, blocked)."),
        ("Execution Log", "Timing and detail for each module that ran."),
        ("Audit Trace", "Complete JSON export of all module inputs and outputs."),
    ]
    
    for title_text, desc in components:
        p = doc.add_paragraph()
        run = p.add_run(f"{title_text}: ")
        run.font.bold = True
        p.add_run(desc)
    
    add_heading_styled(doc, "9.2 Code Snippet — Build Outcome", 2)
    add_code_block(doc, extract_function("final_response.py", "build_outcome"))
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 10: USER INTERFACE
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "10. User Interface", 1)
    
    doc.add_paragraph(
        "The interactive UI is built as a single HTML file with embedded CSS and "
        "JavaScript. It follows the 'Survey & Ledger' design concept, inspired by "
        "surveyor's plans and transit line diagrams."
    )
    
    add_heading_styled(doc, "10.1 Design System", 2)
    
    design_features = [
        ("Pipeline Rail", "6 stations on a horizontal rail showing the pipeline status (done, skipped, blocked)."),
        ("Surveyor's Map", "Interactive campus graph with axis rulers, category-specific node glyphs, and A* route highlighting."),
        ("Clearance Card", "A ledger-style pass with a barcode and bordered stamp for the decision."),
        ("Search Trace", "Numbered expansion order overlaid on the campus map."),
    ]
    
    for title_text, desc in design_features:
        p = doc.add_paragraph()
        run = p.add_run(f"{title_text}: ")
        run.font.bold = True
        p.add_run(desc)
    
    # Add screenshots
    add_heading_styled(doc, "10.2 Screenshots", 2)
    
    screenshots = [
        ("claude2_screen1_service_desk.png", "Screen 1: Service Desk — Ali's Full Service Request (Approved)"),
        ("claude2_screen2_decision_record.png", "Screen 2: Decision Record — Complete audit trail"),
        ("claude2_screen3_sara_rejected.png", "Screen 3: Sara's Request — Rejected at Logic/KB"),
    ]
    
    for filename, caption in screenshots:
        path = os.path.join(UI_DIR, filename)
        add_screenshot(doc, path, caption)
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 11: END-TO-END SCENARIOS
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "11. End-to-End Scenarios", 1)
    
    doc.add_paragraph(
        "The system is tested with 5 predefined scenarios that demonstrate "
        "different request types and pipeline behaviors."
    )
    
    scenarios = [
        ("Scenario 1: Ali — Full Service Request (Approved)",
         "All 6 pipeline stages run. ANN predicts Urgent (98.8%). Logic/KB authorizes (R1, R3). "
         "CSP assigns Lab 1 at 10:00. A* finds route Main_Gate -> Parking -> Science_Block -> AI_Lab (cost 6.0)."),
        ("Scenario 2: Sara — Full Service Request (Rejected)",
         "ANN still predicts Urgent (98.7%), but Logic/KB rejects because Sara has not completed "
         "ProgrammingFundamentals. Pipeline halts. CSP and Search do not execute. "
         "This demonstrates intelligence separation."),
        ("Scenario 3: Dr. Khan — Eligibility Check",
         "Only Logic/KB runs (Eligibility_Check type). Rules R2 and R4 fire. "
         "Dr. Khan is authorized as an AI instructor. ANN, CSP, Search are not routed."),
        ("Scenario 4: Ali — Navigation Only",
         "Only Search runs. A* finds route Main_Gate -> Admin_Block -> Student_Services -> Library (cost 7.0). "
         "ANN, Logic/KB, CSP are not routed."),
        ("Scenario 5: Validation Error",
         "Severity is set to -1 (invalid). Preprocessing catches the error and halts at Ingestion. "
         "No other modules execute."),
    ]
    
    for title_text, desc in scenarios:
        add_heading_styled(doc, title_text, 2)
        doc.add_paragraph(desc)
    
    doc.add_page_break()
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION 12: HOW TO RUN
    # ═══════════════════════════════════════════════════════════════
    add_heading_styled(doc, "12. How to Run the Program", 1)
    
    add_heading_styled(doc, "12.1 Requirements", 2)
    doc.add_paragraph("Python 3.10 or higher\nnumpy (pip install numpy)")
    
    add_heading_styled(doc, "12.2 Run All Scenarios", 2)
    
    run_code = """cd src
python main.py 1    # Ali - Full Service - Approved
python main.py 2    # Sara - Full Service - Rejected at Logic/KB
python main.py 3    # Dr. Khan - Eligibility Check
python main.py 4    # Ali - Navigation Only
python main.py 5    # Validation Error"""
    add_code_block(doc, run_code)
    
    add_heading_styled(doc, "12.3 Run Individual Modules", 2)
    
    module_code = """cd src
python preprocessing.py         # Test Input & Preprocessing
python ann_module.py            # Test ANN Priority Prediction
python logic_kb.py              # Test Logic / Knowledge Base
python csp_scheduler.py         # Test CSP Scheduler
python search_navigation.py     # Test Search & Navigation
python router.py                # Test Request Router"""
    add_code_block(doc, module_code)
    
    add_heading_styled(doc, "12.4 View UI", 2)
    doc.add_paragraph('Open "Claude design v2/claude2_app.html" in any modern web browser (Chrome, Firefox, Edge).')
    
    add_heading_styled(doc, "12.5 Modules Completed", 2)
    
    table = doc.add_table(rows=8, cols=3)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    mod_headers = ["Module", "File", "Status"]
    for i, h in enumerate(mod_headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        set_cell_shading(cell, "1F3A5F")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    
    mod_data = [
        ("Input & Preprocessing", "preprocessing.py", "Complete"),
        ("ANN Priority Prediction", "ann_module.py", "Complete"),
        ("Logic / Knowledge Base", "logic_kb.py", "Complete"),
        ("CSP Scheduler", "csp_scheduler.py", "Complete"),
        ("Search & Navigation", "search_navigation.py", "Complete"),
        ("Request Router", "router.py", "Complete"),
        ("Final Response", "final_response.py", "Complete"),
    ]
    
    for i, (mod, file, status) in enumerate(mod_data, 1):
        table.rows[i].cells[0].text = mod
        table.rows[i].cells[1].text = file
        table.rows[i].cells[1].paragraphs[0].runs[0].font.name = 'Consolas'
        table.rows[i].cells[1].paragraphs[0].runs[0].font.size = Pt(9)
        table.rows[i].cells[2].text = status

    # ─── SAVE ───────────────────────────────────────────────────────
    os.makedirs(REPORT_DIR, exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(f"Report saved to: {OUTPUT_PATH}")
    print(f"Size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")


if __name__ == "__main__":
    build_report()
