# path: backend/app/agents/debugger.py
from crewai import Agent, Task
from app.agents.retriever import get_llm


def create_debugger_agent() -> Agent:
    return Agent(
        role="Code Debugger & Analyzer",
        goal=(
            "Analyze user-submitted code for bugs, logical errors, edge case failures, "
            "and performance issues. Provide specific line-by-line feedback."
        ),
        backstory=(
            "You are a debugging expert who has reviewed thousands of code submissions. "
            "You can instantly spot common pitfalls like off-by-one errors, null pointer issues, "
            "and suboptimal loops. You explain bugs clearly with fix suggestions."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_debug_task(agent: Agent, user_code: str, problem_description: str) -> Task:
    return Task(
        description=f"""
Analyze this code for the problem: "{problem_description}"

```python
{user_code}
```

Identify:
1. Syntax errors (if any)
2. Logic bugs with line numbers
3. Edge cases not handled (empty input, large N, negatives, etc.)
4. Performance bottlenecks
5. Memory leaks or inefficiencies

Provide a corrected version if bugs are found.
""",
        expected_output=(
            "Bug report with line numbers, severity levels, edge cases, "
            "performance issues, and corrected code."
        ),
        agent=agent,
    )