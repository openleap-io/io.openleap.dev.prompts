# Prompt: QA Analysis for an Existing OpenLeap Microservice (v2)

> **Purpose:** Perform a comprehensive quality analysis of an existing OpenLeap microservice implementation
> **Version:** 2.0.0
> **Output:** QA reports in `QA/` folder of the target repo + updated `landscape/implementation-status.json` in `io.openleap.spec`
> **Prerequisites:** `gh` CLI authenticated, access to `openleap-io` GitHub org; `io.openleap.spec` checked out at `/tmp/spec-repo`

---

## Prompt Inputs

| Variable | Description | Example |
|----------|-------------|---------|
| `REPO_ID` | Repository name (without org prefix) | `io.openleap.sd.ord` |
| `SPEC_FILE` | Path to spec in `io.openleap.spec` | `spec/T3_Domains/SD/sd_ord-spec.md` |
| `GUIDELINES_REF` | Git ref for `io.openleap.dev.guidelines` | `main` |

---

## Phase 1: Setup

### 1.1 Clone Target Repo

```bash
git clone https://github.com/openleap-io/$REPO_ID /tmp/$REPO_ID
```

### 1.2 Clone Reference Repos

```bash
git clone --branch ${GUIDELINES_REF:-main} --single-branch \
  https://github.com/openleap-io/io.openleap.dev.guidelines /tmp/devguidelines
git clone https://github.com/openleap-io/io.openleap.spec /tmp/spec-repo
```

### 1.3 Read the Specification

Read `$SPEC_FILE` from `/tmp/spec-repo/` carefully. This is the source of truth for what the service should do.

### 1.4 Read the Guidelines

Read ALL ADRs in `/tmp/devguidelines/adr/`. These are binding architectural decisions.

---

## Phase 2: Static Checks

Run these checks against `/tmp/$REPO_ID`. Record every finding.

| Check | Command | Pass Condition |
|-------|---------|----------------|
| No unmanaged versions in pom.xml | `grep -n '<version>' pom.xml` | Only parent + project versions |
| `@EntityScan` present | `grep -r '@EntityScan' src/` | Found |
| Sequences for all entity tables | `grep -i 'create sequence' src/main/resources/db/migration/*.sql` | Each entity table has `{table}_seq` |
| No BIGSERIAL for entity PKs | `grep -i 'BIGSERIAL' src/main/resources/db/migration/*.sql` | Empty (or only infra tables) |
| `spring-boot-flyway` dep declared | `grep 'spring-boot-flyway' pom.xml` | Found |
| Repackage goal declared | `grep -A5 'spring-boot-maven-plugin' pom.xml \| grep repackage` | Found |
| `out-of-order: true` in application.yaml | `grep 'out-of-order' src/main/resources/application.yaml` | Found |
| Entities extend starter base class | `grep -r 'extends.*Entity' src/main/java/` | AuditableEntity/PersistenceEntity |
| `.gitignore` exists | `test -f .gitignore && echo EXISTS` | EXISTS |
| `target/` not tracked | `git -C /tmp/$REPO_ID ls-files target/` | Empty output |
| QA folder exists | `test -d QA && echo EXISTS` | EXISTS (may be absent) |
| DevOps folder present | `test -d devops && echo EXISTS` | EXISTS |
| Docker setup present | `test -f devops/docker/docker-compose.yml && echo EXISTS` | EXISTS |
| Kubernetes setup present | `test -d devops/k8s && echo EXISTS` | EXISTS |
| API tooling present | `test -d devops/api && echo EXISTS` | EXISTS |
| README.md present | `test -f README.md && echo EXISTS` | EXISTS |

---

## Phase 3: ADR Compliance Analysis

For each ADR in `/tmp/devguidelines/adr/` that is applicable to this service, check compliance:

| ADR | Check |
|-----|-------|
| ADR-001 Four-tier layering | Package structure follows `domain`, `application`, `infrastructure`, `api` |
| ADR-002 CQRS | Separate command/query paths present |
| ADR-003 Event-driven | Events defined and published for state changes in spec |
| ADR-004 Hybrid ingress | REST + RabbitMQ listeners present |
| ADR-006 Command records | Commands are Java records |
| ADR-007 Command handlers | Dedicated `CommandHandler` implementations |
| ADR-008 Command gateway | `CommandGateway`/command bus in use |
| ADR-011 Thin events | Events contain only IDs + essential fields |
| ADR-013 Outbox publishing | Outbox table in migrations; `OutboxPublisher` used |
| ADR-014 At-least-once delivery | DLQ configured for RabbitMQ consumers |
| ADR-016 PostgreSQL | Only PostgreSQL as persistence store |
| ADR-017 Read/write models | Separate read projections (views) present |
| ADR-020 Dual-key pattern | `Long id` PK + `UUID businessId`/`olUuid` present |
| ADR-021 `OlUuid.create()` | Uses `OlUuid.create()` for UUID generation (NOT `UUID.randomUUID()`) |
| ADR-029 Saga orchestration | Sagas present when spec defines distributed flows |

Classify each ADR check as: **Compliant**, **Partially Compliant**, **Non-Compliant**, **Not Applicable**.

---

## Phase 4: Specification Completeness Analysis

For each element defined in `$SPEC_FILE`:

1. **Aggregates** — Is each aggregate root class present in `src/`?
2. **Use Cases / Commands** — Is each listed use case handled by a command?
3. **Domain Events** — Is each event published by the corresponding handler?
4. **API Endpoints** — Does each REST endpoint in the spec have a controller method?
5. **Domain Rules** — Are domain invariants enforced in the domain model?
6. **Integrations** — Are incoming/outgoing event subscriptions as specified?

Classify each element as: **Implemented**, **Partially Implemented**, **Missing**, **Extra**.

Calculate:
```
Completeness = (Implemented + 0.5 × Partial) / Total × 100
```

---

## Phase 5: DevOps Compliance Analysis

Run the standalone DevOps QA prompt against the `devops/` folder:

> **See:** [`prompts/qa-devops.md`](qa-devops.md) v1.0.0

This validates:
- **Folder structure** — all required files present under `devops/docker/`, `devops/k8s/`, `devops/api/`
- **Docker** — Dockerfile (multi-stage, non-root, healthcheck), docker-compose (health checks, depends_on, volumes), shell scripts (executable, correct behavior)
- **Kubernetes** — Deployment (probes, resources, security context), Service, ConfigMap/Secret separation, Ingress, HPA, Kustomize base
- **API Tooling** — Bruno collection (environments, assertions), Insomnia environment, OpenAPI 3.1 spec (paths, schemas, security)

The output is `QA/DEVOPS_COMPLIANCE_REPORT.md` with sub-scores for each area and a weighted overall DevOps score.

---

## Phase 6: Generate QA Reports

Create the `QA/` folder in `/tmp/$REPO_ID` if it does not exist.

### 6.1 `QA/SPEC_COMPLETENESS_REPORT.md`

```markdown
# Specification Completeness Report — {REPO_ID}

> Generated: {date}
> Prompt: `qa-microservice.md` v2.0.0
> Spec version: {implSpecVersion}
> Completeness score: {X}%

## Aggregates
| Name | Status | Notes |
|------|--------|-------|
...

## Use Cases / Commands
| Use Case | Command | Handler | Status |
|----------|---------|---------|--------|
...

## Domain Events
| Event | Publisher | Status |
|-------|-----------|--------|
...

## API Endpoints
| Path | Method | Controller | Status |
|------|--------|------------|--------|
...

## Missing Items
- ...

## Extra Items (not in spec)
- ...
```

### 6.2 `QA/ADR_COMPLIANCE_REPORT.md`

```markdown
# ADR Compliance Report — {REPO_ID}

> Generated: {date}
> Prompt: `qa-microservice.md` v2.0.0
> Guidelines version: {GUIDELINES_REF}
> Compliance score: {X}%

| ADR | Title | Status | Findings |
|-----|-------|--------|----------|
...

## Non-Compliant Items (fixes required)
...

## Partial Compliance Items
...
```

### 6.3 `QA/OPENLEAP_COMPLIANCE_REPORT.md`

```markdown
# OpenLeap Platform Compliance Report — {REPO_ID}

> Generated: {date}
> Prompt: `qa-microservice.md` v2.0.0
> Score: {X}%

## Static Checks
| Check | Result | Notes |
|-------|--------|-------|
...

## Platform Module Usage
| Starter Feature | Used | Notes |
|----------------|------|-------|
...
```

### 6.4 `QA/COMPLIANCE_SUMMARY.md`

```markdown
# Compliance Summary — {REPO_ID}

> Generated: {date}
> Prompt: `qa-microservice.md` v2.0.0
> DevOps QA Prompt: `qa-devops.md` v1.0.0

| Analysis | Score | Status |
|----------|-------|--------|
| Specification Completeness | X% | GREEN/YELLOW/RED |
| ADR Compliance | X% | GREEN/YELLOW/RED |
| OpenLeap Platform Compliance | X% | GREEN/YELLOW/RED |
| DevOps Compliance | X% | GREEN/YELLOW/RED |

Thresholds: GREEN ≥ 90%, YELLOW ≥ 70%, RED < 70%
Overall: {lowest score}

## Top Issues
1. ...
2. ...
3. ...
```

### 6.5 `QA/compliance_scores.json`

```json
{
  "repo": "{REPO_ID}",
  "analysisDate": "{date}",
  "promptVersions": {
    "qa-microservice": "2.0.0",
    "qa-devops": "1.0.0"
  },
  "guidelinesRef": "{GUIDELINES_REF}",
  "specCompleteness": <0-100>,
  "adrCompliance": <0-100>,
  "openleapCompliance": <0-100>,
  "devopsCompliance": <0-100>,
  "overallScore": <min of above>,
  "status": "GREEN|YELLOW|RED"
}
```

---

## Phase 7: Commit QA Reports

```bash
cd /tmp/$REPO_ID
git add QA/
git commit -m "chore(qa): add compliance QA reports

Generated by qa-microservice.md v2.0.0 (qa-devops.md v1.0.0).
Spec: $SPEC_FILE
Guidelines: $GUIDELINES_REF

Co-Authored-By: Paperclip <noreply@paperclip.ing>"
git push
```

---

## Rules

- The spec is the source of truth. Measure implementation against `$SPEC_FILE`.
- ADRs are requirements, not suggestions — flag all deviations.
- Do NOT modify implementation code during QA. This is analysis-only.
- Score thresholds: GREEN ≥ 90%, YELLOW ≥ 70%, RED < 70%.
- Every non-compliant or missing item MUST appear in the summary Top Issues list.
- Commit QA reports to the implementation repo, not to the spec repo.