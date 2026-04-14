# Prompt: Upgrade Domain Service Spec to TPL-SVC v1.0.0 (v1)

> **Purpose:** Bring a single domain service spec to full structural and content compliance with TPL-SVC v1.0.0
> **Version:** 1.0.0
> **Output:** Updated spec file, `status/spec-changelog.md`, `status/spec-open-questions.md`
> **Prerequisites:** Target spec file path (e.g., `spec/T3_Domains/SD/sd_shp-spec.md`)
> **Template:** `concepts/templates/platform/domain/domain-service-spec.md` (TPL-SVC v1.0.0)
> **Dev Guidelines:** `io.openleap.dev.guidelines` v4.1.0+ (required for ADR-067 extensibility, ADR-011 custom fields)
> **Governance:** `concepts/governance/template-governance.md` (GOV-TPL-001, §6)

---

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `{SPEC_FILE}` | Relative path to the spec file to upgrade | `spec/T3_Domains/SD/sd_shp-spec.md` |

---

## Core Principles

1. **Non-destructive.** All existing content MUST be preserved. Only ADD or EXPAND — never remove or replace existing substantive content unless it contradicts the template structure.
2. **Domain expertise.** For content-deep sections (§3 attributes, §6 request/response, §8 table definitions), use business domain knowledge and web research to produce realistic, meaningful content. Reference the equivalent SAP module processes (e.g., SD-TRA for shipping, FI-GL for general ledger) as domain inspiration.
3. **OPEN QUESTION discipline.** If required information cannot be reasonably inferred from the existing spec content or domain expertise, add an `OPEN QUESTION` entry in §14.3 rather than fabricating facts. Mark the affected section with `> OPEN QUESTION: See Q-{ID} in §14.3`.
4. **Style consistency.** Use MUST/SHOULD/MAY for normative statements. Prefer short sentences and lists. Keep terminology consistent (Aggregate, Domain Service, Application Service, Command, Event).

---

## Dev Guidelines ADR Reference

The following ADRs from `io.openleap.dev.guidelines` constrain how content should be authored. Apply them in the sections indicated:

| ADR | Topic | Applies To |
|-----|-------|------------|
| ADR-001 | Four-tier layering | §1 (context), §7 (no cross-tier direct deps) |
| ADR-002 | CQRS | §5 (use case type WRITE/READ), §6 (separate read/write models) |
| ADR-003 | Event-driven architecture | §7 (event patterns, choreography) |
| ADR-004 | Hybrid ingress (REST + messaging) | §5 (trigger types), §6 (REST), §7 (consumed events) |
| ADR-006 | Commands as Java records | §5 (domain operations map to command records) |
| ADR-007 | Separate command handlers | §5 (one handler per command) |
| ADR-008 | Central command gateway | §5 (gateway dispatches to handlers) |
| ADR-011 | Thin events | §7 (payload = IDs + changeType, not full entity) |
| ADR-013 | Outbox publishing | §7 (event publishing), §8 (outbox table) |
| ADR-014 | At-least-once delivery | §5 (idempotency), §7 (retry + DLQ) |
| ADR-016 | PostgreSQL | §8 (storage, column types) |
| ADR-017 | Separate read/write models | §5 (READ use cases), §6 (query endpoints) |
| ADR-020 | Dual-key pattern | §8 (UUID PK + business key UK) |
| ADR-021 | OlUuid.create() | §8 (UUID generation) |
| ADR-029 | Saga orchestration | §5.4 (cross-domain workflows), §7 (orchestration pattern) |
| ADR-067 | Extensibility (JSONB custom fields) | §12 (which aggregates are extensible), §8 (custom_fields column) |

---

## Instructions

### Step 1: Load Reference Materials

Read the following files into context before making any changes:

1. **Template:** `concepts/templates/platform/domain/domain-service-spec.md`
2. **Target spec:** `{SPEC_FILE}`
3. **Template registry:** `concepts/templates/template-registry.json` (for current TPL-SVC version)
4. **Suite spec:** Derive from the target spec's `Suite` metadata — e.g., if Suite is `sd`, read `spec/T3_Domains/SD/_sd_suite.md`
5. **Related specs:** Read any specs referenced in the target's §0.4 Related Documents

---

### Step 2: Perform Gap Analysis

Compare the target spec against the template section-by-section. Produce a gap analysis table before making changes:

| Section | Template Sub-sections | Present | Content Depth | Gap Description |
|---------|-----------------------|---------|---------------|-----------------|
| Preamble | Meta, Guidelines Compliance | ? | ? | ... |
| §0 | 0.1–0.4 | ? | ? | ... |
| §1 | 1.1–1.5 | ? | ? | ... |
| ... | ... | ... | ... | ... |
| §15 | 15.1–15.4 | ? | ? | ... |

Assess two dimensions per section:
- **Structural:** Are the heading and sub-heading hierarchy present?
- **Content depth:** Does the content match the template's expected depth? (e.g., §3 needs attribute tables, not just a Mermaid diagram; §6 needs request/response JSON, not just bullet endpoints)

This table serves as the upgrade plan. Present it to the user before proceeding.

---

### Step 3: Structural Compliance — Ensure All Sections Exist

For any section heading missing from the spec, add it with the correct Markdown heading level from the template:

- `## N. Section Title` — H2 for top-level sections
- `### N.M Sub-section` — H3 for sub-sections
- `#### N.M.K Detail` — H4 for detail sections
- `##### Aggregate Root / Child Entities / Value Objects` — H5 for domain model detail

**Sections to verify (all 16 + preamble):**

| Section | Required Sub-sections |
|---------|-----------------------|
| Preamble | Meta Information block, Guidelines Compliance block |
| §0 | 0.1 Purpose, 0.2 Audience, 0.3 Scope, 0.4 Related Documents |
| §1 | 1.1 Domain Purpose, 1.2 Business Value, 1.3 Key Stakeholders, 1.4 Strategic Positioning, 1.5 Service Context (with Responsibilities, Authoritative Sources, context diagram) |
| §2 | Service Identity table, Team table |
| §3 | 3.1 Conceptual Overview, 3.2 Core Concepts, 3.3 Aggregate Definitions (per aggregate: Aggregate Root with attribute table + lifecycle + invariants + events, Child Entities, Value Objects), 3.4 Enumerations, 3.5 Shared Types |
| §4 | 4.1 Business Rules Catalog, 4.2 Detailed Rule Definitions, 4.3 Data Validation Rules, 4.4 Reference Data Dependencies |
| §5 | 5.1 Business Logic Placement, 5.2 Use Cases (canonical format + detail), 5.3 Process Flow Diagrams, 5.4 Cross-Domain Workflows |
| §6 | 6.1 API Overview, 6.2 Resource Operations (full request/response), 6.3 Business Operations, 6.4 OpenAPI Specification |
| §7 | 7.1 Architecture Pattern, 7.2 Published Events (detailed), 7.3 Consumed Events (detailed), 7.4 Event Flow Diagrams, 7.5 Integration Points Summary |
| §8 | 8.1 Storage Technology, 8.2 Conceptual Data Model (ER diagram), 8.3 Table Definitions (columns, indexes, relationships, retention), 8.4 Reference Data Dependencies |
| §9 | 9.1 Data Classification, 9.2 Access Control, 9.3 Compliance Requirements |
| §10 | 10.1 Performance, 10.2 Availability & Reliability, 10.3 Scalability, 10.4 Maintainability |
| §11 | 11.1 Purpose, 11.2 Feature Dependency Register, 11.3 Endpoints per Feature, 11.4 BFF Aggregation Hints, 11.5 Impact Assessment |
| §12 | 12.1 Purpose, 12.2 Custom Fields, 12.3 Extension Events, 12.4 Extension Rules, 12.5 Extension Actions, 12.6 Aggregate Hooks, 12.7 Extension API Endpoints, 12.8 Extension Points Summary & Guidelines |
| §13 | 13.1 Data Migration, 13.2 Deprecation & Sunset |
| §14 | 14.1 Consistency Checks, 14.2 Decisions & Conflicts, 14.3 Open Questions, 14.4 ADRs, 14.5 Suite-Level ADR References |
| §15 | 15.1 Glossary, 15.2 References, 15.3 Status Output Requirements, 15.4 Change Log |

---

### Step 4: Content Depth — Domain Model (Section 3)

This is typically the largest content gap. For each aggregate identified in the existing Mermaid class diagram:

#### 4a. Aggregate Root Attribute Table

Create the full attribute table per the template:

```markdown
| Attribute | Type | Format | Description | Constraints | Required | Read-Only |
|-----------|------|--------|-------------|-------------|----------|-----------|
```

Derive attributes from the Mermaid class diagram fields. For each attribute:
- Map Mermaid types to schema types: `UUID` → `string/uuid`, `String` → `string`, `Decimal` → `number/decimal`, `LocalDateTime` → `string/date-time`, `int` → `integer/int32`, `enum(...)` → `string` with `enum_ref`
- Add meaningful **Description** using domain expertise (e.g., `carrierTrackingNumber` → "Carrier-assigned tracking identifier for shipment tracking")
- Add **Constraints** (e.g., patterns, min/max, string lengths)
- Mark `id`, `version`, `tenantId`, `createdAt`, `updatedAt` as **Read-Only**

Also add:
- **State Descriptions** table (State / Description / Business Meaning)
- **Allowed Transitions** table (From State / To State / Trigger / Guard)
- **Domain Events Emitted** list (cross-reference with §7 published events)

#### 4b. Child Entity Attribute Tables

For each child entity in the aggregate, create:
- Attribute table (same columns as aggregate root, minus Read-Only)
- **Business Purpose** description
- **Collection Constraints** (min/max items)
- **Invariants** (reference BR-xxx from §4)

#### 4c. Value Objects

Identify value objects from the domain (e.g., `Money` with amount + currencyCode, `Address`, `GeoLocation`). For each:
- Attribute table
- **Validation Rules** list

#### 4d. Enumerations (Section 3.4)

For each `enum(...)` referenced in the class diagram, create:

```markdown
| Value | Description | Deprecated |
|-------|-------------|------------|
```

Use domain expertise to write meaningful descriptions for each enum value.

#### 4e. Shared Types (Section 3.5)

Identify types reused across aggregates (e.g., `Money`). Document with:
- Attribute table
- Validation rules
- **Used By** references (list the aggregates that use this type)

**Domain knowledge guidance:** Use the SAP equivalent module (e.g., SD-TRA for shipping/transportation, FI-GL for general ledger, MM-IM for inventory) as inspiration for attribute completeness and enum values. Web research is encouraged for industry-standard field definitions.

---

### Step 5: Content Depth — Business Rules (Section 4)

#### 5a. Detailed Rule Definitions (§4.2)

For each row in the existing §4.1 catalog table, create the full rule definition block:

```markdown
#### BR-{ID}: {Rule Name}

**Business Context:** {Why does this rule exist?}

**Rule Statement:** {Formal statement in business terms}

**Applies To:**
- Aggregate: {AggregateName}
- Operations: {Create, Update, Delete, ...}

**Enforcement:** {How the system enforces this rule}

**Validation Logic:** {Plain language check}

**Error Handling:**
- **Error Code:** `{CODE}`
- **Error Message:** "{Message}"
- **User action:** {What user should do to resolve}

**Examples:**
- **Valid:** {Scenario}
- **Invalid:** {Scenario}
```

#### 5b. Data Validation Rules (§4.3)

Create two tables by examining the attribute tables from Step 4:

**Field-Level Validations:**

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|

Every `Required: Yes` attribute gets a "Required" entry. Every constrained attribute (pattern, min/max, format) gets a validation entry.

**Cross-Field Validations:**
- List logical dependencies (e.g., "plannedDeliveryDate must be >= plannedPickupDate")

#### 5c. Reference Data Dependencies (§4.4)

Identify which attributes reference external catalogs:

| Catalog | Source Service | Fields Referencing | Validation |
|---------|----------------|-------------------|------------|

Common: countries (ref-data-svc), currencies (ref-data-svc), units of measure (si-unit-svc).

---

### Step 6: Content Depth — Use Cases, API, Events, Data Model (Sections 5–8)

#### 6a. Use Cases (Section 5)

- **§5.1 Business Logic Placement:** Add the standard placement table:

  | Logic Type | Placement | Examples |
  |------------|-----------|----------|
  | Aggregate invariants | Domain Object | Validation, state transitions |
  | Cross-aggregate logic | Domain Service | Operations spanning aggregates |
  | Orchestration & transactions | Application Service | Use case coordination, event publishing |

- **§5.2 Use Case Detail:** For each existing canonical format block, ADD below the table:

  ```markdown
  **Actor:** {User Role}

  **Preconditions:**
  - {Condition 1}
  - {Condition 2}

  **Main Flow:**
  1. Actor initiates {action}
  2. System validates {criteria}
  3. System creates/updates {entity}
  4. System publishes {event}

  **Postconditions:**
  - {Entity} is in {state}

  **Business Rules Applied:**
  - BR-{ID}: {Rule name}

  **Alternative Flows:**
  - **Alt-1:** If {condition}, then {alternative action}

  **Exception Flows:**
  - **Exc-1:** If {error condition}, then {error handling}
  ```

- **§5.4 Cross-Domain Workflows:** If the domain consumes or publishes cross-domain events (check §7), add the workflow documentation with: Pattern (Choreography vs Orchestration per ADR-029), Participating Services table, Workflow Steps with success/failure paths, Business Implications.

#### 6b. REST API (Section 6)

For each endpoint currently listed as a bullet point, expand to the full template format:

```markdown
#### 6.2.N {Resource} - {Operation}

`​`​`http
{METHOD} /api/{suite}/{domain}/v1/{path}
Authorization: Bearer {token}
Content-Type: application/json
`​`​`

**Request Body:**
`​`​`json
{ ... }
`​`​`

**Success Response:** `{status code}`
`​`​`json
{
  "id": "uuid",
  "version": 1,
  ...
  "_links": {
    "self": { "href": "/api/..." }
  }
}
`​`​`

**Response Headers:**
- `Location: /api/...` (for 201 Created)
- `ETag: "{version}"`

**Business Rules Checked:**
- BR-{ID}: {Rule name}

**Events Published:**
- `{suite}.{domain}.{aggregate}.{changeType}`

**Error Responses:**
- `400 Bad Request` — Validation error
- `404 Not Found` — Resource does not exist
- `409 Conflict` — Duplicate business key
- `412 Precondition Failed` — ETag mismatch
- `422 Unprocessable Entity` — Business rule violation
```

Guidelines:
- Follow ADR-002 (CQRS): Read endpoints return read models; write endpoints accept command-shaped request bodies
- Follow ADR-004: Write operations accept both REST and messaging triggers
- Business operations (non-CRUD): Use `POST /resource/{id}:{action}` pattern
- Add `### 6.4 OpenAPI Specification` reference block: location, version (OpenAPI 3.1), docs URL

#### 6c. Events (Section 7)

- **§7.1 Architecture Pattern:** Add pattern selection, broker, rationale. Reference the suite spec's integration pattern decision.

- **§7.2 Published Events:** For each event in the existing summary table, expand to:

  ```markdown
  #### Event: {Aggregate}.{ChangeType}

  **Routing Key:** `{suite}.{domain}.{aggregate}.{changeType}`

  **Business Purpose:** {What business fact this communicates}

  **When Published:** {Business condition}

  **Payload Structure:**
  `​`​`json
  {
    "aggregateType": "{suite}.{domain}.{aggregate}",
    "changeType": "{changeType}",
    "entityIds": ["uuid"],
    "version": 1,
    "occurredAt": "ISO-8601"
  }
  `​`​`

  **Event Envelope:**
  `​`​`json
  {
    "eventId": "uuid",
    "traceId": "string",
    "tenantId": "uuid",
    "occurredAt": "ISO-8601",
    "producer": "{suite}.{domain}",
    "schemaRef": "https://schemas.openleap.io/...",
    "payload": { ... }
  }
  `​`​`

  **Known Consumers:**
  | Consumer Service | Handler | Purpose | Processing Type |
  |-----------------|---------|---------|-----------------|
  ```

  Follow ADR-011 (thin events: IDs + changeType, not full entity) and ADR-013 (outbox publishing).

- **§7.3 Consumed Events:** Expand each with handler class name, business logic, queue configuration (`{suite}.{domain}.in.{source-suite}.{source-domain}.{topic}`), failure handling (retry 3x exponential backoff → DLQ per ADR-014).

- **§7.5 Integration Points Summary:** Add upstream dependencies table and downstream consumers table with: Service / Purpose / Integration Type / Criticality / Endpoints Used / Fallback.

#### 6d. Data Model (Section 8)

- **§8.2 Conceptual Data Model:** Add a Mermaid ER diagram showing all tables and their relationships.

- **§8.3 Table Definitions:** For each table in the existing stub, expand to:

  ```markdown
  #### Table: {table_name}

  **Business Description:** {What this table represents}

  **Columns:**
  | Column | Type | Nullable | PK | FK | Description |
  |--------|------|----------|----|----|-------------|

  **Indexes:**
  | Index Name | Columns | Unique |
  |------------|---------|--------|

  **Relationships:**
  - To {table}: {relationship type} via {column}

  **Data Retention:**
  - Soft/hard delete policy
  - Retention period
  ```

  Every table MUST include standard columns: `id UUID PK`, `tenant_id UUID NOT NULL` (RLS), `version INTEGER NOT NULL`, `created_at TIMESTAMPTZ NOT NULL`, `updated_at TIMESTAMPTZ NOT NULL` — per ADR-016 (PostgreSQL) and ADR-020 (dual-key: UUID PK + business key UK).

  For extensible aggregate tables (see §12.2): add `custom_fields JSONB NOT NULL DEFAULT '{}'` column plus a GIN index.

  Include the outbox table (`{prefix}_outbox_events`) per ADR-013.

- **§8.4 Reference Data Dependencies:** Add external catalogs table.

---

### Step 7: Content Depth — Security, Quality, Features, Extensions, Migration (Sections 9–13)

#### 7a. Security (Section 9)

- **§9.1 Data Classification:** Add overall classification and sensitivity levels table:

  | Data Element | Classification | Rationale | Protection Measures |
  |--------------|----------------|-----------|---------------------|

- **§9.2 Access Control:** Preserve existing RBAC matrix. Restructure to include Roles & Permissions table, expanded Permission Matrix, and Data Isolation description (RLS via tenant_id).

- **§9.3 Compliance Requirements:** Add applicable regulations checklist (GDPR, SOX, etc. — check which apply to this domain), compliance controls (data retention, right to erasure, data portability, audit trail).

#### 7b. Quality Attributes (Section 10)

Preserve existing performance numbers. Add missing sub-sections:

- **§10.1:** Add Throughput (peak read/write req/sec, event processing/sec) and Concurrency (simultaneous users, concurrent transactions)
- **§10.2 Availability & Reliability:** RTO/RPO targets, failure scenarios table (database failure, broker outage, downstream unavailable — with impact and mitigation)
- **§10.3 Scalability:** Horizontal scaling strategy, database read replicas, event consumer scaling, capacity planning (data growth, storage, event volume)
- **§10.4 Maintainability:** API versioning strategy, backward compatibility policy, monitoring (health checks, metrics), alerting (error rate, response time thresholds)

#### 7c. Feature Dependencies (Section 11)

- **§11.1 Purpose:** Add standard explanatory text from template
- **§11.2 Feature Dependency Register:** If feature specs referencing this service exist under the suite's `features/` directory, list them. Otherwise add OPEN QUESTION: "Which product features depend on this service's endpoints?"
- **§11.3–§11.5:** Add structural framework from template. Populate where possible from existing spec content (e.g., map REST endpoints to likely feature usage). Add OPEN QUESTION entries for unknowns.

#### 7d. Extension Points (Section 12)

The Conceptual Stack (§3.6) defines **five extension point types** at the domain/service level. All five MUST be considered when populating §12. Products fill these extension points in their product spec (§17.5) — the domain service spec declares what CAN be extended.

| Extension Type | Declared In | Filled By | Example |
|---------------|-------------|-----------|---------|
| **extension-field** | §12.2 Custom Fields | Product addon | "Add costCenter, projectCode to Shipment" |
| **extension-event** | §12.3 Extension Events | Product spec §17.5 | "React to post-delivery with custom handler" |
| **extension-rule** | §12.4 Extension Rules | Product addon | "Custom carrier eligibility validation" |
| **extension-action** | §12.5 Extension Actions | Product spec §17.5 | "Custom 'Export to Legacy' button on shipment detail" |
| **aggregate-hook** | §12.6 Aggregate Hooks | Product spec §17.5 | "Pre-create enrichment, post-transition notification" |

> **Implementation:** Custom fields and extension rules are implemented via the `core-extension` module (`io.openleap.starter`). See ADR-067 (extensibility architecture) and ADR-011 (implementation guide) in `io.openleap.dev.guidelines` for implementation details.

- **§12.1 Purpose:** Add standard explanatory text from template. Emphasize the Open-Closed Principle: platform is open for extension but closed for modification.

- **§12.2 Custom Fields (extension-field):** For each aggregate, decide whether it supports custom fields and document:

  ```markdown
  #### Custom Fields: {AggregateName}

  **Extensible:** Yes / No
  **Rationale:** {Why this aggregate needs (or doesn't need) custom fields}

  **Storage:** `custom_fields JSONB` column on `{table_name}`

  **API Contract:**
  - Custom fields included in aggregate REST responses under `customFields: { ... }`
  - Custom fields accepted in create/update request bodies under `customFields: { ... }`
  - Validation failures return HTTP 422

  **Field-Level Security:** Custom field definitions carry `readPermission` and `writePermission`.
  The BFF MUST filter custom fields based on the user's permissions.

  **Event Propagation:** Custom field values included in event payload under `customFields`.

  **Extension Candidates:**
  - {Likely custom field candidates based on domain knowledge — e.g., customs reference numbers,
    internal cost center codes, customer-specific routing codes}
  ```

  **Which aggregates should be extensible?** Mark as extensible any aggregate that:
  - Is customer-facing (orders, shipments, invoices, projects — yes; internal lookup tables — usually no)
  - Has known variance across customer deployments
  - Is referenced in product-feature extension zones

  Custom fields MUST NOT store business-critical data — they are for product-specific additions only.

  Add OPEN QUESTION if the extensibility decision is unclear for a specific aggregate.

- **§12.3 Extension Events:** Identify potential extension event hooks based on aggregate lifecycle (e.g., `ext.pre-carrier-assignment`, `ext.post-delivery-confirmation`). These differ from integration events in §7 — they exist for product-level customization. Follow fire-and-forget semantics.

- **§12.4 Extension Rules:** Identify where products might need custom validation beyond the platform's business rules. Define:

  | Rule Slot ID | Aggregate | Lifecycle Point | Default Behavior | Product Override |
  |-------------|-----------|----------------|-----------------|-----------------|

- **§12.5 Extension Actions:** Identify where products might add custom actions (buttons/operations) to the aggregate (e.g., "Export shipment to legacy TMS", "Generate custom shipping label"). These surface as extension zones in the feature spec's AUI screen contract.

- **§12.6 Aggregate Hooks:** Add pre/post lifecycle hooks for the main aggregate (e.g., pre-create validation, post-create enrichment, pre-transition gate). Define Hook Contract (input, output, timeout, failure mode).

- **§12.7 Extension API Endpoints:** Add the extension management endpoints from the template (register handler, extension config).

- **§12.8 Extension Points Summary & Guidelines:** Quick-reference matrix of all extension points. Add the guideline list from the template.

**Data model impact:** For each extensible aggregate, add to §8.3:
- Column: `custom_fields JSONB NOT NULL DEFAULT '{}'`
- GIN index on `custom_fields`

#### 7e. Migration & Evolution (Section 13)

- **§13.1 Data Migration:** Add legacy system mapping framework. Reference the SAP equivalent tables/transactions as source (e.g., VTTK/VTTS for shipping, BKPF/BSEG for accounting). Create the Source / Target / Mapping / Data Quality Issues table.
- **§13.2 Deprecation & Sunset:** Add framework (Deprecated Features table, Communication Plan).
- Preserve any existing future extension notes as roadmap items.

---

### Step 8: Guidelines Compliance & Consistency (Preamble + Section 14)

#### 8a. Guidelines Compliance Block

Populate the `## Specification Guidelines Compliance` section with the three standard sub-sections verbatim from the template:

```markdown
## Specification Guidelines Compliance

> ### Non-Negotiables
> - Never invent facts. If required info is missing, add an **OPEN QUESTION** entry.
> - Preserve intent and decisions. Only change meaning when explicitly requested.
> - Do not remove normative constraints unless they are explicitly replaced.
> - Keep the spec **self-contained**: no "see chat", no implicit context.
>
> ### Source of Truth Priority
> When sources conflict:
> 1. Spec (explicit) wins
> 2. Starter specs (implementation constraints) next
> 3. Guidelines (best practices) last
>
> Record conflicts in the **Decisions & Conflicts** section (see Section 14).
>
> ### Style Guide
> - Prefer short sentences and lists.
> - Use MUST/SHOULD/MAY for normative statements.
> - Keep terminology consistent (Aggregate, Domain Service, Application Service, Command, Event).
> - Avoid ambiguous words ("often", "maybe") unless explicitly noting uncertainty.
> - Keep examples minimal and clearly marked as examples.
> - Do not add implementation code unless the chapter explicitly requires it.
```

#### 8b. Consistency Checks (§14.1)

Run the 7 consistency checks from the template against the upgraded spec. Mark each as Pass or Fail with notes:

| Check | Status | Notes |
|-------|--------|-------|
| Every REST WRITE endpoint maps to exactly one WRITE use case | Pass / Fail | ... |
| Every WRITE use case maps to exactly one domain operation | Pass / Fail | ... |
| Events listed in use cases appear in §7 with schema refs | Pass / Fail | ... |
| Persistence and multitenancy assumptions consistent | Pass / Fail | ... |
| No chapter contradicts another | Pass / Fail | ... |
| Feature dependencies (§11) align with feature spec SS5 refs | Pass / Fail | ... |
| Extension points (§12) do not duplicate integration events (§7) | Pass / Fail | ... |

For any Fail, add an OPEN QUESTION in §14.3 or a Decision in §14.2 explaining the inconsistency.

#### 8c. Decisions & Conflicts (§14.2)

Add the source priority note and document any decisions or conflicts identified during the upgrade process.

#### 8d. Open Questions (§14.3)

Preserve all existing open questions. Renumber if needed to follow the `Q-{DOMAIN}-{NNN}` pattern. Add any new OPEN QUESTION entries raised during Steps 4–7.

#### 8e. ADRs (§14.4) and Suite-Level ADR Refs (§14.5)

Preserve existing ADR references. Add §14.4 framework for domain-level ADRs if not present.

---

### Step 9: Update Metadata

1. **Recalculate Template Compliance:** Count how many of the 16 sections (§0–§15) have meaningful content beyond a stub heading. Score = `(complete sections / 16) × 100`, rounded to nearest 5%.

2. **Update the meta block:**
   - Set `**Version:**` to today's date
   - Update `**Template Compliance:**` with the new percentage and list any remaining gaps
   - Ensure `**Template:**` reads `` `domain-service-spec.md` v1.0.0 ``

3. **Add changelog entry** in §15.4:

   ```markdown
   | {today} | {next version} | {Author} | Upgraded to full TPL-SVC v1.0.0 compliance |
   ```

---

### Step 10: Produce Output Artifacts and Verify

Produce three output artifacts:

#### 10a. Updated Spec File

The fully upgraded `{SPEC_FILE}`.

#### 10b. Changelog (`status/spec-changelog.md`)

Following the format from template §15.3:

```markdown
# Spec Changelog - {suite}.{domain}

## Summary
- {3-8 bullet points summarizing changes}

## Added Sections
- {List of new sections}

## Modified Sections
- {List of changed sections with brief description}

## Removed Sections
- None (non-destructive upgrade)

## Decisions Taken
- {Key decisions made during upgrade}

## Open Questions Raised
- {References to new open questions}
```

#### 10c. Open Questions (`status/spec-open-questions.md`)

```markdown
# Open Questions - {suite}.{domain}

## Q-{DOMAIN}-{NNN}: {Question Title}
- **Question:** {The question}
- **Why it matters:** {Generator/implementation impact}
- **Suggested options:** {Option A, Option B, ...}
- **Owner:** TBD
```

#### 10d. Self-Verification Checklist

Before completing, verify all of the following:

- [ ] All 16 sections (§0–§15) present with correct heading hierarchy
- [ ] Guidelines Compliance block populated (Non-Negotiables, Source Priority, Style Guide)
- [ ] Every aggregate has attribute tables (Type/Format/Description/Constraints/Required/Read-Only)
- [ ] Every `enum(...)` in Mermaid diagrams has a corresponding §3.4 enumeration table
- [ ] Every business rule in §4.1 has a detailed definition in §4.2
- [ ] Every use case has Actor/Preconditions/Main Flow/Postconditions
- [ ] Every REST endpoint has request/response bodies with JSON examples
- [ ] Every published event has envelope format and payload example
- [ ] Every consumed event has queue config and failure handling
- [ ] Every database table has column definitions and indexes
- [ ] Extension points §12 covers all 5 types (custom fields, events, rules, actions, hooks)
- [ ] Extensible aggregates have `custom_fields JSONB` column in §8 table definitions
- [ ] Consistency checks in §14.1 are filled in with Pass/Fail
- [ ] Template compliance percentage is recalculated
- [ ] No existing content was removed or lost
- [ ] All new OPEN QUESTION entries are tracked in §14.3

---

## Edge Cases

**Specs with no Mermaid class diagram in §3:** Build the attribute tables from the existing prose description and use case inputs/outputs. Add OPEN QUESTION for any attributes that cannot be inferred.

**Specs with extensive existing detail in some sections:** Do not "flatten" or restructure well-written content. Only add the missing sub-sections around it.

**Specs referencing features that do not yet have feature specs:** In §11, add the structural framework but mark specific feature IDs as OPEN QUESTION.

**Specs in suites without a suite spec:** Skip the suite spec read in Step 1. In §7.1, note that the suite-level integration pattern is not yet defined and add OPEN QUESTION.

**German-language content:** If the spec contains German prose, preserve it. New content added by this prompt should be in English (matching the template language). Add a note in §14.2 about the bilingual state if applicable.

---

## Expected Scope

Based on typical domain service specs in this repository:

- **Input:** One `.md` spec file, typically 400–600 lines at ~55–72% compliance
- **Output:** Upgraded spec file, typically 1,200–1,500 lines at ~95% compliance
- **Largest content additions:** §3 attribute tables (~250–300 lines), §6 request/response bodies (~150–200 lines), §8 table definitions (~100–150 lines)
- **New sections added:** §11, §12, §13 content (~100–150 lines total)
- **Typical OPEN QUESTIONs generated:** 5–15 new entries
- **Unchanged sections:** §0 (usually complete), §2 (usually complete)
