from typing import List, Optional

import requests

from domain.integration_models import ModuleResult

MARKER = "<!-- semantic-uml-diff-comment -->"


class GitHubPublisher:
    def __init__(self, token: Optional[str], repo: Optional[str], pr_number: Optional[int]):
        self.token = token
        self.repo = repo
        self.pr_number = pr_number
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def publish(self, results: List[ModuleResult]) -> None:
        if not self.token or not self.repo or not self.pr_number:
            print("GitHub configuration missing. Skipping PR comment.")
            return

        body = self._build_markdown(results)

        # 1. Search for existing comment
        api_url = f"https://api.github.com/repos/{self.repo}/issues/{self.pr_number}/comments"

        try:
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
            comments = response.json()

            existing_comment_id = None
            for c in comments:
                if MARKER in c.get("body", ""):
                    existing_comment_id = c["id"]
                    break

            if existing_comment_id:
                # Update existing comment
                patch_url = f"https://api.github.com/repos/{self.repo}/issues/comments/{existing_comment_id}"
                resp = requests.patch(patch_url, headers=self.headers, json={"body": body})
                resp.raise_for_status()
                print("Successfully updated existing GitHub PR comment.")
            else:
                # Create new comment
                resp = requests.post(api_url, headers=self.headers, json={"body": body})
                resp.raise_for_status()
                print("Successfully created new GitHub PR comment.")

        except Exception as e:
            print(f"Error publishing to GitHub: {e}")

    def _build_markdown(self, results: List[ModuleResult]) -> str:
        total_changes = sum(len(res.diff.changes) for res in results)
        lines = [
            MARKER,
            "## 🔍 Semantic UML Diff",
            f"**Total Modules Modified:** {len(results)}",
            f"**Total Changes:** {total_changes}",
            ""
        ]

        for res in results:
            lines.extend([
                f"### `{res.module_name}`",
            ])
            if res.diff.complexity_level is not None and res.diff.complexity_score is not None:
                lines.append(f"* **Complejidad Arquitectónica:** {res.diff.complexity_level} ({res.diff.complexity_score} puntos)")
            lines.extend([
                f"<details><summary>View Diagram ({len(res.diff.changes)} changes)</summary>",
                "",
            ])
            if res.image_url:
                lines.append(f"![Semantic Diff]({res.image_url})")
            else:
                lines.append("_No diagram image available._")
            lines.extend([
                "",
                "</details>",
                ""
            ])

        return "\n".join(lines)
