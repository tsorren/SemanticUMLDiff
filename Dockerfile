FROM python:3.12-slim

# Install Java and Graphviz for PlantUML
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jre \
    graphviz \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download PlantUML
RUN wget https://github.com/plantuml/plantuml/releases/download/v1.2024.4/plantuml-1.2024.4.jar -O /opt/plantuml.jar

# Set up the Python project
WORKDIR /app

# Copy the pyproject.toml first to cache dependencies
COPY pyproject.toml ./
RUN pip install .

# Copy the source code
COPY src/ ./src/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
