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

system_prompt = """
You are the Crisis-to-Action Agent.

You can use a calculator tool when numerical calculations are required.

Your job:
1. Understand the user's situation.
2. Identify constraints and deadlines.
3. Decide whether a calculation is needed.
4. Use the calculator when needed.
5. Explain the result clearly.
6. Do not invent external facts.
7. Do not make the final decision for the user.
"""

user_input = """
I have ₹40,000 available for relocation.

My estimated expenses are:
Travel: ₹5,000
Initial accommodation: ₹12,000
Food and local transport: ₹8,000

Calculate how much money I would have remaining after these expenses.
"""

response = client.chat.completions.create(
    model="nvidia/Nemotron-3_5-Lightning",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ],
)

print("🤖 Agent:")
print(response.choices[0].message.content)

# Agent's calculation
remaining = calculate("40000 - 5000 - 12000 - 8000")

print("\n🛠️ Calculator Tool:")
print(f"Remaining budget: ₹{remaining}")