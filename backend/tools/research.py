import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()


def research_via_n8n(query: str, case_id: str = "case_001", max_results: int = 5) -> dict:
    """
    Execute research via published n8n research webhook.
    """
    webhook_url = os.getenv("N8N_RESEARCH_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("N8N_RESEARCH_WEBHOOK_URL environment variable is not set")

    payload = {
        "case_id": case_id,
        "query": query,
        "constraints": {
            "max_results": max_results
        }
    }

    print(f"[n8n] Routing research request through webhook for query: '{query}'...")

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        if response.status not in (200, 201):
            raise RuntimeError(f"n8n webhook returned HTTP status {response.status}")
        
        response_body = response.read().decode("utf-8")
        n8n_data = json.loads(response_body)

    print("[n8n] Research succeeded.")

    timestamp = datetime.now().astimezone().isoformat()
    evidence_data = {
        "query": query,
        "searched_at": timestamp,
        "case_id": n8n_data.get("case_id", case_id),
        "status": n8n_data.get("status", "success"),
        "evidence": n8n_data.get("evidence", []),
        "sources": n8n_data.get("sources", n8n_data.get("evidence", []))
    }

    # Save evidence persistence
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/evidence.json", "w", encoding="utf-8") as file:
            json.dump(evidence_data, file, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[WARNING] Failed to save evidence to data/evidence.json: {err}")

    return evidence_data


def web_search(query, max_results=5):
    """
    Search the web and save source-backed evidence.
    Routes to n8n if N8N_RESEARCH_WEBHOOK_URL is set, falling back to DDGS.
    """
    webhook_url = os.getenv("N8N_RESEARCH_WEBHOOK_URL")

    if webhook_url:
        try:
            return research_via_n8n(query, case_id="case_001", max_results=max_results)
        except Exception as err:
            print(f"[WARNING] n8n research failed ({err}). Falling back to local DDGS web search.")

    # Local DDGS Fallback
    results = DDGS(timeout=10).text(
        query,
        region="in-en",
        safesearch="moderate",
        max_results=max_results,
        backend="bing,brave,duckduckgo,google,mojeek,qwant,yahoo,yandex",
    )

    timestamp = datetime.now().astimezone().isoformat()

    evidence = {
        "query": query,
        "searched_at": timestamp,
        "sources": [
            {
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", ""),
            }
            for result in results
        ],
    }

    # Save evidence
    os.makedirs("data", exist_ok=True)
    with open("data/evidence.json", "w", encoding="utf-8") as file:
        json.dump(evidence, file, indent=2, ensure_ascii=False)

    return evidence


if __name__ == "__main__":
    result = web_search(
        "Bangalore PG accommodation for working professionals",
        max_results=5,
    )

    print("[RESEARCH] Completed.")
    print("[RESEARCH] Evidence saved to: data/evidence.json")
    sources_count = len(result.get("sources", []))
    print(f"[RESEARCH] Sources found: {sources_count}")