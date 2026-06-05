import json
from typing import Optional

import requests

from domain.diff_models import ChangeType, DiffResult


class DiscordPublisher:
    def __init__(self, webhook_url: Optional[str]):
        self.webhook_url = webhook_url

    def publish(self, diff: DiffResult, png_bytes: Optional[bytes]) -> None:
        if not self.webhook_url:
            print("Discord webhook URL missing. Skipping Discord notification.")
            return

        added = sum(1 for c in diff.changes if c.change_type == ChangeType.ADDED)
        removed = sum(1 for c in diff.changes if c.change_type == ChangeType.REMOVED)
        modified = sum(1 for c in diff.changes if c.change_type == ChangeType.MODIFIED)

        embed = {
            "title": "🔍 Semantic UML Diff Complete",
            "color": 3447003, # Blue
            "fields": [
                {"name": "Module", "value": diff.module_name, "inline": True},
                {"name": "Changes", "value": f"🟢 {added} Added\n🔴 {removed} Removed\n🟡 {modified} Modified", "inline": True}
            ]
        }

        payload = {
            "embeds": [embed]
        }

        try:
            if png_bytes:
                # Attach image directly to embed
                embed["image"] = {"url": "attachment://diff.png"}
                files = {
                    "file": ("diff.png", png_bytes, "image/png")
                }
                # To send JSON payload alongside files in requests, we need to send it as `payload_json`
                data = {"payload_json": json.dumps(payload)}
                response = requests.post(self.webhook_url, data=data, files=files)
            else:
                response = requests.post(self.webhook_url, json=payload)

            response.raise_for_status()
            print("Successfully published to Discord.")
        except Exception as e:
            print(f"Error publishing to Discord: {e}")
