# Semantic UML Diff GitHub Action

This GitHub Action performs a deterministic, semantic structural comparison between two sets of PlantUML diagrams and generates reduced visual diffs. It is designed to be used in Pull Requests to help reviewers quickly understand architectural and structural changes without the noise of textual diffs.

## Features

- **Semantic comparison**: Compares actual UML models, not raw text.
- **Noise reduction**: Shows only what changed and the minimal required context.
- **Deterministic**: Guarantees identical output for identical inputs.
- **PR Feedback**: Automatically posts diagrams to the Pull Request.

## Usage

This action assumes that you have already generated `.puml` files for both your base branch and your PR branch in earlier steps of your workflow. 

### Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `base_uml_dir` | Path to the directory containing PlantUML diagrams for the base branch. | Yes | N/A |
| `pr_uml_dir` | Path to the directory containing PlantUML diagrams for the PR branch (with new changes). | Yes | N/A |
| `github_token` | GitHub token for posting PR comments. | No | `${{ github.token }}` |

### Example Workflow

```yaml
name: UML Diff Review

on:
  pull_request:
    branches:
      - main

jobs:
  uml-diff:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout base branch
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.base.ref }}
          path: base_repo

      - name: Generate Base UML
        run: |
          # Your custom script to generate UML for the base branch
          # Save outputs to ./base_uml_dir
          mkdir -p ./base_uml_dir
          # ./generate_uml.sh ./base_repo ./base_uml_dir

      - name: Checkout PR branch
        uses: actions/checkout@v4
        with:
          path: pr_repo

      - name: Generate PR UML
        run: |
          # Your custom script to generate UML for the PR branch
          # Save outputs to ./pr_uml_dir
          mkdir -p ./pr_uml_dir
          # ./generate_uml.sh ./pr_repo ./pr_uml_dir

      - name: Semantic UML Diff
        uses: ./ # Or your-org/semantic-uml-diff@v1
        with:
          base_uml_dir: ./base_uml_dir
          pr_uml_dir: ./pr_uml_dir
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Development

This project is built following **Spec Driven Development** guided by AI. See [`SPEC.md`](SPEC.md) and the `specs/` folder for details on the architecture, domain, and agent interaction workflow.
