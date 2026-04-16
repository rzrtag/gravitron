import sys
import os
import sqlite3
import hashlib

STATE_DIR = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))
DB_PATH = os.path.join(STATE_DIR, "context.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # WAL mode: enables multi-agent concurrency without SQLITE_BUSY locking
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("CREATE TABLE IF NOT EXISTS context (id TEXT PRIMARY KEY, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS audit (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, action TEXT)")
    conn.commit()
    conn.close()

def log_action(action):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check for HCF (Distributed Loop detection)
    # Trigger if this action has appeared 2 times already in the last 5 entries
    cursor.execute("SELECT action FROM audit ORDER BY rowid DESC LIMIT 5")
    rows = cursor.fetchall()
    
    count = 0
    for r in rows:
        if r[0] == action:
            count += 1
            
    if count >= 2:
        print("!!! HALT AND CATCH FIRE (HCF) TRIGGERED !!!")
        print(f"Action loop detected: {action} (Seen {count+1} times in last 6 ops)")
        print("Continuous redundant operations detected. Terminating trajectory.")
        conn.close()
        sys.exit(137)

    cursor.execute("INSERT INTO audit (action) VALUES (?)", (action,))
    conn.commit()
    conn.close()

def store_content():
    content = sys.stdin.read()
    if not content.strip():
        print("Empty input")
        return
    
    log_action("store_content")
    # Simple hash for ID
    ctx_id = hashlib.md5(content.encode()).hexdigest()[:8]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO context (id, content) VALUES (?, ?)", (ctx_id, content))
    conn.commit()
    conn.close()
    
    print(f"ctx:{ctx_id}")
    print(f"Summary: Stored {len(content)} characters. Use 'gravitron util fetch {ctx_id}' to retrieve.")

def fetch_content(ctx_id):
    log_action(f"fetch_content:{ctx_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM context WHERE id = ?", (ctx_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        print(row[0])
    else:
        print(f"Error: Context ID {ctx_id} not found.")

def surgical_read(filename, start, end):
    log_action(f"surgical_read:{filename}:{start}:{end}")
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            # 1-indexed conversion
            start_idx = max(0, start - 1)
            end_idx = min(len(lines), end)
            for i in range(start_idx, end_idx):
                print(f"{i+1}: {lines[i].rstrip()}")
    except Exception as e:
        print(f"Error: {e}")

def triage_log(filename):
    log_action(f"triage:{filename}")
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            # Capture last 100 lines
            snapshot = lines[-100:]
            # Filter for high-signal error lines
            signal = []
            capture = False
            for line in snapshot:
                if any(x in line for x in ["Traceback", "Error", "Exception", "FAILED", "FAIL"]):
                    capture = True
                if capture:
                    signal.append(line)
            
            if not signal:
                signal = snapshot[-20:] # Fallback to last 20 lines
            
            # Store in relay
            content = "".join(signal)
            ctx_id = hashlib.md5(content.encode()).hexdigest()[:8]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO context (id, content) VALUES (?, ?)", (ctx_id, content))
            conn.commit()
            conn.close()
            print(f"ctx:{ctx_id}")
            print(f"Summary: Triage complete. Extracted {len(signal)} signal lines from {filename}.")
    except Exception as e:
        print(f"Error during triage: {e}")

if __name__ == "__main__":
    init_db()
    if len(sys.argv) < 2:
        print("Usage: gravitron util [store | fetch <id> | surgical <file> <start> <end> | triage <file> | log <action>]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "store":
        store_content()
    elif cmd == "fetch":
        if len(sys.argv) < 3:
            print("Error: Provide Context ID")
        else:
            fetch_content(sys.argv[2])
    elif cmd == "surgical":
        if len(sys.argv) < 5:
            print("Error: Provide <file> <start> <end>")
        else:
            surgical_read(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "triage":
        if len(sys.argv) < 3:
            print("Error: Provide log file path")
        else:
            triage_log(sys.argv[2])
    elif cmd == "log":
        if len(sys.argv) < 3:
            print("Error: Provide action string")
        else:
            log_action(" ".join(sys.argv[2:]))
