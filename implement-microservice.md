# Task: Implement Microservice from Specification (v3)

> **Version:** 3.0.0

You are implementing a microservice defined in the `spec/` folder of this repository.
This is a production-quality implementation — you MUST follow all guidelines strictly.

---

## REFLECTION SKILL (Active Throughout ALL Phases)

> **This is not optional. This is the most important behavior in this entire prompt.**

You MUST maintain a running reflection log in `spec/improvements.md`. After EVERY
significant step, decision, workaround, fix, or incident, stop and reflect:

1. **What just happened?** — Describe the problem, decision, or fix.
2. **Root cause** — Why did this happen? Was it a missing guideline? A misleading rule?
   A gap in the starter? An unclear spec? A framework breaking change?
3. **What should change?** — Propose a concrete improvement. This can be:
   - A guideline that should be added or corrected in `io.openleap.dev.guidelines`
   - A starter module that should provide something it doesn't
   - A spec template that should include a section it's missing
   - A parent POM change that would prevent the issue
   - A better default in `application.yaml` template
4. **Severity** — `CRITICAL` (blocks startup), `HIGH` (causes runtime bugs), `MEDIUM` (code quality), `LOW` (minor friction)

**When to reflect:**
- You hit a compilation error caused by a missing dependency or config
- You discover the guidelines say one thing but the framework requires another
- You invent something not covered by any guideline
- You work around a starter limitation
- You spend more than 5 minutes debugging a configuration issue
- A test fails for non-obvious reasons
- You make a choice not covered by the spec or guidelines

**Format for `spec/improvements.md`:**

```markdown
# Implementation Improvements Log

## [IMP-001] Short title
- **Phase:** 2.1 Maven Setup
- **What happened:** [description]
- **Root cause:** [analysis]
- **Proposed improvement:** [concrete change]
- **Target:** guidelines | starter | parent-pom | spec-template
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
```

Append to this file throughout all phases. Do NOT wait until the end.

---

## Prompt Inputs

Before running this prompt, set the following variables. All git refs default to `main` if not provided.

| Variable | Description | Default |
|----------|-------------|---------|
| `GUIDELINES_REF` | Git tag or branch for `io.openleap.dev.guidelines` | `main` |
| `STARTER_REF` | Git tag or branch for `io.openleap.starter` | `main` |
| `PARENT_REF` | Git tag or branch for `io.openleap.parent` | `main` |

---

## Phase 1: Study Reference Material

Before writing ANY code, clone and study these repositories. Do not skip this step.

### 1.1 Clone References

Clone each repository at the specified ref (tag or branch). If no ref was provided, use `main`.

```bash
git clone --branch ${GUIDELINES_REF:-main} --single-branch https://github.com/openleap-io/io.openleap.dev.guidelines /tmp/devguidelines
git clone --branch ${PARENT_REF:-main} --single-branch https://github.com/openleap-io/io.openleap.parent /tmp/parent
git clone --branch ${STARTER_REF:-main} --single-branch https://github.com/openleap-io/io.openleap.starter /tmp/starter
```

> **Note:** Use `--branch` with a tag name (e.g., `v1.2.0`) or branch name (e.g., `develop`).
> After cloning, verify the checked-out ref matches what was requested:
> ```bash
> git -C /tmp/devguidelines log --oneline -1
> git -C /tmp/parent log --oneline -1
> git -C /tmp/starter log --oneline -1
> ```

### 1.2 Read the Development Guidelines (MANDATORY)

Read ALL files in `/tmp/devguidelines/`. Pay special attention to:

- **`adr/`** — Architecture Decision Records. These are binding constraints, not suggestions.
- **`adr/ADR-016-DATABASE.md`** — Database and Flyway setup, including Spring Boot 4.x breaking changes.
- **`common/core-service-starter.en.md`** — Available starter features, entity hierarchy, infrastructure tables, Docker setup.
- **`common/ADR/ADR-005-entity-persistence-auditing.md`** — Entity base classes, JPA sequence requirements, `@EntityScan` rule.
- **`parent-pom-overview.md`** — Managed dependencies, plugin configuration, Spring Boot 4.x breaking changes table.
- **`ontology/`** — All implementation patterns and coding standards.

> **Reflect:** If any guideline is unclear, contradictory, or seems incomplete — log it immediately in `spec/improvements.md`.

### 1.3 Read the Parent POM

Study `/tmp/parent/pom.xml` to understand:
- Which dependency versions are managed (do NOT declare versions for managed deps)
- Which plugins are in `pluginManagement` (you must declare them in `<plugins>` to activate)
- The Java version, encoding, and compiler settings

### 1.4 Read the Starter Modules

Study `/tmp/starter/` to understand:
- Available modules and their Maven coordinates
- Base entity classes (`PersistenceEntity`, `VersionedEntity`, `AuditableEntity`)
- Command bus, event publisher, identity holder, idempotency support
- Flyway migrations bundled in the starter JARs (V0.1, V0.2)

### 1.5 Read the Specification

Read everything in `spec/` carefully. The spec is the ultimate source of truth.
If the spec conflicts with a guideline, the spec wins (Override Rule).

---

## Phase 2: Implementation

Implement the complete microservice. Follow this checklist rigorously.

### 2.1 Maven Setup

- [ ] Parent POM: `io.openleap:io.openleap.parent` (use the version from the parent repo)
- [ ] Starter dependency: use the correct `io.openleap.core` module coordinates from the starter repo
- [ ] Do NOT declare versions for parent-managed dependencies
- [ ] `spring-boot-maven-plugin` MUST be in `<plugins>` with explicit `<goal>repackage</goal>` execution
- [ ] `spring-boot-flyway` dependency MUST be declared (Spring Boot 4.x moved Flyway auto-config to separate module)
- [ ] `flyway-core` and `flyway-database-postgresql` dependencies MUST be declared

### 2.2 Application Class

- [ ] `@SpringBootApplication` on the main class
- [ ] `@EntityScan(basePackages = "io.openleap")` — REQUIRED because starter entity registrars override default scanning

### 2.3 Flyway Migrations

- [ ] Every entity table MUST have a corresponding `{table}_seq` sequence with `INCREMENT BY 50`
- [ ] PK columns MUST be `BIGINT`, NOT `BIGSERIAL` — JPA manages IDs via the sequence
- [ ] Infrastructure tables (`idempotency`, `outbox`) MUST be created in the service schema with `IF NOT EXISTS`
- [ ] `spring.flyway.out-of-order: true` MUST be set in `application.yaml`
- [ ] Schema MUST be explicitly created: `CREATE SCHEMA IF NOT EXISTS {schema_name}`

### 2.4 Application Configuration (`application.yaml`)

- [ ] Datasource with PostgreSQL driver
- [ ] JPA `ddl-auto: validate` with `default_schema` matching Flyway schema
- [ ] Flyway with `enabled: true`, `schemas`, `default-schema`, `locations: classpath:db/migration`, `out-of-order: true`
- [ ] RabbitMQ connection settings
- [ ] OpenLeap starter properties (`ol.persistence`, `ol.web`, `ol.security`, `ol.messaging`, `ol.idempotency`, `ol.telemetry`)
- [ ] Actuator endpoints exposure
- [ ] SpringDoc OpenAPI paths

### 2.5 Domain Model

- [ ] All entities extend `AuditableEntity` (or at minimum `PersistenceEntity`)
- [ ] `@Table` with explicit schema
- [ ] Business identifiers implement `BusinessId` pattern where applicable
- [ ] Enums use `@Enumerated(EnumType.STRING)`
- [ ] Domain validation in factory methods, not in setters
- [ ] Follow the spec's aggregate definitions exactly

### 2.6 Application Layer

- [ ] Command records following the starter's `Command` pattern
- [ ] Command handlers implementing starter's `CommandHandler` interface
- [ ] Query services for read operations
- [ ] Event publishing via starter's `EventPublisher` where spec defines events
- [ ] `@Idempotent` annotation on command handlers where spec requires idempotency

### 2.7 API Layer

- [ ] REST controllers with correct base path from spec
- [ ] Request/Response DTOs — do NOT expose domain entities directly
- [ ] `@Valid` on request bodies
- [ ] Correct HTTP status codes (201 for creation, 204 for deletion, etc.)
- [ ] Cache-Control headers where spec defines caching

### 2.8 Testing

- [ ] Unit tests for domain logic (`*Test.java`)
- [ ] Unit tests for command handlers with mocked repositories
- [ ] Integration tests (`*IT.java`) where appropriate
- [ ] Test naming follows parent POM conventions

### 2.9 DevOps Setup (Docker, Kubernetes, API Tooling)

Run the standalone DevOps prompt to create the full `devops/` folder structure:

> **See:** [`prompts/devops.md`](devops.md) v1.0.0

This creates:
- `devops/docker/` — Dockerfile, docker-compose, shell scripts
- `devops/k8s/` — Kubernetes manifests (Deployment, Service, ConfigMap, Secret, Ingress, HPA, Kustomize)
- `devops/api/` — Bruno collection, Insomnia environment, OpenAPI spec

### 2.10 Commit

Commit the implementation with a conventional commit message:

```bash
git add -A
git commit -m "feat(<domain>): implement <service> microservice

Phases: Maven setup, domain model, application layer, API, tests, DevOps.
Spec: spec/<path-to-spec>.md
Guidelines: ${GUIDELINES_REF}

Co-Authored-By: Paperclip <noreply@paperclip.ing>"
```

---

## Phase 3: Build and Verify

1. Run `mvn clean verify` — fix ALL compilation errors and test failures
2. Verify the fat JAR is created: check `target/*.jar` contains `BOOT-INF/`
3. Verify Flyway migrations are in the JAR: check `BOOT-INF/classes/db/migration/`
4. Verify `spring-boot-flyway` is in the JAR: check `BOOT-INF/lib/spring-boot-flyway-*.jar`

> **Reflect:** If any build or test failure required a non-obvious fix, log it.

---

## Phase 4: README

Write a comprehensive `README.md` for the microservice. Use the template from the platform:

```bash
git clone https://github.com/openleap-io/io.openleap.dev.spec /tmp/spec-repo
cat /tmp/spec-repo/https://github.com/openleap-io/io.openleap.dev.concepts/blob/main/templates/platform/readme-microservice.md
```

Read this template and fill it out completely based on your implementation.
Every section in the template MUST be present and populated with real, accurate information
from this service — no placeholders, no TODOs, no "replace this" markers.

---

## Rules

- The spec is the source of truth. `spec/` overrides `devguidelines/` on conflicts.
- Follow guidelines strictly — they are requirements, not suggestions.
- Reuse starter modules. Do NOT reimplement base classes, command bus, event publisher, or identity handling.
- Do NOT invent features not in the spec.
- Do NOT declare versions for parent-managed dependencies.
- Commit frequently with conventional commit messages (`feat:`, `fix:`, `test:`, `chore:`).
- The build MUST pass (`mvn clean verify`) before final commit.
- The service MUST start and respond to health checks before final commit.
- `spec/improvements.md` MUST exist and contain at least one entry before final commit.
- Reflection is not optional. It is the mechanism by which the platform improves.
