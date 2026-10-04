import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

# Load current living Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    current_state = json.load(file)


# New information received from the user
new_information = """
The company has confirmed that accommodation will be provided
for the first month after joining. The accommodation will start
when the employee joins the company.
"""


system_prompt = """
You are the Re-Planning Engine of the Crisis-to-Action Agent.

You receive an existing Case State and new information.

Your job is to:
1. Identify what changed.
2. Identify which constraints changed.
3. Identify which dependencies are affected.
4. Remove actions that are no longer necessary.
5. Add new actions that are now necessary.
6. Update risks and uncertainties.
7. Produce a revised action plan.

Return ONLY valid JSON:

{
  "changes_detected": [],
  "affected_constraints": [],
  "affected_dependencies": [],
  "removed_actions": [],
  "new_actions": [],
  "updated_risks": [],
  "remaining_uncertainties": [],
  "revised_plan": [],
  "status": ""
}

Rules:
- Do not invent facts.
- Preserve useful information from the existing Case State.
- Do not remove an issue unless the new information actually resolves it.
- Do not make the final decision for the user.
- Clearly distinguish confirmed information from assumptions.
"""


user_message = f"""
CURRENT CASE STATE:

{json.dumps(current_state, indent=2, ensure_ascii=False)}


NEW INFORMATION:

{new_information}


Re-plan the case based on this new information.
"""


response = client.chat.completions.create(
    model="nvidia/Nemotron-3_5-Lightning",
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ],
)

raw_response = response.choices[0].message.content or ""

print("\n🧠 RAW RE-PLAN RESPONSE:")
print(repr(raw_response))

if not raw_response.strip():
    print("❌ Nemotron returned an empty response.")
    raise RuntimeError("Re-plan response was empty.")

try:
    start = raw_response.find("{")
    end = raw_response.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Nemotron response.")

    json_text = raw_response[start:end + 1]

    replan = json.loads(json_text)

except (json.JSONDecodeError, ValueError) as e:
    print("❌ Could not extract valid JSON from Re-plan response.")
    print(f"Error: {e}")
    print(raw_response)
    raise


# Save re-planning result
with open(
    "data/replan.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        replan,
        file,
        indent=2,
        ensure_ascii=False
    )


print("✅ Re-planning completed.")
print("🔄 Agent detected changes and generated a revised plan.")
print("📁 Saved to: data/replan.json")