"""Assemble the ReAct agent: bind the LLM, tools, and prompt, then wrap in an
executor that actually runs the Thought/Action/Observation loop."""

try:
   from langchain_classic.agents import create_react_agent, AgentExecutor
except ImportError:
   from langchain.agents import create_react_agent, AgentExecutor
from .llm import build_llm
from .tools import build_tools
from .prompt import REACT_PROMPT
from .config import MAX_ITERATIONS


def build_agent(verbose: bool = True) -> AgentExecutor:
    llm = build_llm()
    tools = build_tools()

    # create_react_agent ties the prompt to the LLM and the tool list.
    agent = create_react_agent(llm, tools, REACT_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,                 # prints the Thought/Action trace
        handle_parsing_errors=True,      # recover if the model mis-formats a step
        max_iterations=MAX_ITERATIONS,   # don't loop forever
    )
