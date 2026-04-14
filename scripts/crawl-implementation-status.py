#!/usr/bin/env python3
"""
Crawl OpenLeap GitHub repos tagged 'backend-service' and write
landscape/implementation-status.json.

Tracks activity status, spec/qa folder presence, and platform dependency
versions. Preserves QA-owned fields (ADR compliance) set by a separate process.

Usage:
    export GITHUB_TOKEN=ghp_...
    python3 scripts/crawl-implementation-status.py [--dry-run]

Prerequisites:
    - GITHUB_TOKEN env var with read access to the openleap-io organization
    - Python 3.10+ with `requests` (pip install requests)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from base64 import b64decode
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ORG = "openleap-io"
REGISTRY_PATH = Path("landscape/implementation-status.json")
BACKEND_TOPIC = "backend-service"
TODAY = date.today().isoformat()

# Fields owned by QA analysis — crawler must never overwrite these.
QA_OWNED_FIELDS = {
    "adrComplianceScore",
    "adrReviewGuidelinesVersion",
    "adrReviewCommitHash",
}

# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

session = requests.Session()


def init_session(token: str) -> None:
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )


def gh_get(url: str, **kwargs: Any) -> requests.Response:
    """GET with rate-limit awareness."""
    resp = session.get(url, **kwargs)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset - int(datetime.now(timezone.utc).timestamp()), 1)
        print(f"  Rate limited — waiting {wait}s", file=sys.stderr)
        import time

        time.sleep(wait + 1)
        resp = session.get(url, **kwargs)
    return resp


def list_org_repos() -> list[dict]:
    """List all repos in the org, handling pagination."""
    repos: list[dict] = []
    page = 1
    while True:
        resp = gh_get(
            f"https://api.github.com/orgs/{ORG}/repos",
            params={"per_page": 100, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def get_head_sha(repo_name: str) -> str | None:
    """Return short (7-char) HEAD SHA or None."""
    resp = gh_get(f"https://api.github.com/repos/{ORG}/{repo_name}/commits/HEAD")
    if resp.status_code != 200:
        return None
    return resp.json()["sha"][:7]


_root_listing_cache: dict[str, list[str]] = {}


def get_root_names(repo_name: str) -> list[str]:
    """Return lowercased root entry names for a repo, cached per repo."""
    if repo_name not in _root_listing_cache:
        resp = gh_get(f"https://api.github.com/repos/{ORG}/{repo_name}/contents/")
        if resp.status_code != 200:
            _root_listing_cache[repo_name] = []
        else:
            _root_listing_cache[repo_name] = [
                item["name"].lower() for item in resp.json() if isinstance(item, dict)
            ]
    return _root_listing_cache[repo_name]


def folder_exists(repo_name: str, folder: str) -> bool:
    """Check if a folder exists in the repo root (case-insensitive)."""
    return folder.lower() in get_root_names(repo_name)


def list_folder(repo_name: str, folder: str) -> list[str]:
    """List file names in a repo folder."""
    resp = gh_get(
        f"https://api.github.com/repos/{ORG}/{repo_name}/contents/{folder}"
    )
    if resp.status_code != 200:
        return []
    return [item["name"] for item in resp.json() if isinstance(item, dict)]


def get_file_content(repo_name: str, path: str) -> str | None:
    """Fetch raw file content from a repo. Returns None on failure."""
    resp = gh_get(
        f"https://api.github.com/repos/{ORG}/{repo_name}/contents/{path}"
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data.get("encoding") == "base64":
        return b64decode(data["content"]).decode("utf-8", errors="replace")
    return data.get("content")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def extract_spec_version(content: str) -> str | None:
    """Extract **Version:** date from a spec markdown file."""
    m = re.search(r"\*\*Version:\*\*\s*(\d{4}-\d{2}-\d{2})", content)
    return m.group(1) if m else None


def parse_pom(pom_xml: str) -> dict[str, Any]:
    """Extract parentVersion, starterVersion, and coreDependencies from a pom.xml.

    coreDependencies is a list of [artifactId, version] pairs for all
    io.openleap.core group dependencies that declare an explicit version.
    starterVersion is resolved from (in priority order):
      1. core-service-parent parent artifactId
      2. any io.openleap.*:core-* dependency (covers io.openleap.core,
         io.openleap.common, io.openleap.starter group variants)
      3. io.openleap:io.openleap.starter monolithic starter dependency

    Maven property references (${...}) are resolved from the <properties> block.
    """
    result: dict[str, Any] = {
        "parentVersion": None,
        "starterVersion": None,
        "coreDependencies": [],
    }

    # Extract <properties> for variable resolution
    props: dict[str, str] = {}
    props_match = re.search(r"<properties>\s*(.*?)\s*</properties>", pom_xml, re.DOTALL)
    if props_match:
        for pm in re.finditer(r"<([^/][^>]*)>([^<]+)</\1>", props_match.group(1)):
            props[pm.group(1).strip()] = pm.group(2).strip()

    def resolve(value: str) -> str:
        """Resolve ${property} references using the <properties> block."""
        return re.sub(r"\$\{([^}]+)\}", lambda m: props.get(m.group(1), m.group(0)), value)

    # Parent block
    parent_match = re.search(r"<parent>\s*(.*?)\s*</parent>", pom_xml, re.DOTALL)
    if parent_match:
        parent_block = parent_match.group(1)
        artifact_match = re.search(r"<artifactId>([^<]+)</artifactId>", parent_block)
        version_match = re.search(r"<version>([^<]+)</version>", parent_block)
        if artifact_match and version_match:
            artifact_id = artifact_match.group(1).strip()
            version = resolve(version_match.group(1).strip())
            if artifact_id == "core-service-parent":
                result["starterVersion"] = version
            elif artifact_id == "io.openleap.parent":
                result["parentVersion"] = version

    # Scan all dependencies for openleap platform artifacts
    dep_pattern = re.compile(
        r"<dependency>\s*"
        r"<groupId>([^<]+)</groupId>\s*"
        r"<artifactId>([^<]+)</artifactId>\s*"
        r"<version>([^<]+)</version>",
        re.DOTALL,
    )
    for m in dep_pattern.finditer(pom_xml):
        group_id = m.group(1).strip()
        artifact_id = m.group(2).strip()
        version = resolve(m.group(3).strip())

        if not group_id.startswith("io.openleap"):
            continue

        # Collect core dependencies (io.openleap.core group)
        if group_id == "io.openleap.core":
            result["coreDependencies"].append([artifact_id, version])

        # Detect starterVersion: any io.openleap.* group with a core-* artifact
        # (covers io.openleap.core, io.openleap.common, io.openleap.starter variants)
        if not result["starterVersion"] and artifact_id.startswith("core-"):
            result["starterVersion"] = version

        # Also catch monolithic io.openleap:io.openleap.starter dependency
        if not result["starterVersion"] and artifact_id == "io.openleap.starter":
            result["starterVersion"] = version

    return result


def find_backend_repos() -> set[str]:
    """Find repos with the 'backend-service' GitHub topic."""
    repos: set[str] = set()
    page = 1
    while True:
        resp = gh_get(
            "https://api.github.com/search/repositories",
            params={
                "q": f"org:{ORG} topic:{BACKEND_TOPIC}",
                "per_page": 100,
                "page": page,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            repos.add(item["name"])
        if len(repos) >= data.get("total_count", 0):
            break
        page += 1
    return repos


def determine_activity_status(repo_meta: dict) -> str:
    """Determine implementation status from repo metadata."""
    if repo_meta.get("archived"):
        return "archived"

    pushed_at = repo_meta.get("pushed_at")
    if not pushed_at:
        return "stale"

    try:
        last_push = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return "stale"

    now = datetime.now(timezone.utc)
    age = now - last_push

    if age <= timedelta(days=30):
        return "active"
    elif age <= timedelta(days=90):
        return "maintained"
    else:
        return "stale"


# ---------------------------------------------------------------------------
# Entry processing
# ---------------------------------------------------------------------------


def empty_entry() -> dict[str, Any]:
    """Return a new entry with all fields initialized to defaults."""
    return {
        "repository": None,
        "repositoryUrl": None,
        "implementationStatus": None,
        "hasSpecFolder": None,
        "implSpecVersion": None,
        "hasQaFolder": None,
        "qaFolderNotes": None,
        "notes": "",
        "lastAnalysisCommitHash": None,
        "lastAnalysisAt": None,
        "adrComplianceScore": None,
        "adrReviewGuidelinesVersion": None,
        "adrReviewCommitHash": None,
        "parentVersion": None,
        "starterVersion": None,
        "coreDependencies": [],
    }


def process_entry(entry: dict[str, Any], repo_meta: dict, existing_sha: str | None) -> dict[str, Any]:
    """Process a single backend-service repo entry. Returns updated entry."""
    repo_name = entry["repository"]

    print(f"  {repo_name}...", end=" ", flush=True)

    current_sha = get_head_sha(repo_name)

    if current_sha and current_sha == existing_sha:
        print("unchanged (skipping deep analysis)")
        return entry

    # Check spec/ folder
    has_spec = folder_exists(repo_name, "spec")
    entry["hasSpecFolder"] = has_spec

    if has_spec:
        spec_files = [f for f in list_folder(repo_name, "spec") if f.endswith(".md")]
        impl_version = None
        for sf in spec_files:
            content = get_file_content(repo_name, f"spec/{sf}")
            if content:
                v = extract_spec_version(content)
                if v:
                    impl_version = v
                    break
        entry["implSpecVersion"] = impl_version
    else:
        entry["implSpecVersion"] = None

    # Check qa/ folder
    has_qa = folder_exists(repo_name, "qa")
    entry["hasQaFolder"] = has_qa
    if not has_qa and not entry.get("qaFolderNotes"):
        entry["qaFolderNotes"] = f"Checked {TODAY} via GitHub API - no /qa folder found."

    # Read pom.xml for platform versions
    pom_content = get_file_content(repo_name, "pom.xml")
    if pom_content:
        pom = parse_pom(pom_content)
        entry["parentVersion"] = pom["parentVersion"]
        entry["starterVersion"] = pom["starterVersion"]
        entry["coreDependencies"] = pom["coreDependencies"]
    else:
        entry["parentVersion"] = None
        entry["starterVersion"] = None
        entry["coreDependencies"] = []

    # Activity status
    entry["implementationStatus"] = determine_activity_status(repo_meta)

    # Analysis metadata
    entry["lastAnalysisCommitHash"] = current_sha
    entry["lastAnalysisAt"] = TODAY
    entry["repositoryUrl"] = f"https://github.com/{ORG}/{repo_name}"

    print(f"done (status={entry['implementationStatus']})")
    return entry


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl OpenLeap backend-service repos")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(1)

    init_session(token)

    # Load existing data for SHA-based skip logic
    existing: dict[str, dict] = {}
    if REGISTRY_PATH.exists():
        try:
            prev = json.loads(REGISTRY_PATH.read_text())
            for svc in prev.get("services", []):
                if svc.get("repository"):
                    existing[svc["repository"]] = svc
        except Exception:
            pass

    # Find all backend-service repos
    print(f"Searching for repos with topic '{BACKEND_TOPIC}'...")
    backend_ids = find_backend_repos()
    print(f"Found {len(backend_ids)} repos with '{BACKEND_TOPIC}' topic")

    # Fetch org repos for metadata
    print("Fetching org repos (all pages)...")
    org_repo_list = list_org_repos()
    org_repos = {r["name"]: r for r in org_repo_list}
    print(f"Found {len(org_repos)} repos in {ORG}")

    # Process each backend-service repo
    print("\nProcessing repos:")
    services: list[dict[str, Any]] = []
    for repo_name in sorted(backend_ids):
        repo_meta = org_repos.get(repo_name)
        if not repo_meta:
            print(f"  {repo_name}... not found in org, skipping")
            continue

        prev_entry = existing.get(repo_name, {})

        # Start from prev_entry so all analysis fields survive SHA-based skips.
        # process_entry overwrites fields it re-analyzes; on skip it returns entry as-is.
        entry = {**empty_entry(), **prev_entry}
        entry["repository"] = repo_name
        entry["repositoryUrl"] = f"https://github.com/{ORG}/{repo_name}"

        entry = process_entry(entry, repo_meta, prev_entry.get("lastAnalysisCommitHash"))

        # Restore QA-owned fields (never overwrite)
        for k in QA_OWNED_FIELDS:
            if prev_entry.get(k) is not None:
                entry[k] = prev_entry[k]

        services.append(entry)

    # Build output
    registry = {
        "lastCrawled": TODAY,
        "lastUpdated": TODAY,
        "services": services,
    }

    output = json.dumps(registry, indent=2, ensure_ascii=False) + "\n"

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {len(services)} entries to {REGISTRY_PATH}")
    else:
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_PATH.write_text(output)
        print(f"\nWrote {len(services)} entries to {REGISTRY_PATH}")

    print(generate_summary(services))


def generate_summary(services: list[dict]) -> str:
    """Generate a markdown summary of the crawl results."""
    status_counts: dict[str, int] = {}
    qa_with = 0
    qa_without = 0
    adr_with = 0
    starter_versions: dict[str, int] = {}
    no_qa: list[str] = []
    no_spec_folder: list[str] = []

    for s in services:
        status = s.get("implementationStatus", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

        if s.get("hasQaFolder"):
            qa_with += 1
        else:
            qa_without += 1
            no_qa.append(s.get("repository", "?"))

        if not s.get("hasSpecFolder"):
            no_spec_folder.append(s.get("repository", "?"))

        if s.get("adrComplianceScore"):
            adr_with += 1

        sv = s.get("starterVersion")
        if sv:
            starter_versions[sv] = starter_versions.get(sv, 0) + 1

    lines = [
        f"\n## Implementation Status Summary — {TODAY}\n",
        f"**Total repos:** {len(services)}\n",
        "### Activity Status",
        "| Status | Count |",
        "|---|---|",
    ]
    for k in ["active", "maintained", "stale", "archived"]:
        if status_counts.get(k, 0) > 0:
            lines.append(f"| {k} | {status_counts[k]} |")

    lines += [
        "",
        "### QA Coverage",
        "| Metric | Count |",
        "|---|---|",
        f"| With QA folder | {qa_with} |",
        f"| Without QA folder | {qa_without} |",
        f"| With ADR compliance score | {adr_with} |",
    ]

    if starter_versions:
        lines += [
            "",
            "### Platform Versions (Starter)",
            "| Version | Repos |",
            "|---|---|",
        ]
        for v, n in sorted(starter_versions.items()):
            lines.append(f"| {v} | {n} |")

    lines += ["", "### Attention Required"]
    if no_qa:
        lines.append(f"- **No QA folder ({len(no_qa)}):** {', '.join(no_qa[:10])}")
    if no_spec_folder:
        lines.append(f"- **No /spec folder ({len(no_spec_folder)}):** {', '.join(no_spec_folder[:10])}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
