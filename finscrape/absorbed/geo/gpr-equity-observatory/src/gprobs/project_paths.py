from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))

    @property
    def data_raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def data_interim(self) -> Path:
        return self.root / "data" / "interim"

    @property
    def data_processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def data_metadata(self) -> Path:
        return self.root / "data" / "metadata"

    @property
    def reports_figures(self) -> Path:
        return self.root / "reports" / "figures"

    @property
    def reports_tables(self) -> Path:
        return self.root / "reports" / "tables"

    def ensure_output_dirs(self) -> None:
        for path in [
            self.data_processed,
            self.data_metadata,
            self.reports_figures,
            self.reports_tables,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_project_paths(root: Path | None = None) -> ProjectPaths:
    return ProjectPaths(root or project_root())
