from typing import Dict, Set

import networkx as nx

from domain.diff_models import ChangeType, DiffResult
from domain.models import UMLModel, UMLRelation
from domain.render_models import RenderSpec


def reduce_graph(base: UMLModel, pr: UMLModel, diff: DiffResult, context_depth: int = 1) -> RenderSpec:
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
                highlight_dict[item.entity_name] = "added"
            elif item.change_type == ChangeType.REMOVED:
                highlight_dict[item.entity_name] = "removed"
            elif item.change_type == ChangeType.MODIFIED:
                if item.context == "moved":
                    highlight_dict[item.entity_name] = "moved"
                else:
                    highlight_dict[item.entity_name] = "modified"
        elif item.entity_type in ("attribute", "method"):
            seed_nodes.add(item.context)
            if item.context not in highlight_dict or highlight_dict[item.context] == "impacted":
                highlight_dict[item.context] = "modified"
        elif item.entity_type == "relation":
            parts = item.entity_name.split()
            if len(parts) >= 3:
                source = parts[0]
                target = parts[-1]
                seed_nodes.add(source)
                seed_nodes.add(target)
                if source not in highlight_dict:
                    highlight_dict[source] = "impacted"
                if target not in highlight_dict:
                    highlight_dict[target] = "impacted"

    # 3. Context Expansion (distance = context_depth)
    included_nodes: Set[str] = set(seed_nodes)

    if context_depth > 0:
        current_level = set(seed_nodes)
        for _ in range(context_depth):
            next_level = set()
            for seed in current_level:
                if seed in graph:
                    for neighbor in graph.neighbors(seed):
                        if neighbor not in included_nodes:
                            next_level.add(neighbor)
            included_nodes.update(next_level)
            current_level = next_level

    # Apply 'impacted' stereotype to context nodes
    for node in included_nodes:
        if node not in highlight_dict:
            highlight_dict[node] = "impacted"

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
