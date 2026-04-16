# Test: Gravitron Skill Validator Plugin
# Verify that the skill-validator audits the actual usr/skills/ registry

## Run
`skill-validator`

## Assert
- contains "Skill Registry Audit"
- contains "dark-factory.md"
- NOT contains "CRITICAL SECURITY ALERT"
