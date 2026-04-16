#!/usr/bin/env python3
import os
import sys
import re
import shutil
import subprocess
import tempfile
import glob

GRAVITRON_ROOT = os.environ.get("GRAVITRON_ROOT", os.path.expanduser("~/.gravitron"))

class GravitronTester:
    def __init__(self, test_file):
        self.test_file = test_file
        self.test_dir = tempfile.mkdtemp(prefix="gravitron_test_")
        self.results = []
        
    def run(self):
        print(f"--- Running Test: {os.path.basename(self.test_file)} ---")
        try:
            with open(self.test_file, 'r') as f:
                content = f.read()
            
            # 1. Setup Mock Files
            self.setup_mocks(content)
            
            # 2. Run Command
            output = self.run_command(content)
            
            # 3. Assertions
            self.verify_assertions(content, output)
            
            return all(r['status'] == 'PASS' for r in self.results)
        finally:
            shutil.rmtree(self.test_dir)

    def setup_mocks(self, content):
        print("  [Setting up Sandbox]")
        # Matches: - path/to/file: "content"
        mocks = re.findall(r'- (.*?): "(.*?)"', content)
        for path, data in mocks:
            full_path = os.path.join(self.test_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(data)

    def run_command(self, content):
        print("  [Executing Command]")
        # Match: `gravitron X args` or just `X args` (for standalone plugin tests)
        match = re.search(r'## Run\n`(?:gravitron )?(.*?)`', content)
        if not match:
            print("  ✗ No command found in ## Run section")
            return ""
        
        cmd_str = match.group(1)
        # Use the global gravitron router and isolate State for the test
        env = os.environ.copy()
        env["GRAVITRON_STATE"] = self.test_dir
        # Wrap the command so it uses the harness in the shell
        full_cmd = f"source {GRAVITRON_ROOT}/core/bin/bootstrap.sh && gravitron {cmd_str}"
        res = subprocess.run(full_cmd, cwd=self.test_dir, capture_output=True, text=True, env=env, shell=True, executable='/bin/bash')
        return res.stdout + res.stderr

    def verify_assertions(self, content, actual_output):
        print("  [Verifying Assertions]")
        assertions = re.findall(r'- (contains|NOT contains|exists|NOT exists) (?:["\'](.*?)["\']|(.*))', content)
        for op, val1, val2 in assertions:
            val = val1 or val2
            target = f"'{val}'"
            
            if op == "contains":
                passed = val in actual_output
            elif op == "NOT contains":
                passed = val not in actual_output
            elif op == "exists":
                passed = len(glob.glob(os.path.join(self.test_dir, val))) > 0
            elif op == "NOT exists":
                passed = len(glob.glob(os.path.join(self.test_dir, val))) == 0
            
            status = "PASS" if passed else "FAIL"
            print(f"    {status} {op} {target}")
            self.results.append({"op": op, "target": target, "status": status})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: gravitron test <test_file.md | dir>")
        sys.exit(1)
    
    target = sys.argv[1]
    tests = []
    if os.path.isdir(target):
        tests = [os.path.join(target, f) for f in os.listdir(target) if f.endswith(".md")]
    else:
        tests = [target]

    overall_pass = True
    for t in tests:
        tester = GravitronTester(t)
        if not tester.run():
            overall_pass = False
    
    sys.exit(0 if overall_pass else 1)
