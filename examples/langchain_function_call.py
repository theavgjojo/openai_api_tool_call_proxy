import math
import pprint
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool


@tool
def add_ints(x: int, y: int) -> int:
    """Adds two integers: a and b.

    Args:
        x: int
        y: int
    """
    return x + y


@tool
def factorial_int(x: int) -> int:
    """Finds the factorial of an integer.

    Args:
        x: int
    """
    return math.factorial(x)


llm = ChatOpenAI(
    openai_api_base='http://127.0.0.1:8001/v1',
    openai_api_key='NULL',
    model_name='NousResearch/Hermes-2-Pro-Llama-3-8B',
)

llm_with_tools = llm.bind_tools([add_ints, factorial_int])
query = "Find 500 + 1234 and the factorial of 35"

tool_calls = llm_with_tools.invoke(query).tool_calls
pprint.pprint(tool_calls)
for tool_call in tool_calls:
    selected_tool = {"add_ints": add_ints, "factorial_int": factorial_int}[tool_call["name"].lower()]
    tool_output = selected_tool.invoke(tool_call["args"])
    print(f'{tool_call["name"].lower()}: {tool_output}')
