import subprocess
import sys
from pathlib import Path


def test_run_script_e2e_positional(tmp_path: Path) -> None:
    # base_puml is the old version (User only has id)
    base_puml = tmp_path / "old.puml"
    base_puml.write_text("""@startuml
class User {
    + id: int
}
@enduml
""", encoding="utf-8")

    # pr_puml is the new version (User has id and name)
    pr_puml = tmp_path / "new.puml"
    pr_puml.write_text("""@startuml
class User {
    + id: int
    + name: String
}
@enduml
""", encoding="utf-8")

    output_dir = tmp_path / "my_output"
    run_py_path = Path(__file__).parents[2] / "run.py"

    # User terminology: base is the new changes, target is the old version
    # So: base_pos = new.puml, target_pos = old.puml
    cmd = [
        sys.executable,
        str(run_py_path),
        str(pr_puml),   # first argument: new changes (base)
        str(base_puml),  # second argument: old version (target)
        "-o", str(output_dir),
        "--plantuml-jar", "nonexistent.jar"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.returncode == 0
    assert "SEMANTIC UML DIFF SUMMARY" in result.stdout
    assert "ADDED" in result.stdout
    assert "attribute: name" in result.stdout

    assert (output_dir / "diff.puml").exists()
    assert (output_dir / "report.md").exists()

    puml_content = (output_dir / "diff.puml").read_text(encoding="utf-8")
    assert "@startuml" in puml_content
    assert "User" in puml_content

    report_content = (output_dir / "report.md").read_text(encoding="utf-8")
    assert "## 1. Parser Layer" in report_content
    assert "## 2. Semantic Diff Layer" in report_content
    assert "## 3. Graph Reduction Layer" in report_content
    assert "## 4. Render Layer" in report_content
    assert "Total Classes: `1`" in report_content
    assert "**Detected Changes**: `1`" in report_content
    assert "retained in the reduced graph" in report_content


def test_run_script_e2e_named(tmp_path: Path) -> None:
    # base_puml is the old version (User only has id)
    base_puml = tmp_path / "old.puml"
    base_puml.write_text("""@startuml
class User {
    + id: int
}
@enduml
""", encoding="utf-8")

    # pr_puml is the new version (User has id and name)
    pr_puml = tmp_path / "new.puml"
    pr_puml.write_text("""@startuml
class User {
    + id: int
    + name: String
}
@enduml
""", encoding="utf-8")

    output_dir = tmp_path / "my_output"
    run_py_path = Path(__file__).parents[2] / "run.py"

    cmd = [
        sys.executable,
        str(run_py_path),
        "--base", str(pr_puml),
        "--target", str(base_puml),
        "-o", str(output_dir),
        "--plantuml-jar", "nonexistent.jar"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0
    assert "SEMANTIC UML DIFF SUMMARY" in result.stdout
    assert "ADDED" in result.stdout
    assert "attribute: name" in result.stdout
    assert (output_dir / "diff.puml").exists()
    assert (output_dir / "report.md").exists()


def test_run_script_missing_args() -> None:
    run_py_path = Path(__file__).parents[2] / "run.py"
    cmd = [
        sys.executable,
        str(run_py_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1
    assert "Error: Both base (new changes) and target (old version) diagram paths must be specified." in result.stdout


def test_run_script_e2e_simple_render(tmp_path: Path) -> None:
    base_puml = tmp_path / "old.puml"
    base_puml.write_text("""@startuml
class User {
    + id: int
}
@enduml
""", encoding="utf-8")

    pr_puml = tmp_path / "new.puml"
    pr_puml.write_text("""@startuml
class User {
    + id: int
    + name: String
}
@enduml
""", encoding="utf-8")

    output_dir = tmp_path / "my_output_simple"
    run_py_path = Path(__file__).parents[2] / "run.py"

    cmd = [
        sys.executable,
        str(run_py_path),
        "--base", str(pr_puml),
        "--target", str(base_puml),
        "-o", str(output_dir),
        "--render-style", "simple",
        "--plantuml-jar", "nonexistent.jar"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0
    assert (output_dir / "diff.puml").exists()
    assert (output_dir / "report.md").exists()

    puml_content = (output_dir / "diff.puml").read_text(encoding="utf-8")
    assert 'package "' not in puml_content
