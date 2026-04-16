# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from Andrej Karpathy's observations.

## 1. Think Before Coding
- State assumptions explicitly.
- Surface tradeoffs and interpretations.
- Push back on overcomplication.

## 2. Simplicity First
- Minimum code that solves the problem.
- No speculative features or abstractions.
- Bias toward caution and readability.

## 3. Surgical Changes
- Touch only what you must.
- Clean up only your own mess.
- Match existing style.

## 4. Goal-Driven Execution
- Define success criteria before coding.
- Loop autonomously until verified.
- sequence: [Step] -> verify: [check]

## 5. QA Engineering (DOM Verification)
- For any change affecting the UI or web-state, you MUST use the `browser_subagent` to verify the final DOM state.
- Do not rely on code logic alone; visually verify that elements are present, visible, and interactive.
