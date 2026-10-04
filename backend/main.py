import os
import sys
import json
import re
from json import JSONDecoder
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        encoded = text.encode("utf-8", errors="replace").decode("ascii", errors="replace")
        print(encoded, **kwargs)


from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from backend.tools.research import web_search
from backend.tools.execution import execute_via_n8n


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")

if not NEBIUS_API_KEY:
    raise RuntimeError("NEBIUS_API_KEY is missing from .env")


# ============================================================
# NEBIUS CLIENT
# ============================================================

client = OpenAI(
    api_key=NEBIUS_API_KEY,
    base_url="https://api.tokenfactory.nebius.com/v1/",
    timeout=120.0,
)


MODEL_NAME = "nvidia/Nemotron-3_5-Lightning"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="CRISIS → ACTION",
    description="Decision-to-Execution Agent powered by NVIDIA Nemotron",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")

CASE_STATE_FILE = os.path.join(
    DATA_DIR,
    "case_state.json"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class CaseRequest(BaseModel):
    situation: str


class ReplanRequest(BaseModel):
    current_situation: str
    new_information: str


# ============================================================
# CASE STATE HELPERS
# ============================================================

def load_case_state():

    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CASE_STATE_FILE):
        return {}

    try:

        with open(
            CASE_STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


def save_case_state(case_data):
    if isinstance(case_data, dict):
        case_data["last_updated"] = datetime.now().astimezone().isoformat()

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(
        CASE_STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            case_data,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# ROBUST JSON EXTRACTOR & DIAGNOSTIC LOGGING
# ============================================================

def log_safe_diagnostic(tag, text, err=None):
    if not text:
        print(f"\n[{tag}] Safe Diagnostic: Model response is empty or None.")
        return
    safe_str = str(text)
    # Redact potential authorization headers or secret key patterns
    safe_str = re.sub(r'(Bearer\s+|key=)[A-Za-z0-9_\-\.]+', r'\1[REDACTED]', safe_str)
    snippet = safe_str[:300].replace('\n', ' ')
    print(f"\n[{tag}] Safe Diagnostic - Length: {len(text)} chars | Snippet: {snippet}...")
    if err:
        print(f"[{tag}] Parsing exception: {str(err)}")


def repair_json_string(s):
    if not s:
        return ""
    s = s.strip()
    
    # Strip markdown code blocks if wrapped
    if s.startswith("```"):
        lines = s.splitlines()
        if len(lines) > 1:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            s = "\n".join(lines).strip()

    # Remove trailing commas before closing braces/brackets
    s = re.sub(r',\s*([\}\]])', r'\1', s)

    in_string = False
    escape = False
    stack = []
    
    for char in s:
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in '{[':
                stack.append('}' if char == '{' else ']')
            elif char in '}]':
                if stack and stack[-1] == char:
                    stack.pop()

    if in_string:
        s += '"'
    
    while stack:
        s = s.rstrip().rstrip(',')
        s += stack.pop()
        
    return s


def extract_json_object(text):
    if not text:
        log_safe_diagnostic("JSON_EXTRACT_ERROR", text, "Empty text provided")
        raise ValueError("Empty model response")

    clean = text.strip()

    # Strip reasoning/thinking tags and preamble text blocks
    clean = re.sub(r'<think>.*?</think>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'\[THINKING\].*?\[/THINKING\]', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<reasoning>.*?</reasoning>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<thought>.*?</thought>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'^(?:Here\'s|Thinking|Let\'s|I will|Below is|Sure).*?(?=\{)', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = clean.strip()

    search_texts = []

    # Check for markdown code fences
    fence_matches = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', clean, flags=re.DOTALL | re.IGNORECASE)
    if fence_matches:
        search_texts.extend(fence_matches)
    
    search_texts.append(clean)

    decoder = JSONDecoder()
    candidates = []

    domain_keys = {
        "goal", "case_changed", "change_summary", "options",
        "immediate_actions", "revised_plan", "new_actions",
        "context", "constraints", "deadlines", "dependencies", 
        "evidence", "decision_summary", "revised_decision_summary", "research_evidence",
        "missing_information", "risks_and_tradeoffs", "risks", "actions", "summary"
    }

    def count_populated_fields(parsed_obj):
        if not isinstance(parsed_obj, dict):
            return 0
        pop = 0
        for v in parsed_obj.values():
            if isinstance(v, str) and len(v.strip()) > 2:
                pop += 1
            elif isinstance(v, list) and len(v) > 0:
                pop += len(v)
            elif isinstance(v, dict) and len(v) > 0:
                pop += len(v)
            elif isinstance(v, bool):
                pop += 1
        return pop

    def evaluate_and_collect(parsed_obj):
        if not isinstance(parsed_obj, dict):
            return
        
        clean_keys = set()
        for k in parsed_obj.keys():
            if isinstance(k, str):
                ck = re.sub(r'^[^\w]+', '', k).strip().lower().lstrip("./_\\ ")
                clean_keys.add(ck)
        
        score = len(clean_keys.intersection(domain_keys))
        pop_score = count_populated_fields(parsed_obj)
        if score > 0:
            candidates.append((score, pop_score, len(parsed_obj), parsed_obj))
        
        for v in parsed_obj.values():
            if isinstance(v, dict):
                evaluate_and_collect(v)

    for txt in search_texts:
        brace_indices = [m.start() for m in re.finditer(r'\{', txt)]
        for idx in brace_indices:
            sub = txt[idx:]
            
            # 1. Standard raw_decode
            try:
                parsed, _ = decoder.raw_decode(sub)
                evaluate_and_collect(parsed)
            except Exception:
                pass

            # 2. Repaired JSON string decode
            try:
                repaired = repair_json_string(sub)
                parsed = json.loads(repaired)
                evaluate_and_collect(parsed)
            except Exception:
                pass

            # 3. Substring between '{' and last '}'
            end_idx = sub.rfind("}")
            if end_idx != -1:
                slice_str = sub[:end_idx + 1]
                try:
                    parsed = json.loads(slice_str)
                    evaluate_and_collect(parsed)
                except Exception:
                    try:
                        repaired = repair_json_string(slice_str)
                        parsed = json.loads(repaired)
                        evaluate_and_collect(parsed)
                    except Exception:
                        pass

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        return candidates[0][3]

    log_safe_diagnostic("JSON_EXTRACT_FAILED", text)
    raise ValueError("Could not extract a valid JSON object from model response")


# ============================================================
# NORMALIZE ANALYSIS
# ============================================================

def normalize_analysis(data):

    default = {
        "goal": "",
        "context": [],
        "constraints": [],
        "deadlines": [],
        "dependencies": [],
        "missing_information": [],
        "options": [],
        "risks_and_tradeoffs": [],
        "immediate_actions": [],
        "evidence": [],
        "decision_summary": "",
        "research_evidence": []
    }

    if not isinstance(data, dict):
        data = {}

    clean_data = {}
    for k, v in data.items():
        if isinstance(k, str):
            clean_key = re.sub(r'^[^\w]+', '', k).strip().lower().lstrip("./_\\ ")
            clean_data[clean_key] = v

    alias_map = {
        "goal": ["goal", "case_goal", "target_goal"],
        "context": ["context", "situation_context", "background"],
        "constraints": ["constraints", "limitation", "limitations"],
        "deadlines": ["deadlines", "timeline", "dead_lines"],
        "dependencies": ["dependencies", "dependancies"],
        "missing_information": ["missing_information", "missing_info", "unknowns"],
        "options": ["options", "choices", "alternatives"],
        "risks_and_tradeoffs": ["risks_and_tradeoffs", "risks", "tradeoffs", "risks_tradeoffs"],
        "immediate_actions": ["immediate_actions", "actions", "next_steps"],
        "evidence": ["evidence", "user_evidence"],
        "decision_summary": ["decision_summary", "summary", "decision"],
        "research_evidence": ["research_evidence", "web_evidence", "external_evidence"]
    }

    result = {}
    for key, default_val in default.items():
        found_val = None
        aliases = alias_map.get(key, [key])
        
        for alias in aliases:
            if alias in clean_data:
                found_val = clean_data[alias]
                break
            elif alias in data:
                found_val = data[alias]
                break

        if found_val is None:
            found_val = default_val

        if isinstance(default_val, list):
            if isinstance(found_val, list):
                result[key] = [str(x).strip() for x in found_val if x is not None and str(x).strip()]
            elif isinstance(found_val, str) and found_val.strip():
                result[key] = [found_val.strip()]
            else:
                result[key] = []
        else:
            result[key] = str(found_val).strip() if found_val is not None else ""

    return result


# ============================================================
# NORMALIZE REPLAN
# ============================================================

def normalize_replan(data):

    default = {
        "case_changed": False,
        "change_summary": "",
        "resolved_items": [],
        "removed_actions": [],
        "new_actions": [],
        "updated_risks": [],
        "revised_plan": [],
        "revised_decision_summary": ""
    }

    if not isinstance(data, dict):
        return default

    clean_data = {}
    for k, v in data.items():
        if isinstance(k, str):
            clean_key = k.lstrip("./_\\ ").strip().lower()
            clean_data[clean_key] = v

    result = {}

    for key in default:
        val = clean_data.get(key, data.get(key, default[key]))
        if isinstance(val, list):
            cleaned = []
            for item in val:
                if item is None:
                    continue
                if isinstance(item, str) and not item.strip():
                    continue
                cleaned.append(item)
            result[key] = cleaned
        else:
            result[key] = val

    return result


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "status": "online",
        "project": "CRISIS → ACTION",
        "model": MODEL_NAME
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model": MODEL_NAME
    }


def format_research_evidence(web_res):
    if not web_res or not isinstance(web_res, dict):
        return []

    raw_items = []
    if isinstance(web_res.get("evidence"), list) and len(web_res["evidence"]) > 0:
        raw_items = web_res["evidence"]
    elif isinstance(web_res.get("sources"), list) and len(web_res["sources"]) > 0:
        raw_items = web_res["sources"]

    formatted = []
    for item in raw_items[:5]:
        if isinstance(item, dict):
            title = (
                item.get("title")
                or item.get("name")
                or item.get("source_title")
                or "Web Source"
            )
            snippet = (
                item.get("snippet")
                or item.get("content")
                or item.get("body")
                or item.get("summary")
                or ""
            )
            url = (
                item.get("url")
                or item.get("source")
                or item.get("href")
                or item.get("link")
                or ""
            )
            if snippet.strip() == url.strip():
                snippet = ""
            formatted.append({
                "title": str(title).strip() or "Web Source",
                "snippet": str(snippet).strip(),
                "url": str(url).strip()
            })
        elif isinstance(item, str):
            clean_str = item.strip()
            if clean_str.startswith("http"):
                domain_title = "Web Source"
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(clean_str).netloc
                    if domain:
                        domain_title = domain.replace("www.", "")
                except Exception:
                    pass
                formatted.append({
                    "title": domain_title,
                    "snippet": "",
                    "url": clean_str
                })
            else:
                formatted.append({
                    "title": "Web Source",
                    "snippet": clean_str,
                    "url": ""
                })

    return formatted


# ============================================================
# ANALYZE
# ============================================================

@app.post("/analyze")
def analyze_case(request: CaseRequest):

    web_res = None
    try:
        web_res = web_search(request.situation, max_results=5)
    except Exception as err:
        safe_print(f"[WARNING] Web search inside /analyze failed: {err}")

    research_text = ""
    evidence_for_prompt = format_research_evidence(web_res)
    if evidence_for_prompt:
        formatted = []
        for idx, item in enumerate(evidence_for_prompt[:3], 1):
            t = item.get("title", "Web Source")
            s = item.get("snippet", "")
            u = item.get("url", "")
            content_desc = s if s else u
            formatted.append(f"{idx}. {t}: {content_desc[:140]}")
        research_text = "\n".join(formatted)

    user_prompt_content = f"USER SITUATION:\n{request.situation}"
    if research_text:
        user_prompt_content += f"\n\nEXTERNAL WEB RESEARCH FINDINGS (Use these real web sources to inform your options, risks, and decision summary):\n{research_text}"

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",

                "content": """You are the Crisis-to-Action Decision Agent.

Your task is to convert a messy real-world situation into a structured decision case.

CRITICAL INSTRUCTION: Output ONLY valid JSON starting immediately with '{'. Do NOT write any preamble, reasoning, or meta-comments.

Use EXACTLY these keys:

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
  "evidence": [],
  "decision_summary": ""
}

STRICT GROUNDING RULES:
- Context, constraints, deadlines, dependencies, missing_information, evidence, options, risks_and_tradeoffs, and immediate_actions MUST be based ONLY on:
  1. Facts explicitly provided by the user in the prompt.
  2. Clearly identified external web research findings.
  3. Reasonable planning implications explicitly labeled as assumptions or inferences.
- NEVER present an unstated or inferred detail as an established user fact.
- Do NOT invent origin cities, location history, employer details, belongings volume, notice period requirements, family situation, salary, rent, dates, or prices unless explicitly provided by the user.
- If a detail is unknown (such as current location, notice period, or exact office address), put it under "missing_information" (e.g. "Current city and whether belongings need relocation are unstated", "Notice period status is unknown").
- "goal": Provide a concise 1-sentence objective statement summarizing what the user needs to accomplish based ONLY on their explicit objective. Do NOT repeat the full user situation prompt.
- "decision_summary": Explain (a) decision direction fitting goal and constraints, (b) main reason, and (c) key information to verify before making the final decision. Frame as a recommendation, keeping the human as the final decision-maker.
- "evidence": Include only facts explicitly provided by the user or clearly identified as missing/verified information. Return [] if empty.
- Keep all array items concise (max 2-3 items per array, 1 short sentence per item). Provide 3 concrete immediate_actions.
"""
            },

            {
                "role": "user",
                "content": user_prompt_content
            }
        ],

        temperature=0.1,
        max_tokens=4096,

        response_format={
            "type": "json_object"
        }
    )

    raw_response = response.choices[0].message.content

    print("\n" + "=" * 60)
    print("ANALYZE RAW RESPONSE")
    print("=" * 60)
    safe_print(raw_response)
    print("=" * 60)

    try:

        analysis = extract_json_object(
            raw_response
        )

        analysis = normalize_analysis(
            analysis
        )

        analysis["research_evidence"] = format_research_evidence(web_res)

        print("\nANALYZE JSON SUCCESS")

    except Exception as error:

        log_safe_diagnostic("ANALYZE_PARSING_FAILED", raw_response, error)

        analysis = normalize_analysis({})
        analysis["research_evidence"] = format_research_evidence(web_res)

    if not analysis.get("goal") or analysis.get("goal", "").startswith("Address crisis situation:"):
        analysis["goal"] = "Secure suitable accommodation and manage decision timeline within available budget constraints."

    if not analysis.get("context"):
        analysis["context"] = [
            f"User-stated situation: {request.situation[:140]}"
        ]

    if not analysis.get("constraints"):
        analysis["constraints"] = [
            "Stated financial and timeline constraints."
        ]

    if not analysis.get("deadlines"):
        analysis["deadlines"] = [
            "Stated joining and transition deadlines."
        ]

    if not analysis.get("dependencies"):
        analysis["dependencies"] = [
            "Availability of suitable options matching constraints."
        ]

    if not analysis.get("missing_information"):
        analysis["missing_information"] = [
            "Specific unstated preferences and detailed logistical terms."
        ]

    if not analysis.get("options"):
        analysis["options"] = [
            "Evaluate short-term and immediate options within budget.",
            "Verify unstated constraints and refine search criteria."
        ]

    if not analysis.get("risks_and_tradeoffs"):
        analysis["risks_and_tradeoffs"] = [
            "Short-term cost and availability trade-offs."
        ]

    if not analysis.get("immediate_actions"):
        analysis["immediate_actions"] = [
            "Research and compare 2-3 suitable options within budget.",
            "Verify missing details and clarify key constraints.",
            "Finalize immediate transition steps."
        ]

    if not analysis.get("evidence"):
        analysis["evidence"] = [
            f"User-provided situation: {request.situation[:140]}"
        ]

    if not analysis.get("decision_summary"):
        analysis["decision_summary"] = (
            "Prioritize evaluating short-term options that satisfy stated budget and timeline constraints. "
            "Verify key missing information before making the final decision."
        )

    # --------------------------------------------------------
    # Save initial case
    # --------------------------------------------------------

    case_data = analysis

    save_case_state(case_data)

    return {
        "status": "success",
        "model": "NVIDIA Nemotron",
        "analysis": analysis
    }


# ============================================================
# APPROVE
# ============================================================

@app.post("/approve")
def approve_plan():

    approval_data = {
        "status": "approved",
        "message": "Plan approved by user.",
        "approved_at": "user-approved"
    }

    case_data = load_case_state()

    case_data["approval"] = approval_data

    # Collect approved actions from existing case state
    replan_info = case_data.get("replan") or {}
    analysis_info = case_data.get("analysis") or {}

    actions_to_execute = (
        replan_info.get("new_actions")
        or replan_info.get("revised_plan")
        or analysis_info.get("immediate_actions")
        or [
            "Research temporary accommodation options",
            "Compare housing options within budget",
            "Verify missing information with employer and landlords"
        ]
    )

    # Trigger post-approval execution workflow
    execution_result = execute_via_n8n(actions_to_execute, case_id="case_001")

    case_data["execution"] = execution_result

    save_case_state(case_data)

    return {
        "status": "success",
        "approval": approval_data,
        "execution": execution_result
    }


# ============================================================
# LIVE CASE STATUS
# ============================================================

def get_case_summary(case_data: dict) -> dict:
    if not case_data:
        return {
            "status": "success",
            "case_id": "case_001",
            "case": None
        }

    analysis = case_data.get("analysis") or {}
    replan = case_data.get("replan") or {}
    approval = case_data.get("approval")
    execution = case_data.get("execution")
    last_updated = case_data.get("last_updated", datetime.now().astimezone().isoformat())

    goal = analysis.get("goal", "")
    decision_summary = replan.get("revised_decision_summary") or analysis.get("decision_summary", "")
    risks = replan.get("updated_risks") or analysis.get("risks_and_tradeoffs", [])

    # Collect execution action status map
    executed_actions_map = {}
    if execution and isinstance(execution.get("actions"), list):
        for item in execution["actions"]:
            if isinstance(item, dict):
                act_text = item.get("action") or item.get("title") or ""
                st = item.get("status", "executed")
                if act_text:
                    executed_actions_map[act_text.strip().lower()] = st

    # Determine current active actions
    raw_active_actions = (
        replan.get("new_actions")
        or replan.get("revised_plan")
        or analysis.get("immediate_actions")
        or []
    )

    actions = []
    action_id_counter = 1

    for act in raw_active_actions:
        act_title = act.get("title") if isinstance(act, dict) else str(act)
        clean_title = act_title.strip()
        lower_title = clean_title.lower()

        if lower_title in executed_actions_map:
            st = executed_actions_map[lower_title]
        elif execution and execution.get("status") == "success":
            st = "executed"
        elif approval and approval.get("status") == "approved":
            st = "approved"
        else:
            st = "pending"

        actions.append({
            "id": action_id_counter,
            "title": clean_title,
            "status": st
        })
        action_id_counter += 1

    # Include removed actions from replan if present
    removed_actions_list = replan.get("removed_actions") or []
    for act in removed_actions_list:
        act_title = act.get("title") if isinstance(act, dict) else str(act)
        actions.append({
            "id": action_id_counter,
            "title": act_title.strip(),
            "status": "removed"
        })
        action_id_counter += 1

    active_actions = [a for a in actions if a["status"] != "removed"]
    completed_count = len([a for a in active_actions if a["status"] == "executed"])
    pending_count = len([a for a in active_actions if a["status"] in ("pending", "approved")])

    progress = {
        "total": len(active_actions),
        "completed": completed_count,
        "pending": pending_count
    }

    return {
        "status": "success",
        "case_id": "case_001",
        "case": {
            "goal": goal,
            "decision_summary": decision_summary,
            "approval": approval,
            "execution": execution,
            "actions": actions,
            "risks": risks,
            "progress": progress,
            "last_updated": last_updated
        }
    }


@app.get("/case")
def get_case():
    case_data = load_case_state()
    return get_case_summary(case_data)


# ============================================================
# REPLAN
# ============================================================

@app.post("/replan")
def replan_case(request: ReplanRequest):

    # --------------------------------------------------------
    # Load existing case
    # --------------------------------------------------------

    existing_case = load_case_state()

    clean_case = {
        k: v for k, v in existing_case.items()
        if k not in ("replan", "approval", "research_evidence")
    }

    current_case_text = json.dumps(
        clean_case,
        indent=2,
        ensure_ascii=False
    )

    # --------------------------------------------------------
    # Replanning prompt
    # --------------------------------------------------------

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",

                "content": """You are the Crisis-to-Action Replanning Agent.

An existing decision case exists. New information has arrived.
Your job is to compare the ORIGINAL case with the NEW INFORMATION and rebuild the decision case.

CRITICAL INSTRUCTION: Output ONLY valid JSON starting immediately with '{'. Do NOT write any preamble, reasoning, or meta-comments.

Use EXACTLY these keys:

{
  "case_changed": true,
  "change_summary": "",
  "resolved_items": [],
  "removed_actions": [],
  "new_actions": [],
  "updated_risks": [],
  "revised_plan": [],
  "revised_decision_summary": ""
}

Rules:
1. case_changed: true if new information materially changes the case; false otherwise.
2. When case_changed is true, you MUST populate non-empty values for ALL of the following:
   - change_summary: Non-empty string explaining what changed compared to original case.
   - resolved_items: 2-4 items listing previous issues or uncertainties now resolved by the new information.
   - removed_actions: 1-4 items if an old action is obsolete; return [] if no actions are obsolete.
   - new_actions: 2-4 concrete new actions created by the new information. NEVER return empty array when case_changed=true.
   - updated_risks: 2-4 items recalculating risks based on the changed case. NEVER return empty array when case_changed=true.
   - revised_plan: 3-5 concrete steps for the updated overall plan. Preserve valid existing actions conceptually. NEVER return empty array when case_changed=true.
   - revised_decision_summary: Non-empty string answering "Given the new information, what is the current decision direction and why?" and stating key facts to verify before final user approval.
3. Compare the ORIGINAL case with the NEW INFORMATION directly (do not just summarize the new information).
4. Keep human decision authority: Provide a decision direction/recommendation, but keep the user as the final decision-maker.
5. Do not invent facts.
"""
            },

            {
                "role": "user",

                "content": f"""
EXISTING CASE:

{current_case_text}

CURRENT SITUATION:

{request.current_situation}

NEW INFORMATION:

{request.new_information}
"""
            }
        ],

        temperature=0.1,
        max_tokens=4096,

        response_format={
            "type": "json_object"
        }
    )

    raw_response = response.choices[0].message.content

    # --------------------------------------------------------
    # DEBUG LOG
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("REPLAN RAW RESPONSE")
    print("=" * 60)
    safe_print(raw_response)
    print("=" * 60)

    # --------------------------------------------------------
    # Parse model response
    # --------------------------------------------------------

    try:

        replan_data = extract_json_object(
            raw_response
        )

        replan_data = normalize_replan(
            replan_data
        )

        print("\nREPLAN JSON SUCCESS")

    except Exception as error:

        log_safe_diagnostic("REPLAN_PARSING_FAILED", raw_response, error)

        # ----------------------------------------------------
        # Safe fallback
        # ----------------------------------------------------

        replan_data = {
            "case_changed": True,
            "change_summary": (
                "New information was received, "
                "updating case parameters and decision tradeoffs."
            ),
            "resolved_items": ["New details clarify prior uncertainties in the initial situation."],
            "removed_actions": [],
            "new_actions": ["Review updated constraints against initial plan and verify missing details."],
            "updated_risks": ["Adjusted timeline or cost constraints may impact overall plan execution."],
            "revised_plan": ["Update step 1 to incorporate new information.", "Re-evaluate next actions.", "Execute updated workflow."],
            "revised_decision_summary": "The new information modifies key constraints and options. Review the updated risks and revised plan before final approval."
        }
        replan_data = normalize_replan(replan_data)

    if replan_data.get("case_changed"):
        if not replan_data.get("change_summary"):
            replan_data["change_summary"] = "New information materially updates the case parameters."
        if not replan_data.get("resolved_items"):
            replan_data["resolved_items"] = ["New details clarify prior uncertainties in the initial situation."]
        if not replan_data.get("new_actions"):
            replan_data["new_actions"] = ["Review updated constraints against the initial plan and verify missing details."]
        if not replan_data.get("updated_risks"):
            replan_data["updated_risks"] = ["Adjusted timeline or cost constraints may impact overall plan execution."]
        if not replan_data.get("revised_plan"):
            replan_data["revised_plan"] = ["Update step 1 to incorporate new information.", "Re-evaluate next actions.", "Execute updated workflow."]
        if not replan_data.get("revised_decision_summary"):
            replan_data["revised_decision_summary"] = "The new information modifies key constraints and options. Review updated risks and revised plan before final approval."

    # --------------------------------------------------------
    # Save replan inside existing case
    # --------------------------------------------------------

    case_data = load_case_state()

    case_data["replan"] = replan_data

    save_case_state(case_data)

    # --------------------------------------------------------
    # Return to frontend
    # --------------------------------------------------------

    return {
        "status": "success",
        "model": "NVIDIA Nemotron",
        "replan": replan_data
    }