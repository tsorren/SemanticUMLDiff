# 02-architecture.md

## Architecture Specification

## Purpose

This document defines the software architecture for the deterministic semantic UML diff system and its integration into the GitHub PR workflow.

---

## Architectural Goals

- deterministic execution,
- semantic comparison of UML models,
- reduced change visualization,
- automated CI/CD integration,
- Discord publication,
- and maintainable modular Python code.

---

## High-Level Pipeline

1. Receive input PlantUML folders (`base_uml_dir` and `pr_uml_dir`).
2. Detect modules to analyze based on available PlantUML files.
3. Parse PlantUML into semantic models.
4. Normalize both models.
5. Compute semantic diff.
6. Reduce the graph to the changed area plus context.
7. Render the reduced diagram.
8. Publish results to GitHub and Discord.

---

## Proposed System Components

### 1. Module Detector
Identifies which repository modules changed in the PR based on provided diagram folders.

Responsibilities:
- list `.puml` files in base and PR folders,
- map files to module names,
- emit a stable module list for comparison.

### 2. UML Input Adapter
Connects the provided PlantUML folders to the rest of the system.

Responsibilities:
- read `.puml` files from `base_uml_dir` and `pr_uml_dir`,
- standardize input paths,
- handle missing files gracefully (e.g., added or removed modules).

### 3. PlantUML Parser
Transforms textual PlantUML into a semantic intermediate model.

Responsibilities:
- parse supported UML subset,
- normalize syntax differences,
- validate references,
- reject or warn on unsupported constructs.

Implementation note:
- start with controlled regexes and line-based parsing.
- do not parse the entire PlantUML language initially.

### 4. Semantic Model Layer
Contains the normalized in-memory representation.

Responsibilities:
- hold immutable model objects,
- enforce canonical ordering,
- support stable serialization.

### 5. Diff Engine
Compares the base model and the PR model.

Responsibilities:
- dynamically detect the `root_package` using Longest Common Prefix (LCP) and ignore external classes.
- detect added, removed, modified, unchanged items.
- apply heuristics to classify renamed/moved classes by comparing attribute and method intersections.
- compare classes, members, and relations,
- produce structured diff output.

### 6. Graph Reduction Engine
Selects the minimal useful subgraph for display.

Responsibilities:
- build dependency graphs,
- compute changed nodes,
- expand context based on `context_depth` parameter (e.g. 1 or 2 hops),
- produce a reduced render specification marking nodes as added, removed, modified, or impacted.

### 7. Diagram Renderer
Produces the final visual output.

Responsibilities:
- inject dynamic CSS `<style>` blocks for theming.
- convert reduced diff spec back to PlantUML using stereotypes (`<<added>>`, etc.),
- render PNG or SVG using a local `plantuml.jar` execution via subprocess,
- preserve deterministic ordering.

### 8. GitHub Publisher
Posts information back to the PR.

Responsibilities:
- upload artifacts,
- add or update PR comments,
- optionally add check run summaries.

### 9. Discord Publisher
Sends richer review media to a Discord channel.

Responsibilities:
- send message summaries,
- attach rendered images,
- include PR metadata and changelog summary.

---

## Recommended Internal Package Structure

```text
src/
  domain/
    models.py
    diff.py
    render.py
  parser/
    plantuml_parser.py
    normalization.py
    validators.py
  diff/
    semantic_diff.py
    rename_detection.py
  graph/
    graph_builder.py
    graph_reduction.py
  render/
    plantuml_builder.py
    plantuml_renderer.py
  integrations/
    github.py
    discord.py
  cli/
    main.py
tests/
```

---

## Data Flow

### Step 1: Module detection
The system produces a list of modules to compare from the available files in the input folders.

### Step 2: UML acquisition
For each module:
- load the base branch PlantUML from `base_uml_dir` (if present),
- load the PR branch PlantUML from `pr_uml_dir` (if present).

### Step 3: Parsing
Both inputs are parsed into semantic UML models.

### Step 4: Normalization
The models are normalized:
- sort members,
- sort relations,
- canonicalize names,
- remove formatting noise.

### Step 5: Diffing
The diff engine compares normalized models and produces a structured result.

### Step 6: Context selection
The graph reducer selects the impacted neighborhood.

### Step 7: Rendering
The renderer creates the final diagram image or SVG.

### Step 8: Publication
The result is published to GitHub and Discord.

---

## Determinism Rules

The system must ensure deterministic behavior by:
- sorting every collection before serialization,
- using stable module ordering,
- using canonical names,
- avoiding random IDs,
- avoiding timestamps in output,
- avoiding unordered set iteration,
- using explicit render order.

If graph traversal is used, traversal order must be stable and explicitly sorted.

---

## Rendering Strategy

### Recommended output format
Prefer SVG for local review and PNG for broad compatibility.

### Recommended coloring
- green: added
- red: removed
- yellow: modified
- gray: context

### Recommended views
- reduced diff view,
- side-by-side optional later,
- full diagram optional for archival artifacts.

---

## GitHub Integration Design

### Trigger
The GitHub Action is designed to be called within a larger workflow that runs on `pull_request` (or manually). It is packaged as a **Docker Container Action**.

### Action Inputs
- `base_uml_dir`: Path to the generated PlantUML diagrams for the base branch.
- `pr_uml_dir`: Path to the generated PlantUML diagrams for the PR branch.
- `github_token`: Token to post PR comments.

### Required permissions
- `contents: read`
- `pull-requests: write`

### Suggested jobs
- `detect-changes`
- `generate-uml`
- `semantic-diff`
- `render-diff`
- `publish-review`

### PR comment content
- summary of modified modules,
- list of semantic changes,
- link to artifacts,
- failed tests summary,
- optional image preview.
- **Sticky Update**: The Action will search for an existing comment it previously created (using a hidden HTML marker like `<!-- semantic-uml-diff-comment -->`) and update it, rather than spamming the PR with new comments.

## Technical Debt & Future Work

* **Rename Detection:** Currently, renaming a class, attribute, or method is processed as a `REMOVED` entity and a newly `ADDED` entity. This is a deliberate simplification for the MVP. The `DiffItem` and `ChangeType` enums are designed to be extensible so a `RENAMED` state can be cleanly added in future iterations when structural similarity heuristics are developed.

### Visualizing Differences
The final `.puml` artifact communicates differences through explicit colors and HTML markup:
- **Added Classes/Relations:** Highlighted in Green (`#D4EDDA`).
- **Removed Classes/Relations:** Highlighted in Red (`#F8D7DA`).
- **Modified Classes:** Highlighted in Yellow (`#FFF3CD`).
- **Modified Members (Attributes/Methods):** When a member's signature or type changes, both states are shown inside the class. The old state is crossed out in red (`<color:red><s:red>...</s></color>`), followed immediately by the new state in green (`<color:green>...</color>`). This explicit before/after representation is critical for code review clarity.

---

## Discord Integration Design

### Recommended approach
Use a Discord webhook for simplicity.

### Message format
- PR number,
- branch name,
- summary of changed classes/methods/relations,
- attached diff images.

### When to send
Only when the PR contains semantic changes or when tests fail.

---

## Suggested Algorithms

### Module reduction
Use available `.puml` files in the input directories to map to module names. **Convention: 1 `.puml` file represents 1 module** (e.g. `kernel.puml` = `kernel` module).

### Semantic comparison
Use canonical object comparison rather than text diff.

### Graph context selection
Use `networkx` to build a graph and compute:
- affected nodes,
- first-hop neighbors,
- subgraph boundaries.

### Rename detection
Optional later pass:
- compare similarity between removed and added entities,
- use stable heuristics only if they remain deterministic.

---

## Suggested Regex Strategy

The parser should use a small and explicit set of regexes.

Typical patterns to support:

- class declaration
- interface declaration
- enum declaration
- method signature
- attribute declaration
- relation declaration

Avoid regexes that attempt to support all PlantUML language features in one pass.

---

## Alternative UML Generation Approach

The repository expects the user to provide pre-generated PlantUML diagrams (e.g. from an existing automated pipeline). The GitHub Action purely consumes these diagrams.

---

## Testing Strategy

### Unit tests
- parser tests,
- normalization tests,
- diff tests,
- graph reduction tests,
- renderer determinism tests.

### Golden tests
Store expected output for:
- canonical PlantUML parse,
- known diff cases,
- reduced diagrams.

### Determinism tests
Run the same input twice and assert identical output.

### Integration tests
Test the full pipeline with:
- base branch sample,
- PR branch sample,
- publication output.

---

## Failure Handling

The system should classify errors as:
- parse error,
- unsupported construct,
- missing file,
- render failure,
- publish failure.

Behavior:
- keep going when possible,
- record warnings,
- fail the job only when a critical stage cannot complete.

---

## Observability

The system should emit structured logs with:
- module name,
- phase,
- status,
- warnings,
- duration,
- output paths.

Logs must remain deterministic in format even if values change.

---

## Security Considerations

- Do not execute untrusted generated code.
- Do not allow arbitrary shell input.
- Keep GitHub token permissions minimal.
- Use webhook secrets securely.
- Avoid leaking private repo structure in public messages.

---

## Future Extensions

- historical diff timeline,
- architecture drift metrics,
- coupling/cycle detection,
- rename inference,
- richer Markdown reports,
- multi-branch snapshot storage,
- code review annotations per changed entity.

---

## Architecture Acceptance Criteria

The architecture is acceptable when:
- the system is deterministic,
- the semantic diff is independent from raw formatting,
- only changed modules are processed,
- output is meaningful for code review,
- and the workflow can run unattended in GitHub Actions.

---

## 5. Integration Pipeline & Publishing

To provide immediate feedback in the code review process, the system implements a modular, extensible integration pipeline.

### Configurable Publishers
The pipeline executes based on environment configurations (`PUBLISH_GITHUB`, `PUBLISH_DISCORD`), allowing specific targets to be enabled or disabled gracefully:
1. **GitHub Publisher:** Searches for a sticky comment using a hidden markdown marker (`<!-- semantic-uml-diff-comment -->`). If found, it uses `PATCH` to update it (avoiding spam). Otherwise, it creates a new comment using `POST`.
2. **Discord Publisher:** Posts a rich embed (showing counts of added, removed, and modified elements) and directly attaches the generated diagram.

### Image Hosting & CDN Strategy (`IMAGE_HOSTING_PROVIDER`)
GitHub markdown does not allow embedding local files directly in issue comments via standard API calls; it requires a public URL (`![Diagram](https://...)`).
To solve this without demanding custom infrastructure:
- The system defines an `ImageUploader` Protocol.
- **`discord` (DiscordUploader):** By default, it uploads the physical `.png` file (generated locally via `plantuml.jar`) to a Discord webhook. It parses the response to extract the public `attachment.url` and passes this URL to the `GitHubPublisher`. This effectively uses Discord as a free CDN.
- **`plantuml_server` (PlantUMLServerUploader):** A fallback that completely skips file uploads by mathematically encoding the PlantUML string into a stateless Kroki/PlantUML URL.
- **Extensibility:** New uploaders (like Google Drive or AWS S3) can be trivially added by implementing the `upload(puml_text, png_bytes) -> str` method.
