"""Load the local subgraph (parquet) into a networkx DiGraph."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import networkx as nx
import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=4)
def load_graph(data_dir: str | None = None) -> nx.DiGraph:
    d = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    neurons = pd.read_parquet(d / "neurons.parquet")
    edges = pd.read_parquet(d / "edges.parquet")

    g = nx.DiGraph()
    for row in neurons.itertuples(index=False):
        g.add_node(
            int(row.bodyId),
            type=getattr(row, "type", None),
            instance=getattr(row, "instance", None),
            pre=int(getattr(row, "pre", 0) or 0),
            post=int(getattr(row, "post", 0) or 0),
            size=int(getattr(row, "size", 0) or 0),
            status=getattr(row, "status", None),
        )
    for row in edges.itertuples(index=False):
        g.add_edge(int(row.bodyId_pre), int(row.bodyId_post), weight=int(row.weight))
    return g


def graph_stats(g: nx.DiGraph | None = None) -> dict:
    g = g or load_graph()
    return {
        "n_nodes": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "density": round(nx.density(g), 6),
        "weak_components": nx.number_weakly_connected_components(g),
        "avg_degree": round(
            sum(d for _, d in g.degree()) / max(g.number_of_nodes(), 1), 2
        ),
    }
