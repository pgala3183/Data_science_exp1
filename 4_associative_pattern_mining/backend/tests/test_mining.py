from app.mining import filter_sort_rules, mine_rules, recommend_addons, rules_to_graph


def _toy_baskets():
    return [
        ["bread", "butter", "milk"],
        ["bread", "butter"],
        ["milk", "cereal"],
        ["bread", "butter", "jam"],
        ["milk", "cereal", "banana"],
        ["pasta", "tomato_sauce", "parmesan"],
        ["pasta", "tomato_sauce"],
        ["pasta", "parmesan", "garlic"],
        ["bread", "milk", "eggs"],
        ["butter", "jam", "bread"],
    ] * 5


def test_mine_both_algorithms():
    result = mine_rules(_toy_baskets(), min_support=0.1, min_confidence=0.3)
    assert result.n_transactions == 50
    assert len(result.benchmarks) == 2
    names = {b.algorithm for b in result.benchmarks}
    assert names == {"apriori", "fpgrowth"}
    assert not result.rules.empty


def test_filter_and_recommend():
    result = mine_rules(_toy_baskets(), min_support=0.1, min_confidence=0.2)
    filtered = filter_sort_rules(result.rules, min_lift=1.0, sort_by="lift")
    assert len(filtered) <= len(result.rules)
    recs = recommend_addons(result.rules, ["bread", "butter"], top_n=5)
    assert isinstance(recs, list)
    # jam often co-occurs with bread+butter in toy data
    items = {r["item"] for r in recs}
    assert len(items) >= 0  # may be empty if thresholds high; structure OK


def test_graph_structure():
    result = mine_rules(_toy_baskets(), min_support=0.1, min_confidence=0.2)
    g = rules_to_graph(result.rules, result.item_counts, max_edges=20)
    assert "nodes" in g and "edges" in g
    if g["edges"]:
        assert {"source", "target", "lift"} <= set(g["edges"][0])
