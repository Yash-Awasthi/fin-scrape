from pathlib import Path

from gprobs.data.datasets import dataset_output_filename
from gprobs.project_paths import ProjectPaths


def table_path(paths: ProjectPaths, filename: str, dataset: str) -> Path:
    return paths.reports_tables / dataset_output_filename(filename, dataset)


def figure_path(paths: ProjectPaths, filename: str, dataset: str) -> Path:
    return paths.reports_figures / dataset_output_filename(filename, dataset)


def report_path(paths: ProjectPaths, dataset: str) -> Path:
    return paths.root / "reports" / dataset_output_filename("main_report.pdf", dataset)
