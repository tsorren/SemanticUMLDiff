import base64
import zlib
from typing import Optional, Protocol

import requests


class ImageUploader(Protocol):
    def upload(self, puml_text: str, png_bytes: Optional[bytes]) -> Optional[str]:
        """Returns the public URL of the image, or None if failed/disabled."""
        ...


class DiscordUploader:
    def __init__(self, webhook_url: Optional[str]):
        self.webhook_url = webhook_url

    def upload(self, puml_text: str, png_bytes: Optional[bytes]) -> Optional[str]:
        if not self.webhook_url or not png_bytes:
            return None

        try:
            files = {
                "file": ("diff.png", png_bytes, "image/png")
            }
            payload = {"content": "Artifact from Semantic UML Diff"}

            url = self.webhook_url
            if "?" not in url:
                url += "?wait=true"
            elif "wait=true" not in url:
                url += "&wait=true"

            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()

            data = response.json()
            if "attachments" in data and len(data["attachments"]) > 0:
                return str(data["attachments"][0]["url"])
            return None
        except Exception as e:
            print(f"Error uploading to Discord CDN: {e}")
            return None


class PlantUMLServerUploader:
    def upload(self, puml_text: str, png_bytes: Optional[bytes]) -> Optional[str]:
        # Using Kroki as the standard stateless PlantUML server
        try:
            encoded = base64.urlsafe_b64encode(zlib.compress(puml_text.encode('utf-8'))).decode('utf-8')
            return f"https://kroki.io/plantuml/svg/{encoded}"
        except Exception:
            return None


class NullUploader:
    def upload(self, puml_text: str, png_bytes: Optional[bytes]) -> Optional[str]:
        return None
