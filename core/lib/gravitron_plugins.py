#!/usr/bin/env python3
"""
## Gravitron Plugin Manager
name: plugins
description: List, enable, and disable Gravitron plugins and skills
version: 1.1
commands: [list, enable, disable, skills, skill-enable, skill-disable]
"""
import os
import sys
import re

GRAVITRON_ROOT = os.environ.get("GRAVITRON_ROOT", os.path.expanduser("~/.gravitron"))
PLUGIN_DIR     = os.path.join(GRAVITRON_ROOT, "usr", "plugins")
SKILL_DIR      = os.path.join(GRAVITRON_ROOT, "usr", "skills")

# ── Metadata Parsing ─────────────────────────────────────────────────────────
def get_metadata(filepath):
    """Parse structured YAML-style metadata from a plugin/skill docstring or comment header."""
    name        = os.path.splitext(os.path.basename(filepath).replace(".disabled", ""))[0]
    description = ""
    version     = ""
    commands    = ""
    try:
        with open(filepath, errors="replace") as f:
            content = f.read(2048)
        for line in content.splitlines():
            stripped = line.strip().lstrip("#").lstrip("*").strip()
            if stripped.startswith("description:"):
                description = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("version:"):
                version = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("commands:"):
                commands = stripped.split(":", 1)[1].strip()
            # For markdown skills: use first non-title line as description
            elif not description and stripped and not stripped.startswith("#") and not any(
                stripped.startswith(k) for k in ("name:", "version:", "commands:", "---")
            ):
                if len(stripped) > 10:
                    description = stripped[:80]
    except:
        pass
    return name, description, version

# ── Plugin Management ─────────────────────────────────────────────────────────
def _scan_dir(directory, exts=(".py", ".sh"), md_exts=None):
    """Scan a directory and return (enabled, disabled) lists of full paths."""
    if md_exts:
        all_exts = exts + md_exts
    else:
        all_exts = exts
    enabled, disabled = [], []
    if not os.path.isdir(directory):
        return enabled, disabled
    for fname in sorted(os.listdir(directory)):
        full = os.path.join(directory, fname)
        if fname.endswith(".disabled"):
            disabled.append(full)
        elif any(fname.endswith(e) for e in all_exts):
            enabled.append(full)
    return enabled, disabled

def list_plugins():
    enabled, disabled = _scan_dir(PLUGIN_DIR)
    print("=== [Gravitron Plugins] Installed Capabilities ===\n")
    if enabled:
        print("  ENABLED:")
        for f in enabled:
            name, desc, ver = get_metadata(f)
            ver_s = f" v{ver}" if ver else ""
            print(f"    ✓  gravitron {name:<22} {ver_s:<6}  {desc[:55]}")
    if disabled:
        print("\n  DISABLED:")
        for f in disabled:
            name, desc, ver = get_metadata(f)
            print(f"    ✗  {name:<30}  {desc[:55]} [disabled]")
    print(f"\n  Tip: gravitron enable <name> | gravitron disable <name>")

def list_skills():
    enabled, disabled = _scan_dir(SKILL_DIR, exts=(), md_exts=(".md",))
    print("=== [Gravitron Skills] Behavioral Registry ===\n")
    if enabled:
        print("  ACTIVE:")
        for f in enabled:
            name, desc, _ = get_metadata(f)
            print(f"    ✓  {name:<30}  {desc[:60]}")
    if disabled:
        print("\n  INACTIVE:")
        for f in disabled:
            name, desc, _ = get_metadata(f)
            print(f"    ✗  {name:<30}  {desc[:60]} [disabled]")
    print(f"\n  Tip: gravitron skill-enable <name> | gravitron skill-disable <name>")

def _enable(directory, name, label="gravitron"):
    for fname in os.listdir(directory):
        if fname.startswith(name) and fname.endswith(".disabled"):
            src = os.path.join(directory, fname)
            dst = src.replace(".disabled", "")
            os.rename(src, dst)
            if dst.endswith((".py", ".sh")):
                os.chmod(dst, 0o755)
            print(f"  ✓ Enabled: {label} {name}")
            return
    print(f"  ✗ '{name}' not found in disabled state.")

def _disable(directory, name, label="gravitron"):
    for fname in os.listdir(directory):
        # Match without .disabled suffix
        base = fname.replace(".disabled", "")
        stem = os.path.splitext(base)[0] if not base.endswith(".md") else base.replace(".md", "")
        if stem == name and not fname.endswith(".disabled"):
            src = os.path.join(directory, fname)
            dst = src + ".disabled"
            os.rename(src, dst)
            print(f"  ✗ Disabled: {name}")
            return
    print(f"  ✗ '{name}' not found in enabled state.")

# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        list_plugins()
    elif cmd == "enable" and len(sys.argv) > 2:
        _enable(PLUGIN_DIR, sys.argv[2])
    elif cmd == "disable" and len(sys.argv) > 2:
        _disable(PLUGIN_DIR, sys.argv[2])
    elif cmd == "skills":
        list_skills()
    elif cmd == "skill-enable" and len(sys.argv) > 2:
        _enable(SKILL_DIR, sys.argv[2], label="skill")
    elif cmd == "skill-disable" and len(sys.argv) > 2:
        _disable(SKILL_DIR, sys.argv[2], label="skill")
    else:
        print("Usage: gravitron plugins | skills")
        print("       gravitron enable/disable <plugin>")
        print("       gravitron skill-enable/skill-disable <skill>")
