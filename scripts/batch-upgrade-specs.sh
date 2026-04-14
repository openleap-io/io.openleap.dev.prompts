#!/usr/bin/env bash
#
# Batch Upgrade Domain Service Specs to TPL-SVC v1.0.0
#
# Runs the upgrade-domain-service-spec.md prompt against each domain service spec.
# Uses claude CLI in non-interactive mode (-p) with permission bypass for automation.
#
# Usage:
#   ./scripts/batch-upgrade-specs.sh                    # All specs
#   ./scripts/batch-upgrade-specs.sh --suite sd         # Only SD suite
#   ./scripts/batch-upgrade-specs.sh --dry-run          # List specs without running
#   ./scripts/batch-upgrade-specs.sh --resume-from FILE # Resume from a specific file
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROMPT_FILE="$REPO_ROOT/prompts/upgrade-domain-service-spec.md"
LOG_DIR="$REPO_ROOT/scripts/upgrade-logs"
SKIP_FILE="$REPO_ROOT/scripts/upgrade-skip.txt"

# Specs already upgraded (add paths here to skip)
ALREADY_DONE=(
  "spec/T3_Domains/SD/sd_shp-spec.md"
)

# Parse arguments
SUITE_FILTER=""
DRY_RUN=false
RESUME_FROM=""
MODEL="sonnet"
PARALLEL=1

while [[ $# -gt 0 ]]; do
  case $1 in
    --suite) SUITE_FILTER="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --resume-from) RESUME_FROM="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    --help)
      echo "Usage: $0 [--suite NAME] [--dry-run] [--resume-from FILE] [--model MODEL] [--parallel N]"
      echo ""
      echo "Options:"
      echo "  --suite NAME       Only process specs in this suite (e.g., sd, iam, pps)"
      echo "  --dry-run          List specs that would be processed, without running"
      echo "  --resume-from FILE Resume batch from this file (skip all before it)"
      echo "  --model MODEL      Claude model to use (default: sonnet)"
      echo "  --parallel N       Run N specs in parallel (default: 1)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

mkdir -p "$LOG_DIR"

# Collect all domain service spec files (exclude feature specs, suite specs, product specs)
mapfile -t ALL_SPECS < <(
  find "$REPO_ROOT/spec" -name '*-spec.md' \
    -not -name '*feature-spec*' \
    -not -name '*suite*' \
    -not -name '*product-spec*' \
    -not -path '*/features/*' \
    | sort
)

# Apply suite filter if specified
if [[ -n "$SUITE_FILTER" ]]; then
  FILTERED=()
  for spec in "${ALL_SPECS[@]}"; do
    if echo "$spec" | grep -qi "/$SUITE_FILTER[/_]"; then
      FILTERED+=("$spec")
    fi
  done
  ALL_SPECS=("${FILTERED[@]}")
fi

# Remove already-done specs
SPECS=()
for spec in "${ALL_SPECS[@]}"; do
  rel_path="${spec#$REPO_ROOT/}"
  skip=false
  for done_spec in "${ALREADY_DONE[@]}"; do
    if [[ "$rel_path" == "$done_spec" ]]; then
      skip=true
      break
    fi
  done
  # Also check skip file if it exists
  if [[ -f "$SKIP_FILE" ]] && grep -qF "$rel_path" "$SKIP_FILE"; then
    skip=true
  fi
  if ! $skip; then
    SPECS+=("$spec")
  fi
done

# Handle resume-from
if [[ -n "$RESUME_FROM" ]]; then
  RESUMED=()
  found=false
  for spec in "${SPECS[@]}"; do
    if [[ "$spec" == *"$RESUME_FROM"* ]]; then
      found=true
    fi
    if $found; then
      RESUMED+=("$spec")
    fi
  done
  if ! $found; then
    echo "ERROR: --resume-from file not found in spec list: $RESUME_FROM"
    exit 1
  fi
  SPECS=("${RESUMED[@]}")
fi

echo "============================================"
echo "Batch Spec Upgrade to TPL-SVC v1.0.0"
echo "============================================"
echo "Total specs to process: ${#SPECS[@]}"
echo "Model: $MODEL"
echo "Parallel: $PARALLEL"
echo "Log directory: $LOG_DIR"
echo "============================================"
echo ""

if $DRY_RUN; then
  echo "DRY RUN — specs that would be processed:"
  echo ""
  for i in "${!SPECS[@]}"; do
    rel="${SPECS[$i]#$REPO_ROOT/}"
    echo "  $((i + 1)). $rel"
  done
  echo ""
  echo "Run without --dry-run to execute."
  exit 0
fi

TOTAL=${#SPECS[@]}
RESULTS_DIR=$(mktemp -d)

# Function to upgrade a single spec
upgrade_spec() {
  local spec="$1"
  local idx="$2"
  local total="$3"
  local repo_root="$4"
  local model="$5"
  local log_dir="$6"
  local skip_file="$7"
  local results_dir="$8"

  local rel_path="${spec#$repo_root/}"
  local log_name
  log_name=$(echo "$rel_path" | tr '/' '_' | sed 's/.md$//')
  local log_file="$log_dir/${log_name}.log"

  echo "[$idx/$total] Starting: $rel_path"

  local prompt="Read the upgrade prompt at prompts/upgrade-domain-service-spec.md and apply it to ${rel_path}. Follow all 10 steps in the prompt. The parameter {SPEC_FILE} is ${rel_path}. Write the upgraded spec in place. Do not ask questions — use OPEN QUESTION entries for unknowns."

  if claude -p "$prompt" \
    --model "$model" \
    --dangerously-skip-permissions \
    --no-session-persistence \
    > "$log_file" 2>&1; then

    echo "[$idx/$total] ✓ Done: $rel_path"
    echo "$rel_path" >> "$skip_file"
    echo "ok" > "$results_dir/$idx"
  else
    echo "[$idx/$total] ✗ FAILED: $rel_path (see $log_file)"
    echo "fail" > "$results_dir/$idx"
  fi
}

export -f upgrade_spec

if [[ "$PARALLEL" -le 1 ]]; then
  # Sequential execution
  for i in "${!SPECS[@]}"; do
    upgrade_spec "${SPECS[$i]}" "$((i + 1))" "$TOTAL" "$REPO_ROOT" "$MODEL" "$LOG_DIR" "$SKIP_FILE" "$RESULTS_DIR"
  done
else
  # Parallel execution using background jobs
  RUNNING=0
  for i in "${!SPECS[@]}"; do
    upgrade_spec "${SPECS[$i]}" "$((i + 1))" "$TOTAL" "$REPO_ROOT" "$MODEL" "$LOG_DIR" "$SKIP_FILE" "$RESULTS_DIR" &
    RUNNING=$((RUNNING + 1))

    # Wait if we hit the parallel limit
    if [[ "$RUNNING" -ge "$PARALLEL" ]]; then
      wait -n 2>/dev/null || true
      RUNNING=$((RUNNING - 1))
    fi
  done

  # Wait for remaining jobs
  wait
fi

# Count results
SUCCESS=0
FAILED=0
for f in "$RESULTS_DIR"/*; do
  [[ -f "$f" ]] || continue
  if [[ "$(cat "$f")" == "ok" ]]; then
    SUCCESS=$((SUCCESS + 1))
  else
    FAILED=$((FAILED + 1))
  fi
done
rm -rf "$RESULTS_DIR"

echo "============================================"
echo "Batch Upgrade Complete"
echo "============================================"
echo "  Total:   $TOTAL"
echo "  Success: $SUCCESS"
echo "  Failed:  $FAILED"
echo "============================================"

if [[ $FAILED -gt 0 ]]; then
  echo ""
  echo "Failed specs — check logs in $LOG_DIR"
  exit 1
fi
