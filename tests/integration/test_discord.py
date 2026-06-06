from unittest.mock import MagicMock, patch

from domain.diff_models import DiffResult
from domain.integration_models import ModuleResult
from integrations.publishers.discord import DiscordPublisher


@patch("integrations.publishers.discord.requests.post")
def test_discord_chunking(mock_post: MagicMock) -> None:
    publisher = DiscordPublisher("http://fake")

    # 12 modules = 12 embeds + 1 summary embed = 13 embeds.
    # Should result in 2 chunks (first 10, next 3)
    results = [
        ModuleResult(
            module_name=f"module{i}",
            diff=DiffResult(f"module{i}", ()),
            puml_text="puml",
            png_bytes=b"png",
            image_url="url"
        ) for i in range(12)
    ]

    publisher.publish(results)

    assert mock_post.call_count == 2

    # First chunk: 1 summary embed + 9 module embeds = 10 embeds
    first_payload = mock_post.call_args_list[0][1]["data"]["payload_json"]
    import json
    first_data = json.loads(first_payload)
    assert len(first_data["embeds"]) == 10

    # Second chunk: 3 module embeds = 3 embeds
    second_payload = mock_post.call_args_list[1][1]["data"]["payload_json"]
    second_data = json.loads(second_payload)
    assert len(second_data["embeds"]) == 3
