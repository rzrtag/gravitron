#!/usr/bin/env python3
"""
## Gravitron Plugin: Shortcode Dispatcher
name: shortcut
description: Execute [noun][action] agent orchestration shortcodes
version: 1.0
commands: [gravitron shortcut "[noun][action]"]
"""
import os
import sys
import re
import subprocess

GRAVITRON_ROOT  = os.environ.get("GRAVITRON_ROOT", os.path.expanduser("~/.gravitron"))
GRAVITRON_STATE = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))

# ── Shortcode Registry ────────────────────────────────────────────────────────
# Format: (noun, action) → command_string
# Command strings are passed to subprocess shell=True within the Gravitron env.
REGISTRY = {
    ("snap",   "ingest"):    "gravitron snap . --mode ingest --tag midnight-missile",
    ("snap",   "blueprint"): "gravitron snap .",
    ("snap",   "list"):      f"ls -lh {GRAVITRON_ROOT}/output/snaps/",
    ("doc",    "run"):       "gravitron doctor",
    ("test",   "run"):       f"gravitron test {GRAVITRON_ROOT}/usr/tests/",
    ("brief",  "run"):       "gravitron brief",
    ("engine", "push"):      "gravitron push-update",
    ("engine", "pull"):      "gravitron update",
    ("plugin", "list"):      "gravitron plugins",
    ("skill",  "list"):      "gravitron skills",
    ("ctx",    "ttl"):       "gravitron context-ttl",
    ("ctx",    "validate"):  "gravitron skill-validator",
}

def parse_shortcode(raw):
    """Parse '[noun][action]' or 'noun action' — returns (noun, action, remaining_args)."""
    raw = raw.strip()
    # Bracket syntax: [snap][ingest] [extra args...]
    m = re.match(r'\[(\w[\w-]*)\]\[(\w[\w-]*)\](.*)', raw)
    if m:
        return m.group(1).lower(), m.group(2).lower(), m.group(3).strip()
    # Space syntax: noun action [extra args...]
    parts = raw.lower().split(None, 2)
    if len(parts) >= 2:
        return parts[0], parts[1], parts[2] if len(parts) > 2 else ""
    return None, None, ""

def list_shortcuts():
    print("=== [Gravitron Shortcodes] Agent Orchestration Registry ===\n")
    # Group by noun
    nouns = sorted(set(n for n, _ in REGISTRY))
    for noun in nouns:
        actions = {a: cmd for (n, a), cmd in REGISTRY.items() if n == noun}
        for action, cmd in sorted(actions.items()):
            print(f"  [{noun}][{action}]  →  {cmd}")
    print(f"\n  Usage:  gravitron shortcut \"[noun][action]\"")
    print(f"  Edit:   {GRAVITRON_ROOT}/usr/skills/agent-shortcuts.md")

def dispatch(raw):
    noun, action, extra_args = parse_shortcode(raw)
    if not noun:
        print(f"  ✗ Could not parse shortcode: '{raw}'")
        print(f"    Expected format: [noun][action] or 'noun action'")
        sys.exit(1)

    key = (noun, action)
    if key not in REGISTRY:
        print(f"  ✗ Unknown shortcode: [{noun}][{action}]")
        print(f"    Run 'gravitron shortcut list' to see available shortcuts.")
        sys.exit(1)

    cmd = REGISTRY[key]
    if extra_args:
        cmd = f"{cmd} {extra_args}"
    print(f"  ▶  [{noun}][{action}]  →  {cmd}\n")
    
    # Source bootstrap so Gravitron env is available
    bootstrap = os.path.join(GRAVITRON_ROOT, "core", "bin", "bootstrap.sh")
    full_cmd = f"source {bootstrap} && {cmd}"
    result = subprocess.run(full_cmd, shell=True, executable="/bin/bash")
    sys.exit(result.returncode)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        list_shortcuts()
    else:
        dispatch(" ".join(sys.argv[1:]))
