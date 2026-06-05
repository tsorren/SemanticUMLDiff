from dataclasses import dataclass
from typing import Optional


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

    # Discord Auth
    discord_webhook_url: Optional[str] = None
