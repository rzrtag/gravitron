#!/usr/bin/env python3
"""
## Gravitron Plugin: Skill Validator
name: skill-validator
description: Audit usr/skills/ for structural integrity and adversarial injection patterns
version: 1.0
commands: [gravitron skill-validator]
"""
import os
import sys
import re

GRAVITRON_ROOT = os.environ.get("GRAVITRON_ROOT", os.path.expanduser("~/.gravitron"))
SKILL_DIR = os.path.join(GRAVITRON_ROOT, "usr", "skills")

FORBIDDEN_PHRASES = [
    "ignore previous instructions",
    "bypass constraints",
    "forget all prior",
    "disregard rules",
    "you are now",
    "pretend you are",
]

REQUIRED_SECTIONS = ["##"]  # Must have at least one H2 section

def validate_skill(filepath):
    issues = []
    warnings = []
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return False, [f"File read error: {e}"], []

    lower = content.lower()

    # Pass 1: Check minimum structure (has a title + sections)
    if not content.strip().startswith("#"):
        warnings.append("No H1 title found — skill may not be parseable by agent")
    
    has_section = any(line.startswith("##") for line in content.splitlines())
    if not has_section:
        warnings.append("No H2 sections found — skill lacks structured directives")

    # Pass 2: Minimum content length
    if len(content.strip()) < 100:
        warnings.append(f"Very short skill ({len(content)} chars) — may provide insufficient guidance")

    # Pass 3: ToxicSkill adversarial scan
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            issues.append(f"SECURITY: Forbidden phrase detected: '{phrase}'")

    # Pass 4: Check for any external URL injection
    urls = re.findall(r"https?://(?!github\.com|docs\.python\.org)", content)
    if urls:
        warnings.append(f"External URLs found ({len(urls)}) — verify they are not injections: {urls[:2]}")

    return len(issues) == 0, issues, warnings

def run_audit():
    print("=== [Skill Validator] Gravitron Skill Registry Audit ===\n")
    
    if not os.path.isdir(SKILL_DIR):
        print(f"  ✗ Skill directory not found: {SKILL_DIR}")
        sys.exit(1)

    skills = [f for f in os.listdir(SKILL_DIR) if f.endswith(".md")]
    if not skills:
        print("  No skills found.")
        return

    pass_count, fail_count, warn_count = 0, 0, 0
    for fname in sorted(skills):
        fpath = os.path.join(SKILL_DIR, fname)
        ok, issues, warnings = validate_skill(fpath)
        
        if issues:
            fail_count += 1
            print(f"  ✗ FAIL  {fname}")
            for issue in issues:
                print(f"         → {issue}")
        elif warnings:
            warn_count += 1
            print(f"  ⚠ WARN  {fname}")
            for w in warnings:
                print(f"         → {w}")
        else:
            pass_count += 1
            print(f"  ✓ OK    {fname}")

    print(f"\n  Results: {pass_count} passed, {warn_count} warnings, {fail_count} failed")
    sys.exit(1 if fail_count > 0 else 0)

if __name__ == "__main__":
    run_audit()
