import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

# Load existing Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    current_state = json.load(file)

# New information from the user
new_information = """
The company has confirmed that they will provide accommodation
for the first month after joining.
"""

system_prompt = """
You are the Crisis-to-Action Agent.

You are updating an existing Case State after receiving new information.

Return ONLY valid JSON with exactly these fields:

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
- Preserve useful information from the existing state.
- Incorporate the new information.
- Remove or update dependencies that are no longer relevant.
- Recalculate affected actions and risks.
- Do not invent external facts.
- Do not make the final decision for the user.
"""

user_message = f"""
EXISTING CASE STATE:

{json.dumps(current_state, indent=2, ensure_ascii=False)}

NEW INFORMATION:

{new_information}

Update the Case State based on this new information.
"""

response = client.chat.completions.create(
    model="nvidia/Nemotron-3_5-Lightning",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
)

updated_state = json.loads(response.choices[0].message.content)

# Save updated Case State
with open("data/case_state.json", "w", encoding="utf-8") as file:
    json.dump(updated_state, file, indent=2, ensure_ascii=False)

print("✅ Case State updated successfully.")
print("🔄 Agent re-planned using the new information.")
print("📁 Saved to: data/case_state.json")