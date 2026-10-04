import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

# Load Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    case_state = json.load(file)

system_prompt = """
You are the Decision Engine of the Crisis-to-Action Agent.

You receive:
1. A user's current Case State
2. Evidence collected from web research

Analyze the evidence and update the decision workspace.

Return ONLY valid JSON with exactly these fields:

{
  "evidence_summary": [],
  "verified_facts": [],
  "uncertainties": [],
  "options": [],
  "risks_and_tradeoffs": [],
  "recommended_next_actions": [],
  "questions_to_verify": []
}

Rules:
- Do not invent facts.
- Do not treat search snippets as guaranteed facts.
- Preserve uncertainty when a source does not provide enough detail.
- Do not make the final decision for the user.
- Do not claim an accommodation is available unless the evidence actually supports it.
- Separate verified information from assumptions.
- Focus on useful next actions.
"""

user_message = f"""
CURRENT CASE STATE:

{json.dumps(case_state, indent=2, ensure_ascii=False)}

Analyze the evidence currently stored in the Case State
and produce an evidence-based decision workspace.
"""

response = client.chat.completions.create(
    model="nvidia/Nemotron-3_5-Lightning",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
)

decision = json.loads(response.choices[0].message.content)

# Save decision workspace
with open(
    "data/decision.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        decision,
        file,
        indent=2,
        ensure_ascii=False
    )

print("✅ Decision analysis completed.")
print("🧠 Evidence analyzed by Nemotron.")
print("📁 Saved to: data/decision.json")