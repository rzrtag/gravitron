---
description: Total codebase recovery from a self-contained snapshot file.
---

## Phoenix Protocol — Zero-Dependency Rebuild

Every snapshot produced by `gravitron snap` contains its own engine source code.
You can rebuild a lost system using **only the snapshot file**.

### Step 1 — Extract the Engine
Open the snapshot `.md` file and find the block:
```
### `TIME_SWITCH_ENGINE.py` [SOURCE]
```
Copy the Python source from that block and save it as `time_switch.py`.

### Step 2 — Run the Rebuild
```bash
python3 time_switch.py rebuild /path/to/snapshot.md --target /path/to/restore-dir
```

### Step 3 — If gravitron snap is already installed
```bash
gravitron snap rebuild /path/to/snapshot.md --target /path/to/restore-dir
```

### Step 4 — Verify
```
ls /path/to/restore-dir
```
The full directory tree should be restored with original file permissions.

---

## Snapshot Locations

Active snapshots are stored per-project at:
```
~/.gemini/antigravity/snapshots/
├── workspace/
│   ├── 0414-2356-snapshot.md
│   └── archive/
├── iron-void/
└── ...
```

Manual archive (move active → archive):
```bash
gravitron snap archive --project workspace
```

Auto-archive triggers at **30 snapshots** per project.
