import json
from typing import List, Optional

import requests

from domain.diff_models import ChangeType
from domain.integration_models import ModuleResult


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

    def publish(self, results: List[ModuleResult]) -> None:
        if not self.webhook_url:
            print("Discord webhook URL missing. Skipping Discord notification.")
            return

        title = "🔍 Semantic UML Diff Complete"
        if self.repository and self.pr_number:
            repo_name = self.repository.split('/')[-1] if '/' in self.repository else self.repository
            title = f"🔍 Semantic UML Diff: {repo_name}#PR-{self.pr_number}"

        description = []
        if self.head_ref:
            description.append(f"**Branch:** `{self.head_ref}`")
        description.append(f"**Modules Modified:** {len(results)}")

        # Calculate totals
        total_added = sum(sum(1 for c in res.diff.changes if c.change_type == ChangeType.ADDED) for res in results)
        total_removed = sum(sum(1 for c in res.diff.changes if c.change_type == ChangeType.REMOVED) for res in results)
        total_modified = sum(sum(1 for c in res.diff.changes if c.change_type == ChangeType.MODIFIED) for res in results)

        summary_embed = {
            "title": title,
            "description": "\n".join(description),
            "color": 3447003, # Blue
            "fields": [
                {"name": "Total Changes", "value": f"🟢 {total_added} Added\n🔴 {total_removed} Removed\n🟡 {total_modified} Modified", "inline": True}
            ]
        }

        embeds = [summary_embed]
        files = {}

        for i, res in enumerate(results):
            added = sum(1 for c in res.diff.changes if c.change_type == ChangeType.ADDED)
            removed = sum(1 for c in res.diff.changes if c.change_type == ChangeType.REMOVED)
            modified = sum(1 for c in res.diff.changes if c.change_type == ChangeType.MODIFIED)

            filename = f"diff_{i}.png"
            module_embed = {
                "title": f"Module: {res.module_name}",
                "color": 3447003,
                "fields": [
                    {"name": "Changes", "value": f"🟢 {added} Added\n🔴 {removed} Removed\n🟡 {modified} Modified", "inline": True}
                ]
            }
            if res.png_bytes:
                module_embed["image"] = {"url": f"attachment://{filename}"}
                files[f"file{i}"] = (filename, res.png_bytes, "image/png")

            embeds.append(module_embed)

        # Chunk into messages if > 10 embeds (Discord limit is 10 embeds per message)
        chunk_size = 10
        for i in range(0, len(embeds), chunk_size):
            chunk_embeds = embeds[i:i+chunk_size]

            # Filter files to only include those referenced in the chunk
            chunk_files = {}
            for emb in chunk_embeds:
                if "image" in emb:
                    img_filename = emb["image"]["url"].replace("attachment://", "")
                    for k, v in files.items():
                        if v[0] == img_filename:
                            chunk_files[k] = v

            payload = {"embeds": chunk_embeds}

            try:
                if chunk_files:
                    data = {"payload_json": json.dumps(payload)}
                    response = requests.post(self.webhook_url, data=data, files=chunk_files)
                else:
                    response = requests.post(self.webhook_url, json=payload)

                response.raise_for_status()
                print(f"Successfully published to Discord (chunk {i//chunk_size + 1}).")
            except Exception as e:
                print(f"Error publishing to Discord (chunk {i//chunk_size + 1}): {e}")
