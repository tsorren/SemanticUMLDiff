import os
import sys
from pathlib import Path

from domain.integration_models import IntegrationConfig
from parser.plantuml_parser import PlantUMLParser
from pipeline import run_integration_pipeline


def main() -> None:
    # 1. Read Inputs
    base_dir_str = os.getenv("INPUT_BASE_UML_DIR")
    pr_dir_str = os.getenv("INPUT_PR_UML_DIR")
    
    if not base_dir_str or not pr_dir_str:
        print("Error: base_uml_dir and pr_uml_dir inputs are required.")
        sys.exit(1)
        
    base_dir = Path(base_dir_str)
    pr_dir = Path(pr_dir_str)
    
    # Extract PR number from GITHUB_REF (e.g., refs/pull/123/merge)
    gh_ref = os.getenv("GITHUB_REF", "")
    pr_num = None
    if "pull" in gh_ref:
        try:
            pr_num = int(gh_ref.split("/")[2])
        except Exception:
            print("Warning: Could not parse PR number from GITHUB_REF")
    
    # 2. Config
    config = IntegrationConfig(
        publish_github=os.getenv("PUBLISH_GITHUB", "true").lower() == "true",
        publish_discord=os.getenv("PUBLISH_DISCORD", "true").lower() == "true",
        image_hosting_provider=os.getenv("IMAGE_HOSTING_PROVIDER", "discord"),
        plantuml_jar_path=os.getenv("PLANTUML_JAR_PATH", "/app/plantuml.jar"),
        github_token=os.getenv("INPUT_GITHUB_TOKEN"),
        github_repository=os.getenv("GITHUB_REPOSITORY"),
        github_pr_number=pr_num,
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
        layout_orthogonal_lines=os.getenv("INPUT_LAYOUT_ORTHOGONAL_LINES", "false").lower() == "true",
        method_parameter_style=os.getenv("INPUT_METHOD_PARAMETER_STYLE", "types_only"),
        group_by_package=os.getenv("INPUT_GROUP_BY_PACKAGE", "true").lower() == "true"
    )
    
    # 3. Match modules
    pr_files = {f.name for f in pr_dir.glob("*.puml")} if pr_dir.exists() else set()
    base_files = {f.name for f in base_dir.glob("*.puml")} if base_dir.exists() else set()
    
    all_modules = pr_files.union(base_files)
    
    if not all_modules:
        print("No PlantUML files found in the specified directories.")
        sys.exit(0)
        
    # 4. Run pipeline
    for module_file in all_modules:
        module_name = module_file.replace(".puml", "")
        
        pr_file_path = pr_dir / module_file
        base_file_path = base_dir / module_file
        
        pr_text = pr_file_path.read_text(encoding="utf-8") if pr_file_path.exists() else ""
        base_text = base_file_path.read_text(encoding="utf-8") if base_file_path.exists() else ""
        
        try:
            pr_parser = PlantUMLParser(module_name)
            base_parser = PlantUMLParser(module_name)
            
            pr_model = pr_parser.parse(pr_text)
            base_model = base_parser.parse(base_text)
            
            run_integration_pipeline(base_model, pr_model, config)
        except Exception as e:
            print(f"Error processing module {module_name}: {e}")

if __name__ == "__main__":
    main()
