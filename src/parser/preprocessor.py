import re
from typing import List


def preprocess(plantuml_text: str) -> List[str]:
    """
    Cleans PlantUML text by removing comments, empty lines, and extraneous whitespace.
    """
    # Remove block comments first
    text = re.sub(r"/'(.*?)'/", "", plantuml_text, flags=re.DOTALL)

    clean_lines = []
    for line in text.splitlines():
        line = line.strip()

        # Remove single line comments
        if line.startswith("'"):
            continue

        # Ignore empty lines
        if not line:
            continue

        # Ignore @startuml and @enduml
        if line in ("@startuml", "@enduml"):
            continue

        clean_lines.append(line)

    return clean_lines
