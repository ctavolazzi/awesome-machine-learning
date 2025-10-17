# Resource Explorer Dashboard MVP Plan

## 1. Vision and Target Audience
- **Who it's for:** Maintainers and contributors of the `awesome-machine-learning` list who need a fast way to audit coverage, curate additions, and showcase the ecosystem to stakeholders.
- **What it should achieve:** Provide a shareable snapshot of the curated resources that highlights breadth, surfaces gaps, and makes it simple to drill into specific sections without leaving the browser.

## 2. MVP Scope and Core Outcomes
The minimum viable product should deliver the following user-facing capabilities:
1. **Automated ingestion** of the markdown curation files into a structured model that captures categories, sections, and individual resources.
2. **Interactive-quality dashboard export** that renders:
   - Hero metrics summarizing total categories, sections, and resources covered.
   - A bar chart visualizing category coverage, regenerated from repository data.
   - Section cards with concise descriptions and resource listings, including tags for quick scanning.
3. **One-command generation path** (CLI entry point) that emits both the HTML dashboard and accompanying assets to a chosen output directory.
4. **CI-visible smoke tests** that validate parsing, chart generation, and HTML rendering whenever curated markdown files change.

Anything outside these outcomes—packaging for PyPI, multi-user servers, or client-side interactivity—should be explicitly deferred to post-MVP phases.

## 3. Technical Requirements
### Data Loading and Normalization
- Reuse `examples/resource_explorer/resource_loader.py` to parse markdown files; extend it only where normalization or metadata extraction gaps appear.
- Define a stable `ResourceCollection` interface (dataclasses or typed dictionaries) so downstream renderers receive consistent inputs.
- Add lightweight validation (e.g., ensuring mandatory fields like name and URL are present) with actionable error messages when ingestion fails.

### Dashboard Rendering
- Consolidate HTML generation within `examples/resource_explorer/dashboard.py`:
  - Produce deterministic output by sorting sections and resources.
  - Ensure all user-provided strings are escaped to guard against malformed Markdown entries.
  - Bundle CSS inline for portability while keeping the layout legible on desktop and tablet breakpoints.
- Embed the SVG chart (from `visualize.py`) directly in the dashboard to avoid external asset dependencies.

### Command-Line Interface
- Expose a `resource-explorer dashboard` command (via `app.py`) that accepts:
  - `--source-root` for alternative markdown locations.
  - `--output` directory for exported HTML and chart files.
  - Optional filters (`--include-category`, `--keyword`) with sane defaults so the simplest invocation (`resource-explorer dashboard`) produces a ready-to-share artifact.
- Emit progress logs (info-level) describing ingestion counts, chart generation, and write paths to aid debugging.

### Quality and Automation
- Expand `examples/resource_explorer/tests` with:
  - Snapshot coverage for the normalized data model (focused on structure, not raw HTML).
  - Regression checks for the hero metrics block and embedded chart markup.
  - CLI invocation tests using temporary directories to confirm files are written and contain expected anchors.
- Wire up CI (or document a pre-commit hook) to run `pytest examples/resource_explorer/tests` so dashboard regressions block merges.

## 4. Simplification Guardrails
- Favor pure-Python, dependency-light solutions; avoid introducing JS frameworks or bundlers in the MVP.
- Ship a single `docs/resource_explorer_dashboard_sample.html` artifact as living documentation instead of building a gallery of variants.
- Resist optimizing for extreme performance or dataset sizes until real constraints appear; the curated lists are modest in scale.
- Keep configuration surface minimal—advanced theming or localization can wait.

## 5. Path Toward the MVP
1. **Stabilize data contracts:** Lock in the resource loader structures and error handling; add tests that cover representative markdown files.
2. **Finalize dashboard layout:** Iterate on `dashboard.py` to ensure hero metrics, chart, and section cards render cleanly with deterministic ordering.
3. **Polish the CLI flow:** Guarantee that a single command generates the dashboard without manual copying, and document the workflow in `examples/resource_explorer/README.md`.
4. **Automate verification:** Introduce targeted tests and, if available, CI wiring so contributors see failures when they break ingestion or rendering.
5. **Document the MVP boundaries:** Update the repository overview once the above steps are complete so newcomers know exactly what the dashboard guarantees and what remains aspirational.

## 6. Expert Recommendations for Next Steps
From the current prototype, the quickest wins that move us toward the MVP are:
1. **Normalize loader outputs** to a typed structure and document the contract. This reduces fragility as we expand tests and renderers.
2. **Add deterministic ordering and escaping** in the HTML generator so snapshot tests remain stable and security hygiene improves.
3. **Create end-to-end CLI tests** that run the dashboard command into a temp directory, asserting hero metrics, chart markup, and section cards appear together.
4. **Automate dashboard regeneration** in CI or a `make` target to keep the checked-in sample aligned with the code.
5. **Defer non-essential polish** (like advanced theming or packaging) until after the above foundation is locked in.

Executing these steps keeps the scope tight, minimizes premature optimization, and ensures every addition directly supports the MVP goals.

## 7. Current Implementation Snapshot

The latest iteration of the example project now satisfies the MVP requirements outlined above:

- Markdown ingestion flows through a typed `ResourceCollection` contract with per-entry validation, ensuring downstream renderers receive consistent titles, URLs, and summaries.
- The HTML dashboard centralizes rendering in `examples/resource_explorer/dashboard.py`, escapes all user-supplied data, sorts sections deterministically, and reuses the SVG chart emitted by the visualization helper.
- A unified CLI (`python -m examples.resource_explorer.app`) exposes `browse`, `chart`, and `dashboard` subcommands with shared flags such as `--source-root`, giving contributors a one-command path to generate demo artifacts.
- Tests under `examples/resource_explorer/tests` now exercise the normalized data model, dashboard hero metrics, artifact writing, and CLI dispatch so regressions are caught automatically.
- The repository includes an up-to-date `docs/resource_explorer_dashboard_sample.html` artifact generated by the new CLI for instant visual verification.
