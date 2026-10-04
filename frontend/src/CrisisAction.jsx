import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

export default function CrisisAction() {
  const [situation, setSituation] = useState("");
  const [newInformation, setNewInformation] = useState("");

  const [loading, setLoading] = useState(false);
  const [replanLoading, setReplanLoading] = useState(false);

  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [replan, setReplan] = useState(null);

  const [approved, setApproved] = useState(false);
  const [execution, setExecution] = useState(null);
  const [caseStatus, setCaseStatus] = useState(null);
  const [showWhy, setShowWhy] = useState(false);

  // Demo Runner State
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStage, setDemoStage] = useState(0);
  const [demoLogs, setDemoLogs] = useState([]);
  const [demoSummary, setDemoSummary] = useState(null);

  const fetchCaseStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/case`);
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.case) {
          setCaseStatus(data.case);
        }
      }
    } catch (err) {
      console.error("Failed to fetch case status:", err);
    }
  };

  // --------------------------------------------------
  // DEMO SCENARIO RUNNER
  // --------------------------------------------------

  const DEMO_SITUATION =
    "I got a new job in Bangalore and my joining is in 10 days. My current accommodation ends in 8 days. I have ₹40,000 available for housing-related expenses and I have not found a long-term place yet.";

  const DEMO_UPDATE =
    "New information: The company will provide temporary accommodation for the first 7 days after joining.";

  const runFullDemo = async () => {
    if (demoRunning || loading || replanLoading) return;

    setDemoRunning(true);
    setDemoStage(0);
    setDemoLogs([]);
    setDemoSummary(null);
    setError("");
    setSituation(DEMO_SITUATION);
    setNewInformation("");
    setAnalysis(null);
    setReplan(null);
    setApproved(false);
    setExecution(null);
    setCaseStatus(null);

    const delay = (ms) => new Promise((res) => setTimeout(res, ms));

    try {
      // 01 UNDERSTAND
      setDemoStage(1);
      setLoading(true);
      setDemoLogs((prev) => [...prev, "✓ Situation submitted"]);

      const analyzeRes = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ situation: DEMO_SITUATION }),
      });

      if (!analyzeRes.ok) throw new Error(`Analyze failed: ${analyzeRes.status}`);

      const analyzeData = await analyzeRes.json();
      const parsedAnalysis =
        analyzeData.analysis || extractJsonObject(analyzeData.raw_response || "");

      if (!parsedAnalysis) throw new Error("Invalid analysis format");

      setAnalysis(parsedAnalysis);
      setLoading(false);
      setDemoLogs((prev) => [...prev, "✓ Situation understood"]);

      // 02 RESEARCH
      setDemoStage(2);
      setDemoLogs((prev) => [...prev, "✓ Research attached"]);
      await delay(1000);

      // 03 DECIDE
      setDemoStage(3);
      setDemoLogs((prev) => [...prev, "✓ Decision generated"]);
      await fetchCaseStatus();
      await delay(1200);

      // 04 & 05 APPROVE & EXECUTE
      setDemoStage(4);
      setDemoLogs((prev) => [...prev, "✓ Human approval completed"]);
      await delay(800);

      setDemoStage(5);
      setDemoLogs((prev) => [...prev, "✓ Safe execution simulated"]);

      const approveRes = await fetch(`${API_URL}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved: true }),
      });

      if (!approveRes.ok) throw new Error(`Approve failed: ${approveRes.status}`);

      const approveData = await approveRes.json();
      setApproved(true);
      if (approveData.execution) {
        setExecution(approveData.execution);
      }

      // 06 TRACK
      setDemoStage(6);
      await fetchCaseStatus();
      setDemoLogs((prev) => [...prev, "✓ Case state updated"]);
      await delay(1500);

      // 07 NEW INFORMATION
      setDemoStage(7);
      setNewInformation(DEMO_UPDATE);
      setDemoLogs((prev) => [...prev, "✓ New information received"]);
      await delay(1200);

      // 08 REPLAN
      setDemoStage(8);
      setReplanLoading(true);

      const replanRes = await fetch(`${API_URL}/replan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_situation: DEMO_SITUATION,
          new_information: DEMO_UPDATE,
        }),
      });

      if (!replanRes.ok) throw new Error(`Replan failed: ${replanRes.status}`);

      const replanData = await replanRes.json();
      setReplan(replanData.replan);
      setReplanLoading(false);
      setDemoLogs((prev) => [...prev, "✓ Plan regenerated"]);

      // 09 FINAL STATE
      setDemoStage(9);
      await fetchCaseStatus();
      setDemoLogs((prev) => [...prev, "✓ Final case state updated"]);

      const initialActionsCount = asArray(parsedAnalysis.immediate_actions).length;
      const rep = replanData.replan || {};
      const updatedActionsCount = (rep.new_actions || rep.revised_plan || []).length;
      const resolvedCount = (rep.resolved_items || []).length;
      const removedCount = (rep.removed_actions || []).length;
      const newActionsCount = (rep.new_actions || []).length;

      setDemoSummary({
        initialActions: initialActionsCount,
        updatedActions: updatedActionsCount,
        resolvedItems: resolvedCount,
        removedActions: removedCount,
        newActions: newActionsCount,
      });

    } catch (err) {
      console.error("Demo run error:", err);
      setError(`Demo execution failed: ${err.message}`);
    } finally {
      setLoading(false);
      setReplanLoading(false);
      setDemoRunning(false);
    }
  };

  // --------------------------------------------------
  // ANALYZE INITIAL SITUATION
  // --------------------------------------------------

  const analyzeSituation = async () => {
    if (!situation.trim()) {
      setError("Please describe your situation first.");
      return;
    }

    setLoading(true);
    setError("");
    setAnalysis(null);
    setReplan(null);
    setApproved(false);
    setExecution(null);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          situation: situation.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      let parsed = null;

      try {
        if (typeof data.analysis === "string") {
          let clean = data.analysis.trim();

          if (clean.startsWith("```")) {
            clean = clean
              .replace(/^```json/i, "")
              .replace(/^```/i, "")
              .replace(/```$/i, "")
              .trim();
          }

          parsed = JSON.parse(clean);
        } else if (data.analysis && typeof data.analysis === "object") {
          parsed = data.analysis;
        } else if (data && typeof data === "object") {
          parsed = data.analysis || data;
        }

        if (parsed && parsed.analysis && typeof parsed.analysis === "object" && !Array.isArray(parsed.analysis)) {
          parsed = parsed.analysis;
        }
      } catch (parseError) {
        console.error("JSON parsing error:", parseError);
      }

      if (!parsed) {
        throw new Error("Nemotron returned an invalid analysis format.");
      }

      setAnalysis(parsed);
      await fetchCaseStatus();
    } catch (err) {
      console.error("Analysis error:", err);

      setError(
        "Could not connect to the agent. Make sure the FastAPI backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  const replanCase = async () => {
    if (!newInformation.trim()) {
      setError("Please enter the new information first.");
      return;
    }

    if (!analysis) {
      setError("Analyze the situation first.");
      return;
    }

    setReplanLoading(true);
    setError("");
    setReplan(null);

    try {
      const response = await fetch(`${API_URL}/replan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_situation: situation.trim(),
          new_information: newInformation.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Replan failed: ${response.status}`);
      }

      const data = await response.json();

      console.log("Replan response:", data);

      setReplan(data.replan);
      await fetchCaseStatus();
    } catch (err) {
      console.error("Replan error:", err);

      setError(
        "Could not rebuild the plan. Make sure the FastAPI backend is running."
      );
    } finally {
      setReplanLoading(false);
    }
  };
  // --------------------------------------------------
  // APPROVE
  // --------------------------------------------------

  const approvePlan = async () => {
    try {
      setError("");

      const response = await fetch(`${API_URL}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          approved: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Approval failed: ${response.status}`);
      }

      const data = await response.json();

      console.log("Plan approval:", data);

      setApproved(true);
      if (data.execution) {
        setExecution(data.execution);
      }
      await fetchCaseStatus();
    } catch (err) {
      console.error("Approval error:", err);

      setError(
        "Could not approve the plan. Make sure the FastAPI backend is running."
      );
    }
  };

  // --------------------------------------------------
  // HELPERS
  // --------------------------------------------------

  const getItemText = (item) => {
    if (item === null || item === undefined) return "";
    if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") {
      return String(item).trim();
    }
    if (typeof item === "object") {
      const text = item.text || item.risk || item.step || item.action || item.description || item.title || item.summary || item.item || item.details;
      if (text && typeof text === "string") {
        return text.trim();
      }
      const stringValues = Object.values(item).filter(v => typeof v === "string" && v.trim());
      if (stringValues.length > 0) {
        return stringValues.join(" - ");
      }
      return JSON.stringify(item);
    }
    return String(item).trim();
  };

  const asArray = (value) => {
    if (!value) return [];

    let rawList = [];
    if (Array.isArray(value)) {
      rawList = value;
    } else if (typeof value === "object") {
      rawList = Object.values(value);
    } else {
      rawList = [value];
    }

    return rawList
      .map(getItemText)
      .filter((text) => text && text.length > 0);
  };

  const renderList = (
    value,
    emptyText = "Nothing identified yet."
  ) => {
    const items = asArray(value);

    if (items.length === 0) {
      return <p>{emptyText}</p>;
    }

    return (
      <div className="section-content">
        {items.map((item, index) => (
          <div className="list-item" key={index}>
            <span className="item-index">
              {String(index + 1).padStart(2, "0")}
            </span>

            <span>{getItemText(item)}</span>
          </div>
        ))}
      </div>
    );
  };

  const getFieldArray = (target, ...keys) => {
    if (!target || typeof target !== "object") return [];
    for (const key of keys) {
      if (target[key] !== undefined && target[key] !== null) {
        const arr = asArray(target[key]);
        if (arr.length > 0) return arr;
      }
    }
    return [];
  };

  const options = asArray(analysis?.options);
  const actions = asArray(analysis?.immediate_actions);
  const risks = asArray(analysis?.risks_and_tradeoffs);

  const removedActions = getFieldArray(replan, "removed_actions", "removedActions", "removed_items", "removed");
  const newActions = getFieldArray(replan, "new_actions", "newActions", "added_actions", "new");
  const updatedRisks = getFieldArray(replan, "updated_risks", "updatedRisks", "risks", "new_risks");
  const revisedPlan = getFieldArray(replan, "revised_plan", "revisedPlan", "plan", "updated_plan");
  const resolvedItems = getFieldArray(replan, "resolved_items", "resolvedItems", "resolved");

  return (
    <div className="app-shell">

      {/* TOP BAR */}
      <header className="topbar">
        <div className="brand">
          CRISIS <span>→</span> ACTION
        </div>

        <div className="agent-status">
          <span className="status-dot"></span>
          NEMOTRON
        </div>
      </header>

      {/* MAIN WORKSPACE */}
      <main className="workspace">

        {/* HERO */}
        <section className="hero">

          <div className="hero-eyebrow">
            DECISION-TO-EXECUTION AGENT
          </div>

          <h1>
            Turn a messy situation
            <br />
            into a clear next move.
          </h1>

          <p>
            Describe what is happening. The agent will identify
            constraints, dependencies, options and next actions.
          </p>

          {/* DECISION THREAD */}
          <div className="decision-thread">

            <div className="thread-step">
              <span className="thread-number">01</span>
              <span>UNDERSTAND</span>
            </div>

            <span className="thread-line">→</span>

            <div className="thread-step">
              <span className="thread-number">02</span>
              <span>EXPLORE</span>
            </div>

            <span className="thread-line">→</span>

            <div className="thread-step">
              <span className="thread-number">03</span>
              <span>DECIDE</span>
            </div>

            <span className="thread-line">→</span>

            <div className="thread-step">
              <span className="thread-number">04</span>
              <span>ACT</span>
            </div>

          </div>
        </section>

        {/* DEMO MODE */}
        <section className="demo-mode-section" style={{
          background: "rgba(30, 41, 59, 0.7)",
          border: "1px solid rgba(56, 189, 248, 0.25)",
          borderRadius: "12px",
          padding: "1.25rem 1.5rem",
          marginBottom: "1.5rem",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.75rem" }}>
            <div>
              <div style={{ fontSize: "0.7rem", letterSpacing: "0.1em", color: "#38bdf8", fontWeight: "700", textTransform: "uppercase" }}>
                CRISIS → ACTION DEMO
              </div>
              <div style={{ fontSize: "0.95rem", fontWeight: "600", color: "#f8fafc", marginTop: "0.15rem" }}>
                Hackathon Full-Lifecycle Scenario Runner
              </div>
            </div>

            <button
              onClick={runFullDemo}
              disabled={demoRunning || loading || replanLoading}
              style={{
                background: demoRunning ? "rgba(56, 189, 248, 0.2)" : "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
                color: "#ffffff",
                border: "1px solid rgba(56, 189, 248, 0.4)",
                padding: "0.6rem 1.25rem",
                borderRadius: "8px",
                fontSize: "0.85rem",
                fontWeight: "700",
                cursor: demoRunning ? "not-allowed" : "pointer",
                letterSpacing: "0.05em",
                boxShadow: demoRunning ? "none" : "0 2px 10px rgba(2, 132, 199, 0.3)",
                transition: "all 0.2s ease"
              }}
            >
              {demoRunning ? `RUNNING (STAGE ${demoStage}/09)...` : "⚡ RUN FULL DEMO"}
            </button>
          </div>

          {/* TIMELINE PROGRESS */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(70px, 1fr))", gap: "0.35rem", marginBottom: "0.75rem" }}>
            {[
              "01 Understand",
              "02 Research",
              "03 Decide",
              "04 Approve",
              "05 Execute",
              "06 Track",
              "07 New Info",
              "08 Replan",
              "09 Final State"
            ].map((label, idx) => {
              const stageNum = idx + 1;
              const isActive = demoStage === stageNum;
              const isPast = demoStage > stageNum;

              return (
                <div key={idx} style={{
                  fontSize: "0.65rem",
                  fontWeight: isActive || isPast ? "700" : "500",
                  textAlign: "center",
                  padding: "0.35rem 0.2rem",
                  borderRadius: "4px",
                  background: isActive
                    ? "rgba(56, 189, 248, 0.25)"
                    : isPast
                    ? "rgba(52, 211, 153, 0.15)"
                    : "rgba(255, 255, 255, 0.03)",
                  color: isActive
                    ? "#38bdf8"
                    : isPast
                    ? "#34d399"
                    : "#64748b",
                  border: isActive
                    ? "1px solid rgba(56, 189, 248, 0.5)"
                    : isPast
                    ? "1px solid rgba(52, 211, 153, 0.3)"
                    : "1px solid rgba(255, 255, 255, 0.04)",
                  transition: "all 0.2s ease"
                }}>
                  {label}
                </div>
              );
            })}
          </div>

          {/* DEMO LOGS */}
          {demoLogs.length > 0 && (
            <div style={{ background: "rgba(0,0,0,0.25)", borderRadius: "6px", padding: "0.5rem 0.75rem", marginBottom: "0.5rem", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem 0.85rem", fontSize: "0.78rem" }}>
                {demoLogs.map((msg, idx) => (
                  <span key={idx} style={{ color: "#34d399", fontWeight: "500" }}>{msg}</span>
                ))}
              </div>
            </div>
          )}

          {/* DEMO COMPLETE SUMMARY */}
          {demoSummary && (
            <div style={{
              background: "rgba(52, 211, 153, 0.08)",
              border: "1px solid rgba(52, 211, 153, 0.3)",
              borderRadius: "8px",
              padding: "0.85rem 1rem",
              marginTop: "0.5rem"
            }}>
              <div style={{ fontSize: "0.8rem", fontWeight: "700", color: "#34d399", letterSpacing: "0.08em", marginBottom: "0.35rem" }}>
                DEMO COMPLETE
              </div>
              <div style={{ fontSize: "0.825rem", color: "#cbd5e1", display: "flex", flexWrap: "wrap", gap: "0.5rem 1.25rem", marginBottom: "0.4rem" }}>
                <span>Initial plan: <strong>{demoSummary.initialActions} actions</strong></span>
                <span>Updated plan: <strong>{demoSummary.updatedActions} actions</strong></span>
                <span>Resolved items: <strong>{demoSummary.resolvedItems}</strong></span>
                <span>Removed actions: <strong>{demoSummary.removedActions}</strong></span>
                <span>New actions: <strong>{demoSummary.newActions}</strong></span>
              </div>
              <div style={{ fontSize: "0.78rem", color: "#94a3b8", fontStyle: "italic", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "0.35rem" }}>
                "CRISIS → ACTION continuously updates the decision and action state when real-world conditions change."
              </div>
            </div>
          )}
        </section>

        {/* INPUT */}
        <section className="input-zone">

          <div className="input-meta">
            <span>YOUR SITUATION</span>
            <span>INPUT</span>
          </div>

          <textarea
            value={situation}
            onChange={(e) => setSituation(e.target.value)}
            placeholder="Example: I got a new job in Bangalore. My joining is in 10 days. My current accommodation ends in 8 days, and I have ₹40,000 available..."
            disabled={loading}
          />

          <div className="input-footer">

            <div className="input-hint">
              The agent structures the situation before suggesting actions.
            </div>

            <button
              className="primary-button"
              onClick={analyzeSituation}
              disabled={loading}
            >
              {loading && <span className="loader"></span>}

              {loading
                ? "ANALYZING..."
                : "UNDERSTAND MY SITUATION →"}
            </button>

          </div>

          {error && (
            <div className="error-box">
              <span>ERROR</span>
              {error}
            </div>
          )}

        </section>

        {/* CASE WORKSPACE */}
        {analysis && (
          <section className="case-workspace">

            {/* LIVE CASE STATUS */}
            {caseStatus && (
              <section className="live-case-status" style={{
                background: "rgba(15, 23, 42, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                padding: "1.25rem 1.5rem",
                marginBottom: "2rem",
                boxShadow: "0 4px 20px rgba(0,0,0,0.3)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "0.75rem" }}>
                  <div>
                    <div style={{ fontSize: "0.7rem", letterSpacing: "0.1em", color: "#38bdf8", fontWeight: "700", textTransform: "uppercase" }}>
                      LIVE CASE STATUS
                    </div>
                    <div style={{ fontSize: "0.9rem", fontWeight: "600", color: "#f8fafc", marginTop: "0.15rem" }}>
                      Case ID: {caseStatus.case_id || "case_001"}
                    </div>
                  </div>
                  {caseStatus.last_updated && (
                    <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                      Updated {new Date(caseStatus.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  )}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem", marginBottom: "1.25rem" }}>
                  <div style={{ background: "rgba(255,255,255,0.03)", padding: "0.6rem 0.85rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Decision</div>
                    <div style={{ fontSize: "0.85rem", fontWeight: "600", color: "#38bdf8", marginTop: "0.15rem" }}>✓ Made</div>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.03)", padding: "0.6rem 0.85rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Approval</div>
                    <div style={{ fontSize: "0.85rem", fontWeight: "600", color: caseStatus.approval ? "#34d399" : "#fbbf24", marginTop: "0.15rem" }}>
                      {caseStatus.approval ? "✓ Approved" : "○ Pending"}
                    </div>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.03)", padding: "0.6rem 0.85rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Execution</div>
                    <div style={{ fontSize: "0.85rem", fontWeight: "600", color: caseStatus.execution ? "#34d399" : "#94a3b8", marginTop: "0.15rem" }}>
                      {caseStatus.execution ? "✓ In Progress" : "○ Pending"}
                    </div>
                  </div>
                </div>

                {caseStatus.progress && (
                  <div style={{ marginBottom: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#cbd5e1", fontWeight: "600", marginBottom: "0.35rem" }}>
                      Progress: {caseStatus.progress.completed} / {caseStatus.progress.total} actions completed
                    </div>
                    <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
                      <div style={{
                        width: `${caseStatus.progress.total > 0 ? (caseStatus.progress.completed / caseStatus.progress.total) * 100 : 0}%`,
                        height: "100%",
                        backgroundColor: "#34d399",
                        transition: "width 0.3s ease"
                      }} />
                    </div>
                  </div>
                )}

                {caseStatus.actions && caseStatus.actions.length > 0 && (
                  <div style={{ marginBottom: "1rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
                      Actions
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                      {caseStatus.actions.map((act) => {
                        const isExec = act.status === "executed";
                        const isRem = act.status === "removed";
                        const isApp = act.status === "approved";
                        const statusColor = isExec ? "#34d399" : isRem ? "#f87171" : isApp ? "#60a5fa" : "#fbbf24";
                        const icon = isExec ? "✓" : isRem ? "✕" : "○";

                        return (
                          <div key={act.id} style={{
                            fontSize: "0.85rem",
                            color: isRem ? "#64748b" : "#e2e8f0",
                            textDecoration: isRem ? "line-through" : "none",
                            display: "flex",
                            justify: "space-between",
                            alignItems: "center",
                            background: "rgba(255,255,255,0.02)",
                            padding: "0.45rem 0.75rem",
                            borderRadius: "6px",
                            border: "1px solid rgba(255,255,255,0.04)"
                          }}>
                            <span>
                              <span style={{ color: statusColor, marginRight: "0.5rem", fontWeight: "bold" }}>{icon}</span>
                              {act.title}
                            </span>
                            <span style={{
                              fontSize: "0.7rem",
                              fontWeight: "700",
                              color: statusColor,
                              letterSpacing: "0.05em",
                              textTransform: "uppercase",
                              background: `rgba(${isExec ? "52,211,153" : isRem ? "248,113,113" : isApp ? "96,165,250" : "251,191,36"}, 0.12)`,
                              padding: "0.15rem 0.5rem",
                              borderRadius: "4px"
                            }}>
                              {act.status}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {caseStatus.risks && caseStatus.risks.length > 0 && (
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "#fbbf24", fontWeight: "700", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.35rem" }}>
                      Risks
                    </div>
                    {caseStatus.risks.slice(0, 3).map((r, idx) => (
                      <div key={idx} style={{ fontSize: "0.8rem", color: "#cbd5e1", marginBottom: "0.2rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
                        <span style={{ color: "#fbbf24" }}>⚠</span> {typeof r === "string" ? r : r.title || String(r)}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* CASE HEADER */}
            <div className="case-header">

              <div>

                <div className="section-eyebrow">
                  STEP 01 / 04 — UNDERSTAND
                </div>

                <h1>
                  Here is what I understand.
                </h1>

                <p>
                  The situation has been structured into decisions,
                  constraints and actions.
                </p>

              </div>

              <div className="agent-status">
                <span className="status-dot"></span>
                CASE STRUCTURED
              </div>

            </div>

            {/* OBJECTIVE */}
            <section className="objective">

              <div className="objective-label">
                GOAL
              </div>

              <h2>
                {analysis.goal || "Goal not identified."}
              </h2>

            </section>

            {/* CONTEXT + CONSTRAINTS */}
            <div className="case-grid">

              <section className="workspace-section">

                <div className="section-eyebrow">
                  CONTEXT
                </div>

                <h2>
                  What is happening
                </h2>

                {renderList(analysis.context)}

              </section>

              <section className="workspace-section">

                <div className="section-eyebrow">
                  CONSTRAINTS
                </div>

                <h2>
                  What limits the decision
                </h2>

                {renderList(analysis.constraints)}

              </section>

            </div>

            {/* DEADLINES + DEPENDENCIES */}
            <div className="case-grid">

              <section className="workspace-section accent-section">

                <div className="section-eyebrow">
                  DEADLINES
                </div>

                <h2>
                  What cannot wait
                </h2>

                {renderList(analysis.deadlines)}

              </section>

              <section className="workspace-section">

                <div className="section-eyebrow">
                  DEPENDENCIES
                </div>

                <h2>
                  What depends on what
                </h2>

                {renderList(analysis.dependencies)}

              </section>

            </div>

            {/* MISSING INFORMATION */}
            <section className="workspace-section">

              <div className="section-eyebrow">
                MISSING INFORMATION
              </div>

              <h2>
                What still needs to be known
              </h2>

              {renderList(analysis.missing_information)}

            </section>

            {/* EVIDENCE */}
            <section className="workspace-section">

              <div className="section-eyebrow">
                EVIDENCE & RESEARCH
              </div>

              <h2>
                What the agent knows & discovered
              </h2>

              <div style={{ display: "flex", flexDirection: "column", gap: "28px", marginTop: "20px" }}>

                {/* USER-PROVIDED EVIDENCE */}
                <div>
                  <div
                    style={{
                      fontSize: "11px",
                      fontWeight: "700",
                      letterSpacing: "0.08em",
                      color: "#9ca3af",
                      marginBottom: "12px",
                      textTransform: "uppercase",
                      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                    }}
                  >
                    USER-PROVIDED EVIDENCE
                  </div>
                  {renderList(analysis.evidence, "No user-provided evidence.")}
                </div>

                {/* WEB RESEARCH EVIDENCE */}
                <div>
                  <div
                    style={{
                      fontSize: "11px",
                      fontWeight: "700",
                      letterSpacing: "0.08em",
                      color: "#9ca3af",
                      marginBottom: "14px",
                      textTransform: "uppercase",
                      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                    }}
                  >
                    WEB RESEARCH EVIDENCE (VIA N8N WEBHOOK)
                  </div>

                  {Array.isArray(analysis.research_evidence) && analysis.research_evidence.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                      {analysis.research_evidence.map((item, index) => {
                        const title = typeof item === "object" ? (item.title || "Web Source") : "Web Source";
                        const snippet = typeof item === "object" ? (item.snippet || item.body || item.summary || "") : String(item);
                        const url = typeof item === "object" ? item.url : (typeof item === "string" && item.startsWith("http") ? item : "");

                        return (
                          <div
                            key={index}
                            style={{
                              padding: "18px 20px",
                              background: "#0d0f12",
                              border: "1px solid #30333a",
                              borderRadius: "8px",
                            }}
                          >
                            <div
                              style={{
                                fontSize: "14px",
                                fontWeight: "600",
                                color: "#f5f5f5",
                                marginBottom: "8px",
                              }}
                            >
                              {index + 1}. {title}
                            </div>

                            {snippet && (
                              <p
                                style={{
                                  fontSize: "14px",
                                  lineHeight: "1.6",
                                  color: "#9fa7b4",
                                  margin: "0 0 10px 0",
                                }}
                              >
                                {snippet}
                              </p>
                            )}

                            {url && (
                              <a
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  fontSize: "12px",
                                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                                  color: "#60a5fa",
                                  textDecoration: "underline",
                                  wordBreak: "break-all",
                                }}
                              >
                                🔗 {url}
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p style={{ color: "#8f99a8", fontSize: "14px" }}>No web research evidence gathered yet.</p>
                  )}
                </div>

              </div>

            </section>

            {/* OPTIONS */}
            <section className="options-section">

              <div className="section-eyebrow">
                STEP 02 / 04 — EXPLORE
              </div>

              <h2>
                Options & trade-offs
              </h2>

              <div className="option-list">

                {options.length > 0 ? (

                  options.map((option, index) => (

                    <div
                      className="option-row"
                      key={index}
                    >

                      <div className="option-number">
                        OPTION{" "}
                        {String(index + 1).padStart(2, "0")}
                      </div>

                      <div className="option-text">
                        {String(option)}
                      </div>

                      <div className="option-arrow">
                        →
                      </div>

                    </div>

                  ))

                ) : (

                  <p>
                    Nothing identified yet.
                  </p>

                )}

              </div>

            </section>

            {/* RISKS & DECISION SUMMARY */}
            <section className="workspace-section">

              <div className="section-eyebrow">
                STEP 03 / 04 — DECIDE
              </div>

              <h2>
                Decision direction & risks
              </h2>

              {analysis.decision_summary && (
                <div
                  style={{
                    marginBottom: "32px",
                    padding: "24px",
                    background: "#0d0f12",
                    border: "1px solid #30333a",
                    borderRadius: "8px",
                  }}
                >
                  <div className="section-eyebrow" style={{ marginBottom: "12px", color: "#dce3eb" }}>
                    DECISION SUMMARY
                  </div>

                  <p
                    style={{
                      fontSize: "16px",
                      lineHeight: "1.65",
                      color: "#f5f5f5",
                      margin: 0,
                    }}
                  >
                    {typeof analysis.decision_summary === "string"
                      ? analysis.decision_summary
                      : getItemText(analysis.decision_summary)}
                  </p>
                </div>
              )}

              <h3
                style={{
                  fontSize: "15px",
                  fontWeight: "600",
                  letterSpacing: "0.04em",
                  color: "#aab1bd",
                  margin: "0 0 16px 0",
                  textTransform: "uppercase",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                }}
              >
                Risks & trade-offs
              </h3>

              {risks.length > 0 ? (
                renderList(risks)
              ) : (
                <p>
                  Nothing identified yet.
                </p>
              )}

            </section>

            {/* ACTIONS */}
            <section className="actions-section">

              <div className="section-eyebrow">
                STEP 04 / 04 — ACT
              </div>

              <h2>
                Your next actions
              </h2>

              <div className="action-list">

                {actions.length > 0 ? (

                  actions.map((action, index) => (

                    <div
                      className="action-row"
                      key={index}
                    >

                      <div className="action-check">
                        {String(index + 1).padStart(2, "0")}
                      </div>

                      <div>
                        {String(action)}
                      </div>

                    </div>

                  ))

                ) : (

                  <p>
                    Nothing identified yet.
                  </p>

                )}

              </div>

            </section>

            {/* --------------------------------------------------
                REPLAN
            -------------------------------------------------- */}

            <section
              className="workspace-section"
              style={{
                marginTop: "70px",
                paddingTop: "50px",
                borderTop: "1px solid #30333a",
              }}
            >

              <div className="section-eyebrow">
                LIVING CASE
              </div>

              <h2>
                Did something change?
              </h2>

              <p>
                Add new information. The agent will compare it with
                the current case and rebuild the plan.
              </p>

              <textarea
                value={newInformation}
                onChange={(e) =>
                  setNewInformation(e.target.value)
                }
                placeholder="Example: The company will provide accommodation for the first month after joining."
                disabled={replanLoading}
                style={{
                  width: "100%",
                  minHeight: "150px",
                  marginTop: "24px",
                  padding: "18px",
                  border: "1px solid #30333a",
                  borderRadius: "8px",
                  resize: "vertical",
                  fontSize: "16px",
                  lineHeight: "1.6",
                  fontFamily: "inherit",
                  background: "#0d0f12",
                  color: "#f5f5f5",
                  boxSizing: "border-box",
                }}
              />

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "20px",
                  marginTop: "18px",
                  flexWrap: "wrap",
                }}
              >

                <div className="input-hint">
                  The original case stays intact. Only the changed
                  parts are rebuilt.
                </div>

                <button
                  className="primary-button"
                  onClick={replanCase}
                  disabled={replanLoading}
                >
                  {replanLoading
                    ? "REBUILDING PLAN..."
                    : "REPLAN CASE →"}
                </button>

              </div>

            </section>

            {/* --------------------------------------------------
                REPLAN RESULT
            -------------------------------------------------- */}

            {replan && (

              <section className="replan-result">

                {/* REPLAN THREAD */}

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    flexWrap: "wrap",
                    marginBottom: "35px",
                    fontSize: "13px",
                    letterSpacing: "0.08em",
                    fontWeight: "600",
                  }}
                >

                  <span>NEW INFORMATION</span>

                  <span>→</span>

                  <span>
                    {replan.case_changed
                      ? "CASE CHANGED"
                      : "NO CASE CHANGE"}
                  </span>

                  <span>→</span>

                  <span>
                    {replan.case_changed
                      ? "PLAN REBUILT"
                      : "PLAN UNCHANGED"}
                  </span>

                </div>

                {/* CHANGE SUMMARY */}

                <div className="section-eyebrow">
                  CHANGE DETECTED
                </div>

                <h2>
                  {replan.change_summary ||
                    "The case has been updated."}
                </h2>

                {/* RESOLVED */}

                <div
                  className="case-grid"
                  style={{
                    marginTop: "40px",
                  }}
                >

                  <section className="workspace-section">

                    <div className="section-eyebrow">
                      RESOLVED
                    </div>

                    <h2>
                      What is no longer blocking the case
                    </h2>

                    {renderList(
                      resolvedItems,
                      "No previous issue was fully resolved."
                    )}

                  </section>

                  {/* REMOVED ACTIONS */}

                  <section className="workspace-section">

                    <div className="section-eyebrow">
                      REMOVED ACTIONS
                    </div>

                    <h2>
                      What is no longer needed
                    </h2>

                    {renderList(
                      removedActions,
                      "No actions were removed."
                    )}

                  </section>

                </div>

                {/* REVISED DECISION SUMMARY */}
                {replan.revised_decision_summary && (
                  <div
                    style={{
                      marginTop: "35px",
                      padding: "24px",
                      background: "#0d0f12",
                      border: "1px solid #30333a",
                      borderRadius: "8px",
                    }}
                  >
                    <div className="section-eyebrow" style={{ marginBottom: "12px", color: "#dce3eb" }}>
                      REVISED DECISION SUMMARY
                    </div>

                    <p
                      style={{
                        fontSize: "16px",
                        lineHeight: "1.65",
                        color: "#f5f5f5",
                        margin: 0,
                      }}
                    >
                      {typeof replan.revised_decision_summary === "string"
                        ? replan.revised_decision_summary
                        : getItemText(replan.revised_decision_summary)}
                    </p>
                  </div>
                )}

                {/* NEW ACTIONS */}

                <section
                  className="workspace-section"
                  style={{
                    marginTop: "35px",
                  }}
                >

                  <div className="section-eyebrow">
                    NEW ACTIONS
                  </div>

                  <h2>
                    What needs to happen now
                  </h2>

                  {renderList(
                    newActions,
                    "No new actions were created."
                  )}

                </section>

                {/* UPDATED RISKS */}

                <section
                  className="workspace-section"
                  style={{
                    marginTop: "35px",
                  }}
                >

                  <div className="section-eyebrow">
                    UPDATED RISKS
                  </div>

                  <h2>
                    What changed in the risk picture
                  </h2>

                  {renderList(
                    updatedRisks,
                    "No new risks identified."
                  )}

                </section>

                {/* REVISED PLAN */}

                <section
                  className="actions-section"
                  style={{
                    marginTop: "35px",
                  }}
                >

                  <div className="section-eyebrow">
                    REVISED PLAN
                  </div>

                  <h2>
                    The case has been rebuilt.
                  </h2>

                  <div className="action-list">

                    {revisedPlan.length > 0 ? (

                      revisedPlan.map((step, index) => (

                        <div
                          className="action-row"
                          key={index}
                        >

                          <div className="action-check">
                            {String(index + 1).padStart(2, "0")}
                          </div>

                          <div>
                            {getItemText(step)}
                          </div>

                        </div>

                      ))

                    ) : (

                      <p>
                        No revised plan available.
                      </p>

                    )}

                  </div>

                </section>

              </section>

            )}

            {/* WHY */}

            <section className="why-section">

              <button
                className="why-button"
                onClick={() => setShowWhy(!showWhy)}
              >

                <span>
                  WHY DID THE AGENT STRUCTURE IT THIS WAY?
                </span>

                <span>
                  {showWhy ? "↑" : "↓"}
                </span>

              </button>

              {showWhy && (

                <div className="why-content">

                  <div>
                    <strong>GOAL</strong>

                    <span>
                      Separates the desired outcome from the
                      situation details.
                    </span>
                  </div>

                  <div>
                    <strong>CONSTRAINTS</strong>

                    <span>
                      Makes limits visible before actions are proposed.
                    </span>
                  </div>

                  <div>
                    <strong>DEPENDENCIES</strong>

                    <span>
                      Shows which actions depend on missing information
                      or previous actions.
                    </span>
                  </div>

                  <div>
                    <strong>ACTIONS</strong>

                    <span>
                      Converts the analysis into concrete next steps
                      while keeping the human in control.
                    </span>
                  </div>

                </div>

              )}

            </section>

            {/* APPROVAL */}

            <section className="approval-section">

              <div>

                <div className="section-eyebrow">
                  {approved
                    ? "PLAN APPROVED"
                    : "READY FOR REVIEW"}
                </div>

                <h2>
                  {approved
                    ? "Plan approved."
                    : "Review the plan before taking action."}
                </h2>

                <p>
                  {approved
                    ? "Your approved plan has been recorded."
                    : "Nothing is executed automatically. You stay in control."}
                </p>

              </div>

              <button
                className="approve-button"
                onClick={approvePlan}
                disabled={!analysis || approved}
              >
                {approved
                  ? "PLAN APPROVED ✓"
                  : "APPROVE PLAN →"}
              </button>

            </section>

            {approved && (
              <section style={{
                background: "rgba(16, 185, 129, 0.04)",
                border: "1px solid rgba(16, 185, 129, 0.2)",
                borderRadius: "12px",
                padding: "1.25rem 1.5rem",
                marginTop: "1rem"
              }}>
                <div style={{
                  fontSize: "0.75rem",
                  letterSpacing: "0.08em",
                  color: "#34d399",
                  fontWeight: "700",
                  textTransform: "uppercase",
                  marginBottom: "0.25rem"
                }}>
                  EXECUTION STATUS
                </div>
                <div style={{
                  fontSize: "1rem",
                  fontWeight: "600",
                  color: "#f8fafc",
                  marginBottom: "0.5rem"
                }}>
                  Execution
                </div>
                <div style={{
                  fontSize: "0.875rem",
                  color: "#94a3b8",
                  marginBottom: "0.75rem"
                }}>
                  {execution?.actions?.length || 0} action{(execution?.actions?.length || 0) === 1 ? '' : 's'} sent to execution workflow.
                </div>

                {execution?.actions && execution.actions.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {execution.actions.map((act, idx) => (
                      <div
                        key={idx}
                        style={{
                          fontSize: "0.85rem",
                          color: "#cbd5e1",
                          display: "flex",
                          justify: "space-between",
                          alignItems: "center",
                          background: "rgba(0, 0, 0, 0.2)",
                          padding: "0.5rem 0.85rem",
                          borderRadius: "6px",
                          border: "1px solid rgba(255, 255, 255, 0.05)"
                        }}
                      >
                        <span style={{ fontWeight: "500" }}>
                          {idx + 1}. {act.action || act.title}
                        </span>
                        <span style={{
                          fontSize: "0.7rem",
                          fontWeight: "700",
                          color: "#34d399",
                          letterSpacing: "0.05em",
                          textTransform: "uppercase",
                          background: "rgba(52, 211, 153, 0.12)",
                          padding: "0.2rem 0.55rem",
                          borderRadius: "4px"
                        }}>
                          {act.status || "EXECUTED"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

          </section>
        )}

        {/* EMPTY STATE */}

        {!analysis && !loading && (

          <section className="case-workspace">

            <div className="case-header">

              <div>

                <div className="section-eyebrow">
                  READY
                </div>

                <h1>
                  Describe your situation.
                </h1>

                <p>
                  Your decision workspace will appear here after
                  the agent analyzes it.
                </p>

              </div>

            </div>

          </section>

        )}

      </main>

      {/* FOOTER */}

      <footer className="footer">
        <span>CRISIS → ACTION</span>
        <span>POWERED BY NVIDIA NEMOTRON · NEBIUS</span>
      </footer>

    </div>
  );
}