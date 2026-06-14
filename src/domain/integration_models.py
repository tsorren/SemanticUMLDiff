from dataclasses import dataclass
from typing import Optional

from domain.diff_models import DiffResult


@dataclass
class ModuleResult:
    module_name: str
    diff: DiffResult
    puml_text: str
    png_bytes: Optional[bytes]
    image_url: Optional[str]


@dataclass(frozen=True)
class IntegrationConfig:
    publish_github: bool = True
    publish_discord: bool = True
    image_hosting_provider: str = "discord"  # "discord", "plantuml_server", "none"
    plantuml_jar_path: str = "plantuml.jar"

    # GitHub Auth
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    github_pr_number: Optional[int] = None
    github_head_ref: Optional[str] = None

    # Discord Auth
    discord_webhook_url: Optional[str] = None

    # Rendering Config
    layout_orthogonal_lines: bool = False
    method_parameter_style: str = "types_only"
    group_by_package: bool = True
    theme: str = "modern"
    diagram_spacing: int = 30
    root_package: str = ""
    context_depth: int = 1
    render_style: str = "default"

