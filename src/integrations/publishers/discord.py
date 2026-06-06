import json
from typing import Optional

import requests

from domain.diff_models import ChangeType, DiffResult


class DiscordPublisher:
    def __init__(
        self, 
        webhook_url: Optional[str],
        repository: Optional[str] = None,
        pr_number: Optional[int] = None,
        head_ref: Optional[str] = None
    ):
        self.webhook_url = webhook_url
        self.repository = repository
        self.pr_number = pr_number
        self.head_ref = head_ref

    def publish(self, diff: DiffResult, png_bytes: Optional[bytes]) -> None:
        if not self.webhook_url:
            print("Discord webhook URL missing. Skipping Discord notification.")
            return

        added = sum(1 for c in diff.changes if c.change_type == ChangeType.ADDED)
        removed = sum(1 for c in diff.changes if c.change_type == ChangeType.REMOVED)
        modified = sum(1 for c in diff.changes if c.change_type == ChangeType.MODIFIED)

        title = "🔍 Semantic UML Diff Complete"
        if self.repository and self.pr_number:
            repo_name = self.repository.split('/')[-1] if '/' in self.repository else self.repository
            title = f"🔍 Semantic UML Diff: {repo_name}#PR-{self.pr_number}"

        description = []
        if self.head_ref:
            description.append(f"**Branch:** `{self.head_ref}`")
        description.append(f"**Component:** `{diff.module_name}`")

        embed = {
            "title": title,
            "description": "\n".join(description),
            "color": 3447003, # Blue
            "fields": [
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
