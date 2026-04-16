# Test: Gravitron Snap Gitignore Respect
# Verify that the snap engine correctly ignores files listed in .gitignore

## Mock Files
- .gitignore: "ignored_dir/\n*.secret"
- src/main.py: "print('hello')"
- ignored_dir/trash.txt: "should be ignored"
- config.secret: "password123"

## Run
`gravitron snap . --mode ingest --tag test-gitignore --project certify`

## Assert
- contains "Snapshot created"
- NOT contains "ignored_dir/trash.txt"
- NOT contains "config.secret"
- exists "snapshots/certify/*-test-gitignore.md"
