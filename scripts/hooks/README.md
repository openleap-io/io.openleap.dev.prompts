# Git Hooks

Shared hooks for the spec repository. Install by copying to `.git/hooks/`:

```bash
cp scripts/hooks/* .git/hooks/
chmod +x .git/hooks/*
```

## post-commit

Detects when spec files tracked by `landscape/impl-status.json` in [dev.hub](https://github.com/openleap-io/io.openleap.dev.hub) are modified in a commit but the status file itself is not updated. Injects an `attentionRequired` entry into the JSON so the dashboard surfaces a staleness warning.

**Behavior:**
- Spec changed, status NOT updated → adds `attentionRequired[].type = "dashboard-stale"` warning
- Status file updated in same commit → clears any existing warning
- Non-spec commits → no action

**Requires:** Python 3 (for JSON manipulation)
