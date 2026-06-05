FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends default-jre graphviz wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Download a stable version of PlantUML
RUN wget -q https://github.com/plantuml/plantuml/releases/download/v1.2024.4/plantuml-1.2024.4.jar -O /app/plantuml.jar

# Install Python dependencies natively
RUN pip install --no-cache-dir networkx==3.* requests==2.*

COPY src/ /app/src/

# Set Python Path so imports work
ENV PYTHONPATH="/app/src"

ENTRYPOINT ["python", "/app/src/main.py"]
