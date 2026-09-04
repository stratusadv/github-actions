# GitHub Actions

A collection of shared, reusable GitHub Actions for CI/CD pipelines.

## Available Actions

- **linting** - Code quality checks using Ruff and scans for common issues.
- **tests** - Django test runner with unittest and pytest support.
- **ai_code_review** - AI-powered inline code review on pull requests.
- **security** - Security audit using pip-audit and Trivy.

## Usage

We should reference actions in our workflow files using the repository path and version tag:

```yaml
- uses: stratusadv/github-actions/<action_name>@v2
```

Each action's available inputs are documented in its `action.yml` file.

### Example Workflow

```yaml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  PYTHON_VERSION: '3.11'

jobs:
  linting:
    name: Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: stratusadv/github-actions/linting@v2
        with:
          python-version: ${{ env.PYTHON_VERSION }}

  ai-review:
    name: AI Code Review
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
      pull-requests: write
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - uses: stratusadv/github-actions/ai_code_review@v2
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          ai-api-host: ${{ secrets.AI_API_HOST }}
          ai-api-key: ${{ secrets.AI_API_KEY }}
          ai-api-model: ${{ secrets.AI_API_MODEL }}
          dandy-settings-module: dandy_settings
          opencode-module: my_project.opencode_pkg

  tests:
    name: Tests
    runs-on: ubuntu-latest
    needs: linting
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
      - uses: stratusadv/github-actions/tests@v2
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          settings-module: system.testing.settings
          test-runner: pytest
          test-ignore: atlassian

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: stratusadv/github-actions/security@v2
        with:
          python-version: ${{ env.PYTHON_VERSION }}
```

## Releasing Changes

The actions are pinned by consumers using a major version tag (e.g., `@v2`). After merging changes to `main`, move the tag forward:

```
git tag -f v2
git push origin -f v2
```

This is safe for additive changes such as new actions, new optional inputs, or bug fixes within existing actions.

### Breaking Changes

If a change would break existing consumers such as removing inputs, renaming actions, changing required behavior, then release a new major version instead:

```
git tag v3
git push origin v3
```

and then update client projects to reference `@v3` as needed.
