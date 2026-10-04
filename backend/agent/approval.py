import json

# Load the current Case State
with open("data/case_state.json", "r", encoding="utf-8") as file:
    case_state = json.load(file)

plan = case_state.get("immediate_actions", [])

print("\n🧠 CURRENT ACTION PLAN\n")

for index, action in enumerate(plan, start=1):
    print(f"{index}. {action}")

print("\n⚠️ The agent will NOT execute any consequential action automatically.")

approval = input("\nDo you approve this action plan? (yes/no): ").strip().lower()

if approval == "yes":

    case_state["approval"] = {
        "status": "approved",
        "approved_actions": plan
    }

    print("\n✅ Plan approved by user.")

elif approval == "no":

    case_state["approval"] = {
        "status": "rejected",
        "approved_actions": []
    }

    print("\n❌ Plan rejected. Agent must revise the plan.")

else:

    case_state["approval"] = {
        "status": "pending",
        "approved_actions": []
    }

    print("\n⏸️ Approval remains pending.")

# Save approval state
with open("data/case_state.json", "w", encoding="utf-8") as file:
    json.dump(
        case_state,
        file,
        indent=2,
        ensure_ascii=False
    )

print("\n📁 Case State updated with approval status.")