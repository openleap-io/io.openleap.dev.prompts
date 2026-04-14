# Prompt: Crawl GitHub Repos to Update Implementation Status (v1)

> **Purpose:** Crawl all OpenLeap GitHub repositories to determine implementation status and spec version sync
> **Version:** 1.0.0
> **Output:** Updated `landscape/impl-status.json` in [dev.hub](https://github.com/openleap-io/io.openleap.dev.hub)
> **Prerequisites:** `gh` CLI authenticated with access to the `openleap-io` GitHub organization
> **Governance:** `https://github.com/openleap-io/io.openleap.dev.concepts/blob/main/governance/template-governance.md` (GOV-TPL-001)

---

## Instructions

Update `landscape/impl-status.json` in [dev.hub](https://github.com/openleap-io/io.openleap.dev.hub) by crawling the `openleap-io` GitHub organization to determine which specs have been implemented and whether their versions are in sync.

### Step 1: Load Current Registry

Read `landscape/impl-status.json` in [dev.hub](https://github.com/openleap-io/io.openleap.dev.hub) to get the current list of tracked specs and their known repository mappings.

### Step 2: Discover Repositories

Use the GitHub API to list **all** repos in the organization with pagination. The org currently has >100 repos — always fetch all pages:

```bash
# Page 1
gh api 'orgs/openleap-io/repos?per_page=100&page=1' --jq '.[].name'
# Page 2
gh api 'orgs/openleap-io/repos?per_page=100&page=2' --jq '.[].name'
# Continue until an empty page is returned
```

Or using the `gh` CLI with `--limit 200` (adjust if org grows past 200):

```bash
gh repo list openleap-io --limit 200 --json name,pushedAt,isArchived
```

**Important:** Never assume one page of 100 is sufficient. The org exceeded 100 repos in April 2026 and the pagination bug caused `io.openleap.ps.tim` and 5 other PS repos to be missed entirely in the 2026-04-05 crawl.

Cross-reference with `landscape/repo-catalog.yaml in dev.hub` to identify backend-service repos.

### Step 3: For Each Mapped Repository

For each entry in `implementation-status.json` that has a non-null `repository` field:

#### 3a. Check for staleness vs. last analysis

Before re-analyzing, compare the current HEAD SHA against `lastAnalysisCommitHash`:

```bash
CURRENT_SHA=$(gh api repos/openleap-io/{repo-id}/commits/HEAD --jq '.sha' 2>/dev/null | cut -c1-7)
```

If `CURRENT_SHA == lastAnalysisCommitHash` (and `lastAnalysisAt` is recent enough), the entry may be skipped for a deep re-analysis (still update `lastCrawled` at the top level). If the SHA has changed, perform a full re-analysis of the entry.

#### 3b. Verify the repo exists

```bash
gh repo view openleap-io/{repo-id} --json name,updatedAt,isArchived 2>/dev/null
```

If the repo doesn't exist, set `implementationStatus` to `"not-found"` and `versionSync` to `"spec-only"`.

#### 3c. Check for a `spec/` folder

```bash
gh api repos/openleap-io/{repo-id}/contents/spec --jq '.[].name' 2>/dev/null
```

Set `hasSpecFolder` to `true` or `false` based on whether the folder exists.

#### 3d. If `spec/` exists, find and read the spec file

Look for `.md` files in the `spec/` folder that match the domain name:

```bash
gh api repos/openleap-io/{repo-id}/contents/spec --jq '.[].name' | grep -i '.md'
```

For each matching spec file, read its content and extract the `**Version:**` date:

```bash
gh api repos/openleap-io/{repo-id}/contents/spec/{filename} --jq '.content' | base64 -d | grep -oP '\*\*Version:\*\*\s*\K[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1
```

Set `implSpecVersion` to the found version date.

#### 3e. Determine version sync

Compare `specVersion` (from this repo) with `implSpecVersion` (from the implementation repo):

| Condition | `versionSync` value |
|---|---|
| Both versions exist and are equal | `in-sync` |
| `specVersion` is newer than `implSpecVersion` | `spec-ahead` |
| `implSpecVersion` is newer than `specVersion` | `impl-ahead` |
| Both exist but cannot be compared (different formats) | `diverged` |
| No implementation repo | `spec-only` |
| Implementation repo exists but no spec in it | `unknown` |
| Implementation repo has spec but this repo doesn't | `impl-only` |

#### 3f. Capture the HEAD commit hash

For each repo that exists, record the current HEAD commit SHA so staleness can be detected in future runs:

```bash
gh api repos/openleap-io/{repo-id}/commits/HEAD --jq '.sha' 2>/dev/null | cut -c1-7
```

Set `lastAnalysisCommitHash` to the short SHA (7 chars).
Set `lastAnalysisAt` to today's date (ISO 8601, e.g. `"2026-04-05"`).

If the repo does not exist, set both to `null`.

This enables staleness detection: if a future crawl finds the repo's HEAD has moved beyond `lastAnalysisCommitHash`, the `versionSync` and implementation status fields may be stale and should be re-evaluated.

#### 3g. Check for a `qa/` folder

```bash
gh api repos/openleap-io/{repo-id}/contents/qa --jq '.[].name' 2>/dev/null
```

Set `hasQaFolder` to `true` or `false` based on whether the folder exists.

If the folder does not exist, set `qaFolderNotes` to a brief explanation (e.g. `"Checked {date} via GitHub API - no /qa folder found."`).

If the folder exists, leave `qaFolderNotes` unchanged (it may contain analysis notes from a prior QA run).

**Important:** The QA folder is the source of ADR compliance data. The fields `adrComplianceScore`, `adrReviewGuidelinesVersion`, and `adrReviewCommitHash` are populated by the QA analysis process, NOT by this crawl. The crawler only detects whether the `qa/` folder exists — it must **never overwrite** existing ADR compliance fields. If `hasQaFolder` is `true` and these fields already have values, preserve them.

#### 3h. Read `pom.xml` for platform dependency versions

For backend-service repos (those matching `io.openleap.{suite}.{domain}` naming), read the root `pom.xml` to extract the parent and starter versions:

```bash
gh api repos/openleap-io/{repo-id}/contents/pom.xml --jq '.content' 2>/dev/null | base64 -d
```

If the `pom.xml` exists, extract:

- **`parentVersion`**: The version of `io.openleap.parent` or `core-service-parent` declared in the `<parent>` block:
  ```xml
  <parent>
      <groupId>io.openleap.core</groupId>
      <artifactId>core-service-parent</artifactId>
      <version>4.0.0-SNAPSHOT</version>  <!-- this is starterVersion -->
  </parent>
  ```
  Some repos may use `io.openleap.parent` as the parent instead:
  ```xml
  <parent>
      <groupId>io.openleap</groupId>
      <artifactId>io.openleap.parent</artifactId>
      <version>3.0.3-SNAPSHOT</version>  <!-- this is parentVersion -->
  </parent>
  ```

- **`starterVersion`**: If the `<parent>` is `core-service-parent`, that version IS the starter version. If the `<parent>` is `io.openleap.parent`, look for `core-service-parent` in `<dependencyManagement>` or `<dependencies>` to find the starter version.

- Most backend services use `core-service-parent` as their direct parent, so `starterVersion` = the `<parent><version>` and `parentVersion` may be `null` (inherited transitively).

If `pom.xml` does not exist (non-Java repo), set both to `null`.

**Note:** The `devGuidelinesVersion` field is NOT populated by this crawl. It is only known after a QA/ADR analysis and is stored as `adrReviewGuidelinesVersion`. Do not set or overwrite it.

#### 3i. Update implementation status

Based on the repo's GitHub metadata:
- `isArchived: true` → `"archived"`
- Last commit within 30 days → `"active"`
- Last commit within 90 days → `"maintained"`
- Last commit older than 90 days → `"stale"`

### Step 4: Check for Untracked Repos

Look for backend-service repos in the GitHub org that are NOT in `implementation-status.json`:

```bash
# Get all repos from GitHub
gh repo list openleap-io --limit 200 --json name --jq '.[].name'
```

For any repo that matches the `io.openleap.{suite}.{domain}` naming pattern but has no corresponding entry in the registry, flag it as a potential `impl-only` entry and add it with:
- `specFile`: null
- `versionSync`: `"impl-only"`
- `implementationStatus`: determine from repo activity (step 3i)
- `hasSpecFolder`: check per step 3c
- `hasQaFolder`: check per step 3g
- `parentVersion` / `starterVersion`: read from `pom.xml` per step 3h
- `notes`: brief explanation (e.g. "Discovered via crawl {date}. No matching spec in spec mono-repo.")

### Step 5: Update Registry Metadata

After processing all entries:
- Set `lastCrawled` to today's date (ISO 8601)
- Set `lastUpdated` to today's date
- Sort entries by `specFile` path

Note: `lastAnalysisCommitHash` and `lastAnalysisAt` are set **per service entry** in step 3e, not at the top level. Top-level `lastCrawled` reflects when the crawl ran; per-service `lastAnalysisAt` reflects when that specific entry was last meaningfully analyzed.

### Step 6: Write Updated Registry

Write the updated `landscape/impl-status.json` in [dev.hub](https://github.com/openleap-io/io.openleap.dev.hub) with proper formatting (2-space indent).

### Step 7: Generate Summary Report

Output a markdown summary table:

```markdown
## Implementation Status Summary — {date}

### Sync Overview
| Status | Count |
|---|---|
| In sync | {n} |
| Spec ahead | {n} |
| Impl ahead | {n} |
| Spec only (no repo) | {n} |
| Unknown (needs crawl) | {n} |

### Implementation Status
| Status | Count |
|---|---|
| Active | {n} |
| Maintained | {n} |
| Stale | {n} |
| Not started | {n} |

### QA Coverage
| Metric | Count |
|---|---|
| With QA folder | {n} |
| Without QA folder | {n} |
| With ADR compliance score | {n} |

### Platform Versions
| Version | Repos using it |
|---|---|
| core-service-parent {version} | {n} |
| ... | ... |

### Attention Required
- **Spec ahead:** {list of specs where spec is newer than impl}
- **Impl ahead:** {list of specs where impl is newer than spec}
- **Impl only:** {list of repos with no matching spec}
- **No QA folder:** {list of repos with implementations but no QA folder}
```

---

## Rate Limiting

The GitHub API has rate limits. To avoid hitting them:
- Use `gh api` with `--cache 1h` where appropriate
- Process repos sequentially (not in parallel)
- If rate-limited, wait and retry
- The full crawl should take approximately 2-3 minutes for ~20 repos with implementations

## Output Schema

Each entry in the `services` array has these fields:

| Field | Type | Source |
|---|---|---|
| `specFile` | string \| null | Spec mono-repo path |
| `specVersion` | string \| null | Parsed from spec file |
| `templateId` | string | Template mapping |
| `templateVersion` | string | Template mapping |
| `templateCompliance` | string \| null | Template compliance check |
| `repository` | string \| null | Repo name |
| `repositoryUrl` | string \| null | Repo URL |
| `implementationStatus` | string | Step 3i |
| `hasSpecFolder` | boolean \| null | Step 3c |
| `implSpecVersion` | string \| null | Step 3d |
| `versionSync` | string | Step 3e |
| `notes` | string | Manual or crawl notes |
| `hasQaFolder` | boolean \| null | Step 3g |
| `qaFolderNotes` | string \| null | Step 3g |
| `lastAnalysisCommitHash` | string \| null | Step 3f |
| `lastAnalysisAt` | string \| null | Step 3f |
| `adrComplianceScore` | string \| null | QA analysis (not crawl) |
| `adrReviewGuidelinesVersion` | string \| null | QA analysis (not crawl) |
| `adrReviewCommitHash` | string \| null | QA analysis (not crawl) |
| `parentVersion` | string \| null | Step 3h |
| `starterVersion` | string \| null | Step 3h |

Fields marked "QA analysis (not crawl)" are populated by a separate QA/ADR review process. The crawler must **preserve** these values and never overwrite them.

## Expected Results

Based on the current registry (~134 entries):
- ~20-25 entries have mapped repositories
- ~110 entries are spec-only (no implementation yet)
- Most implementations are in T1 Platform (IAM, param, dms, i18n, jc, ref, rpt, zugferd, nfs)
- T3 domain implementations growing (PS suite: agl, bud, tim; FI suite: gl, ap, ar, slc, bank)
