# Agent Orchestration Shortcuts
# Loaded automatically via `gravitron brief` at session start.
#
# Shortcode format: [noun][action]
#   noun   → what you are operating on
#   action → what you want to do
#
# When a user types a shortcode, the agent executes the mapped
# Gravitron command immediately without further clarification.

## Shortcode Reference

| Shortcode          | Gravitron Command                                              | Description                              |
|--------------------|--------------------------------------------------------------|------------------------------------------|
| `[snap][ingest]`   | `gravitron snap . --mode ingest --tag midnight-missile`      | Fire ingest snapshot for deep research   |
| `[snap][blueprint]`| `gravitron snap .`                                           | Full recovery blueprint snapshot         |
| `[snap][list]`     | `ls -lh ~/.gravitron/output/snaps/`                          | List available snapshots                 |
| `[doc][run]`       | `gravitron doctor`                                           | Full environmental health audit          |
| `[test][run]`      | `gravitron test ~/.gravitron/usr/tests/`                     | Run full integration test suite          |
| `[brief][run]`     | `gravitron brief`                                            | Generate session context brief           |
| `[engine][push]`   | `gravitron push-update`                                      | Commit and push engine to GitHub         |
| `[engine][pull]`   | `gravitron update`                                           | Pull latest engine from GitHub           |
| `[plugin][list]`   | `gravitron plugins`                                          | List installed plugins with versions     |
| `[skill][list]`    | `gravitron skills`                                           | List active behavioral skills            |
| `[ctx][ttl]`       | `gravitron context-ttl`                                      | Expire stale context relay entries       |
| `[ctx][validate]`  | `gravitron skill-validator`                                  | Audit skill registry for integrity       |

## Noun Taxonomy

| Noun      | Domain                          |
|-----------|---------------------------------|
| `snap`    | Snapshot engine operations      |
| `doc`     | Engine health and diagnostics   |
| `test`    | Integration test suite          |
| `brief`   | Session context aggregation     |
| `engine`  | Git-backed Logic Core (GitHub)  |
| `plugin`  | Plugin management               |
| `skill`   | Behavioral skill registry       |
| `ctx`     | Context relay / SQLite store    |

## Action Taxonomy

| Action      | Meaning                              |
|-------------|--------------------------------------|
| `ingest`    | Generate research-optimized output   |
| `blueprint` | Generate full-recovery output        |
| `list`      | Display available items              |
| `run`       | Execute the primary command          |
| `push`      | Send to remote / GitHub              |
| `pull`      | Fetch latest from remote / GitHub    |
| `ttl`       | Clean up expired / stale data        |
| `validate`  | Run integrity checks                 |

## Expansion Protocol

To add a new shortcode:
1. Add a row to the Shortcode Reference table above.
2. If adding a new noun: add it to the Noun Taxonomy.
3. If adding a new action: add it to the Action Taxonomy.
4. Run `gravitron push-update "feat: add [noun][action] shortcode"`.

No code changes required. The agent reads this table at session start.
