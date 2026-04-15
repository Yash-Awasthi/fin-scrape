"""
Pytest configuration for finscrape tests.

The top-level finscrape/__init__.py imports the full pipeline which pulls in
heavy C-extension dependencies (curl_cffi, etc.) that may not be installed in
a lightweight test environment.  We pre-load the finscrape package entry in
sys.modules with a minimal stub so that submodule imports
(finscrape.models, finscrape.storage, …) resolve without triggering the
pipeline import chain.
"""

import importlib
import sys
import types
from pathlib import Path

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Insert a lightweight stub for the top-level finscrape package so that
# "from finscrape.models import …" works without executing finscrape/__init__.py
# which would drag in the full engine/pipeline dependency tree.
if "finscrape" not in sys.modules:
    _stub = types.ModuleType("finscrape")
    _stub.__path__ = [str(Path(__file__).resolve().parent.parent / "finscrape")]
    _stub.__package__ = "finscrape"
    sys.modules["finscrape"] = _stub

# Also stub finscrape.analysis to avoid importing ai_client (needs requests)
if "finscrape.analysis" not in sys.modules:
    _analysis_stub = types.ModuleType("finscrape.analysis")
    _analysis_stub.__path__ = [str(Path(__file__).resolve().parent.parent / "finscrape" / "analysis")]
    _analysis_stub.__package__ = "finscrape.analysis"
    sys.modules["finscrape.analysis"] = _analysis_stub
