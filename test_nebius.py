import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

system_prompt = """
You are the Crisis-to-Action Agent.

Analyze the user's real-world situation and return ONLY valid JSON.

Use exactly these fields:

{
  "goal": "",
  "context": [],
  "constraints": [],
  "deadlines": [],
  "dependencies": [],
  "missing_information": [],
  "options": [],
  "risks_and_tradeoffs": [],
  "immediate_actions": [],
  "status": ""
}

Rules:
- Do not invent facts.
- Do not invent prices, availability, locations, policies, or other external facts.
- If information is unknown, put it in missing_information.
- Do not rank options unless the user provides criteria for ranking.
- Do not make the final decision for the user.
"""

user_input = """
I got a new job in Bangalore.
My joining date is in 10 days.
I have ₹40,000 available.
My current accommodation ends in 8 days.
I have not found a place to stay yet.
"""

response = client.chat.completions.create(
    model="nvidia/Nemotron-3_5-Lightning",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ],
)

content = response.choices[0].message.content

# Convert AI response into Python data
case_state = json.loads(content)

# Save Case State
with open("data/case_state.json", "w", encoding="utf-8") as file:
    json.dump(case_state, file, indent=2, ensure_ascii=False)

print("✅ Case State generated and saved successfully.")
print("📁 Saved to: data/case_state.json")