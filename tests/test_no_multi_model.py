"""Guards that multi_model / analyze_batch / batch prompts stay deleted."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_no_multi_model_references_in_source():
    result = subprocess.run(
        [
            "grep", "-rn", "multi_model\\|analyze_batch\\|BATCH_ANALYSIS",
            "--include=*.py",
            # first-party source only — vendored/reference trees have their own rules
            "--exclude-dir=.venv", "--exclude-dir=.git",
            "--exclude-dir=reference", "--exclude-dir=absorbed",
            "--exclude-dir=node_modules",
            ".",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    hits = [
        line for line in result.stdout.splitlines()
        if ".venv" not in line and "test_no_multi_model.py" not in line
    ]
    assert hits == [], f"stale references found:\n" + "\n".join(hits)


def test_multi_model_module_deleted():
    assert not (REPO_ROOT / "finscrape" / "analysis" / "multi_model.py").exists()


def test_analyze_batch_not_exported():
    import finscrape.analysis as analysis
    assert not hasattr(analysis, "analyze_batch")


def test_batch_prompt_constants_removed():
    import finscrape.analysis.prompts as prompts
    assert not hasattr(prompts, "BATCH_SYSTEM_PROMPT")
    assert not hasattr(prompts, "BATCH_ANALYSIS_PROMPT")
