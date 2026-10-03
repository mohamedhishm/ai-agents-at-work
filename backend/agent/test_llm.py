from agent.llm import get_llm


llm = get_llm()

response = llm.invoke(
    "Hello! Explain in one sentence what an AI agent is."
)

print(response.content)