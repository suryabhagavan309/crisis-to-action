import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

steps = [
    ("Research", ["backend/tools/research.py"]),
    ("Sync Evidence", ["backend/agent/sync_evidence.py"]),
    ("Decision Engine", ["backend/agent/decision_engine.py"]),
    ("Merge Decision", ["backend/agent/merge_decision.py"]),
    ("Re-plan", ["backend/agent/replan.py"]),
    ("Merge Re-plan", ["backend/agent/merge_replan.py"]),
    ("Approval", ["backend/agent/approval.py"]),
]

print("\n🚀 CRISIS-TO-ACTION AGENT")
print("=" * 50)

for name, command in steps:
    print(f"\n▶️ Running: {name}")

    result = subprocess.run(
        [sys.executable] + command,
        cwd=ROOT
    )

    if result.returncode != 0:
        print(f"\n❌ {name} failed.")
        sys.exit(result.returncode)

    print(f"✅ {name} completed.")

print("\n" + "=" * 50)
print("🎉 FULL AGENT WORKFLOW COMPLETED")
print("📁 Case State: data/case_state.json")
print("=" * 50)