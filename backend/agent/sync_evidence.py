import json

# Load Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    case_state = json.load(file)

# Load Research Evidence
with open("data/evidence.json", "r", encoding="utf-8") as file:
    evidence = json.load(file)

# Add research information to Case State
case_state["evidence"] = evidence["sources"]

# Save updated Case State
with open("data/case_state.json", "w", encoding="utf-8") as file:
    json.dump(
        case_state,
        file,
        indent=2,
        ensure_ascii=False
    )

print("✅ Evidence synced successfully.")
print(f"📚 Evidence sources added: {len(evidence['sources'])}")
print("📁 Updated: data/case_state.json")