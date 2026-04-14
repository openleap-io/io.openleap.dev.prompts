# Prompt: Update All Specs with Template Version References and Compliance Scores (v1)

> **Purpose:** Add `Template:` version references and `Template Compliance:` scores to all existing specification instances
> **Version:** 1.0.0
> **Scope:** All `.md` spec files under `spec/`
> **Registry:** `https://github.com/openleap-io/io.openleap.dev.concepts/blob/main/templates/template-registry.json` (source of truth for versions)
> **Governance:** `https://github.com/openleap-io/io.openleap.dev.concepts/blob/main/governance/template-governance.md` (GOV-TPL-001, §6)

---

## Instructions

Update all specification files under `spec/` to include a template version reference and compliance score in their meta information block, per GOV-TPL-001 §6.

### Step 1: Classify Each Spec File

For every `.md` file under `spec/`, determine which template it was instantiated from:

| Classification Rule | Template File | Template ID |
|---|---|---|
| Files with `Template: domain-service-spec.md` in `<!-- TEMPLATE COMPLIANCE:` comment | `domain-service-spec.md` | TPL-SVC |
| Files with `Template: suite-spec.md` in `<!-- TEMPLATE COMPLIANCE:` comment | `suite-spec.md` | TPL-SUITE |
| Files named `_*_suite.md` or `*_suite.md` (suite overview files) | `suite-spec.md` | TPL-SUITE |
| Domain/service spec files (most `*-spec.md` or `*.md` files in suite directories) | `domain-service-spec.md` | TPL-SVC |
| Feature leaf specs (files matching `F-{SUITE}-{NNN}-{NN}*.md` or in `features/` with leaf node type) | `feature-spec.md` | TPL-FEAT |
| Feature composition specs (files matching `F-{SUITE}-{NNN}*.md` with composition node type) | `feature-composition-spec.md` | TPL-FCOMP |
| Product specs (in product directories or with product metadata) | `product-spec.md` | TPL-PROD |
| Workflow specs (files matching `wf-*.md` or with workflow metadata) | `workflow-spec.md` | TPL-WF |

### Step 2: Skip Non-Template Files

The following files are NOT template instances and MUST be skipped:

- `SYSTEM_OVERVIEW.md` — living reference document
- `OPENLEAP_PLATFORM_GENERAL.md` — platform overview
- `OPA_IAM_Integration_Analysis.md` — analysis document
- Any `README.md` files
- Files that are clearly analysis documents, integration guides, or reference material (not domain/service/feature specs)

### Step 3: Determine Compliance Score

For each classified spec file, determine the compliance score:

#### 3a. Files WITH existing `<!-- TEMPLATE COMPLIANCE:` comment (52 files)

Extract the score and missing sections directly from the existing HTML comment:

```html
<!-- TEMPLATE COMPLIANCE: ~65%
Template: domain-service-spec.md
Present sections: §0 (...), §1 (...), §3 (...)
Missing sections: §2 (...), §11 (...), §12 (...)
-->
```

- **Score:** Use the existing `~NN%` value as-is
- **Missing sections:** Extract the section numbers from the `Missing sections:` line
- **Also update** the `Template:` line in the HTML comment to include the version: `Template: domain-service-spec.md v1.0.0`

#### 3b. Files WITHOUT existing compliance comment

Evaluate compliance by comparing the spec's sections against the template's required sections:

**For TPL-SVC (`domain-service-spec.md`)** — required sections:
- §0 Document Purpose & Scope
- §1 Business Context
- §2 Service Identity (table)
- §3 Domain Model
- §4 Business Rules
- §5 Use Cases / Business Processes
- §6 REST API
- §7 Events (produced/consumed)
- §8 Data Model
- §9 Security
- §10 Quality Attributes / NFR
- §11 Feature Dependency Register
- §12 Extension Points
- §13 Migration / Evolution
- §14 Open Questions / Decisions
- §15 Appendix (Glossary)

**For TPL-SUITE (`suite-spec.md`)** — required sections:
- §0 Document Purpose & Scope
- §1 Business Context
- §2 Suite Identity
- §3 Service Landscape
- §4 Integration Architecture
- §5 Cross-Cutting Concerns
- §6 Feature Catalog
- §7 Open Questions

**Score calculation:**
```
score = (present required sections / total required sections) × 100
```

Round to the nearest 5%. A section is "present" if it has meaningful content beyond a placeholder heading.

After evaluating, **add** a `<!-- TEMPLATE COMPLIANCE:` HTML comment block at the top of the file:

```html
<!-- TEMPLATE COMPLIANCE: ~{NN}%
Template: domain-service-spec.md v1.0.0
Present sections: §0 (...), §1 (...)
Missing sections: §2 (...), §11 (...)
Priority: {LOW | MEDIUM | HIGH}
-->
```

### Step 4: Add Template Reference and Compliance to Meta Block

For each classified spec file, add TWO lines to the `> **Meta Information**` block.

**Standard meta block format** — insert after the `**Version:**` line:

```markdown
> **Meta Information**
> - **Version:** 2026-02-23
> - **Template:** `domain-service-spec.md` v1.0.0
> - **Template Compliance:** ~65% — §2, §11, §12 missing
> - **Author(s):** OpenLeap Architecture Team
> - **Status:** DRAFT
```

**Rules:**
- The `Template:` line goes immediately after `**Version:**`
- The `Template Compliance:` line goes immediately after `**Template:**`
- Use backticks around the template filename
- Version is always `v1.0.0` for this initial rollout (baseline)
- Compliance score uses `~` prefix (approximate) and `%` suffix
- After the percentage, list missing sections as `§N, §M missing`
- For fully compliant specs: `> - **Template Compliance:** 100%`
- If the meta block already has a `**Template:**` line, update it to include the version and add compliance

### Step 5: Handle Edge Cases

**Compact feature spec headers** (e.g., SRV feature specs with inline format):
```markdown
> **Suite:** `srv` | **Node type:** LEAF | **Version:** 2026-03-28
```

For these, add new lines below the compact header:
```markdown
> **Suite:** `srv` | **Node type:** LEAF | **Version:** 2026-03-28
> **Template:** `feature-spec.md` v1.0.0
> **Template Compliance:** ~{NN}% — {missing sections}
```

**Files without any meta block:** Add a minimal meta block after the first heading:
```markdown
> **Meta Information**
> - **Template:** `domain-service-spec.md` v1.0.0
> - **Template Compliance:** ~{NN}% — {missing sections}
```

**German-language spec files** (e.g., `_srv_suite.de.md`): Apply the same rules — template references and compliance scores are always in English.

**Files with existing `**Template:**` line but no compliance:** Add only the compliance line after the existing template line.

### Step 6: Verify

After all updates, run verification:

1. **Template reference coverage:** Grep all `.md` files under `spec/` for `Template:` with a version pattern (`v[0-9]`). Every spec file should match, except those on the skip list.

2. **Compliance coverage:** Grep all `.md` files under `spec/` for `Template Compliance:`. Every spec file with a template reference should also have a compliance score.

3. **Format check:** Ensure all `Template:` lines follow the format `` `{filename}` v{X.Y.Z} `` and all `Template Compliance:` lines follow the format `~{NN}% — {details}` or `100%`.

4. **HTML comment sync:** For files with both an HTML compliance comment and a meta block compliance line, verify the percentages match.

5. **Count check:** Report total files updated, files skipped, and any gaps.

---

## Expected Scope

Based on current repository state:

- **52 spec files** already have `<!-- TEMPLATE COMPLIANCE: ~NN% -->` HTML comments — extract scores from these
- **Remaining spec files** (~4-10) need compliance evaluated from scratch
- **Most common template:** `domain-service-spec.md` (TPL-SVC) — used by the majority of specs
- **Suite specs:** ~11 suite files using `suite-spec.md` (TPL-SUITE)
- **Feature specs:** Files in `spec/T3_Domains/SRV/features/` using `feature-spec.md` (TPL-FEAT)
- **All baseline version:** `v1.0.0`
- **Typical compliance range:** 55%–85% for existing specs (based on the 52 audited files)
