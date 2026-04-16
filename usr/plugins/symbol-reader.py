#!/usr/bin/env python3
"""
## Gravitron Plugin: Symbol Reader
name: symbol-reader
description: Surgical AST symbol extraction from Python files (zero external deps)
version: 1.0
commands: [gravitron symbol-reader <file.py> <SymbolName>]
"""
import ast
import sys
import os

def extract_symbol(filepath, symbol_name):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    size = os.path.getsize(filepath)
    if size > 1_048_576:  # 1MB guard — fall back to regex
        return regex_fallback(filepath, symbol_name)

    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        return regex_fallback(filepath, symbol_name, reason=str(e))

    lines = source.splitlines()
    for node in ast.walk(tree):
        # Match classes, functions, and async functions
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == symbol_name:
                start = node.lineno - 1
                end = node.end_lineno
                extracted = "\n".join(lines[start:end])
                tier = type(node).__name__
                token_savings = (len(lines) - (end - start)) * 10
                print(f"✓  [{tier}] {symbol_name} found at lines {node.lineno}-{node.end_lineno}")
                print(f"   Estimated token savings: ~{token_savings:,} tokens vs. full file read")
                print(f"\n```python\n{extracted}\n```")
                return

    # Regex fallback
    regex_fallback(filepath, symbol_name, reason="Symbol not found in AST")

def regex_fallback(filepath, symbol_name, reason="File too large for AST"):
    import re
    print(f"  [Tier 4 Regex] {reason}")
    with open(filepath, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    pattern = re.compile(rf"^(class|def|async def)\s+{re.escape(symbol_name)}\b")
    for i, line in enumerate(lines):
        if pattern.match(line):
            block = []
            indent = len(line) - len(line.lstrip())
            for l in lines[i:]:
                if l.strip() == "" or len(l) - len(l.lstrip()) > indent or l.strip().startswith("#"):
                    block.append(l)
                elif len(l) - len(l.lstrip()) == indent and l.strip() and l != lines[i]:
                    break
                else:
                    block.append(l)
            print(f"  Line {i+1}: {''.join(block)}")
            return
    print(f"  ✗ Symbol '{symbol_name}' not found in {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: gravitron ast <file.py> <SymbolName>")
        sys.exit(1)
    extract_symbol(sys.argv[1], sys.argv[2])
