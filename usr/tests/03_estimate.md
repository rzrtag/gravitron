# Test: Gravitron Context Estimation
# Verify that the estimate tool can evaluate file sizes for context optimization

## Mock Files
- small.py: "print('small')"
- large.txt: "LOREM IPSUM ... [REPEAT 100 TIMES] ..."

## Run
`gravitron estimate small.py large.txt`

## Assert
- contains "Task Scope"
- contains "Logic Density"
- contains "Execution Tier"
