# Test: Gravitron Symbol Reader Plugin
# Verify that symbol-reader extracts a named function from a Python file

## Run
`symbol-reader /home/conrad/.gravitron/core/lib/gravitron_snap.py cmd_snap`

## Assert
- contains "cmd_snap"
- NOT contains "cmd_list"
