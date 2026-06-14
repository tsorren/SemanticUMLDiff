import os
from pathlib import Path

import pytest

from diff.compute import compute_diff_deepdiff
from graph.reducer import reduce_graph
from parser.plantuml_parser import LarkPlantUMLParser
from render.puml_renderer import render_puml


def test_donaciones_puml_snapshot() -> None:
    # 1. Paths to files
    base_path = "information/modelo_tecnico.puml"
    pr_path = "fixtures/donaciones_pr_modelo_tecnico.puml"

    assert os.path.exists(base_path), f"Base file {base_path} not found"
    assert os.path.exists(pr_path), f"PR file {pr_path} not found"

    # 2. Read contents
    with open(base_path, "r", encoding="utf-8") as f:
        base_text = f.read()
    with open(pr_path, "r", encoding="utf-8") as f:
        pr_text = f.read()

    # 3. Parse models
    base_model = LarkPlantUMLParser("donaciones").parse(base_text)
    pr_model = LarkPlantUMLParser("donaciones").parse(pr_text)

    # 4. Compute diff
    diff = compute_diff_deepdiff(base_model, pr_model)

    # 5. Graph reduction
    spec = reduce_graph(base_model, pr_model, diff, context_depth=1)

    # 6. Render PUML
    puml_output = render_puml(
        base_model,
        pr_model,
        diff,
        spec,
        method_parameter_style="types_only",
        group_by_package=True
    )

    # 7. Snapshot assertion
    snapshot_path = Path("tests/integration/snapshots/donaciones_diff.puml")
    if not snapshot_path.exists():
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(puml_output, encoding="utf-8")
        pytest.skip("Snapshot creado por primera vez")

    expected = snapshot_path.read_text(encoding="utf-8")
    assert puml_output == expected, "El PUML generado difiere del snapshot"
