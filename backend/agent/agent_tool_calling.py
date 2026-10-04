import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from backend.tools.calculator import calculateā

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

tools = [
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
                        "description": "A mathematical expression such as 40000-5000-12000-8000"
                    }
                },
                "required": ["expression"],
            },
        },
    }
]

messages = [
    {
        "role": "system",
        "content": """
You are the Crisis-to-Action Agent.

Use the calculator tool whenever a numerical calculation is required.
Do not calculate the answer yourself when the calculator tool can do it.
After receiving the tool result, explain the result clearly.
"""
    },
    {
        "role": "user",
        "content": """
I have ₹40,000.

Travel costs ₹5,000.
Accommodation costs ₹12,000.
Food and local transport costs ₹8,000.

How much money will remain?
"""
    }
]

# First request: let Nemotron decide whether to use the tool
response = client.chat.completions.create(
    model="nvidia/Nemotron-3_5-Lightning",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

message = response.choices[0].message

# Check whether the model requested a tool
if message.tool_calls:

    print("🤖 Nemotron requested a tool.")

    messages.append(message)

    for tool_call in message.tool_calls:

        if tool_call.function.name == "calculate":

            arguments = json.loads(tool_call.function.arguments)

            expression = arguments["expression"]

            print(f"🛠️ Calculator expression: {expression}")

            result = calculate(expression)

            print(f"🧮 Calculator result: ₹{result}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )

    # Second request: give the tool result back to Nemotron
    final_response = client.chat.completions.create(
        model="nvidia/Nemotron-3_5-Lightning",
        messages=messages,
        tools=tools,
    )

    print("\n🤖 Final Agent Response:")
    print(final_response.choices[0].message.content)

else:
    print("🤖 Nemotron did not request a tool.")
    print(message.content)