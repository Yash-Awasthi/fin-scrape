import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineStep:
    label: str
    script_name: str
    accepts_refresh: bool = False


PIPELINE_STEPS = [
    PipelineStep("Build ETF returns", "build_returns_panel.py", accepts_refresh=True),
    PipelineStep("Build daily GPR data", "build_gpr_dataset.py", accepts_refresh=True),
    PipelineStep("Build market controls", "build_market_controls.py", accepts_refresh=True),
    PipelineStep("Build combined analysis panel", "build_analysis_panel.py"),
    PipelineStep("Run data diagnostics", "run_data_diagnostics.py"),
    PipelineStep("Run event studies", "run_event_study.py"),
    PipelineStep("Run event robustness checks", "run_event_robustness.py"),
    PipelineStep("Run panel regressions", "run_panel_regression.py"),
    PipelineStep("Run panel sample robustness", "run_panel_sample_robustness.py"),
    PipelineStep("Run quantile regressions", "run_quantile_regression.py"),
    PipelineStep("Run local projections", "run_local_projections.py"),
    PipelineStep("Run drawdown model", "run_drawdown_model.py"),
    PipelineStep("Build evidence summary", "run_evidence_summary.py"),
    PipelineStep("Run rolling GPR sensitivity", "run_rolling_sensitivity.py"),
    PipelineStep("Write results brief", "write_results_brief.py"),
    PipelineStep("Plot initial trends", "plot_initial_trends.py"),
]


def run_pipeline(
    project_root: Path,
    python_executable: str = sys.executable,
    *,
    refresh: bool = False,
) -> None:
    """Run the full reproducible MVP pipeline in dependency order."""
    scripts_dir = project_root / "scripts"

    for step in PIPELINE_STEPS:
        script_path = scripts_dir / step.script_name
        command = [python_executable, script_path]
        if refresh and step.accepts_refresh:
            command.append("--refresh")

        print(f"\n==> {step.label}", flush=True)
        subprocess.run(
            command,
            cwd=project_root,
            check=True,
        )
