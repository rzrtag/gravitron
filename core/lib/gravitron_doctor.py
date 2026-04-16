#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

GRAVITRON_ROOT  = os.environ.get("GRAVITRON_ROOT",  os.path.expanduser("~/.gravitron"))
GRAVITRON_CORE  = os.path.join(GRAVITRON_ROOT, "core")
GRAVITRON_USR   = os.path.join(GRAVITRON_ROOT, "usr")
GRAVITRON_STATE = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))

def check_env():
    print("--- [1/3] Environment Audit ---")
    vars = ["GRAVITRON_ROOT", "GRAVITRON_STATE", "GRAVITRON_CORE"]
    for v in vars:
        val = os.environ.get(v)
        status = "✓" if val else "✗"
        print(f"  {status} {v}: {val}")

def check_runtimes():
    print("\n--- [2/3] Runtime Connectivity ---")
    runtimes = [
        ("Node", f"{GRAVITRON_CORE}/runtimes/node/bin/node --version"),
        ("Python", f"{GRAVITRON_CORE}/runtimes/python/bin/python3 --version"),
        ("Browser", f"ls {GRAVITRON_CORE}/runtimes/browser/chrome-linux64/chrome")
    ]
    for name, cmd in runtimes:
        try:
            res = subprocess.run(cmd.split(), capture_output=True, text=True)
            if res.returncode == 0:
                print(f"  ✓ {name}: {res.stdout.strip() or 'Found'}")
            else:
                print(f"  ✗ {name}: Failed (exit {res.returncode})")
        except Exception as e:
            print(f"  ✗ {name}: Missing or Unreachable ({e})")

def check_silo():
    print("\n--- [3/3] Silo Connectivity ---")
    snapshots = os.path.join(GRAVITRON_STATE, "snapshots")
    if os.path.isdir(snapshots):
        rel_state = GRAVITRON_STATE.replace(os.path.expanduser("~"), "~")
        print(f"  ✓ State Silo: Connected ({rel_state})")
        projects = os.listdir(snapshots)
        print(f"  ✓ Active Silos: {', '.join(projects) if projects else 'None'}")
    else:
        print(f"  ✗ State Silo: DISCONNECTED (Missing path: {snapshots})")

def check_skills():
    print("\n--- [4/4] Skill Registry Integrity ---")
    skill_dir = os.path.join(GRAVITRON_USR, "skills")
    if not os.path.isdir(skill_dir):
        print(f"  ✗ Skills directory missing: {skill_dir}")
        return
    skills = [f for f in os.listdir(skill_dir) if f.endswith(".md")]
    if not skills:
        print("  ⚠ No skills found in usr/skills/")
        return
    for fname in skills:
        fpath = os.path.join(skill_dir, fname)
        with open(fpath) as f:
            content = f.read()
        has_title = content.strip().startswith("#")
        has_section = any(l.startswith("##") for l in content.splitlines())
        status = "✓" if has_title and has_section else "⚠"
        print(f"  {status} {fname}")

if __name__ == "__main__":
    print("=== [Gravitron Doctor] Logic Core Physical Audit ===")
    check_env()
    check_runtimes()
    check_silo()
    check_skills()
    print("\nAudit Complete.")
