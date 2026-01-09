---
description: How to add a new technical indicator to the Research Agent system
---

# Adding a New Indicator

This workflow guides you through adding a new technical indicator (e.g., ADX, SuperTrend) so that the AI Research Agent can use it.

1.  **Update Schema** (`research_agent/schema.py`):
    -   Add the indicator key to the `IndicatorType` Enum.
    -   Example: `SUPERTREND = "supertrend"`

2.  **Update Compiler** (`research_agent/compiler.py`):
    -   Add the Numba-optimized implementation to `INDICATOR_TEMPLATES`.
    -   **Constraint**: Must use `numpy` (and `numba` if possible). Avoid pandas in the core logic loop for speed.
    -   Add the call logic to `_generate_indicator_calls`.

3.  **Update Translator** (`research_agent/translator.py`):
    -   Update the system prompt to list the new indicator as "Supported".
    -   (Optional) If using `langchain` prompt templates, update the template string.

4.  **Verification**:
    -   Create a manual test spec in `research_agent/compiler.py` (`__main__` block) using the new indicator.
    -   Run `python -m research_agent.compiler` to ensure it generates valid Python code.
