# path: backend/app/agents/crew.py
from crewai import Crew, Process
from typing import AsyncGenerator, Dict, Any
import asyncio, json, logging

from app.agents.retriever import create_retriever_agent, retrieve_context, get_llm
from app.agents.generators import create_generator_agent, create_generation_task
from app.agents.debugger import create_debugger_agent, create_debug_task
from app.agents.optimizer import create_optimizer_agent, create_optimization_task
from app.utils.dsa_graphs import compute_dsa_score, astar_query_optimizer

logger = logging.getLogger(__name__)

async def run_crew_streaming(
    payload: Dict[str, Any], session_id: str
) -> AsyncGenerator[Dict, None]:
    query = payload.get("query", "")
    user_code = payload.get("user_code", "")
    mode = payload.get("mode", "solve")

    # Check for LLM
    llm = get_llm()
    if not llm:
        yield {
            "type": "error", 
            "content": "API Key Missing: Please add OPENAI_API_KEY or GOOGLE_API_KEY to your backend/.env file to solve problems.",
            "session_id": session_id
        }
        return

    yield {"type": "status", "message": "🔍 Optimizing pipeline...", "session_id": session_id}

    # Step 1: Retrieve context
    yield {"type": "agent_start", "agent": "Retriever", "session_id": session_id}
    context = await retrieve_context(query, k=5)
    yield {
        "type": "agent_result",
        "agent": "Retriever",
        "data": context[:2],
        "message": f"Found {len(context)} relevant problems",
        "session_id": session_id,
    }

    # Step 2: Create agents
    generator_agent = create_generator_agent()
    debugger_agent = create_debugger_agent()
    optimizer_agent = create_optimizer_agent()

    tasks = []
    if mode in ("solve", "all"):
        tasks.append(create_generation_task(generator_agent, query, context))
    if mode in ("debug", "all") and user_code:
        tasks.append(create_debug_task(debugger_agent, user_code, query))
    if mode in ("optimize", "all") and user_code:
        tasks.append(create_optimization_task(optimizer_agent, user_code, "O(n)"))

    if not tasks:
        tasks.append(create_generation_task(generator_agent, query, context))

    crew = Crew(
        agents=[generator_agent, debugger_agent, optimizer_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )

    yield {"type": "agent_start", "agent": "Generator", "session_id": session_id}

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, crew.kickoff)
        result_text = str(result)
    except Exception as e:
        logger.error(f"Crew error: {e}")
        yield {"type": "error", "message": f"Agent error: {e}. Check libraries.", "session_id": session_id}
        return

    # Extract DSA score
    dsa_score = None
    if user_code or "```python" in result_text:
        import re
        code_blocks = re.findall(r"```python\n(.*?)```", result_text, re.DOTALL)
        if code_blocks:
            dsa_score, score_details = compute_dsa_score(user_code or code_blocks[0], code_blocks[0], "O(n)", "O(n)")
            yield {"type": "dsa_score", "score": dsa_score, "details": score_details, "session_id": session_id}

    yield {
        "type": "final",
        "content": result_text,
        "dsa_score": dsa_score,
        "session_id": session_id,
    }
