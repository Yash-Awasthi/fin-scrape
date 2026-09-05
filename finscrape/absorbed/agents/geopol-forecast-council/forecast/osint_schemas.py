SIGNALS_PER_HORIZON = 5


def _source_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "url": {"type": "string"},
            "access_tier": {
                "type": "string",
                "enum": ["free", "paid", "freemium", "registration"],
            },
            "type": {"type": "string"},
            "language": {"type": "string"},
        },
        "required": ["name", "url", "access_tier", "type", "language"],
    }


def _signal_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "signal": {"type": "string"},
            "signal_class": {"type": "string"},
            "interpretation": {"type": "string"},
            "monitoring_strategy": {"type": "string"},
            "sources": {
                "type": "array",
                "minItems": 2,
                "maxItems": 5,
                "items": _source_schema(),
            },
            "rationale": {"type": "string"},
            "novelty_self_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": [
            "signal",
            "signal_class",
            "interpretation",
            "monitoring_strategy",
            "sources",
            "rationale",
            "novelty_self_score",
        ],
    }


def osint_member_schema(horizons: list[str], n_per_horizon: int = SIGNALS_PER_HORIZON) -> dict:
    props = {}
    for h in horizons:
        props[h] = {
            "type": "array",
            "minItems": n_per_horizon,
            "maxItems": n_per_horizon,
            "items": _signal_schema(),
        }
    return {
        "name": "osint_council_member_output",
        "schema": {
            "type": "object",
            "properties": {
                "signals": {
                    "type": "object",
                    "properties": props,
                    "required": list(horizons),
                },
                "overall_notes": {"type": "string"},
            },
            "required": ["signals"],
        },
    }
