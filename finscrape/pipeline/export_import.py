"""
Data Export/Import Pipeline — exports scraped data in multiple formats,
supports batch import, and provides data transformation utilities.
"""

import csv
import json
import io
from datetime import datetime
from typing import Any


class DataPipeline:
    """Export and import scraped data in multiple formats."""

    def __init__(self):
        self.transformers: list = []

    def export_json(self, data: list[dict], pretty: bool = True) -> str:
        """Export data as JSON string."""
        return json.dumps(
            data,
            indent=2 if pretty else None,
            default=str,
            ensure_ascii=False,
        )

    def export_csv(self, data: list[dict], delimiter: str = ",") -> str:
        """Export data as CSV string."""
        if not data:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=data[0].keys(), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue()

    def export_ndjson(self, data: list[dict]) -> str:
        """Export data as newline-delimited JSON (NDJSON)."""
        return "\n".join(json.dumps(row, default=str) for row in data)

    def import_json(self, raw: str) -> list[dict]:
        """Import data from JSON string."""
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return [parsed]

    def import_csv(self, raw: str, delimiter: str = ",") -> list[dict]:
        """Import data from CSV string."""
        reader = csv.DictReader(io.StringIO(raw), delimiter=delimiter)
        return [row for row in reader]

    def import_ndjson(self, raw: str) -> list[dict]:
        """Import NDJSON string."""
        return [json.loads(line) for line in raw.strip().split("\n") if line.strip()]

    def add_transformer(self, fn):
        """Register a data transformer function."""
        self.transformers.append(fn)
        return self

    def transform(self, data: list[dict]) -> list[dict]:
        """Apply all registered transformers to the data."""
        result = data
        for fn in self.transformers:
            result = [fn(row) for row in result]
        return result

    def filter_by_date(
        self, data: list[dict], field: str, after: str | None = None, before: str | None = None
    ) -> list[dict]:
        """Filter data by date field."""
        result = []
        for row in data:
            val = row.get(field)
            if val is None:
                continue
            dt = datetime.fromisoformat(str(val))
            if after and dt < datetime.fromisoformat(after):
                continue
            if before and dt > datetime.fromisoformat(before):
                continue
            result.append(row)
        return result

    def aggregate(self, data: list[dict], group_by: str, agg_field: str, agg_fn: str = "sum") -> dict:
        """Aggregate data by grouping field."""
        groups: dict[str, list] = {}
        for row in data:
            key = str(row.get(group_by, "unknown"))
            groups.setdefault(key, []).append(row.get(agg_field, 0))

        result = {}
        for key, values in groups.items():
            numeric = [v for v in values if isinstance(v, (int, float))]
            if agg_fn == "sum":
                result[key] = sum(numeric)
            elif agg_fn == "avg":
                result[key] = sum(numeric) / max(len(numeric), 1)
            elif agg_fn == "min":
                result[key] = min(numeric) if numeric else 0
            elif agg_fn == "max":
                result[key] = max(numeric) if numeric else 0
            elif agg_fn == "count":
                result[key] = len(values)
        return result

    def summary(self, data: list[dict]) -> dict:
        """Generate summary statistics for a dataset."""
        if not data:
            return {"rows": 0, "columns": 0}

        all_keys = set()
        for row in data:
            all_keys.update(row.keys())

        stats = {"rows": len(data), "columns": len(all_keys), "fields": {}}
        for key in all_keys:
            values = [row.get(key) for row in data if key in row]
            numeric = [v for v in values if isinstance(v, (int, float))]
            field_stats: dict[str, Any] = {"count": len(values), "nulls": len(data) - len(values)}
            if numeric:
                field_stats["type"] = "numeric"
                field_stats["min"] = min(numeric)
                field_stats["max"] = max(numeric)
                field_stats["avg"] = sum(numeric) / len(numeric)
            else:
                field_stats["type"] = "text"
                unique = set(str(v) for v in values)
                field_stats["unique"] = len(unique)
                if unique:
                    field_stats["sample"] = list(unique)[:5]
            stats["fields"][key] = field_stats

        return stats
