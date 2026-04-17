# path: backend/app/agents/optimizer.py
from crewai import Agent, Task
from app.agents.retriever import get_llm


def create_optimizer_agent() -> Agent:
    return Agent(
        role="DSA Optimizer",
        goal=(
            "Refactor and optimize code using advanced DSA techniques: "
            "dynamic programming, greedy algorithms, divide & conquer, graph algorithms. "
            "Always compare original vs optimized complexity."
        ),
        backstory=(
            "You are a competitive programmer with deep knowledge of optimization techniques. "
            "You transform brute-force solutions into optimal ones, always explaining "
            "the DSA concept applied (memoization, sliding window, two pointers, etc.)"
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_optimization_task(agent: Agent, original_code: str, current_complexity: str) -> Task:
    return Task(
        description=f"""
Optimize this code (current complexity: {current_complexity}):

```python
{original_code}
```

Provide:
1. Identify the bottleneck (e.g., nested loop = O(n²))
2. Suggest the optimal DSA pattern (DP, greedy, sliding window, etc.)
3. Optimized code with the pattern applied
4. Complexity comparison: Before → After
5. Why this optimization works (intuition)
6. When NOT to use this optimization (trade-offs)
""",
        expected_output=(
            "Optimization report with bottleneck analysis, optimized code, "
            "complexity comparison, DSA pattern explanation, and trade-off discussion."
        ),
        agent=agent,
    )