"""Graph tools exposed to the LLM: queries over the local subgraph."""

from __future__ import annotations

import json

import networkx as nx

from .loader import graph_stats, load_graph


def neuron_info(bodyId: int) -> str:
    g = load_graph()
    if bodyId not in g:
        return f"Neuron {bodyId} not found in the subgraph (2000 bodies)."
    d = g.nodes[bodyId]
    return json.dumps(
        {
            "bodyId": bodyId,
            "type": d.get("type"),
            "instance": d.get("instance"),
            "pre": d.get("pre"),
            "post": d.get("post"),
            "size": d.get("size"),
            "status": d.get("status"),
            "in_degree": g.in_degree(bodyId),
            "out_degree": g.out_degree(bodyId),
        },
        ensure_ascii=False,
    )


def neuron_connections(bodyId: int, top_n: int = 5) -> str:
    g = load_graph()
    if bodyId not in g:
        return f"Neuron {bodyId} not found."
    out_e = sorted(g.out_edges(bodyId, data=True), key=lambda x: -x[2]["weight"])[:top_n]
    in_e = sorted(g.in_edges(bodyId, data=True), key=lambda x: -x[2]["weight"])[:top_n]
    res = {
        "downstream": [
            {"to": v, "type": g.nodes[v].get("type"), "weight": d["weight"]}
            for _, v, d in out_e
        ],
        "upstream": [
            {"from": u, "type": g.nodes[u].get("type"), "weight": d["weight"]}
            for u, _, d in in_e
        ],
    }
    return json.dumps(res, ensure_ascii=False)


def find_by_type(type_name: str, limit: int = 20) -> str:
    g = load_graph()
    hits = [
        {
            "bodyId": n,
            "instance": d.get("instance"),
            "pre": d.get("pre"),
            "post": d.get("post"),
        }
        for n, d in g.nodes(data=True)
        if (d.get("type") or "").lower() == type_name.lower()
    ][:limit]
    if not hits:
        return f"Type '{type_name}' not found in the subgraph."
    return json.dumps(
        {"type": type_name, "count": len(hits), "neurons": hits}, ensure_ascii=False
    )


def shortest_path(a: int, b: int) -> str:
    g = load_graph()
    if a not in g or b not in g:
        missing = [x for x in (a, b) if x not in g]
        return f"Not found: {missing}"
    try:
        path = nx.shortest_path(g, a, b)
    except nx.NetworkXNoPath:
        return f"No path from {a} to {b} (different components)."
    total_w = sum(g.edges[path[i], path[i + 1]]["weight"] for i in range(len(path) - 1))
    return json.dumps(
        {"path": path, "hops": len(path) - 1, "total_weight": total_w},
        ensure_ascii=False,
    )


def hub_neurons(top_n: int = 10) -> str:
    g = load_graph()
    hubs = sorted(g.degree(), key=lambda x: -x[1])[:top_n]
    res = [
        {
            "bodyId": n,
            "degree": d,
            "type": g.nodes[n].get("type"),
            "instance": g.nodes[n].get("instance"),
        }
        for n, d in hubs
    ]
    return json.dumps(res, ensure_ascii=False)


def graph_summary() -> str:
    g = load_graph()
    stats = graph_stats(g)
    return json.dumps(stats, ensure_ascii=False)
