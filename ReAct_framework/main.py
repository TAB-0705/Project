"""Run the Wikipedia ReAct agent on a question.

Usage:
    python main.py "Who wrote the novel that inspired Blade Runner?"
    python main.py                      # then type your question when prompted

With verbose=True you'll see the agent's Thought -> Action -> Observation
loop in the terminal, then the Final Answer.
"""

import sys
from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY from .env

from react_agent.agent import build_agent


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or input("Ask a question: ").strip()
    if not query:
        print("No question provided.")
        return

    executor = build_agent(verbose=True)
    result = executor.invoke({"input": query})

    print("\n" + "=" * 50)
    print("FINAL ANSWER")
    print("=" * 50)
    print(result["output"])


if __name__ == "__main__":
    main()
