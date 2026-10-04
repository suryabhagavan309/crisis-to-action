import json

# Load current Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    case_state = json.load(file)

# Load Decision Engine output
with open("data/decision.json", "r", encoding="utf-8") as file:
    decision = json.load(file)

# Add decision analysis to Case State
case_state["decision"] = decision

# Save updated Case State
with open("data/case_state.json", "w", encoding="utf-8") as file:
    json.dump(
        case_state,
        file,
        indent=2,
        ensure_ascii=False
    )

print("✅ Decision merged into Case State.")
print("🧠 Living Case State updated.")
print("📁 Updated: data/case_state.json")