# Semantic UML Diff GitHub Action

<div align="center">
  <p><b>Cut the noise from your architectural Pull Requests.</b></p>
  <p>This GitHub Action performs a deterministic, semantic structural comparison between two sets of PlantUML diagrams and generates <b>reduced visual diffs</b>.</p>
</div>

## ✨ Features

- **Semantic comparison**: Compares actual UML structural models (classes, methods, parameters), not raw text.
- **Noise reduction**: Discards unmodified entities and visually highlights only what changed, showing the minimal required context.
- **Deterministic output**: Guarantees identical graphic output for identical inputs, heavily mitigating CI flakiness.
- **Unified PR Feedback**: Automatically aggregates all architectural modifications into a single, clean, collapsible comment in your Pull Request.
- **Rich Discord Webhooks**: Pushes visually stunning summary reports to your team's Discord channel with intelligent API chunking for massive PRs.
- **Highly Configurable**: Control diagram layouts, package grouping behavior, and parameter verbosity to suit your team's cognitive load.

## Usage

This action assumes that you have already generated `.puml` files for both your base branch and your PR branch in earlier steps of your workflow. 

### Inputs

| Input | Description | Required | Default |
| --- | --- | --- | --- |
| `base_uml_dir` | Path to the directory containing PlantUML diagrams for the base branch. | Yes | N/A |
| `pr_uml_dir` | Path to the directory containing PlantUML diagrams for the PR branch (with new changes). | Yes | N/A |
| `github_token` | GitHub token for posting PR comments. | No | `${{ github.token }}` |
| `layout_orthogonal_lines` | Use orthogonal lines instead of curved lines for relationships. | No | `false` |
| `method_parameter_style` | How to display method parameters: `types_only` or `names_and_types`. | No | `types_only` |
| `group_by_package` | Group classes by their namespace/package using PlantUML `package` blocks. | No | `true` |

### Environment Variables

To configure the publishing behavior and image hosting, set the following environment variables:

| Variable | Description | Default |
| --- | --- | --- |
| `PUBLISH_GITHUB` | Enable or disable posting sticky comments to the GitHub PR. | `true` |
| `PUBLISH_DISCORD` | Enable or disable sending rich embed notifications to Discord. | `true` |
| `IMAGE_HOSTING_PROVIDER` | Where to host the diff image for the GitHub comment (`discord`, `plantuml_server`, `none`). | `discord` |
| `DISCORD_WEBHOOK_URL` | The Discord Webhook URL for notifications and/or CDN uploading. | N/A |
| `PLANTUML_JAR_PATH` | Path to the local `plantuml.jar` executable. | `plantuml.jar` |

> [!NOTE]
> **Image Hosting Strategy (`IMAGE_HOSTING_PROVIDER`)**: GitHub PR comments require a publicly accessible URL to embed images. This action cleverly uses Discord as a free CDN (`discord`) by uploading the locally generated diagram to the Discord webhook and extracting the public URL for the GitHub comment. Alternatively, you can use `plantuml_server` for a stateless encoding without uploading a file.

> [!IMPORTANT]
> **Discord API Limits**: Discord limits webhooks to 10 embeds per message. If your PR modifies more than 9 architectural components simultaneously, the Action's Unified Reporting system will automatically chunk the embeds into multiple consecutive Discord messages to ensure no visual data is lost.

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
        uses: tsorren/SemanticUMLDiff@main
        with:
          base_uml_dir: ./base_uml_dir
          pr_uml_dir: ./pr_uml_dir
          layout_orthogonal_lines: 'false'
          method_parameter_style: 'types_only'
          group_by_package: 'true'
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

## Support and Issues

If you encounter any problems, errors, or unexpected outputs while using the Semantic UML Diff action, please [open an issue](https://github.com/tsorren/SemanticUMLDiff/issues) on this repository. Provide as much context as possible, including your `action.yml` configuration and the PlantUML diagrams causing the issue if they can be shared publicly.

By using this Action, you agree to the terms in the `LICENSE` (MIT) and understand that the Developers offer community-driven support via GitHub Issues.

## Development

This project is built following **Spec Driven Development** guided by AI. See [`SPEC.md`](SPEC.md) and the `specs/` folder for details on the architecture, domain, and agent interaction workflow.

### Current Status
- [x] Phase 0: Bootstrap
- [x] Phase 1: Domain Model
- [x] Phase 2: PlantUML Parser MVP
- [x] Phase 3: Normalization Engine
- [x] Phase 4: Semantic Diff Engine
- [x] Phase 5: Graph Reduction Engine
- [x] Phase 6: Diff Visualization
- [x] Phase 7: GitHub Integration
- [x] Phase 8: Discord Integration
