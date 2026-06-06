from unittest.mock import patch

from domain.diff_models import DiffResult
from domain.integration_models import IntegrationConfig, ModuleResult
from pipeline import publish_results


@patch("pipeline.GitHubPublisher")
@patch("pipeline.DiscordPublisher")
def test_publish_results_aggregation(mock_discord, mock_github) -> None:
    github_instance = mock_github.return_value
    discord_instance = mock_discord.return_value

    config = IntegrationConfig(
        github_token="fake",
        github_repository="test/repo",
        github_pr_number=1,
        github_head_ref="feature-branch",
        discord_webhook_url="http://fake",
        publish_github=True,
        publish_discord=True
    )

    results = [
        ModuleResult(
            module_name="module1",
            diff=DiffResult("module1", ()),
            puml_text="puml1",
            png_bytes=b"png1",
            image_url="url1"
        )
    ]

    publish_results(results, config)

    github_instance.publish.assert_called_once()
    discord_instance.publish.assert_called_once()
