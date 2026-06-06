from domain.diff_models import ChangeType, DiffItem, DiffResult
from domain.models import UMLAttribute, UMLClass, UMLModel, UMLRelation
from graph.reducer import reduce_graph


def test_reduce_graph_context_expansion() -> None:
    c_changed = UMLClass(name="A", kind="class", attributes=(UMLAttribute(name="id", type="int"),))
    c_neighbor = UMLClass(name="B", kind="class")
    c_distant = UMLClass(name="C", kind="class")

    rel1 = UMLRelation(source="A", target="B", relation_type="association")
    rel2 = UMLRelation(source="B", target="C", relation_type="association")

    base_model = UMLModel(
        module_name="test",
        classes=(c_changed, c_neighbor, c_distant),
        relations=(rel1, rel2)
    )
    pr_model = UMLModel(
        module_name="test",
        classes=(c_changed, c_neighbor, c_distant),
        relations=(rel1, rel2)
    )

    diff = DiffResult(
        module_name="test",
        changes=(
            DiffItem(
                entity_type="attribute",
                entity_name="id",
                change_type=ChangeType.MODIFIED,
                context="A"
            ),
        )
    )

    spec = reduce_graph(base_model, pr_model, diff)

    # A is seed. B is neighbor. C is distant.
    assert "A" in spec.included_nodes
    assert "B" in spec.included_nodes
    assert "C" not in spec.included_nodes

    # Check highlight
    assert ("A", "modified") in spec.highlight_rules
    assert ("B", "impacted") in spec.highlight_rules

    # Check edges
    assert len(spec.included_edges) == 1
    assert spec.included_edges[0].source == "A"
    assert spec.included_edges[0].target == "B"
