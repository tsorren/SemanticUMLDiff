from typing import List, Optional

from diff.compute import compute_diff
from domain.integration_models import IntegrationConfig, ModuleResult
from domain.models import UMLModel
from graph.reducer import reduce_graph
from integrations.hosting import (
    DiscordUploader,
    ImageUploader,
    NullUploader,
    PlantUMLServerUploader,
)
from integrations.plantuml import generate_png
from integrations.publishers.discord import DiscordPublisher
from integrations.publishers.github import GitHubPublisher
from render.puml_renderer import render_puml


def process_module(
    base: UMLModel,
    pr: UMLModel,
    config: IntegrationConfig
) -> Optional[ModuleResult]:
    print(f"Processing module: {pr.module_name}")

    # 1. Compute Diff
    diff = compute_diff(base, pr, config.root_package)
    if not diff.changes:
        print("No changes detected. Skipping integration publishing.")
        return None

    # 2. Graph Reduction
    spec = reduce_graph(base, pr, diff, config.context_depth)

    # 3. Render PUML
    puml_text = render_puml(
        base,
        pr,
        diff,
        spec,
        layout_orthogonal_lines=config.layout_orthogonal_lines,
        method_parameter_style=config.method_parameter_style,
        group_by_package=config.group_by_package,
        theme=config.theme,
        diagram_spacing=config.diagram_spacing
    )

    # 4. Generate PNG locally if needed
    png_bytes = None
    if config.image_hosting_provider == "discord" or config.publish_discord:
        png_bytes = generate_png(puml_text, config.plantuml_jar_path)

    # 5. Image Hosting
    uploader: ImageUploader
    if config.image_hosting_provider == "discord":
        uploader = DiscordUploader(config.discord_webhook_url)
    elif config.image_hosting_provider == "plantuml_server":
        uploader = PlantUMLServerUploader()
    else:
        uploader = NullUploader()

    image_url = uploader.upload(puml_text, png_bytes)

    return ModuleResult(
        module_name=pr.module_name,
        diff=diff,
        puml_text=puml_text,
        png_bytes=png_bytes,
        image_url=image_url
    )

def publish_results(results: List[ModuleResult], config: IntegrationConfig) -> None:
    if not results:
        print("No modules with changes to publish.")
        return

    # 6. Publish to GitHub
    if config.publish_github:
        gh_publisher = GitHubPublisher(
            config.github_token,
            config.github_repository,
            config.github_pr_number
        )
        gh_publisher.publish(results)

    # 7. Publish to Discord
    if config.publish_discord:
        discord_publisher = DiscordPublisher(
            config.discord_webhook_url,
            config.github_repository,
            config.github_pr_number,
            config.github_head_ref
        )
        discord_publisher.publish(results)

    print("Integration pipeline completed.")
