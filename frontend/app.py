"""
frontend/app.py

Streamlit application entrypoint for the Samanvaya Lunar Image Registration Portal.
Integrates directly with lunar_core.ui.app.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is available in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Run the complete lunar_core UI app
import lunar_core.ui.app
