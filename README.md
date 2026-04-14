# OpenLeap AI Automation Prompts & Scripts

Reusable AI prompts for batch operations on the OpenLeap specification and service repositories, plus the scripts and crawlers that support them.

---

## Prompt Architecture

The microservice delivery prompts follow a delegation hierarchy. The **CEO orchestrator** manages the full lifecycle, delegating to specialized engineering and QA prompts:

```
ceo-microservice.md              — Entry point: orchestrates full delivery
  ├── implement-microservice.md  — Engineering: code, DevOps, README
  │   └── devops.md              — DevOps: Docker, K8s, API tooling
  ├── qa-microservice.md         — QA: compliance analysis
  │   └── qa-devops.md           — QA: DevOps-specific checks
  └── (loops until QA passes)
```

## Available Prompts

| Prompt | Version | Purpose |
|--------|---------|---------|
| `ceo-microservice.md` | v1.0.0 | Delivery orchestrator: delegates engineering and QA, cycles until quality gates pass |
| `implement-microservice.md` | v3.0.0 | Microservice implementation from spec: Maven setup, domain model, API layer, testing, DevOps |
| `qa-microservice.md` | v2.0.0 | QA analysis: ADR, spec completeness, platform, DevOps compliance |
| `devops.md` | v1.0.0 | DevOps setup: Docker, Kubernetes manifests, API tooling (Bruno, Insomnia, OpenAPI) |
| `qa-devops.md` | v1.0.0 | DevOps QA: validates `devops/` folder against spec |
| `update-spec-template-references.md` | v1.0.0 | Add template version references and compliance scores to all spec instances |
| `crawl-implementation-status.md` | v1.0.0 | Crawl GitHub repos to update implementation status with version sync data |
| `upgrade-domain-service-spec.md` | v1.0.0 | Upgrade a domain service spec to TPL-SVC v1.0.0 compliance |

## Usage

For full microservice delivery, use `ceo-microservice.md` — it orchestrates everything automatically.

For standalone operations, copy the content of the specific prompt file and paste it into your AI assistant (e.g., Claude Code). Each prompt is self-contained with classification logic, transformation rules, and verification steps.

---

## Scripts (`scripts/`)

Automation tooling that supports the prompts.

| Script | Purpose |
|--------|---------|
| `scripts/batch-upgrade-specs.sh` | Bulk specification upgrade automation |
| `scripts/crawl-implementation-status.py` | Python script to crawl GitHub repos and update status JSON |
| `scripts/crawler/` | Docker-based crawler service (Flask server, Docker Compose) |
| `scripts/hooks/` | Git hooks for spec repo operations |
| `scripts/upgrade-logs/` | Records of past spec upgrade operations |

### Running the Crawler

```bash
cd scripts/crawler
docker-compose up
```

---

## Conventions

- Each prompt file is a standalone markdown document
- Prompts include scope, classification logic, transformation rules, edge cases, and verification steps
- Prompts reference the template registry in [dev.concepts](https://github.com/openleap-io/io.openleap.dev.concepts) (`templates/template-registry.json`) as the source of truth for template versions
- **Version traceability:** Every prompt declares a `> **Version:** X.Y.Z` line in its header. All generated artifacts MUST include a `> Prompt: {filename} vX.Y.Z` line so outputs are traceable to the exact prompt version

---

## Related Repositories

| Repository | Relationship |
|------------|-------------|
| [dev.hub](https://github.com/openleap-io/io.openleap.dev.hub) | Central documentation — landscape status files are updated by the crawler |
| [dev.spec](https://github.com/openleap-io/io.openleap.dev.spec) | The specifications these prompts operate on |
| [dev.concepts](https://github.com/openleap-io/io.openleap.dev.concepts) | Template registry referenced by prompts |
