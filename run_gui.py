"""
Smart Campus AI — Decision Support & Automation System
=======================================================
Root launcher script for the native Python desktop GUI application.

Run:
    python run_gui.py

Course: AL2002 – Artificial Intelligence Lab, Fall 2026
FAST-NUCES
"""

import sys
import os

# Add src directory to system path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from gui import main

if __name__ == "__main__":
    main()
