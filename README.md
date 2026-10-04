# CRISIS → ACTION
Decision-to-Execution Agent

## What it does
**CRISIS → ACTION** turns a messy real-world situation into a living decision workspace:

**Understand → Research → Decide → Human Approval → Execute → Track → Replan**

> **Not just an AI answer. It continuously tracks the case, actions, risks, and changing conditions.**

---

## Problem
Traditional AI assistants provide static, one-time advice. When real-world conditions change—such as a delayed deadline, an unexpected housing offer, or budget shifts—the original AI answer becomes outdated instantly. Users are forced to restart the prompt engineering cycle from scratch, losing track of active commitments and context.

---

## Solution
CRISIS → ACTION introduces a persistent **Case State** and closed-loop decision execution engine:
- **Structured Case State**: Extracts goal, context, constraints, deadlines, dependencies, and missing information.
- **Web Research**: Gathers source-backed evidence via n8n research integration and web search tools.
- **Decision Generation**: Evaluates trade-offs and recommends grounded decision directions.
- **Human Approval**: Requires explicit user consent before taking operational steps.
- **Safe Execution**: Routes approved actions into external n8n execution workflows.
- **Live Case Tracking**: Real-time status tracking for active, approved, executed, and removed actions.
- **Replanning**: Automatically recalculates risks, resolves previous uncertainties, and rebuilds action plans when new real-world information arrives.

---

## Full Lifecycle
The system operates across a complete 9-stage lifecycle:

1. **Understand**: Structure the initial messy user situation.
2. **Research**: Retrieve external web research and evidence.
3. **Decide**: Formulate decision summary, options, and risks.
4. **Approve**: Submit plan for human review and explicit authorization.
5. **Execute**: Dispatch approved actions to execution workflows.
6. **Track**: Update live case state and action progress.
7. **New Information**: Capture real-world condition updates.
8. **Replan**: Compare new facts against original case and rebuild the plan.
9. **Final State**: Present updated decision summary, resolved items, and revised actions.

---

## Architecture

```
User
 ↓
Web Interface
 ↓
FastAPI Backend
 ↓
Agent Controller
 ↓
NVIDIA Nemotron via Nebius
 ↓
Research / Execution Tools
 ↓
Decision + Action Plan
 ↓
Human Approval
 ↓
n8n Workflows
 ↓
Live Case State
 ↓
Replan
```

---

## Technology
- **Python**: Core backend language.
- **FastAPI**: High-performance REST API backend.
- **React**: Modern web workspace interface.
- **Vite**: Frontend build tool and dev server.
- **NVIDIA Nemotron**: LLM engine (`nvidia/Nemotron-3_5-Lightning`).
- **Nebius Token Factory**: Cloud AI inference platform hosting Nemotron.
- **n8n**: Workflow automation platform for research and execution webhooks.
- **Web Research Integration**: Automated research tools for grounded evidence collection.

---

## Human-in-the-Loop
CRISIS → ACTION enforces strict safety controls. Execution never occurs automatically; it explicitly requires human review and authorization before any action is dispatched to execution workflows.

---

## Demo Scenario
**Initial Situation:**
- New job offer in Bangalore with joining in 10 days.
- Current accommodation ends in 8 days.
- ₹40,000 available for housing-related expenses.
- No long-term accommodation found yet.

**Dynamic Replan:**
- *New Information Received:* The company announces temporary accommodation for the first 7 days after joining.
- *Agent Outcome:* The agent compares the new information with the existing case, marks temporary housing searches as resolved/removed, creates new prioritized long-term search actions, and recalculates risks without losing case history.

---

## Key Differentiator
The key differentiator of CRISIS → ACTION is its **persistent Case State** and its ability to adapt the action plan dynamically when new information changes real-world conditions, bridging the gap between passive AI recommendations and operational execution.

---

## Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
```bash
# Run FastAPI Backend (from project root)
uvicorn backend.main:app --reload
```
*Backend runs at `http://127.0.0.1:8000`.*

### Frontend Setup
```bash
# Run React Frontend
cd frontend
npm run dev
```
*Frontend runs at `http://localhost:5173`.*

---

## Hackathon Requirements
- **Nebius**: Powers fast cloud LLM inference via Nebius Token Factory API (`https://api.tokenfactory.nebius.com/v1/`).
- **NVIDIA Nemotron**: Uses `nvidia/Nemotron-3_5-Lightning` for case structuring, decision generation, and replanning.
- **n8n Integration**: Published research and execution webhooks automate evidence gathering and action dispatching.
- **Human-in-the-Loop**: Mandatory human approval stage enforced prior to execution.

---

## Security
- All secret API keys (e.g., `NEBIUS_API_KEY`, n8n webhook URLs) are loaded securely via environment variables.
- Sensitive credentials and authorization patterns are redacted from diagnostic logs.
- `.env` is strictly excluded from version control via `.gitignore`.

---

## Demo
CRISIS → ACTION includes:
- **⚡ 9-Stage Full Demo Runner**: An automated, interactive scenario runner demonstrating the complete Understand → Replan lifecycle.
- **Live Case Status View**: A real-time case tracking component showing active decisions, approval states, progress bars, and action status badges.
