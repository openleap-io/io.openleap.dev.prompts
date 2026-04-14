# Task: DevOps Setup for Microservice (v1)

> **Version:** 1.0.0

You are setting up the DevOps infrastructure for a microservice defined in the `spec/` folder.
This creates the `devops/` folder structure with Docker, Kubernetes, and API tooling artifacts.

---

## Prompt Inputs

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Maven artifact ID (e.g., `io.openleap.services.pps.im`) | — |
| `SERVICE_SHORT` | Short name for container/k8s resources (e.g., `pps-im`) | — |
| `SERVICE_PORT` | Application port | `8080` |
| `MGMT_PORT` | Management/actuator port | `8081` |
| `DB_SCHEMA` | PostgreSQL schema name | derived from `SERVICE_SHORT` |
| `API_BASE_PATH` | REST API base path from spec (e.g., `/api/pps/im/v1`) | — |
| `JAVA_VERSION` | Java version from parent POM | `25` |

---

## Folder Structure

Every microservice MUST have this `devops/` directory at the project root:

```
devops/
  docker/
    Dockerfile
    docker-compose.yml
    .env
    start.sh
    stop.sh
    infra-only.sh
  k8s/
    namespace.yaml
    deployment.yaml
    service.yaml
    configmap.yaml
    secret.yaml
    ingress.yaml
    hpa.yaml
    kustomization.yaml
  api/
    bruno/
      bruno.json
      environments/
        local.bru
      health/
        health-check.bru
      {resource-collections}/
        ...
    insomnia/
      insomnia-environment.json
    openapi/
      openapi.yaml
```

---

## 1. Docker (`devops/docker/`)

### 1.1 Dockerfile

- [ ] Multi-stage build: build stage with Maven, runtime stage with Eclipse Temurin JRE
- [ ] JRE version MUST match the Java version from the parent POM
- [ ] Use `eclipse-temurin:${JAVA_VERSION}-jre-alpine` as the runtime base image
- [ ] Run as non-root user (`appuser`, UID 1000)
- [ ] Copy only the fat JAR into the runtime stage
- [ ] Expose `SERVICE_PORT` and `MGMT_PORT`
- [ ] Set JVM options via `JAVA_OPTS` environment variable with sensible defaults
- [ ] Health check using the actuator health endpoint on `MGMT_PORT`

```dockerfile
# === Build Stage ===
FROM eclipse-temurin:${JAVA_VERSION}-jdk-alpine AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -B clean package -DskipTests

# === Runtime Stage ===
FROM eclipse-temurin:${JAVA_VERSION}-jre-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup -u 1000
WORKDIR /app

COPY --from=build /build/target/*.jar app.jar
RUN chown appuser:appgroup app.jar

USER appuser

ENV JAVA_OPTS="-XX:+UseZGC -XX:MaxRAMPercentage=75.0 -XX:+ExitOnOutOfMemoryError"
EXPOSE ${SERVICE_PORT} ${MGMT_PORT}

HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:${MGMT_PORT}/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

### 1.2 docker-compose.yml

- [ ] Service container built from the Dockerfile
- [ ] PostgreSQL container (use `postgres:17-alpine`)
- [ ] RabbitMQ container (use `rabbitmq:4-management-alpine`)
- [ ] All containers MUST have health checks
- [ ] Service depends on PostgreSQL and RabbitMQ with `condition: service_healthy`
- [ ] Named volumes for database and message broker data
- [ ] Environment variables sourced from `.env` file
- [ ] Network with explicit subnet for service discovery

### 1.3 `.env`

- [ ] Contains all configurable environment variables with test/dev defaults
- [ ] Database credentials, schema name, ports, Spring profiles
- [ ] RabbitMQ credentials
- [ ] MUST be in `.gitignore` — provide `.env.example` as a tracked template

### 1.4 Shell Scripts

All scripts MUST be executable (`chmod +x`).

**`start.sh`** — Builds and starts all containers:
```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up --build -d
echo "Waiting for service health..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T ${SERVICE_SHORT} \
  sh -c 'until wget -qO- http://localhost:${MGMT_PORT}/actuator/health 2>/dev/null | grep -q UP; do sleep 2; done'
echo "Service is healthy."
```

**`stop.sh`** — Stops and removes containers:
```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" down -v
```

**`infra-only.sh`** — Starts only infrastructure (DB + MQ) for local development:
```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d postgres rabbitmq
echo "Infrastructure is ready."
```

---

## 2. Kubernetes (`devops/k8s/`)

All manifests target a dedicated namespace. Use Kustomize for environment-specific overlays.

### 2.1 namespace.yaml

- [ ] Dedicated namespace: `openleap-${SERVICE_SHORT}`
- [ ] Labels: `app.kubernetes.io/part-of: openleap`, `app.kubernetes.io/component: ${SERVICE_SHORT}`

### 2.2 deployment.yaml

- [ ] Deployment with `replicas: 1` (scaled via HPA)
- [ ] Container image: `openleap/${SERVICE_SHORT}:latest`
- [ ] Resource requests and limits:
  - Requests: `cpu: 250m`, `memory: 512Mi`
  - Limits: `cpu: "1"`, `memory: 1Gi`
- [ ] Liveness probe: `httpGet` on `MGMT_PORT` path `/actuator/health/liveness`, `initialDelaySeconds: 30`, `periodSeconds: 10`
- [ ] Readiness probe: `httpGet` on `MGMT_PORT` path `/actuator/health/readiness`, `initialDelaySeconds: 15`, `periodSeconds: 5`
- [ ] Startup probe: `httpGet` on `MGMT_PORT` path `/actuator/health`, `failureThreshold: 30`, `periodSeconds: 2`
- [ ] Environment variables from ConfigMap and Secret references
- [ ] Pod anti-affinity for high availability (preferred, not required)
- [ ] Labels: `app.kubernetes.io/name: ${SERVICE_SHORT}`, `app.kubernetes.io/version: latest`, `app.kubernetes.io/part-of: openleap`
- [ ] `securityContext`: `runAsNonRoot: true`, `runAsUser: 1000`, `readOnlyRootFilesystem: true`
- [ ] `serviceAccountName` referencing a dedicated service account (if needed)

### 2.3 service.yaml

- [ ] ClusterIP service exposing `SERVICE_PORT` (named `http`) and `MGMT_PORT` (named `management`)
- [ ] Selector matching the Deployment's pod labels

### 2.4 configmap.yaml

- [ ] Non-sensitive configuration: Spring profiles, database host/port/name, schema, RabbitMQ host/port, logging levels
- [ ] JVM options (`JAVA_OPTS`)

### 2.5 secret.yaml

- [ ] Sensitive configuration: database credentials, RabbitMQ credentials
- [ ] Values MUST be base64-encoded placeholders — real values injected by CD pipeline or sealed-secrets
- [ ] Add a comment: `# Replace with sealed-secrets or external-secrets in production`

### 2.6 ingress.yaml

- [ ] Ingress resource for the API base path
- [ ] Annotations for nginx ingress controller (rate limiting, body size)
- [ ] TLS section with placeholder for certificate secret
- [ ] Host: `api.openleap.io` (override per environment)
- [ ] Path: `${API_BASE_PATH}` with `pathType: Prefix`

### 2.7 hpa.yaml

- [ ] HorizontalPodAutoscaler targeting the Deployment
- [ ] `minReplicas: 1`, `maxReplicas: 5`
- [ ] Scale on CPU utilization (target 70%) and memory utilization (target 80%)
- [ ] `behavior` with scale-down stabilization window of 300s

### 2.8 kustomization.yaml

- [ ] Lists all resources in order
- [ ] Common labels applied via Kustomize
- [ ] Namespace override
- [ ] Provides a base for environment-specific overlays

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: openleap-${SERVICE_SHORT}

commonLabels:
  app.kubernetes.io/part-of: openleap
  app.kubernetes.io/managed-by: kustomize

resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - configmap.yaml
  - secret.yaml
  - ingress.yaml
  - hpa.yaml
```

---

## 3. API Tooling (`devops/api/`)

### 3.1 Bruno Collection (`devops/api/bruno/`)

[Bruno](https://www.usebruno.com/) is a git-friendly API client. The collection MUST be committed to the repo.

**`bruno.json`** — Collection manifest:
```json
{
  "version": "1",
  "name": "${SERVICE_NAME}",
  "type": "collection",
  "ignore": ["node_modules"]
}
```

**`environments/local.bru`** — Local development environment:
```bru
vars {
  baseUrl: http://localhost:${SERVICE_PORT}${API_BASE_PATH}
  mgmtUrl: http://localhost:${MGMT_PORT}
}
```

**`health/health-check.bru`** — Health check request:
```bru
meta {
  name: Health Check
  type: http
  seq: 1
}

get {
  url: {{mgmtUrl}}/actuator/health
}

assert {
  res.status: eq 200
  res.body.status: eq UP
}
```

- [ ] Create a folder per REST resource/aggregate from the spec
- [ ] Each CRUD operation as a separate `.bru` file
- [ ] Use Bruno variables (`{{baseUrl}}`, `{{id}}`) for dynamic values
- [ ] Include request body examples from the spec
- [ ] Add assertions for expected status codes

### 3.2 Insomnia Environment (`devops/api/insomnia/`)

**`insomnia-environment.json`** — Importable Insomnia environment:
```json
{
  "_type": "export",
  "resources": [
    {
      "_id": "env_openleap_${SERVICE_SHORT}_local",
      "_type": "environment",
      "name": "${SERVICE_NAME} — Local",
      "data": {
        "base_url": "http://localhost:${SERVICE_PORT}${API_BASE_PATH}",
        "mgmt_url": "http://localhost:${MGMT_PORT}",
        "auth_token": ""
      }
    }
  ]
}
```

- [ ] Environment file importable via Insomnia's import dialog
- [ ] Variables for base URL, management URL, and auth token placeholder

### 3.3 OpenAPI Specification (`devops/api/openapi/`)

**`openapi.yaml`** — Standalone OpenAPI 3.1 spec derived from the service specification:

- [ ] OpenAPI version `3.1.0`
- [ ] `info` block with service name, version `0.1.0`, description from spec
- [ ] `servers` entry for local development (`http://localhost:${SERVICE_PORT}${API_BASE_PATH}`)
- [ ] All endpoints defined in the service spec with:
  - Path parameters, query parameters, request bodies
  - Response schemas with correct HTTP status codes
  - `application/json` media types
- [ ] `components/schemas` for all DTOs (request/response) derived from the spec's data model
- [ ] `components/securitySchemes` with Bearer JWT placeholder
- [ ] Tags matching the spec's aggregate/resource grouping

> **Note:** This is a hand-authored spec derived from the domain specification.
> At runtime, SpringDoc generates an OpenAPI spec from annotations — this file serves as the
> design-time contract for API-first development and external tooling.

---

## Rules

- The `devops/` folder is a sibling to `src/` at the project root — NOT inside `src/`.
- All file paths are relative to the microservice project root.
- Docker scripts MUST be executable.
- Kubernetes manifests MUST pass `kubectl --dry-run=client` validation.
- The OpenAPI spec MUST be valid against the OpenAPI 3.1 JSON Schema.
- Bruno collection MUST be openable in Bruno without errors.
- Do NOT hardcode credentials in any tracked file — use placeholders or `.env.example`.
- Reflect on any gaps or issues in `spec/improvements.md` as per the reflection skill.
