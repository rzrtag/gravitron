---
description: Session-close protocol — snapshot the current project state for Gemini Deep Research / NotebookLM / session recovery.
---

## When to Run This

Proactively suggest this workflow when any of these are true:
- A clear phase transition is reached (e.g., research → implementation, tooling → deployment).
- The conversation has accumulated significant iteration noise.
- Clean, documented artifacts now exist and there's no urgent continuation needed.

**Required agent signal phrase**:
> ⚠️ **ADVICE: START NEW CONVERSATION** — context is bloated. Running session close workflow now.

---

## Session Close Workflow

### Step 1 — Update Active READMEs
For every active project directory:
- Update `README.md` to reflect current pipeline status and key findings.
- Ensure the **Next Step** is clearly defined for the next session.

### Step 2 — Run the Snapshot
Decide on the mode based on the objective:

**Blueprint Mode** (Complete recovery/Project Phoenix):
```bash
gravitron snap snap ~/workspace --mode blueprint --tag "v2-stable"
```

**Ingest Mode** (Research/Deep Dive/NotebookLM):
```bash
gravitron snap snap ~/workspace --mode ingest --tag "context-ingest"
```

The snapshot is stored in:
`~/.gemini/antigravity/snapshots/<project-name>/MMDD-HHMM[-tag]-snapshot.md`

Each snapshot is **self-contained** — it embeds the engine source and rebuild protocol.

### Step 3 — Confirm and Report
```bash
gravitron snap list
```
Confirm the snapshot appears and report the path + file count to the user.

> ✓ Session close complete. To resume: start a new conversation and follow `gravitron snap-resume.md`.
