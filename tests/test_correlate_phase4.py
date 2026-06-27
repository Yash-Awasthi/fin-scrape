"""Phase 4: correlation engine — per-detector tests vs the Appendix A formulas (offline)."""

import pytest

from server.correlate import (
    Cluster,
    Market,
    NewsItem,
    Prediction,
    analyze_correlations,
    cluster_news,
    detect_convergence,
    detect_flow_drop,
    detect_flow_price_divergence,
    detect_market,
    detect_prediction_leads_news,
    detect_triangulation,
    detect_velocity_spike,
    jaccard,
    round1,
    tokenize,
)


def _item(
    title, source_type="wire", ts=1000.0, source=None, link=None, lat=None, lon=None
):
    return NewsItem(
        title=title,
        link=link or title,
        source=source or source_type,
        source_type=source_type,
        timestamp=ts,
        lat=lat,
        lon=lon,
    )


def _cluster(members):
    """Build a Cluster directly so detector tests don't depend on clustering."""
    times = [m.timestamp for m in members]
    return Cluster(
        members=members,
        primary=members[0],
        first_seen=min(times),
        last_updated=max(times),
        lat=None,
        lon=None,
        threat=0.0,
    )


# --- primitives ---


def test_round1_half_up():
    assert round1(0.65) == 0.7  # banker's round() would give 0.6
    assert round1(0.85) == 0.9
    assert round1(2.0) == 2.0


def test_tokenize_drops_short_and_stopwords():
    assert tokenize("The OIL tanker, struck!") == {"oil", "tanker", "struck"}


def test_jaccard():
    assert jaccard(set(), set()) == 0.0
    assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)


# --- clustering ---


def test_cluster_groups_similar_and_separates_distinct():
    items = [
        _item("Oil tanker struck in Hormuz strait", ts=3000),
        _item("Tanker struck in Hormuz strait amid tension", ts=2000, source="b"),
        _item("Central bank holds interest rate steady", ts=1000, source="c"),
    ]
    clusters = cluster_news(items)
    sizes = sorted(len(c.members) for c in clusters)
    assert sizes == [1, 2]  # the two tanker stories cluster; rate story alone


def test_cluster_primary_lowest_tier():
    items = [
        _item(
            "Hormuz tanker incident reported",
            source_type="mainstream",
            ts=2000,
            source="m",
        ),
        _item(
            "Hormuz tanker incident reported now",
            source_type="wire",
            ts=1000,
            source="w",
        ),
    ]
    c = cluster_news(items)[0]
    assert c.primary.source_type == "wire"  # wire outranks mainstream


# --- detectors ---


def test_convergence_needs_three_types_within_window():
    base = 5000.0
    members = [
        _item("X", "wire", base),
        _item("X", "gov", base - 100, source="g"),
        _item("X", "intel", base - 200, source="i"),
    ]
    sig = detect_convergence(_cluster(members))
    assert sig and sig.confidence == pytest.approx(0.9)  # 0.6 + 0.1*3
    assert detect_convergence(_cluster(members[:2])) is None  # only two types


def test_triangulation_requires_wire_gov_intel():
    members = [
        _item("a", "wire"),
        _item("a", "gov", source="g"),
        _item("a", "intel", source="i"),
    ]
    sig = detect_triangulation(_cluster(members))
    assert sig and sig.confidence == 0.9
    assert detect_triangulation(_cluster([_item("a", "wire")])) is None


def test_flow_drop():
    members = [
        _item("Gas pipeline supply halt disrupts exports", "wire"),
        _item("Pipeline output cut", "gov", source="g"),
    ]
    sig = detect_flow_drop(_cluster(members))
    assert sig and sig.confidence == pytest.approx(min(0.9, 0.4 + 2 / 10))


def test_market_explained_vs_silent_vs_none():
    explained = detect_market(Market("XOM", 4.0), topic_mentions=0, entity_news=[1])
    assert explained.type == "explained_market_move"
    assert explained.confidence == pytest.approx(0.8)  # 0.5 + 0.1*1 + 4/20
    silent = detect_market(Market("XOM", 4.0), topic_mentions=0, entity_news=[])
    assert silent.type == "silent_divergence" and silent.confidence == pytest.approx(
        0.8
    )
    assert detect_market(Market("XOM", 4.0), topic_mentions=5, entity_news=[]) is None
    assert (
        detect_market(Market("XOM", 1.0), topic_mentions=0, entity_news=[]) is None
    )  # below 2


def test_flow_price_divergence():
    sig = detect_flow_price_divergence(
        Market("CL=F", 2.0), mentions=0, pipeline_signal_count=0
    )
    assert sig and sig.confidence == pytest.approx(0.65)  # 0.4 + 2/8
    assert (
        detect_flow_price_divergence(Market("CL=F", 2.0), 0, 1) is None
    )  # pipeline signal exists
    assert detect_flow_price_divergence(Market("CL=F", 1.0), 0, 0) is None  # below 1.5


def test_velocity_spike():
    assert detect_velocity_spike(
        "energy", velocity=9, baseline=1
    ).confidence == pytest.approx(0.9)
    assert detect_velocity_spike("energy", velocity=5, baseline=1) is None  # not > 6
    assert detect_velocity_spike("energy", velocity=9, baseline=5) is None  # not > 3x


def test_prediction_leads_news():
    sig = detect_prediction_leads_news(Prediction("CL=F", 10.0), related_activity=0)
    assert sig and sig.confidence == pytest.approx(0.9)
    assert (
        detect_prediction_leads_news(Prediction("CL=F", 10.0), related_activity=5)
        is None
    )


# --- orchestrator ---


def test_first_call_emits_nothing():
    items = [_item("Gas pipeline supply halt", "wire")]
    sigs, snap = analyze_correlations(items, prev_snapshot=None)
    assert sigs == [] and "topics" in snap


def test_second_call_emits_and_floors():
    base = 9000.0
    items = [
        _item("Oil pipeline supply halt in strait", "wire", base, source="w"),
        _item("Oil pipeline supply halt in strait", "gov", base - 10, source="g"),
        _item("Oil pipeline supply halt in strait", "intel", base - 20, source="i"),
    ]
    sigs, _ = analyze_correlations(items, prev_snapshot={"topics": {}})
    types = {s.type for s in sigs}
    # corroboration across wire+gov+intel within window -> convergence + triangulation
    assert "triangulation" in types and "convergence" in types
    assert all(s.confidence >= 0.6 for s in sigs)


def test_dedupe_via_seen_set():
    items = [
        _item("a", "wire"),
        _item("a", "gov", source="g"),
        _item("a", "intel", source="i"),
    ]
    seen: set[str] = set()
    analyze_correlations(items, prev_snapshot={"topics": {}}, seen=seen)
    # second run with the same seen set suppresses the already-emitted signals
    sigs2, _ = analyze_correlations(items, prev_snapshot={"topics": {}}, seen=seen)
    assert sigs2 == []
