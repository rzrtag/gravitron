#!/usr/bin/env python3
"""
gravitron brief — Auto-generate a structured session context block.

Reads from: project manifest, snapshots, skills, plugins, context.db.
Outputs a comprehensive brief to inject at the start of any agent session.
"""
import os
import sys
import sqlite3
import datetime
import subprocess

GRAVITRON_ROOT  = os.environ.get("GRAVITRON_ROOT", os.path.expanduser("~/.gravitron"))
GRAVITRON_CORE  = os.path.join(GRAVITRON_ROOT, "core")
GRAVITRON_USR   = os.path.join(GRAVITRON_ROOT, "usr")
GRAVITRON_STATE = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))

# ── Project Discovery ────────────────────────────────────────────────────────
def find_project():
    cwd = os.getcwd()
    while cwd != "/":
        if os.path.exists(os.path.join(cwd, ".gravitron")):
            return cwd, os.path.basename(cwd)
        cwd = os.path.dirname(cwd)
    return None, None

# ── Snapshot Intel ───────────────────────────────────────────────────────────
def get_snapshot_info(project_name):
    snaps_dir = os.path.join(GRAVITRON_STATE, "snapshots", project_name or "workspace")
    if not os.path.isdir(snaps_dir):
        return []
    snaps = sorted(
        [(f, os.path.getmtime(os.path.join(snaps_dir, f)))
         for f in os.listdir(snaps_dir) if f.endswith(".md")],
        key=lambda x: x[1], reverse=True
    )
    result = []
    for fname, mtime in snaps[:3]:
        size  = os.path.getsize(os.path.join(snaps_dir, fname))
        age   = datetime.datetime.now() - datetime.datetime.fromtimestamp(mtime)
        hours = int(age.total_seconds() // 3600)
        mins  = int((age.total_seconds() % 3600) // 60)
        age_s = f"{hours}h {mins}m ago" if hours else f"{mins}m ago"
        result.append((fname, size / 1024, age_s))
    return result

# ── Skills ───────────────────────────────────────────────────────────────────
def get_skills():
    skill_dir = os.path.join(GRAVITRON_USR, "skills")
    if not os.path.isdir(skill_dir):
        return []
    skills = []
    for fname in sorted(os.listdir(skill_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(skill_dir, fname)
        with open(fpath) as f:
            first_lines = [l.strip() for l in f.readlines()[:5] if l.strip()]
        # Grab first non-title line as summary
        summary = next((l.lstrip("#").strip() for l in first_lines if not l.startswith("#")), "")
        skills.append((fname, summary[:80]))
    return skills

# ── Plugins ──────────────────────────────────────────────────────────────────
def get_plugins():
    plugin_dir = os.path.join(GRAVITRON_USR, "plugins")
    if not os.path.isdir(plugin_dir):
        return [], []
    enabled, disabled = [], []
    for fname in sorted(os.listdir(plugin_dir)):
        name = os.path.splitext(fname.replace(".disabled", ""))[0]
        desc = ""
        try:
            with open(os.path.join(plugin_dir, fname)) as f:
                for line in f.readlines()[:10]:
                    if "description:" in line:
                        desc = line.split(":", 1)[1].strip()[:60]
                        break
        except: pass
        if fname.endswith(".disabled"):
            disabled.append((name, desc))
        elif fname.endswith((".py", ".sh")):
            enabled.append((name, desc))
    return enabled, disabled

# ── Context Relay ────────────────────────────────────────────────────────────
def get_recent_context():
    db_path = os.path.join(GRAVITRON_STATE, "context.db")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        cur  = conn.cursor()
        cur.execute("SELECT id, created_at FROM context ORDER BY created_at DESC LIMIT 3")
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        return []

# ── Git Status ───────────────────────────────────────────────────────────────
def get_git_status():
    try:
        log = subprocess.check_output(
            ["git", "-C", GRAVITRON_ROOT, "log", "--oneline", "-3"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return log.splitlines()
    except:
        return []

# ── Render ───────────────────────────────────────────────────────────────────
def render_brief():
    project_path, project_name = find_project()
    snaps    = get_snapshot_info(project_name)
    skills   = get_skills()
    enabled_plugins, disabled_plugins = get_plugins()
    ctx_rows = get_recent_context()
    git_log  = get_git_status()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║         🪐 GRAVITRON SESSION BRIEF                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Project
    if project_path:
        print(f"  📁 Project   : {project_name} ({project_path})")
    else:
        print(f"  📁 Project   : No manifest detected (global context)")
    print(f"  🗄  State Silo : {GRAVITRON_STATE}")
    print()

    # Snapshots
    print("  📸 Recent Snapshots:")
    if snaps:
        for fname, size_kb, age in snaps:
            mode = "blueprint" if "blueprint" in fname else "ingest" if any(t in fname for t in ["-missile", "-ingest"]) else "snap"
            print(f"     [{mode:9s}] {fname:<42} {size_kb:6.0f} KB  {age}")
    else:
        print("     No snapshots found — run: gravitron snap .")
    print()

    # Skills
    print(f"  🧠 Active Skills ({len(skills)}):")
    for fname, summary in skills:
        print(f"     • {fname:<30} {summary}")
    print()

    # Plugins
    print(f"  🔌 Plugins  ({len(enabled_plugins)} enabled, {len(disabled_plugins)} disabled):")
    for name, desc in enabled_plugins:
        print(f"     ✓ gravitron {name:<22} {desc}")
    if disabled_plugins:
        for name, _ in disabled_plugins:
            print(f"     ✗ {name} [disabled]")
    print()

    # Context Relay
    print(f"  💾 Context Relay (last {len(ctx_rows)} entries):")
    if ctx_rows:
        for ctx_id, created_at in ctx_rows:
            print(f"     ctx:{ctx_id}  ({created_at})")
    else:
        print("     Empty — clean slate")
    print()

    # Engine Git Log
    print("  🔧 Engine Commits (last 3):")
    for entry in git_log:
        print(f"     {entry}")
    print()

    print("  ─────────────────────────────────────────────────────────")
    print("  Run 'gravitron doctor' for full health audit.")
    print("  Run 'gravitron test' to verify all tools.")
    print()

if __name__ == "__main__":
    render_brief()
