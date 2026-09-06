"""Apriori vs FP-Growth frequent itemsets + association rules (mlxtend)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

from app.config import DATA_PATH, DEFAULT_MIN_CONFIDENCE, DEFAULT_MIN_SUPPORT


@dataclass
class MiningBenchmark:
    algorithm: str
    seconds: float
    n_itemsets: int
    peak_note: str


@dataclass
class MiningResult:
    baskets: list[list[str]]
    item_counts: dict[str, int]
    n_transactions: int
    rules: pd.DataFrame
    benchmarks: list[MiningBenchmark] = field(default_factory=list)
    one_hot_shape: tuple[int, int] = (0, 0)


def load_baskets(path=DATA_PATH) -> list[list[str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: python data/fetch_data.py from the project root."
        )
    df = pd.read_parquet(path)
    return [list(items) for items in df["items"].tolist()]


def to_one_hot(baskets: list[list[str]]) -> pd.DataFrame:
    te = TransactionEncoder()
    arr = te.fit(baskets).transform(baskets)
    return pd.DataFrame(arr, columns=te.columns_)


def mine_rules(
    baskets: list[list[str]] | None = None,
    min_support: float = DEFAULT_MIN_SUPPORT,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    primary: str = "fpgrowth",
) -> MiningResult:
    baskets = baskets or load_baskets()
    one_hot = to_one_hot(baskets)
    benchmarks: list[MiningBenchmark] = []

    # Benchmark both algorithms on the same matrix
    t0 = time.perf_counter()
    freq_apriori = apriori(one_hot, min_support=min_support, use_colnames=True)
    t_ap = time.perf_counter() - t0
    benchmarks.append(
        MiningBenchmark(
            algorithm="apriori",
            seconds=round(t_ap, 4),
            n_itemsets=len(freq_apriori),
            peak_note="Candidate generation; more RAM/CPU as item cardinality grows",
        )
    )

    t1 = time.perf_counter()
    freq_fp = fpgrowth(one_hot, min_support=min_support, use_colnames=True)
    t_fp = time.perf_counter() - t1
    benchmarks.append(
        MiningBenchmark(
            algorithm="fpgrowth",
            seconds=round(t_fp, 4),
            n_itemsets=len(freq_fp),
            peak_note="FP-tree compresses transactions; usually faster/leaner on sparse baskets",
        )
    )

    freq = freq_fp if primary == "fpgrowth" else freq_apriori
    if freq.empty:
        rules = pd.DataFrame(
            columns=[
                "antecedents",
                "consequents",
                "support",
                "confidence",
                "lift",
                "leverage",
                "conviction",
            ]
        )
    else:
        rules = association_rules(freq, metric="confidence", min_threshold=min_confidence)
        # Normalize frozensets to sorted tuples for JSON
        rules = rules.copy()
        rules["antecedents"] = rules["antecedents"].apply(lambda s: tuple(sorted(s)))
        rules["consequents"] = rules["consequents"].apply(lambda s: tuple(sorted(s)))

    item_counts: dict[str, int] = {}
    for basket in baskets:
        for item in basket:
            item_counts[item] = item_counts.get(item, 0) + 1

    return MiningResult(
        baskets=baskets,
        item_counts=item_counts,
        n_transactions=len(baskets),
        rules=rules,
        benchmarks=benchmarks,
        one_hot_shape=one_hot.shape,
    )


def filter_sort_rules(
    rules: pd.DataFrame,
    *,
    min_support: float | None = None,
    min_confidence: float | None = None,
    min_lift: float | None = None,
    sort_by: str = "lift",
    ascending: bool = False,
) -> pd.DataFrame:
    df = rules
    if df.empty:
        return df
    if min_support is not None:
        df = df[df["support"] >= min_support]
    if min_confidence is not None:
        df = df[df["confidence"] >= min_confidence]
    if min_lift is not None:
        df = df[df["lift"] >= min_lift]
    if sort_by not in df.columns:
        sort_by = "lift"
    return df.sort_values(sort_by, ascending=ascending)


def recommend_addons(
    rules: pd.DataFrame,
    basket: list[str],
    top_n: int = 8,
) -> list[dict]:
    """Score consequent items whose antecedents are subsets of the current basket."""
    if rules.empty or not basket:
        return []
    basket_set = set(basket)
    scores: dict[str, dict] = {}

    for row in rules.itertuples():
        ant = set(row.antecedents)
        cons = set(row.consequents)
        if not ant or not ant.issubset(basket_set):
            continue
        for item in cons:
            if item in basket_set:
                continue
            prev = scores.get(item)
            score = float(row.lift) * float(row.confidence)
            if prev is None or score > prev["score"]:
                scores[item] = {
                    "item": item,
                    "score": score,
                    "lift": float(row.lift),
                    "confidence": float(row.confidence),
                    "support": float(row.support),
                    "rule": {
                        "antecedents": list(row.antecedents),
                        "consequents": list(row.consequents),
                    },
                }

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:top_n]


def rules_to_graph(rules: pd.DataFrame, item_counts: dict[str, int], max_edges: int = 80) -> dict:
    """Items as nodes; each rule becomes directed edges from antecedent→consequent."""
    if rules.empty:
        return {"nodes": [], "edges": []}

    top = rules.sort_values("lift", ascending=False).head(max_edges)
    node_ids: set[str] = set()
    edges = []
    for row in top.itertuples():
        for a in row.antecedents:
            for c in row.consequents:
                node_ids.add(a)
                node_ids.add(c)
                edges.append(
                    {
                        "source": a,
                        "target": c,
                        "lift": round(float(row.lift), 4),
                        "confidence": round(float(row.confidence), 4),
                        "support": round(float(row.support), 4),
                    }
                )

    nodes = [
        {"id": item, "label": item, "count": int(item_counts.get(item, 0))}
        for item in sorted(node_ids)
    ]
    return {"nodes": nodes, "edges": edges}
