import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from backend.tools.calculator import calculate
from backend.tools.research import web_search

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to calculate."
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The web search query."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def execute_tool(tool_name, arguments):

    if tool_name == "calculate":
        return calculate(arguments["expression"])

    if tool_name == "web_search":
        return web_search(
            arguments["query"],
            max_results=5
        )

    raise ValueError(f"Unknown tool: {tool_name}")


messages = [
    {
        "role": "system",
        "content": """
You are the Crisis-to-Action Agent.

You can use:
1. Calculator — for numerical calculations.
2. Web Search — for current or external information.

Use the appropriate tool when necessary.

Important rules:
- Do not invent current information.
- Use web search when the user asks for current, external, or location-specific information.
- Use calculator for numerical calculations.
- After receiving tool results, analyze them before answering.
- Clearly distinguish information found from the web from your own reasoning.
- Do not make the final decision for the user.
"""
    },
    {
        "role": "user",
        "content": """
I am moving to Bangalore for a new job.

I have ₹40,000 available.

Find current information about PG or co-living accommodation
options in Bangalore and help me understand what information
I should compare before choosing one.
"""
    }
]


while True:

    response = client.chat.completions.create(
        model="nvidia/Nemotron-3_5-Lightning",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if not message.tool_calls:

        print("\n🤖 FINAL AGENT RESPONSE:")
        print(message.content)
        break

    messages.append(message)

    for tool_call in message.tool_calls:

        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"\n🧠 Tool requested: {tool_name}")
        print(f"📦 Arguments: {arguments}")

        result = execute_tool(tool_name, arguments)

        print(f"🛠️ Tool completed: {tool_name}")

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            }
        )