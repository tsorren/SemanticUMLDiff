from diff.compute import compute_diff
from domain.integration_models import IntegrationConfig
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


def run_integration_pipeline(
    base: UMLModel,
    pr: UMLModel,
    config: IntegrationConfig
) -> None:
    print(f"Processing module: {pr.module_name}")

    # 1. Compute Diff
    diff = compute_diff(base, pr)
    if not diff.changes:
        print("No changes detected. Skipping integration publishing.")
        return

    # 2. Graph Reduction
    spec = reduce_graph(base, pr, diff)

    # 3. Render PUML
    puml_text = render_puml(base, pr, diff, spec)

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

    # 6. Publish to GitHub
    if config.publish_github:
        gh_publisher = GitHubPublisher(
            config.github_token,
            config.github_repository,
            config.github_pr_number
        )
        gh_publisher.publish(diff, image_url)

    # 7. Publish to Discord
    if config.publish_discord:
        discord_publisher = DiscordPublisher(config.discord_webhook_url)
        discord_publisher.publish(diff, png_bytes)

    print("Integration pipeline completed.")
