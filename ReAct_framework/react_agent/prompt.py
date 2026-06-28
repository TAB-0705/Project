"""The ReAct prompt — the heart of this task.

ReAct = Reasoning + Acting. The prompt teaches the model to alternate between
THOUGHT (reason about what to do) and ACTION (call a tool), reading each
tool's OBSERVATION before deciding the next step, until it can give a Final
Answer. The interleaving of thinking and tool use is the whole framework.

Required template variables for LangChain's create_react_agent:
  {tools}            - descriptions of available tools (filled in automatically)
  {tool_names}       - the names the agent may put after 'Action:'
  {input}            - the user's question
  {agent_scratchpad} - the running Thought/Action/Observation history
"""

from langchain_core.prompts import PromptTemplate

REACT_PROMPT = PromptTemplate.from_template(
    """Answer the following question as best you can. You have access to the
following tools:

{tools}

Use EXACTLY this format:

Question: the input question you must answer
Thought: reason about what to do next
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation cycle can repeat)
Thought: I now know the final answer
Final Answer: a clear, complete answer to the original question

Rules:
- Always start with a Thought.
- Only use a tool when you actually need external information.
- Base your Final Answer on the Observations you gathered, not on guesses.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
)
