"""Build a directed account graph from a non-synthetic banking CSV when entity IDs exist.

Required columns by default: source_account,destination_account. Optional amount column.
This utility intentionally refuses datasets without real entity relationship columns;
it does not invent accounts or edges.
"""
import argparse, json
from pathlib import Path
import pandas as pd
import networkx as nx

def build(csv_path: Path, output_path: Path, source_col: str = "source_account", destination_col: str = "destination_account", amount_col: str = "amount") -> dict:
    df = pd.read_csv(csv_path)
    missing = [c for c in (source_col, destination_col) if c not in df.columns]
    if missing:
        raise ValueError(f"Cannot construct account graph: missing entity columns {missing}. Do not infer or fabricate relationships.")
    df = df.dropna(subset=[source_col, destination_col]).copy()
    g = nx.DiGraph()
    for row in df.itertuples(index=False):
        d = row._asdict()
        src, dst = str(d[source_col]), str(d[destination_col])
        if src == dst: continue
        attrs = {}
        if amount_col in d:
            try: attrs["amount"] = float(d[amount_col])
            except (TypeError, ValueError): pass
        if g.has_edge(src, dst):
            g[src][dst]["transaction_count"] += 1
            if "amount" in attrs: g[src][dst]["amount_sum"] += attrs["amount"]
        else:
            attrs["transaction_count"] = 1
            if "amount" in attrs: attrs["amount_sum"] = attrs.pop("amount")
            g.add_edge(src, dst, **attrs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nodes = [{"account_id": str(n), "in_degree": int(g.in_degree(n)), "out_degree": int(g.out_degree(n))} for n in g.nodes]
    edges = [{"source_account": str(u), "destination_account": str(v), **d} for u,v,d in g.edges(data=True)]
    result = {"source_file": csv_path.name, "nodes": len(nodes), "directed_edges": len(edges), "account_features": nodes, "edges": edges,
      "warning": "Graph relationships are descriptive signals and are not proof of wrongdoing."}
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return {"nodes": len(nodes), "directed_edges": len(edges), "output": str(output_path)}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("csv", type=Path); p.add_argument("--output", type=Path, default=Path("artifacts/banking_graph.json")); p.add_argument("--source-col", default="source_account"); p.add_argument("--destination-col", default="destination_account"); p.add_argument("--amount-col", default="amount")
    a = p.parse_args(); print(json.dumps(build(a.csv, a.output, a.source_col, a.destination_col, a.amount_col), indent=2))
