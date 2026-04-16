import os
import json
import zipfile
from datetime import datetime

STATE_DIR = os.environ.get("GRAVITRON_STATE", os.path.expanduser("~/.gemini/antigravity"))
TRACE_DIR = os.path.join(STATE_DIR, "traces")
ARCHIVE_DIR = os.path.join(STATE_DIR, "archives")

def archive_traces():
    if not os.path.exists(TRACE_DIR):
        print(f"Error: Trace directory {TRACE_DIR} not found.")
        return

    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = os.path.join(ARCHIVE_DIR, f"traces_{timestamp}.zip")

    files = [f for f in os.listdir(TRACE_DIR) if f.endswith(".json")]
    if not files:
        print("No JSON traces found to archive.")
        return

    with zipfile.ZipFile(archive_name, 'w') as zipf:
        for file in files:
            file_path = os.path.join(TRACE_DIR, file)
            zipf.write(file_path, file)
            # Optional: remove file after archiving
            # os.remove(file_path)

    print(f"Archived {len(files)} traces to {archive_name}")

if __name__ == "__main__":
    archive_traces()
