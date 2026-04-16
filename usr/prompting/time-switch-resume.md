---
description: Session resumption protocol — ingest the latest snapshot and synchronize project state.
---

## Resilience Protocol

### Step 1 — Find the Latest Snapshot
```bash
gravitron snap list
```
To rebuild the codebase from this snapshot, use the **Project Phoenix** procedure:

1. Identify the snapshot: `gravitron snap list`
2. **Rebuild**: `gravitron snap rebuild <snapshot-file> --target /path/to/restore`

> [!WARNING]
> If rebuilding from an **INGEST** snapshot, some large or non-core files may be truncated. Always prefer **BLUEPRINT** for full recovery.

### Step 2 — Ingest Snapshot
Read the latest snapshot file from:
`~/.gemini/antigravity/snapshots/<project-name>/`

Identify: active project, current phase, last completed step, and defined Next Step.

### Step 3 — Read Workstation Core (if available)
Review global instruction sets in `~/.gemini/antigravity/prompting/`:
-Use the `gravitron snap` engine to capture the current state of the workspace.

**Blueprint Mode** (Complete recovery):
`gravitron snap snap . --mode blueprint --tag "milestone-1"`

**Ingest Mode** (Research & Analysis):
`gravitron snap snap . --mode ingest --tag "research-session"`
nix.md` — total codebase recovery

### Step 4 — Synchronize Project State
1. Read the active project `README.md` to identify the current **Next Step**.
2. Read any `gem-*` research artifacts in scope.

### Step 5 — Propose Engagement
State the current understood status and confirm with the user before proceeding.
