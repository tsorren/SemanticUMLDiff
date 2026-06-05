# GEMINI.md

## Project Overview

This repository implements a deterministic semantic UML diff system for GitHub Pull Requests.

The system:
- generates PlantUML from source code,
- parses PlantUML into a normalized semantic model,
- compares the current PR version against the base branch version,
- produces a reduced architectural diff visualization,
- and publishes the result to GitHub and Discord.

The primary goal is to help reviewers understand structural changes without noise.

---

## Product Goals

- Deterministic output for the same input.
- Semantic diff instead of textual diff.
- Reduced diagrams focused on changed areas.
- Clear PR feedback and Discord notifications.
- Simple local execution and CI/CD integration.
- Extensible architecture for future metrics and architectural analysis.

---

## Non-Goals

- Full PlantUML language support.
- Visual styling customization beyond what is needed for change highlighting.
- General-purpose UML editing.
- Runtime code generation from diagrams.
- Reverse-engineering every architecture smell from day one.

---

## Core Principles

1. **Determinism first**  
   All outputs must be stable. Given the same codebase and the same base branch, the generated model and rendered diff must be identical.

2. **Semantic comparison**  
   The system compares normalized UML models, never raw text as the source of truth.

3. **Noise reduction**  
   The final diagram should show only what changed and the minimum context needed to understand the change.

4. **Fail loudly, degrade gracefully**  
   If a module cannot be parsed, the system should report the issue and continue with the remaining modules when possible.

5. **Automation over manual steps**  
   The workflow must be friendly to GitHub Actions and automated PR review.

---

## Preferred Stack

- Python 3.12+
- `dataclasses` for immutable domain objects
- `typing` for explicit model contracts
- `networkx` for graph reduction and context selection
- `deepdiff` or custom structural comparison for normalized objects
- PlantUML CLI for rendering
- `pytest` for tests
- GitHub Actions for CI
- Discord webhooks for publication

---

## Reusable Tools and Libraries

### Existing UML generation
The repository already has an automatic PlantUML generator based on source code. That generator should be reused as the source of truth for the "current branch" diagram generation.

### Possible alternatives
If the current generator becomes too limited, a later alternative is to build a custom extractor using:
- the language AST parser,
- a stable serializer,
- and a controlled UML subset.

For Python specifically, future extensions could use:
- `ast` from the standard library,
- `networkx`,
- `pydot`,
- `subprocess` for PlantUML CLI,
- `pathlib` for deterministic file handling.

### Parsing strategy
The parser should use:
- controlled regexes for a supported PlantUML subset,
- strict normalization,
- canonical sorting,
- and explicit validation.

Avoid depending on the exact formatting of generated `.puml` files.

---

## Required Project Structure

A recommended layout:

```text
src/
  domain/
  parser/
  diff/
  render/
  integrations/
  cli/
tests/
docs/
.github/workflows/
```

Recommended file naming:
- `01-domain.md`
- `02-architecture.md`
- `03-workflow.md` later, if needed

---

## Deterministic Rules

The implementation must:
- sort classes, attributes, methods, and relations before serialization,
- avoid nondeterministic iteration over sets or dicts,
- avoid timestamps in output artifacts,
- use stable filenames,
- use stable graph traversal ordering,
- render the same model to the same output in repeated runs.

---

## GitHub Flow Integration

The workflow should:
1. detect changed modules,
2. generate or fetch PlantUML for base and PR branches,
3. compare models semantically,
4. create a reduced diff diagram,
5. upload artifacts,
6. post a PR comment,
7. post richer media to Discord.

If the PR only changes a subset of modules, only those modules should be analyzed and shown.

---

## Discord Integration

Discord should be used for richer visual feedback when the images would be large or multiple.

A Discord message should include:
- PR number,
- branch name,
- summary of changed entities,
- failed tests,
- image attachments or links.

---

## Acceptance Criteria

A change is acceptable when:
- output is deterministic,
- changed items are correctly identified,
- unchanged modules are omitted from the final diagram,
- and the CI workflow can run without manual intervention.

---

## Open Questions for Later Iterations

- Support for more UML element types.
- Renaming detection versus delete+add classification.
- Historical snapshot storage.
- Change metrics and impact analysis.
- Architecture trend reports.
