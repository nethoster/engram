#!/usr/bin/env python3
"""Build a connected subgraph of male-cns:v1.0 via the neuPrint API (seed + BFS).

Requires your own neuPrint token:
    export NEUPRINT_APPLICATION_CREDENTIALS=<token>
(get one free at https://neuprint.janelia.org)

Writes:
  data/neurons.parquet  — body metadata
  data/edges.parquet    — bodyId_pre, bodyId_post, weight
  data/meta.json        — parameters and run statistics
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import pandas as pd
from neuprint import (
    Client,
    NeuronCriteria,
    fetch_adjacencies,
    fetch_neurons,
    fetch_simple_connections,
)

SERVER = "neuprint.janelia.org"
DATASET = "male-cns:v1.0"
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

NEURON_COLUMNS = [
    "bodyId",
    "type",
    "instance",
    "pre",
    "post",
    "size",
    "status",
    "rootSide",
]


def log(msg: str) -> None:
    print(msg, flush=True)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=int, default=2000, help="target neuron count")
    p.add_argument(
        "--seed-body",
        type=str,
        default=None,
        help="comma-separated bodyIds, e.g. 10001,10010",
    )
    p.add_argument(
        "--seed-type",
        type=str,
        default=None,
        help="take seeds from this type (top-N by post)",
    )
    p.add_argument(
        "--seed-n",
        type=int,
        default=10,
        help="number of seeds for auto/seed-type selection",
    )
    p.add_argument("--max-hops", type=int, default=10, help="BFS hop limit")
    p.add_argument(
        "--min-weight",
        type=int,
        default=1,
        help="minimum edge weight during traversal",
    )
    p.add_argument(
        "--batch",
        type=int,
        default=200,
        help="batch size for connectivity queries",
    )
    return p.parse_args()


def select_seeds(client: Client, args: argparse.Namespace) -> list[int]:
    if args.seed_body:
        seeds = [int(x) for x in args.seed_body.split(",") if x.strip()]
        log(f"seeds (explicit): {seeds}")
        return seeds

    criteria = NeuronCriteria(status="Traced")
    if args.seed_type:
        criteria = NeuronCriteria(type=args.seed_type, status="Traced")

    # Narrow columns: bodyId + post for ranking
    neurons, _ = fetch_neurons(
        criteria,
        returned_columns=["bodyId", "type", "post"],
        client=client,
    )
    if neurons.empty:
        raise SystemExit("no seed candidates found")

    neurons = neurons.dropna(subset=["post"]).sort_values("post", ascending=False)
    top = neurons.head(args.seed_n)
    seeds = [int(b) for b in top["bodyId"]]
    label = f"type={args.seed_type}" if args.seed_type else "top by post among Traced"
    log(f"seeds ({label}, n={len(seeds)}): {seeds}")
    return seeds


def frontier_connections(
    client: Client,
    frontier: list[int],
    min_weight: int,
    batch: int,
) -> pd.DataFrame:
    """All edges entering the frontier (pre->post), batched."""
    frames: list[pd.DataFrame] = []
    for i in range(0, len(frontier), batch):
        chunk = frontier[i : i + batch]
        crit = NeuronCriteria(bodyId=chunk)
        # Upstream + downstream, because BFS visits undirected
        for kwargs in ({"upstream_criteria": crit}, {"downstream_criteria": crit}):
            df = fetch_simple_connections(
                properties=[],
                weight_props=["weight"],
                min_weight=min_weight,
                client=client,
                **kwargs,
            )
            if df is None or df.empty:
                continue
            if "conn_roiInfo" in df.columns:
                df = df.drop(columns=["conn_roiInfo"])
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["bodyId_pre", "bodyId_post", "weight"])
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["bodyId_pre", "bodyId_post"])
    return out


def bfs(
    client: Client,
    seeds: list[int],
    target: int,
    max_hops: int,
    min_weight: int,
    batch: int,
) -> tuple[set[int], pd.DataFrame]:
    visited: set[int] = set(seeds)
    all_edges: dict[tuple[int, int], int] = {}
    frontier = list(seeds)
    hop = 0

    log(f"BFS: target={target}, max_hops={max_hops}")
    while len(visited) < target and hop < max_hops and frontier:
        hop += 1
        t0 = time.time()
        edges = frontier_connections(client, frontier, min_weight, batch)
        new_nodes: list[int] = []
        for pre, post, w in edges.itertuples(index=False):
            pre, post, w = int(pre), int(post), int(w)
            all_edges[(pre, post)] = max(all_edges.get((pre, post), 0), w)
            for n in (pre, post):
                if n not in visited:
                    # Trim on the fly: do not overshoot the target
                    if len(visited) >= target:
                        break
                    visited.add(n)
                    new_nodes.append(n)
            if len(visited) >= target:
                break

        log(
            f"  hop {hop}: frontier={len(frontier)} edges={len(edges)} "
            f"new={len(new_nodes)} total={len(visited)} ({time.time() - t0:.1f}s)"
        )
        frontier = new_nodes

    if len(visited) < target:
        log(f"  warning: only collected {len(visited)} < {target}")
    return visited, all_edges


def fetch_final(
    client: Client,
    visited: set[int],
    batch: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    body_ids = sorted(visited)

    log(f"fetch_neurons for {len(body_ids)} bodies...")
    neurons, _ = fetch_neurons(
        NeuronCriteria(bodyId=body_ids),
        returned_columns=NEURON_COLUMNS,
        client=client,
    )
    # The library may return extra columns (roiInfo etc.) — keep only what we need
    neurons = neurons.drop_duplicates(subset=["bodyId"])
    neurons = neurons[[c for c in NEURON_COLUMNS if c in neurons.columns]]
    neurons = neurons.reset_index(drop=True)

    log("fetch_adjacencies (internal edges, omit_rois)...")
    # batch_size inside fetch_adjacencies slices sources; targets = full set
    neurons_df, edges_df = fetch_adjacencies(
        sources=body_ids,
        targets=body_ids,
        omit_rois=True,
        weight_props=["weight"],
        properties=[],
        batch_size=batch,
        client=client,
    )
    # neurons_df from adjacencies may be wider — keep only our bodies
    keep = set(body_ids)
    edges_df = edges_df[
        edges_df["bodyId_pre"].isin(keep) & edges_df["bodyId_post"].isin(keep)
    ].reset_index(drop=True)

    return neurons, edges_df


def graph_report(neurons: pd.DataFrame, edges: pd.DataFrame) -> dict:
    g = nx.DiGraph()
    g.add_nodes_from(int(b) for b in neurons["bodyId"])
    g.add_edges_from(
        (int(p), int(q), {"weight": int(w)})
        for p, q, w in edges[["bodyId_pre", "bodyId_post", "weight"]].itertuples(
            index=False
        )
    )
    # Weak connectivity — sanity check that the subgraph is whole
    n_weak = nx.number_weakly_connected_components(g)
    largest = max((len(c) for c in nx.weakly_connected_components(g)), default=0)
    in_deg = [d for _, d in g.in_degree()]
    out_deg = [d for _, d in g.out_degree()]
    return {
        "n_nodes": g.number_of_nodes(),
        "n_edges": g.number_of_edges(),
        "weakly_connected_components": int(n_weak),
        "largest_wcc": int(largest),
        "isolated_nodes": sum(1 for n in g if g.degree(n) == 0),
        "mean_in_degree": float(sum(in_deg) / len(in_deg)) if in_deg else 0.0,
        "mean_out_degree": float(sum(out_deg) / len(out_deg)) if out_deg else 0.0,
        "density": float(nx.density(g)) if g.number_of_nodes() > 1 else 0.0,
    }


def main() -> int:
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    client = Client(SERVER, dataset=DATASET, progress=False)
    log(
        f"connected: {SERVER} / {DATASET} "
        f"(auth={client.fetch_profile()['AuthLevel']})"
    )

    seeds = select_seeds(client, args)
    visited, bfs_edges = bfs(
        client, seeds, args.target, args.max_hops, args.min_weight, args.batch
    )
    neurons, edges = fetch_final(client, visited, args.batch)
    report = graph_report(neurons, edges)

    neurons_path = DATA_DIR / "neurons.parquet"
    edges_path = DATA_DIR / "edges.parquet"
    meta_path = DATA_DIR / "meta.json"

    neurons.to_parquet(neurons_path, index=False)
    edges.to_parquet(edges_path, index=False)

    meta = {
        "server": SERVER,
        "dataset": DATASET,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "params": {
            "target": args.target,
            "seeds": seeds,
            "seed_type": args.seed_type,
            "seed_body": args.seed_body,
            "max_hops": args.max_hops,
            "min_weight": args.min_weight,
            "batch": args.batch,
        },
        "bfs_edges_seen": len(bfs_edges),
        "report": report,
        "files": {
            "neurons": str(neurons_path),
            "edges": str(edges_path),
        },
        "elapsed_sec": round(time.time() - t_start, 1),
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    log("")
    log(f"neurons: {len(neurons)} -> {neurons_path}")
    log(f"edges:   {len(edges)} -> {edges_path}")
    log(f"report:  {json.dumps(report, ensure_ascii=False)}")
    log(f"meta:    {meta_path}")
    log(f"elapsed: {meta['elapsed_sec']}s")

    # Quick sanity: edges only reference stored bodies
    ids = set(neurons["bodyId"].astype(int))
    dangling = (
        set(edges["bodyId_pre"].astype(int)) | set(edges["bodyId_post"].astype(int))
    ) - ids
    if dangling:
        log(f"ERROR: {len(dangling)} dangling bodyIds in edges")
        return 1
    if report["n_nodes"] < args.target * 0.95:
        log(f"ERROR: collected {report['n_nodes']} < 95% of target")
        return 1
    log("sanity: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
