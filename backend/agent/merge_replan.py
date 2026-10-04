import json

# Load current Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    case_state = json.load(file)

# Load latest re-plan
with open("data/replan.json", "r", encoding="utf-8") as file:
    replan = json.load(file)

# Store latest re-plan in Case State
case_state["replan"] = replan

# Update immediate actions using the revised plan
case_state["immediate_actions"] = replan["revised_plan"]

# Update status
case_state["status"] = replan["status"]

# Save the living Case State
with open("data/case_state.json", "w", encoding="utf-8") as file:
    json.dump(
        case_state,
        file,
        indent=2,
        ensure_ascii=False
    )

print("✅ Re-plan merged into Case State.")
print("🔄 Living Case State now contains the latest plan.")
print("📁 Updated: data/case_state.json")