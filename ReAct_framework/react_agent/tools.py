"""The 'Acting' half of ReAct: the external tool the agent can call.
Here that's Wikipedia search.

Note on the two lines below build_tools(): the `wikipedia` PyPI package is
old and unmaintained, and today's Wikipedia API rejects its defaults:
  1. Wikipedia's API policy requires a *descriptive* User-Agent. The library's
     generic default now gets an empty (non-JSON) response, which surfaces as
     "JSONDecodeError: Expecting value: line 1 column 1 (char 0)".
  2. The library still targets the plain-HTTP endpoint; we pin it to HTTPS.
These two settings are global to the library, so we apply them once at import.
"""

import wikipedia
import wikipedia.wikipedia as _wiki_core

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from .config import WIKI_TOP_K, WIKI_MAX_CHARS

# 1) A compliant, descriptive User-Agent (Wikipedia asks for an app name +
#    contact). Replace the email with a real one if you publish this.
wikipedia.set_user_agent(
    "ReActAgentDemo/1.0 (VIT WNS student project; tabri@example.com)"
)

# 2) Force the modern HTTPS endpoint instead of the library's http:// default.
_wiki_core.API_URL = "https://en.wikipedia.org/w/api.php"


def build_tools():
    wikipedia_tool = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(
            top_k_results=WIKI_TOP_K,
            doc_content_chars_max=WIKI_MAX_CHARS,
        )
    )
    return [wikipedia_tool]
