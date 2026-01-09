---
description: How to generate a new trading strategy using the Research Agent
---

# Strategy Generation Workflow

// turbo
1.  **Run the Master Agent**:
    ```bash
    python -m research_agent.master "Create a trend following strategy using EMA crossover" --provider google --download
    ```

2.  **Review Output**:
    -   Check the "Review Result" section.
    -   If "PASSED", the strategy is in `strategies/`.

3.  **Optimize (Optional)**:
    -   If the initial backtest was good but needed tuning, run the optimizer:
    ```bash
    python -m research_agent.optimizer --symbol SBIN --strategy EmaTrend --pop 40 --gen 20
    ```
