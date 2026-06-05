from typing import Dict, Set

import networkx as nx

from domain.diff_models import ChangeType, DiffResult
from domain.models import UMLModel, UMLRelation
from domain.render_models import RenderSpec


def reduce_graph(base: UMLModel, pr: UMLModel, diff: DiffResult) -> RenderSpec:
    # 1. Build merged graph
    graph = nx.Graph()  # Undirected graph for context expansion

    # Add nodes and edges from base
    for c in base.classes:
        graph.add_node(c.name)
    for r in base.relations:
        graph.add_edge(r.source, r.target)

    # Add nodes and edges from pr
    for c in pr.classes:
        graph.add_node(c.name)
    for r in pr.relations:
        graph.add_edge(r.source, r.target)

    # 2. Identify Seed Nodes and highlight rules
    seed_nodes: Set[str] = set()
    highlight_dict: Dict[str, str] = {}

    for item in diff.changes:
        if item.entity_type == "class":
            seed_nodes.add(item.entity_name)
            if item.change_type == ChangeType.ADDED:
                highlight_dict[item.entity_name] = "green"
            elif item.change_type == ChangeType.REMOVED:
                highlight_dict[item.entity_name] = "red"
        elif item.entity_type in ("attribute", "method"):
            seed_nodes.add(item.context)
            if item.context not in highlight_dict:
                highlight_dict[item.context] = "yellow"
        elif item.entity_type == "relation":
            # the entity_name for relation is "Source relation_type Target"
            parts = item.entity_name.split()
            if len(parts) >= 3:
                source = parts[0]
                target = parts[-1]
                seed_nodes.add(source)
                seed_nodes.add(target)
                if source not in highlight_dict:
                    highlight_dict[source] = "yellow"
                if target not in highlight_dict:
                    highlight_dict[target] = "yellow"

    # 3. Context Expansion (distance = 1)
    included_nodes: Set[str] = set(seed_nodes)
    for seed in seed_nodes:
        if seed in graph:
            for neighbor in graph.neighbors(seed):
                included_nodes.add(neighbor)

    # 4. Edge Filtering
    included_edges: Set[UMLRelation] = set()
    all_relations = set(base.relations).union(set(pr.relations))

    for r in all_relations:
        if r.source in included_nodes and r.target in included_nodes:
            included_edges.add(r)

    # Convert rules to sorted tuple
    highlight_rules = tuple(sorted(highlight_dict.items()))
    sorted_nodes = tuple(sorted(included_nodes))
    sorted_edges = tuple(
        sorted(included_edges, key=lambda r: (r.source, r.target, r.relation_type))
    )

    return RenderSpec(
        included_nodes=sorted_nodes,
        highlight_rules=highlight_rules,
        included_edges=sorted_edges
    )
