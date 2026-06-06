import subprocess
from typing import Optional


def generate_png(puml_text: str, jar_path: str) -> Optional[bytes]:
    """Generates a PNG image from PlantUML text using the local JAR."""
    try:
        # Run plantuml.jar reading from stdin and outputting to stdout (-pipe)
        process = subprocess.run(
            ["java", "-DPLANTUML_LIMIT_SIZE=8192", "-jar", jar_path, "-pipe", "-tpng"],
            input=puml_text.encode("utf-8"),
            capture_output=True,
            check=True
        )
        return process.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error generating PNG locally: {e}")
        return None
