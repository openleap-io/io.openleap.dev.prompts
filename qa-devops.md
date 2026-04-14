# Prompt: DevOps QA Analysis for an OpenLeap Microservice (v1)

> **Purpose:** Validate the `devops/` folder of a microservice against the `devops.md` prompt specification
> **Version:** 1.0.0
> **Output:** `QA/DEVOPS_COMPLIANCE_REPORT.md` in the target repo
> **Prerequisites:** Target repo cloned, `devops.md` prompt available for reference

---

## Prompt Inputs

| Variable | Description | Example |
|----------|-------------|---------|
| `REPO_ID` | Repository name (without org prefix) | `io.openleap.sd.ord` |
| `SERVICE_SHORT` | Short name for container/k8s resources | `sd-ord` |
| `SERVICE_PORT` | Application port | `8080` |
| `MGMT_PORT` | Management/actuator port | `8081` |
| `API_BASE_PATH` | REST API base path from spec | `/api/sd/ord/v1` |
| `JAVA_VERSION` | Java version from parent POM | `25` |

---

## Phase 1: Folder Structure Validation

Verify the complete `devops/` tree exists at the project root.

| Path | Required | Check |
|------|----------|-------|
| `devops/` | YES | Directory exists |
| `devops/docker/Dockerfile` | YES | File exists |
| `devops/docker/docker-compose.yml` | YES | File exists |
| `devops/docker/.env` or `devops/docker/.env.example` | YES | At least `.env.example` tracked |
| `devops/docker/start.sh` | YES | File exists and is executable |
| `devops/docker/stop.sh` | YES | File exists and is executable |
| `devops/docker/infra-only.sh` | YES | File exists and is executable |
| `devops/k8s/namespace.yaml` | YES | File exists |
| `devops/k8s/deployment.yaml` | YES | File exists |
| `devops/k8s/service.yaml` | YES | File exists |
| `devops/k8s/configmap.yaml` | YES | File exists |
| `devops/k8s/secret.yaml` | YES | File exists |
| `devops/k8s/ingress.yaml` | YES | File exists |
| `devops/k8s/hpa.yaml` | YES | File exists |
| `devops/k8s/kustomization.yaml` | YES | File exists |
| `devops/api/bruno/bruno.json` | YES | File exists |
| `devops/api/bruno/environments/local.bru` | YES | File exists |
| `devops/api/bruno/health/health-check.bru` | YES | File exists |
| `devops/api/insomnia/insomnia-environment.json` | YES | File exists |
| `devops/api/openapi/openapi.yaml` | YES | File exists |

Classify: **Present** or **Missing**. Calculate:
```
Structure Score = Present / Total × 100
```

---

## Phase 2: Docker Compliance

### 2.1 Dockerfile

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Multi-stage build | `grep -c 'FROM' devops/docker/Dockerfile` | ≥ 2 |
| Correct JRE base image | `grep "temurin.*${JAVA_VERSION}.*jre" devops/docker/Dockerfile` | Found |
| Non-root user | `grep -E 'USER|adduser' devops/docker/Dockerfile` | Non-root user configured |
| HEALTHCHECK present | `grep 'HEALTHCHECK' devops/docker/Dockerfile` | Found |
| JAVA_OPTS configurable | `grep 'JAVA_OPTS' devops/docker/Dockerfile` | Found |
| Ports exposed | `grep 'EXPOSE' devops/docker/Dockerfile` | Both SERVICE_PORT and MGMT_PORT |

### 2.2 docker-compose.yml

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Service container defined | Service name present | Found |
| PostgreSQL container | `grep -i 'postgres' devops/docker/docker-compose.yml` | Found |
| RabbitMQ container | `grep -i 'rabbitmq' devops/docker/docker-compose.yml` | Found |
| Health checks on all containers | `grep -c 'healthcheck' devops/docker/docker-compose.yml` | ≥ 3 |
| `depends_on` with `service_healthy` | `grep 'service_healthy' devops/docker/docker-compose.yml` | Found |
| Named volumes | `grep -A20 '^volumes:' devops/docker/docker-compose.yml` | At least DB volume |
| No hardcoded credentials | No plaintext passwords outside `.env` reference | No hardcoded secrets |

### 2.3 Shell Scripts

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| `start.sh` executable | `test -x devops/docker/start.sh` | True |
| `stop.sh` executable | `test -x devops/docker/stop.sh` | True |
| `infra-only.sh` executable | `test -x devops/docker/infra-only.sh` | True |
| `set -euo pipefail` in all scripts | `grep 'set -euo pipefail' devops/docker/*.sh` | All 3 scripts |
| `start.sh` builds and waits for health | Script contains `--build` and health wait logic | Found |
| `stop.sh` tears down with volumes | Script contains `down -v` | Found |
| `infra-only.sh` starts only infra | Script starts only postgres and rabbitmq | Found |

---

## Phase 3: Kubernetes Compliance

### 3.1 Deployment

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Liveness probe configured | `livenessProbe` with `/actuator/health/liveness` | Found |
| Readiness probe configured | `readinessProbe` with `/actuator/health/readiness` | Found |
| Startup probe configured | `startupProbe` with `/actuator/health` | Found |
| Resource requests set | `requests.cpu` and `requests.memory` present | Found |
| Resource limits set | `limits.cpu` and `limits.memory` present | Found |
| Security context: non-root | `runAsNonRoot: true` and `runAsUser: 1000` | Found |
| Read-only root filesystem | `readOnlyRootFilesystem: true` | Found |
| Env from ConfigMap/Secret refs | `configMapRef` or `configMapKeyRef` present | Found |
| Env from Secret refs | `secretRef` or `secretKeyRef` present | Found |
| Standard labels | `app.kubernetes.io/name`, `app.kubernetes.io/part-of` | Found |

### 3.2 Service

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| ClusterIP type | `type: ClusterIP` or type absent (default) | True |
| HTTP port exposed | Port named `http` on SERVICE_PORT | Found |
| Management port exposed | Port named `management` on MGMT_PORT | Found |
| Selector matches deployment | Selectors are consistent | True |

### 3.3 ConfigMap & Secret

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| ConfigMap has non-sensitive config | DB host/port, Spring profiles, logging | Found |
| Secret has sensitive config | DB credentials, RabbitMQ credentials | Found |
| Secret values are placeholders | Base64 values are clearly placeholders | True |
| No plaintext secrets in ConfigMap | No passwords/tokens in configmap.yaml | True |

### 3.4 Ingress

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Ingress path matches API base path | Path contains `API_BASE_PATH` | Found |
| TLS section present | `tls:` block defined | Found |
| Ingress class annotation | `ingressClassName` or annotation set | Found |

### 3.5 HPA

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Targets correct deployment | `scaleTargetRef` matches deployment name | True |
| Min/max replicas set | `minReplicas` and `maxReplicas` present | Found |
| CPU metric configured | CPU utilization target defined | Found |
| Scale-down stabilization | `behavior.scaleDown.stabilizationWindowSeconds` | Found |

### 3.6 Kustomization

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| All resources listed | All yaml files referenced in `resources:` | True |
| Namespace set | `namespace:` field present | Found |
| Common labels | `commonLabels` with `app.kubernetes.io/part-of` | Found |

---

## Phase 4: API Tooling Compliance

### 4.1 Bruno Collection

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Valid `bruno.json` | Parseable JSON with `name`, `version`, `type` | Valid |
| Local environment defined | `environments/local.bru` with `baseUrl` and `mgmtUrl` | Found |
| Health check request | `health/health-check.bru` with GET to actuator | Found |
| Resource folders present | At least one resource folder with `.bru` files | Found |
| Assertions in requests | `.bru` files contain `assert` blocks | Found |
| Variables used | `{{baseUrl}}` or similar variable references | Found |

### 4.2 Insomnia Environment

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Valid JSON | Parseable as JSON | Valid |
| Export format | `_type: "export"` present | Found |
| Environment resource | At least one `_type: "environment"` resource | Found |
| Base URL variable | `base_url` in environment data | Found |
| Management URL variable | `mgmt_url` in environment data | Found |

### 4.3 OpenAPI Specification

| Check | Verification | Pass Condition |
|-------|-------------|----------------|
| Valid YAML | Parseable as YAML | Valid |
| OpenAPI version 3.1.x | `openapi: "3.1.0"` or `3.1.x` | Found |
| Info block complete | `info.title`, `info.version`, `info.description` | All present |
| Server entry for local dev | `servers` with localhost URL | Found |
| Paths match spec endpoints | Paths align with service specification | Consistent |
| Component schemas defined | `components.schemas` with request/response DTOs | Found |
| Security scheme defined | `components.securitySchemes` present | Found |
| Tags match spec resources | `tags` align with aggregates/resources | Consistent |

---

## Phase 5: Generate Report

Create `QA/DEVOPS_COMPLIANCE_REPORT.md` in `/tmp/$REPO_ID`:

```markdown
# DevOps Compliance Report — {REPO_ID}

> Generated: {date}
> Prompt: `qa-devops.md` v1.0.0
> Reference: `devops.md` v1.0.0
> Overall DevOps Score: {X}%

## Folder Structure
| Path | Status |
|------|--------|
...

Structure Score: {X}%

## Docker Compliance

### Dockerfile
| Check | Status | Notes |
|-------|--------|-------|
...

### docker-compose.yml
| Check | Status | Notes |
|-------|--------|-------|
...

### Shell Scripts
| Check | Status | Notes |
|-------|--------|-------|
...

Docker Score: {X}%

## Kubernetes Compliance

### Deployment
| Check | Status | Notes |
|-------|--------|-------|
...

### Service
| Check | Status | Notes |
|-------|--------|-------|
...

### ConfigMap & Secret
| Check | Status | Notes |
|-------|--------|-------|
...

### Ingress
| Check | Status | Notes |
|-------|--------|-------|
...

### HPA
| Check | Status | Notes |
|-------|--------|-------|
...

### Kustomization
| Check | Status | Notes |
|-------|--------|-------|
...

Kubernetes Score: {X}%

## API Tooling Compliance

### Bruno Collection
| Check | Status | Notes |
|-------|--------|-------|
...

### Insomnia Environment
| Check | Status | Notes |
|-------|--------|-------|
...

### OpenAPI Specification
| Check | Status | Notes |
|-------|--------|-------|
...

API Tooling Score: {X}%

## Non-Compliant Items (fixes required)
1. ...

## Recommendations
1. ...
```

### Score Calculation

```
Docker Score     = (Docker checks passed / Docker checks total) × 100
Kubernetes Score = (K8s checks passed / K8s checks total) × 100
API Score        = (API checks passed / API checks total) × 100
Structure Score  = (Paths present / Paths total) × 100

Overall DevOps Score = weighted average:
  Structure   × 0.10
  Docker      × 0.30
  Kubernetes  × 0.35
  API Tooling × 0.25
```

---

## Rules

- This is analysis-only — do NOT modify implementation code or devops files.
- Score thresholds: GREEN >= 90%, YELLOW >= 70%, RED < 70%.
- Every non-compliant item MUST appear in the Non-Compliant Items list.
- Validate YAML/JSON syntax where applicable — syntax errors are automatic failures.
- Kubernetes manifests should be checked with `kubectl --dry-run=client` if available.
- OpenAPI spec should be validated against the 3.1 schema if tooling is available.
- Reflect on any gaps in `spec/improvements.md` as per the reflection skill.
