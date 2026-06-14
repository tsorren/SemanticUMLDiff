#!/usr/bin/env python
import argparse
import os
import sys
from pathlib import Path

# Add src/ to PYTHONPATH programmatically
sys.path.insert(0, str(Path(__file__).parent / "src"))

if sys.platform.startswith("win"):
    # Reconfigure stdout/stderr to UTF-8 to prevent encoding errors on Windows when printing emojis
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from diff.complexity import calculate_complexity
from diff.compute import compute_diff
from domain.diff_models import DiffResult
from graph.reducer import reduce_graph
from integrations.plantuml import generate_png
from parser.plantuml_parser import PlantUMLParser
from render.puml_renderer import render_puml


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Semantic UML Diff - Compare two PlantUML files locally."
    )
    # Support positional arguments
    parser.add_argument(
        "base_pos",
        nargs="?",
        help="Path to the PlantUML file with new changes (base)"
    )
    parser.add_argument(
        "target_pos",
        nargs="?",
        help="Path to the PlantUML file with the old version (target)"
    )

    # Also support named arguments
    parser.add_argument(
        "-b", "--base",
        help="Path to the PlantUML file with new changes (base)"
    )
    parser.add_argument(
        "-t", "--target",
        help="Path to the PlantUML file with the old version (target)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Output directory to save results (default: output)"
    )
    parser.add_argument(
        "--plantuml-jar",
        default="plantuml.jar",
        help="Path to plantuml.jar (default: plantuml.jar)"
    )
    parser.add_argument(
        "--context-depth",
        type=int,
        default=1,
        help="Context depth for graph reduction (default: 1)"
    )
    parser.add_argument(
        "--render-style",
        default="default",
        choices=["default", "simple"],
        help="Render style (default: default)"
    )
    parser.add_argument(
        "--theme",
        default="modern",
        help="Theme name (default: modern)"
    )
    parser.add_argument(
        "--method-parameter-style",
        default="types_only",
        choices=["types_only", "full", "none"],
        help="Method parameter style (default: types_only)"
    )
    parser.add_argument(
        "--layout-orthogonal",
        action="store_true",
        help="Use orthogonal lines layout"
    )
    parser.add_argument(
        "--no-group-by-package",
        action="store_true",
        help="Disable grouping by package"
    )

    args = parser.parse_args()

    # Resolve base and target paths
    base_path_str = args.base or args.base_pos
    target_path_str = args.target or args.target_pos

    if not base_path_str or not target_path_str:
        parser.print_help()
        print("\nError: Both base (new changes) and target (old version) diagram paths must be specified.")
        sys.exit(1)

    base_path = Path(base_path_str)
    target_path = Path(target_path_str)

    if not base_path.exists():
        print(f"Error: Base file not found: {base_path}")
        sys.exit(1)
    if not target_path.exists():
        print(f"Error: Target file not found: {target_path}")
        sys.exit(1)

    # Read contents
    try:
        base_text = base_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading base file '{base_path}': {e}")
        sys.exit(1)

    try:
        target_text = target_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading target file '{target_path}': {e}")
        sys.exit(1)

    # Initialize parsers
    # Note: user says: "base" is the one with the new changes, "target" is the old one.
    # In our codebase:
    # - "base" parameter is the old version (baseline)
    # - "pr" parameter is the new version (with changes)
    # So we parse target as target_model (old) and base as base_model (new/pr).
    print(f"Parsing target (old): {target_path.name}")
    target_parser = PlantUMLParser(target_path.stem)
    target_model = target_parser.parse(target_text)

    print(f"Parsing base (new): {base_path.name}")
    base_parser = PlantUMLParser(base_path.stem)
    pr_model = base_parser.parse(base_text)

    # Compute Diff
    # base_model in compute_diff is target_model (old), pr_model is pr_model (new/base)
    print("Computing semantic diff...")
    diff = compute_diff(target_model, pr_model, "", args.method_parameter_style)

    # Calculate complexity
    score, level = calculate_complexity(diff)
    diff = DiffResult(
        module_name=diff.module_name,
        changes=diff.changes,
        complexity_score=score,
        complexity_level=level
    )

    # Print summary
    print("\n" + "=" * 45)
    print("           SEMANTIC UML DIFF SUMMARY")
    print("=" * 45)
    print(f"Module Name:      {diff.module_name}")
    print(f"Complexity Score: {diff.complexity_score}")
    print(f"Complexity Level: {diff.complexity_level}")
    print("-" * 45)

    if not diff.changes:
        print("No structural changes detected.")
    else:
        print(f"Detected {len(diff.changes)} structural change(s):")
        for ch in diff.changes:
            ctx_str = f" in {ch.context}" if ch.context else ""
            print(f"  - [{ch.change_type.value}] {ch.entity_type}: {ch.entity_name}{ctx_str}")

    print("=" * 45 + "\n")

    # Graph reduction
    spec = reduce_graph(target_model, pr_model, diff, args.context_depth)

    # Render PUML
    puml_text = render_puml(
        base=target_model,
        pr=pr_model,
        diff=diff,
        spec=spec,
        layout_orthogonal_lines=args.layout_orthogonal,
        method_parameter_style=args.method_parameter_style,
        group_by_package=not args.no_group_by_package,
        theme=args.theme,
        diagram_spacing=30,
        render_style=args.render_style
    )

    # Resolve output directory and paths
    output_dir = Path(args.output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{output_dir}': {e}")
        sys.exit(1)

    output_puml_path = output_dir / "diff.puml"
    output_png_path = output_dir / "diff.png"
    output_report_path = output_dir / "report.md"

    # Write output PUML
    try:
        output_puml_path.write_text(puml_text, encoding="utf-8")
        print(f"Saved diff PlantUML to: {output_puml_path}")
    except Exception as e:
        print(f"Error writing output PUML file '{output_puml_path}': {e}")
        sys.exit(1)

    # Generate PNG if plantuml.jar is available
    jar_path = args.plantuml_jar
    png_generated = False
    if os.path.exists(jar_path):
        print(f"Found {jar_path}. Generating PNG...")
        png_bytes = generate_png(puml_text, jar_path)
        if png_bytes:
            try:
                output_png_path.write_bytes(png_bytes)
                print(f"Saved diff PNG to: {output_png_path}")
                png_generated = True
            except Exception as e:
                print(f"Error writing output PNG file '{output_png_path}': {e}")
        else:
            print("Could not generate PNG (verify java is installed and plantuml.jar is valid).")
    else:
        print(f"plantuml.jar not found at '{jar_path}'. Skipping PNG generation.")

    # Document layer results in report.md
    changes_list_md = ""
    if not diff.changes:
        changes_list_md = "- No structural changes detected.\n"
    else:
        for ch in diff.changes:
            ctx_str = f" (in `{ch.context}`)" if ch.context else ""
            changes_list_md += f"- **{ch.change_type.value}** {ch.entity_type}: `{ch.entity_name}`{ctx_str}\n"

    png_status_md = "![diff.png](diff.png)" if png_generated else "*(Image generation skipped/failed)*"

    report_content = f"""# Semantic UML Diff Layer Report

## 1. Parser Layer
* **Target Model (Old Version)**:
  * Name: `{target_model.module_name}`
  * Total Classes: `{len(target_model.classes)}`
  * Total Relations: `{len(target_model.relations)}`
* **Base Model (New Changes)**:
  * Name: `{pr_model.module_name}`
  * Total Classes: `{len(pr_model.classes)}`
  * Total Relations: `{len(pr_model.relations)}`

## 2. Semantic Diff Layer
* **Complexity Score**: `{diff.complexity_score}`
* **Complexity Level**: `{diff.complexity_level}`
* **Detected Changes**: `{len(diff.changes)}` change(s)
{changes_list_md}
## 3. Graph Reduction Layer
* **Context Depth**: `{args.context_depth}`
* **Included Classes**: `{len(spec.included_nodes)}` class(es) retained in the reduced graph
* **Included Relations**: `{len(spec.included_edges)}` relation(s) retained in the reduced graph

## 4. Render Layer
* **Generated PlantUML**: [diff.puml](diff.puml)
* **Rendered Diagram Image**: {png_status_md}
"""

    try:
        output_report_path.write_text(report_content, encoding="utf-8")
        print(f"Saved layer report to: {output_report_path}")
    except Exception as e:
        print(f"Error writing report file '{output_report_path}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
