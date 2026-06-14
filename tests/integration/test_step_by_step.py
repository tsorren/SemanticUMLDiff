from diff.compute import compute_diff_deepdiff
from domain.diff_models import ChangeType
from graph.reducer import reduce_graph
from parser.plantuml_parser import LarkPlantUMLParser
from render.puml_renderer import render_puml

BASE_PUML = """@startuml
package "org.domain.core" {
    class User {
        - id: String
        + username: String
        + getDetails(version: int): String
    }
    class Order {
        - orderId: String
        + total: double
    }
}
package "org.domain.billing" {
    class Payment {
        + paymentId: String
    }
}
org.domain.core.User "1" o-- "*" org.domain.core.Order : orders
org.domain.core.Order "1" *-- "1" org.domain.billing.Payment : payment
@enduml
"""

PR_PUML = """@startuml
package "org.domain.core" {
    class User {
        - id: String
        + username: String
        + getDetails(version: int, format: String): String
        + status: String
    }
}
package "org.domain.billing" {
    class Order {
        - orderId: String
        + total: double
    }
    class Payment {
        + paymentId: String
        + amount: double
    }
    class Invoice {
        + invoiceId: String
    }
}
org.domain.core.User "1" o-- "*" org.domain.billing.Order : orders
org.domain.billing.Order "1" *-- "1" org.domain.billing.Payment : payment
org.domain.billing.Order "1" *-- "1" org.domain.billing.Invoice : invoice
@enduml
"""

def test_pipeline_step_by_step() -> None:
    # -------------------------------------------------------------------------
    # Stage 1: Parser
    # -------------------------------------------------------------------------
    parser_base = LarkPlantUMLParser(module_name="core")
    model_base = parser_base.parse(BASE_PUML)

    parser_pr = LarkPlantUMLParser(module_name="core")
    model_pr = parser_pr.parse(PR_PUML)

    # Verify Base parsing
    class_names_base = {c.name for c in model_base.classes}
    assert "org.domain.core.User" in class_names_base
    assert "org.domain.core.Order" in class_names_base
    assert "org.domain.billing.Payment" in class_names_base

    user_base = next(c for c in model_base.classes if c.name == "org.domain.core.User")
    assert len(user_base.attributes) == 2
    assert any(a.name == "id" and a.type == "String" and a.visibility == "-" for a in user_base.attributes)
    assert any(a.name == "username" and a.type == "String" and a.visibility == "+" for a in user_base.attributes)
    assert len(user_base.methods) == 1
    assert user_base.methods[0].name == "getDetails"
    assert user_base.methods[0].parameters == ("version: int",)

    assert user_base.methods[0].return_type == "String"
    assert user_base.methods[0].visibility == "+"

    # Verify relations base
    assert len(model_base.relations) == 2
    rel1 = next(r for r in model_base.relations if r.relation_type == "aggregation")
    assert rel1.source == "org.domain.core.User"
    assert rel1.target == "org.domain.core.Order"
    assert rel1.multiplicity_source == "1"
    assert rel1.multiplicity_target == "*"
    assert rel1.label == "orders"

    # Verify PR parsing
    class_names_pr = {c.name for c in model_pr.classes}
    assert "org.domain.core.User" in class_names_pr
    assert "org.domain.billing.Order" in class_names_pr
    assert "org.domain.billing.Payment" in class_names_pr
    assert "org.domain.billing.Invoice" in class_names_pr

    user_pr = next(c for c in model_pr.classes if c.name == "org.domain.core.User")
    assert len(user_pr.attributes) == 3
    assert any(a.name == "status" and a.type == "String" and a.visibility == "+" for a in user_pr.attributes)
    assert len(user_pr.methods) == 1
    assert user_pr.methods[0].parameters == ("version: int", "format: String")


    # -------------------------------------------------------------------------
    # Stage 2: Serializer
    # -------------------------------------------------------------------------
    from diff.serializer import model_to_dict
    serialized_base = model_to_dict(model_base, method_parameter_style="names_and_types")
    serialized_pr = model_to_dict(model_pr, method_parameter_style="names_and_types")


    assert "org.domain.core.User" in serialized_base["classes"]
    assert "org.domain.billing.Payment" in serialized_pr["classes"]
    assert "label" in serialized_base["relations"]["org.domain.core.User aggregation org.domain.core.Order"]
    assert serialized_base["relations"]["org.domain.core.User aggregation org.domain.core.Order"]["label"] == "orders"

    # -------------------------------------------------------------------------
    # Stage 3: Diff Engine (including heuristics)
    # -------------------------------------------------------------------------
    diff = compute_diff_deepdiff(model_base, model_pr, method_parameter_style="names_and_types")

    # Assert changes
    class_changes = {d.entity_name: d for d in diff.changes if d.entity_type == "class"}
    # Invoice should be added
    assert "org.domain.billing.Invoice" in class_changes
    assert class_changes["org.domain.billing.Invoice"].change_type == ChangeType.ADDED

    # Order should be moved/modified
    # Note: org.domain.core.Order was removed, org.domain.billing.Order was added
    # Heuristics should detect it as modified with context="moved"
    assert "org.domain.billing.Order" in class_changes
    assert class_changes["org.domain.billing.Order"].change_type == ChangeType.MODIFIED
    assert class_changes["org.domain.billing.Order"].context == "moved"

    # Check member changes
    member_changes = {(d.context, d.entity_name): d for d in diff.changes if d.entity_type in ("attribute", "method")}
    # status added to User
    assert ("org.domain.core.User", "status") in member_changes
    assert member_changes[("org.domain.core.User", "status")].change_type == ChangeType.ADDED
    # getDetails modified in User
    assert ("org.domain.core.User", "getDetails(version: int,format: String)") in member_changes
    assert member_changes[("org.domain.core.User", "getDetails(version: int,format: String)")].change_type == ChangeType.MODIFIED


    # Check relation changes
    relation_changes = {d.entity_name: d for d in diff.changes if d.entity_type == "relation"}
    # Invoice relation added
    assert "org.domain.billing.Order composition org.domain.billing.Invoice" in relation_changes
    assert relation_changes["org.domain.billing.Order composition org.domain.billing.Invoice"].change_type == ChangeType.ADDED

    # -------------------------------------------------------------------------
    # Stage 4: Graph Reduction
    # -------------------------------------------------------------------------
    spec = reduce_graph(model_base, model_pr, diff, context_depth=1)

    # All classes should be included since they are all either modified, added, or 1-hop neighbors
    assert "org.domain.core.User" in spec.included_nodes
    assert "org.domain.billing.Order" in spec.included_nodes
    assert "org.domain.billing.Payment" in spec.included_nodes
    assert "org.domain.billing.Invoice" in spec.included_nodes

    # Verify highlight rules
    highlight_rules = dict(spec.highlight_rules)
    assert highlight_rules["org.domain.billing.Invoice"] == "added"
    assert highlight_rules["org.domain.billing.Order"] == "moved"
    assert highlight_rules["org.domain.core.User"] == "modified"
    assert highlight_rules["org.domain.billing.Payment"] == "modified"  # modified because attribute amount was added

    # -------------------------------------------------------------------------
    # Stage 5: Renderer
    # -------------------------------------------------------------------------
    puml = render_puml(model_base, model_pr, diff, spec, method_parameter_style="names_and_types")

    # Assert rendered class definitions with stereotypes
    assert 'class "User" as org.domain.core.User <<modified>>' in puml
    assert 'class "Order" as org.domain.billing.Order <<moved>>' in puml
    assert 'class "Payment" as org.domain.billing.Payment <<modified>>' in puml
    assert 'class "Invoice" as org.domain.billing.Invoice <<added>>' in puml

    # Assert rendered members within classes
    # status added to User: should be green
    assert '+ <color:green>status: String</color>' in puml
    # getDetails modified: should be orange
    assert '+ <color:orange>getDetails(version: int, format: String): String</color>' in puml
    # amount added to Payment: should be green
    assert '+ <color:green>amount: double</color>' in puml

    # Assert relationships rendered with multiplicities and labels
    assert 'org.domain.core.User "1" o-[#green]-- "*" org.domain.billing.Order : orders' in puml
    assert 'org.domain.core.User "1" o-[#red]-- "*" org.domain.core.Order : orders' in puml
    assert 'org.domain.billing.Order "1" *-[#green]-- "1" org.domain.billing.Payment : payment' in puml
    assert 'org.domain.core.Order "1" *-[#red]-- "1" org.domain.billing.Payment : payment' in puml
    # Added relation should be colored green
    assert 'org.domain.billing.Order "1" *-[#green]-- "1" org.domain.billing.Invoice : invoice' in puml


