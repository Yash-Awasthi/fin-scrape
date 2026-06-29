"""finscrape package.

Top-level names (FinScrapePipeline, FinEvent, Verdict) are exposed lazily via
PEP 562 __getattr__ so that importing a light submodule — e.g.
`finscrape.logging_config` or `finscrape.scrapers.world.feeds` — does NOT drag in
the full pipeline/engine (curl_cffi, lxml, scrapling). That keeps the lean API
image importable without the heavy scraper deps; `from finscrape import
FinScrapePipeline` still works for callers that want the brain.
"""

__version__ = "0.2.0"
__all__ = ["FinScrapePipeline", "FinEvent", "Verdict"]


def __getattr__(name: str):
    if name == "FinScrapePipeline":
        from finscrape.pipeline import FinScrapePipeline

        return FinScrapePipeline
    if name in ("FinEvent", "Verdict"):
        from finscrape.models.events import FinEvent, Verdict

        return {"FinEvent": FinEvent, "Verdict": Verdict}[name]
    raise AttributeError(f"module 'finscrape' has no attribute {name!r}")
