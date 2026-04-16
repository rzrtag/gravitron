# Dark Factory: Adversarial Self-Audit

This skill establishes a "fail-closed" verification loop for high-fidelity code generation.

## 1. The Cognitive Pause
Before executing any major file-patch (`replace_file_content` or `multi_replace_file_content`), you MUST perform a self-audit using the `/verify` logic.

### Audit Checklist:
1. **Regressions**: Does this change break any existing tests or adjacent modules?
2. **Technical Debt**: Am I "layering" a fix instead of refactoring the root cause?
3. **Simplicity Alignment**: Does this change adhere to the "Minimum Code" law?
4. **Edge Cases**: Have I handled nulls, timeouts, and boundary conditions?

## 2. Implementation Logic
- You MUST output a hidden or visible "Audit Summary" before the tool call.
- If the audit identifies a failure point, you must pivot and refactor the solution before presenting it.

## 3. Adversarial Mode
Act as your own worst critic. Assume the proposed code will fail in production. Prove why it won't.
