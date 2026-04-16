import sys
import os

def estimate_complexity(files):
    print("--- [Blue Nova Task Router v2] ---")
    total_lines = 0
    complexity_score = 0
    
    for f in files:
        if not os.path.exists(f):
            print(f"Skipping missing file: {f}")
            continue
            
        with open(f, 'r') as file:
            lines = file.readlines()
            total_lines += len(lines)
            # Basic heuristics: presence of complex logic
            content = "".join(lines)
            for marker in ["async", "await", "threading", "multiprocessing", "regex", "sql", "lambda"]:
                if marker in content:
                    complexity_score += 5
    
    # Tier mapping
    if total_lines < 100 and complexity_score < 10:
        tier = "TIER 3 (LITE)"
        suggestion = "Use a fast, low-latency model."
    elif total_lines < 500 and complexity_score < 30:
        tier = "TIER 2 (STANDARD)"
        suggestion = "Standard reasoning model."
    else:
        tier = "TIER 1 (ELITE)"
        suggestion = "High-fidelity reasoning required. Use premium reasoning model (o1/Claude 3.5)."

    print(f"Task Scope: {len(files)} files, {total_lines} lines")
    print(f"Logic Density: {complexity_score}")
    print(f"Execution Tier: {tier}")
    print(f"Suggestion: {suggestion}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: gravitron estimate <file1> <file2> ...")
        sys.exit(1)
    
    estimate_complexity(sys.argv[1:])
