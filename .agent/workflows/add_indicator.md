---
description: How to add a new technical indicator to the Research Agent system
---

# Adding a New Indicator

The system now features an autonomous **Librarian Agent** that handles this process automatically.

## Automated Process
1.  **Request Strategy**: Provide a strategy description with a new indicator (e.g., "Use Keltner Channels").
2.  **Detection**: The Compiler detects `keltner_channel` is missing from the library.
3.  **Librarian Trigger**: The Librarian Agent is invoked.
    -   It classifies the indicator (e.g., "Volatility").
    -   It generates Numba-optimized code.
    -   It appends the code to `calculate/indicators/volatility.py`.
    -   It updates `calculate/indicators/__init__.py`.
4.  **Compilation**: The compilation retries and succeeds.

## Manual Override (If needed)
If you wish to add one manually:
1.  Open the appropriate file in `calculate/indicators/` (e.g., `trend.py`).
2.  Add your `@njit` function: `def calculate_my_ind(...)`.
3.  Add the export to `calculate/indicators/__init__.py`.
