#!/usr/bin/env python3
"""
## Gravitron Plugin: Plugin Manager
name: plugins
description: List, enable, and disable Gravitron plugins in usr/plugins/
version: 1.0
commands: [list, enable, disable]
"""
import os
import sys

GRAVITRON_ROOT = os.environ.get("GRAVITRON_ROOT", os.path.expanduser("~/.gravitron"))
PLUGIN_DIR = os.path.join(GRAVITRON_ROOT, "usr", "plugins")

def get_metadata(filepath):
    """Extract name/description from a plugin's docstring header."""
    name, description = os.path.splitext(os.path.basename(filepath))[0], ""
    try:
        with open(filepath) as f:
            content = f.read(1024)
        for line in content.splitlines():
            line = line.strip().lstrip("#").lstrip("*").strip()
            if line.startswith("description:"):
                description = line.split(":", 1)[1].strip()
                break
    except:
        pass
    return name, description

def list_plugins():
    print("=== [Gravitron Plugins] Installed Capabilities ===\n")
    enabled, disabled = [], []
    for fname in sorted(os.listdir(PLUGIN_DIR)):
        full = os.path.join(PLUGIN_DIR, fname)
        if fname.endswith(".disabled"):
            disabled.append(full)
        elif fname.endswith((".py", ".sh")):
            enabled.append(full)

    if enabled:
        print("  ENABLED:")
        for f in enabled:
            name, desc = get_metadata(f)
            print(f"    ✓  gravitron {name:<20} — {desc}")
    
    if disabled:
        print("\n  DISABLED:")
        for f in disabled:
            base = os.path.basename(f).replace(".disabled", "")
            name = os.path.splitext(base)[0]
            _, desc = get_metadata(f)
            print(f"    ✗  {name:<28} — {desc} [disabled]")

    print(f"\n  Tip: gravitron enable <name> | gravitron disable <name>")

def enable_plugin(name):
    for fname in os.listdir(PLUGIN_DIR):
        if fname.startswith(name) and fname.endswith(".disabled"):
            src = os.path.join(PLUGIN_DIR, fname)
            dst = src.replace(".disabled", "")
            os.rename(src, dst)
            os.chmod(dst, 0o755)
            print(f"  ✓ Enabled: gravitron {name}")
            return
    print(f"  ✗ Plugin '{name}' not found in disabled state.")

def disable_plugin(name):
    for fname in os.listdir(PLUGIN_DIR):
        base = os.path.splitext(fname)[0]
        ext = os.path.splitext(fname)[1]
        if base == name and ext in (".py", ".sh"):
            src = os.path.join(PLUGIN_DIR, fname)
            dst = src + ".disabled"
            os.rename(src, dst)
            print(f"  ✗ Disabled: {name}")
            return
    print(f"  ✗ Plugin '{name}' not found in enabled state.")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        list_plugins()
    elif cmd == "enable" and len(sys.argv) > 2:
        enable_plugin(sys.argv[2])
    elif cmd == "disable" and len(sys.argv) > 2:
        disable_plugin(sys.argv[2])
    else:
        print("Usage: gravitron plugins [list | enable <name> | disable <name>]")
