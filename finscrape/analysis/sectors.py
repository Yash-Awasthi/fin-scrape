"""One sector taxonomy for every surface that reads `events.sector_impact`.

The field is free text written by the analysis LLM: usually one lowercase token
("energy"), often a slash-joined pair ("energy/defense"), sometimes a name the
prompt never offered ("airlines", "agriculture"). Three places used to split and
alias it independently — the Postgres `/api/sectors` route, the SQLite serve
route, and the scenario engine — with two different separator sets, so the same
event could produce one bucket in the sector panel and two legs in a scenario.
"""

from __future__ import annotations

import re

# The eleven names the analysis prompt offers. Anything else is drift.
TAXONOMY = (
    "technology",
    "healthcare",
    "financials",
    "energy",
    "consumer",
    "industrials",
    "materials",
    "utilities",
    "real_estate",
    "communications",
    "other",
)

# NLP `_detect_sector` and the LLM disagree on a few names; alias them onto the
# taxonomy so the panels bucket them together. The second group is drift seen in
# real stored events — the prompt never offered these, and rows written before
# it was tightened still carry them.
ALIASES = {
    "finance": "financials",
    "industrial": "industrials",
    "defense": "industrials",
    "defence": "industrials",
    "aerospace": "industrials",
    "airlines": "industrials",
    "transport": "industrials",
    "transportation": "industrials",
    "agriculture": "materials",
    "commodities": "materials",
    "mining": "materials",
    "consumer_staples": "consumer",
    "consumer_discretionary": "consumer",
    "telecom": "communications",
    "telecommunications": "communications",
    "crypto": "financials",
    "banking": "financials",
    "banks": "financials",
}

# `;` and `|` appear rarely but the scenario engine always accepted them, and
# splitting on a separator one surface ignores is what made the two disagree.
_SEPARATORS = re.compile(r"[/,;|]")


def normalize(value: str | None) -> list[str]:
    """Split a raw `sector_impact` into aliased, lowercased sector names."""
    parts = (p.strip().lower() for p in _SEPARATORS.split(str(value or "")))
    return [ALIASES.get(p, p) for p in parts if p]
