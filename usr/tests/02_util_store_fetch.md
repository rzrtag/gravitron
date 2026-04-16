# Test: Gravitron Context Relay (Util)
# Verify the store and fetch logic of the context relay system

## Mock Files
- test_context.txt: "This is a test of the Gravitron Context Relay system."

## Run
`gravitron util store < test_context.txt`

## Assert
- contains "ctx:"
- contains "Stored"
