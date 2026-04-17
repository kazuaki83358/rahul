# path: backend/app/agents/generator.py
from crewai import Agent, Task
from app.agents.retriever import get_llm
import logging

logger = logging.getLogger(__name__)


def create_generator_agent() -> Agent:
    return Agent(
        role="Code Generator",
        goal=(
            "Generate clean, well-commented Python/JavaScript code solutions with "
            "step-by-step explanations. Always include time and space complexity analysis."
        ),
        backstory=(
            "You are a senior software engineer with expertise in algorithms and data structures. "
            "You write production-quality code with clear explanations suitable for "
            "technical interviews and real-world applications."
        ),
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


def create_generation_task(agent: Agent, query: str, context: list) -> Task:
    context_str = "\n\n".join(
        f"### {c['title']} ({c['difficulty']})\n{c['content']}" for c in context[:3]
    )
    return Task(
        description=f"""
Given the user query: "{query}"

Relevant context from knowledge base:
{context_str}

Generate:
1. A complete, working code solution
2. Step-by-step explanation of the approach
3. Time complexity: O(?) with justification
4. Space complexity: O(?) with justification
5. Edge cases handled
6. Alternative approaches (if any)

Format the code in a ```python code block.
""",
        expected_output=(
            "Complete solution with code block, explanation, complexity analysis, "
            "edge cases, and alternatives."
        ),
        agent=agent,
    )