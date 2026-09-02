"""LangChain integration — prompts and LCEL chains as sibling packages.

Layout:
    llm/prompts/   ChatPromptTemplate definitions (what to say)
    llm/chains/    Runnable composition (how to wire it)

The LLM itself is injected via ``app.api.deps``; neither subpackage owns it.
"""
