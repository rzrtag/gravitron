#!/usr/bin/env python3
"""
gravitron_snap.py — Antigravity Sovereign Snapshot Engine
Project-agnostic rebuild of timeswitch (codebase-snapshot.py).
VERSION: INTERNAL-v2.0

Commands:
  gravitron-snap snap [path] [--mode blueprint|ingest] [--tag NAME] [--project NAME]
  gravitron-snap list [--project NAME]
  gravitron-snap info <snapshot>
  gravitron-snap rebuild <snapshot> [--target DIR]
  gravitron-snap archive [--project NAME]
"""
import os
import sys
import re
import datetime
import subprocess
import argparse
import shutil

# ── Paths & Limits ───────────────────────────────────────────────────────────
GRAVITRON_ROOT  = os.environ.get("GRAVITRON_ROOT",  os.path.expanduser("~/.gravitron"))
GRAVITRON_STATE = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))
GRAVITRON_CORE  = os.path.join(GRAVITRON_ROOT, "core")
GRAVITRON_USR   = os.path.join(GRAVITRON_ROOT, "usr")
SNAPSHOT_BASE   = os.path.join(GRAVITRON_STATE, "snapshots")
AUTO_ARCHIVE_AT  = 30   # Snapshots before auto-archive

MAX_FILE_SIZE_MB  = 2.0  # Hard cap: skip any single file larger than this (both modes)
INGEST_TRUNCATE_KB = 10  # Truncate large non-core files to this in Ingest mode
INGEST_MAX_FILE_KB = 200 # Completely skip files larger than this in Ingest mode

# ── Tier 1: Universal Skip Dirs (both modes) ─────────────────────────────────
# Directories that are NEVER meaningful source content.
SKIP_DIRS = {
    # Python environments
    'venv', '.venv', 'env', 'py-env', 'py_env',
    # Node / JS runtimes & deps
    'node_modules', 'node-internal', '.pnp',
    # Build artifacts
    '__pycache__', '.pytest_cache', 'target', '.cargo',
    'dist', 'build', '.cache', '.next', '.turbo',
    # VCS
    '.git', '.svn', '.hg',
    # Browser runtimes (Chrome for Testing, Chromium, etc.)
    'browser-internal', 'browser-profile', 'browser_recordings',
    'chrome-linux64', 'chrome-win64', 'chrome-mac-x64', 'chrome-mac-arm64',
    # Misc internal dirs
    'temporary', 'timeswitch', 'output', 'archive',
    'html_artifacts', 'traces',
}

# ── Tier 2: Ingest-Only Skip Dirs ────────────────────────────────────────────
# Dirs kept for Blueprint (full recovery) but stripped in Ingest (research context).
INGEST_SKIP_DIRS = {
    'test', 'tests', '__tests__', 'spec',  # Test suites — noise for analysis
    'migrations', 'fixtures',              # DB migration noise
    'static', 'media', 'public', 'assets', # Static assets
    'vendor', 'third_party', 'external',   # Vendored deps
    'brain',                               # Internal conversation logs
    'snapshots',                           # Snapshots of snapshots
    'scratch', 'conversations',
}

# ── Tier 3: Ingest Path-Pattern Guard (regex) ────────────────────────────────
# Last line of defense: if a file's relative path matches any of these patterns,
# skip it in Ingest mode even if it passed the dir and extension filters.
# Catches deeply nested vendor/generated files (e.g., inspector_overlay/main.js).
INGEST_SKIP_PATH_RE = [
    re.compile(r'chrome[-_]', re.IGNORECASE),
    re.compile(r'inspector.overlay', re.IGNORECASE),
    re.compile(r'devtools[-_/]', re.IGNORECASE),
    re.compile(r'/vendor/', re.IGNORECASE),
    re.compile(r'/generated/', re.IGNORECASE),
    re.compile(r'\.min\.', re.IGNORECASE),      # Minified files
    re.compile(r'\.bundle\.', re.IGNORECASE),   # Bundled files
]

# ── Extension Config ─────────────────────────────────────────────────────────
# Core files that should NEVER be truncated in Ingest mode
CORE_EXTS = {'.py', '.sh', '.rs', '.ts', '.tsx', '.js', '.json', '.toml', '.md'}

INCLUDE_EXT = {
    *CORE_EXTS, '.yaml', '.yml', '.xml', '.ron', '.css', '.html',
    '.code-workspace', '.env.example'
}

BOILERPLATE_NAMES = {'LICENSE', 'CHANGELOG', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock'}

LANG = {
    '.py': 'python', '.sh': 'bash', '.rs': 'rust',
    '.ts': 'typescript', '.tsx': 'tsx', '.js': 'javascript',
    '.json': 'json', '.md': 'markdown', '.css': 'css',
    '.html': 'html', '.toml': 'toml', '.yaml': 'yaml',
    '.yml': 'yaml', '.xml': 'xml', '.ron': 'ron',
    '.env.example': 'bash'
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def project_dir(project_name: str) -> str:
    path = os.path.join(SNAPSHOT_BASE, project_name)
    os.makedirs(path, exist_ok=True)
    return path

def archive_dir(project_name: str) -> str:
    path = os.path.join(SNAPSHOT_BASE, project_name, "archive")
    os.makedirs(path, exist_ok=True)
    return path

def get_gitignore_skip(root_dir: str) -> set:
    """Use 'git check-ignore' to find ignored files if in a git repo."""
    ignored = set()
    try:
        # Check if it's a git repo first
        subprocess.run(['git', '-C', root_dir, 'rev-parse'], check=True, capture_output=True)
        # Get all files and see which are ignored
        result = subprocess.run(
            ['git', '-C', root_dir, 'ls-files', '--others', '--ignored', '--exclude-standard', '--directory'],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            ignored.add(line.strip().strip('/'))
    except Exception:
        pass
    return ignored

def load_ignore(root_dir: str) -> set:
    ignore_path = os.path.join(root_dir, ".timeswitchignore")
    extra_skip = set()
    if os.path.exists(ignore_path):
        with open(ignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    extra_skip.add(line)
    return extra_skip

def get_tree(root_dir: str) -> str:
    try:
        result = subprocess.run(
            ['tree', '-d', '-L', '3', '-I', 'venv|.venv|node_modules|target|.git|__pycache__', root_dir],
            capture_output=True, text=True
        )
        return result.stdout
    except Exception:
        return "Tree utility not found."

def list_snapshots(project_name: str) -> list:
    pdir = os.path.join(SNAPSHOT_BASE, project_name)
    if not os.path.isdir(pdir): return []
    files = [f for f in os.listdir(pdir) if f.endswith("-snapshot.md") and os.path.isfile(os.path.join(pdir, f))]
    return sorted(files, reverse=True)

def maybe_auto_archive(project_name: str):
    snaps = list_snapshots(project_name)
    if len(snaps) >= AUTO_ARCHIVE_AT:
        to_archive = snaps[AUTO_ARCHIVE_AT - 1:]
        adir, pdir = archive_dir(project_name), project_dir(project_name)
        for fname in to_archive:
            shutil.move(os.path.join(pdir, fname), os.path.join(adir, fname))
        print(f"[gravitron-snap] Auto-archived {len(to_archive)} old snapshots.")

# ── Logic ─────────────────────────────────────────────────────────────────────
def format_file_content(full_path: str, mode: str) -> str | None:
    """Read and potentially truncate file content based on mode.
    Returns None to signal the file should be completely omitted from output.
    """
    size_bytes = os.path.getsize(full_path)
    ext = os.path.splitext(full_path)[1].lower()
    name = os.path.basename(full_path)

    # 1. Hard cap: skip files too large for any mode (binary/log protection)
    if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        return None

    try:
        if mode == 'blueprint':
            return open(full_path, encoding='utf-8', errors='replace').read()

        # ── Ingest mode ───────────────────────────────────────────────────────
        is_core = ext in CORE_EXTS and name not in BOILERPLATE_NAMES

        # 2. Ingest: completely skip oversized non-core files
        if not is_core and size_bytes > INGEST_MAX_FILE_KB * 1024:
            return None

        # 3. Ingest: include small files and core-extension files in full
        if is_core or size_bytes < INGEST_TRUNCATE_KB * 1024:
            return open(full_path, encoding='utf-8', errors='replace').read()

        # 4. Ingest: truncate mid-size non-core files with a notice
        with open(full_path, encoding='utf-8', errors='replace') as f:
            chunk = f.read(INGEST_TRUNCATE_KB * 1024)
            return chunk + f"\n\n... [TRUNCATED in Ingest mode. File size: {size_bytes/1024:.1f}KB]"

    except Exception as e:
        return f"[read error: {e}]"

def generate_captivity_log(root_dir: str, project_name: str, tag: str | None, mode: str) -> str:
    now = datetime.datetime.now().isoformat()
    log = [
        f"# Codebase Snapshot — {now}",
        f"**Project**: `{project_name}`",
        f"**Root**: `{root_dir}`",
        f"**Mode**: `{mode.upper()}`",
    ]
    if tag: log.append(f"**Tag**: `{tag}`")
    
    log.append("\n## 🧭 CAPTIVITY LOG")
    if mode == 'ingest':
        log.append("- **Objective**: Tactical research and analysis. Optimized for context injection.")
        log.append("- **Constraint**: Non-core/large files are truncated to ~10KB.")
    else:
        log.append("- **Objective**: Strategic lifecycle recovery (Project Phoenix). Bit-perfect source preservation.")
    
    log.append(f"- **Gitignore**: Respected.")
    log.append(f"- **Max File Cap**: {MAX_FILE_SIZE_MB}MB.")
    return "\n".join(log) + "\n"

# ── Snap ──────────────────────────────────────────────────────────────────────
def cmd_snap(root_dir: str, project_name: str, tag: str | None = None, mode: str = 'blueprint'):
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        print(f"Error: '{root_dir}' is not a directory.")
        sys.exit(1)

    extra_skip = load_ignore(root_dir)
    git_skip = get_gitignore_skip(root_dir)
    skip = SKIP_DIRS | extra_skip | git_skip

    pdir = project_dir(project_name)
    ts   = datetime.datetime.now().strftime("%m%d-%H%M")
    
    # ── Simplified Naming Logic ──────────────────────────────────────────────
    if mode == 'blueprint':
        name_tag = "blueprint"
    else:
        # For Ingest, use the project name or tag as the primary identifier
        name_tag = tag if tag else project_name or "ingest"
    
    out_path = os.path.join(pdir, f"{ts}-{name_tag}.md")

    # Tokens are fragmented to prevent self-matching
    H_S, H_M, C_F = "### " + "[", "]" + "(mode:", "~~~~"

    count = 0
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(generate_captivity_log(root_dir, project_name, tag, mode))
        out.write("\n")

        # 🛡️ RESCUE CAPSULE
        out.write("## 🛡️ RESCUE CAPSULE\n")
        if mode == 'ingest':
            out.write("> [!WARNING]\n> This is an INGEST snapshot. It is optimized for research, NOT for full recovery.\n\n")
        out.write("To rebuild this codebase, extract the block below and run:\n")
        out.write("`gravitron snap rebuild this_file.md --target /path/to/restore`\n\n")

        engine_code = open(__file__, 'r').read()
        out.write(f"### `TIME_SWITCH_ENGINE.py` [SOURCE]\n~~~~~python\n{engine_code}\n~~~~~\n\n")

        phoenix_md = os.path.join(GRAVITRON_USR, "prompting", "gravitron-snap-phoenix.md")
        if os.path.exists(phoenix_md):
            out.write(f"### `RESCUE_PROTOCOL.md` [SOURCE]\n~~~~~markdown\n{open(phoenix_md).read()}\n~~~~~\n\n")

        out.write("---\n\n## Directory Structure\n```text\n" + get_tree(root_dir) + "```\n\n---\n\n")

        for root, dirs, files in os.walk(root_dir):
            # ── Tier 1: Universal dir filter ─────────────────────────────────
            dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
            # Protect the antigravity snapshots dir from self-capture
            dirs[:] = [d for d in dirs if os.path.join(root, d) != SNAPSHOT_BASE]
            # ── Tier 2: Ingest-only dir filter ───────────────────────────────
            if mode == 'ingest':
                dirs[:] = [d for d in dirs if d not in INGEST_SKIP_DIRS]

            for fname in sorted(files):
                ext = os.path.splitext(fname)[1].lower()
                name = os.path.basename(fname)
                if ext not in INCLUDE_EXT and name not in BOILERPLATE_NAMES:
                    continue

                full = os.path.join(root, fname)
                rel  = os.path.relpath(full, root_dir)

                # Gitignore filter
                if rel in git_skip:
                    continue

                # ── Tier 3: Ingest path-pattern guard ────────────────────────
                if mode == 'ingest' and any(p.search(rel) for p in INGEST_SKIP_PATH_RE):
                    continue

                content = format_file_content(full, mode)
                # format_file_content returns None to signal a full skip
                if content is None:
                    continue

                mode_bits = oct(os.stat(full).st_mode)[-3:]
                lang = LANG.get(ext, 'text')
                out.write(f"{H_S}{rel}{H_M}{mode_bits})\n{C_F}{lang}\n{content}\n{C_F}\n\n")
                count += 1

    size_kb = os.path.getsize(out_path) / 1024
    print(f"✓ {mode.upper()} Snapshot created: {out_path}")
    print(f"  {count} files | {size_kb/1024:.2f} MB")
    maybe_auto_archive(project_name)

# ── Rest of Commands ──────────────────────────────────────────────────────────
def cmd_list(project_name: str | None = None):
    if not os.path.isdir(SNAPSHOT_BASE):
        print("No snapshots yet."); return
    projects = [project_name] if project_name else sorted(os.listdir(SNAPSHOT_BASE))
    for proj in projects:
        proj_path = os.path.join(SNAPSHOT_BASE, proj)
        if not os.path.isdir(proj_path): continue
        snaps = list_snapshots(proj)
        print(f"\n📁 {proj}/")
        for fname in snaps:
            fpath = os.path.join(proj_path, fname)
            size, mtime = os.path.getsize(fpath)/1024, datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
            print(f"  {fname:<50}  {size/1024:>7.2f} MB   {mtime.strftime('%Y-%m-%d %H:%M')}")

def cmd_info(snapshot_path: str):
    if not os.path.isfile(snapshot_path):
        print(f"Error: '{snapshot_path}' not found."); sys.exit(1)
    size_mb = os.path.getsize(snapshot_path) / 1024 / 1024
    with open(snapshot_path, encoding='utf-8') as f:
        content = f.read()
    mode = "INGEST" if "Mode**: `INGEST`" in content else "BLUEPRINT"
    file_count = len(re.findall(r'^### \[', content, re.MULTILINE))
    source_count = len(re.findall(r'\[SOURCE\]', content))
    print(f"\n📄 {os.path.basename(snapshot_path)}\n   Path: {snapshot_path}\n   Mode: {mode}\n   Size: {size_mb:.2f} MB\n   Files: {max(0, file_count - source_count)}")

def cmd_rebuild(snapshot_path: str, target_dir: str):
    if not os.path.isfile(snapshot_path):
        print(f"Error: Snapshot '{snapshot_path}' not found."); sys.exit(1)
    with open(snapshot_path, encoding='utf-8') as f:
        content = f.read()

    # Check mode from the header only (first 50 lines) to avoid false-positives
    # from the embedded engine source which also contains the literal string.
    header = "\n".join(content.splitlines()[:50])
    if "Mode**: `INGEST`" in header:
        print("⚠️ CAUTION: Rebuilding from an INGEST snapshot. Some files may be truncated.")
        input("Press Enter to proceed or Ctrl+C to abort...")

    target_dir = os.path.abspath(target_dir)
    print(f"🔥 Phoenix Protocol — rebuilding to: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)
    P_STR = (r'^' + '### ' + r'\[' + r'(.*?)' + r'\]' + r'\(mode:' + r'(\d{3})' + r'\)' + r'\n' + r'~~~~' + r'.*?' + r'\n' + r'(.*?)' + r'\n' + r'~~~~')
    pattern = re.compile(P_STR, re.DOTALL | re.MULTILINE)
    matches = pattern.findall(content)
    for rel_path, mode_bits, file_content in matches:
        if rel_path in ("TIME_SWITCH_ENGINE.py", "RESCUE_ENGINE.py", "RESCUE_PROTOCOL.md"): continue
        full_path = os.path.join(target_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f: f.write(file_content)
        try: os.chmod(full_path, int(mode_bits, 8))
        except: pass
    print(f"✅ Rebuild complete.")

def cmd_archive(project_name: str | None = None):
    projects = [project_name] if project_name else (sorted(os.listdir(SNAPSHOT_BASE)) if os.path.isdir(SNAPSHOT_BASE) else [])
    for proj in projects:
        snaps = list_snapshots(proj)
        if not snaps: continue
        adir, pdir = archive_dir(proj), project_dir(proj)
        for fname in snaps: shutil.move(os.path.join(pdir, fname), os.path.join(adir, fname))
        print(f"  {proj}: {len(snaps)} moved to archive.")

# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(prog="gravitron-snap", description="Antigravity Sovereign Snapshot Engine v2.0")
    sub = parser.add_subparsers(dest="command")
    p_snap = sub.add_parser("snap", help="Snapshot a directory")
    p_snap.add_argument("path", nargs="?", default=".", help="Directory to snapshot")
    p_snap.add_argument("--mode", "-m", choices=['blueprint', 'ingest'], default='blueprint', help="Snapshot mode")
    p_snap.add_argument("--tag", "-t", help="Tag for filename")
    p_snap.add_argument("--project", "-p", help="Project name")
    p_list = sub.add_parser("list", help="List snapshots")
    p_list.add_argument("--project", "-p", help="Filter by project")
    p_info = sub.add_parser("info", help="Show metadata")
    p_info.add_argument("snapshot", help="Path to snapshot file")
    p_rebuild = sub.add_parser("rebuild", help="Rebuild codebase")
    p_rebuild.add_argument("snapshot", help="Snapshot path")
    p_rebuild.add_argument("--target", "-o", default=".", help="Target dir")
    p_archive = sub.add_parser("archive", help="Manual archive")
    p_archive.add_argument("--project", "-p", help="Project name")
    args = parser.parse_args()
    if args.command is None or args.command == "snap":
        path = getattr(args, "path", ".")
        tag = getattr(args, "tag", None)
        mode = getattr(args, "mode", 'blueprint')
        proj = getattr(args, "project", None) or os.path.basename(os.path.abspath(path))
        cmd_snap(path, proj, tag, mode)
    elif args.command == "list": cmd_list(getattr(args, "project", None))
    elif args.command == "info": cmd_info(args.snapshot)
    elif args.command == "rebuild": cmd_rebuild(args.snapshot, args.target)
    elif args.command == "archive": cmd_archive(getattr(args, "project", None))

if __name__ == "__main__": main()
