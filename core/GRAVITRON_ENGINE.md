# Gravitron Sovereign Engine v3.0

The **Gravitron Sovereign Engine** is a project-agnostic, self-contained efficiency layer for agentic development. It enforces a strict separation between **Logic Core** (runtimes/tools) and **State Silo** (data/brain).

## 🪐 Architecture

| Domain | Path | Purpose |
|---|---|---|
| **Logic Core** | `~/.gravitron/core` | Immutable guts: runtimes (Node/Py/Chrome), shims, and source logic. |
| **User Layer** | `~/.gravitron/usr` | Features: Customizable skills, prompts, and plugins. |
| **Data Silo**  | `~/.gemini/antigravity` | The Vault: Session brain, context DB, and snapshots. |

## 🚀 Unified Harness

All engine capabilities are accessed through a single, project-aware master router:

| Command | Subcommand | Description |
|---|---|---|
| `gravitron` | `snap` | Dual-mode snapshots (Blueprint/Ingest) for recovery or research. |
| `gravitron` | `util` | Context relay and HCF (Halt and Catch Fire) loop detection. |
| `gravitron` | `search` | Hybrid discovery: grep speed + ast-grep precision. |
| `gravitron` | `doctor` | Environmental health audit and runtime verification. |
| `gravitron` | `test` | Hallucination-free verification via Markdown scenarios. |
| `gravitron` | `npx`/`pip` | Global runtimes using internal Gravitron environments. |

## 🛡️ Sovereign Guardrails

- **HCF (Halt and Catch Fire)**: `gravitron util log` exits `137` if redundant actions are detected in the audit log.
- **Gateway Visibility**: Snapshots are symlinked to `~/.gravitron/output/snaps` for IDE visibility.
- **Encapsulated Rules**: Your project governance lives in `.gravitron/.antigravityrules`.

## 🛠️ Extensibility

New features are added by dropping scripts into `~/.gravitron/usr/plugins/`. The harness automatically discovers them as subcommands.
