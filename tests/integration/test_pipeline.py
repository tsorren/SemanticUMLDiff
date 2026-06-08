from unittest.mock import MagicMock, patch

from domain.diff_models import DiffResult
from domain.integration_models import IntegrationConfig, ModuleResult
from domain.models import UMLClass, UMLModel
from pipeline import process_module, publish_results


@patch("pipeline.GitHubPublisher")
@patch("pipeline.DiscordPublisher")
def test_publish_results_aggregation(mock_discord: MagicMock, mock_github: MagicMock) -> None:
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


def test_process_module_calculates_complexity() -> None:
    c1 = UMLClass(name="User", kind="class")
    c2 = UMLClass(name="Order", kind="class")
    model1 = UMLModel(module_name="test", classes=(c1,))
    model2 = UMLModel(module_name="test", classes=(c1, c2))

    config = IntegrationConfig(
        publish_github=False,
        publish_discord=False,
        image_hosting_provider="none"
    )

    result = process_module(model1, model2, config)
    assert result is not None
    assert result.diff.complexity_score == 10
    assert result.diff.complexity_level == "Baja 🟢"

