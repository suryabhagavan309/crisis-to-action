
import { useState } from "react"

function Section({ title, items }) {
  if (!items || items.length === 0) return null

  return (
    <section
      style={{
        marginTop: "24px",
        padding: "20px",
        background: "#11151a",
        border: "1px solid #292d33",
        borderRadius: "10px",
      }}
    >
      <h3
        style={{
          marginTop: 0,
          marginBottom: "14px",
          fontSize: "14px",
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "#9ca3af",
        }}
      >
        {title}
      </h3>

      <div style={{ color: "#e5e7eb", lineHeight: "1.6" }}>
        {Array.isArray(items) ? (
          <ul style={{ paddingLeft: "20px", margin: 0 }}>
            {items.map((item, index) => (
              <li key={index} style={{ marginBottom: "8px" }}>
                {typeof item === "object"
                  ? JSON.stringify(item)
                  : item}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ margin: 0 }}>{items}</p>
        )}
      </div>
    </section>
  )
}

function CrisisAction() {
  const [situation, setSituation] = useState("")
  const [caseData, setCaseData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function analyzeSituation() {
    if (!situation.trim()) {
      setError("Please describe your situation first.")
      return
    }

    setLoading(true)
    setError("")
    setCaseData(null)

    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          situation: situation,
        }),
      })

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`)
      }

      const data = await response.json()

      let parsed

      try {
        parsed = JSON.parse(data.analysis)
      } catch {
        parsed = data.analysis
      }

      setCaseData(parsed)
    } catch (err) {
      console.error(err)

      setError(
        "Could not connect to the Crisis-to-Action backend."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0b0d10",
        color: "#ffffff",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
          padding: "48px 28px",
        }}
      >
        {/* HEADER */}

        <div style={{ marginBottom: "40px" }}>
          <div
            style={{
              fontSize: "12px",
              letterSpacing: "0.12em",
              color: "#8b929c",
              marginBottom: "12px",
            }}
          >
            CRISIS → ACTION
          </div>

          <h1
            style={{
              fontSize: "42px",
              margin: 0,
              fontWeight: 600,
            }}
          >
            What are you trying to figure out?
          </h1>

          <p
            style={{
              color: "#8b929c",
              marginTop: "12px",
              fontSize: "15px",
            }}
          >
            Turn a messy situation into a structured decision and action plan.
          </p>
        </div>

        {/* INPUT */}

        <div
          style={{
            border: "1px solid #343941",
            borderRadius: "10px",
            background: "#0f1216",
            padding: "20px",
          }}
        >
          <textarea
            value={situation}
            onChange={(e) => setSituation(e.target.value)}
            placeholder="Describe your situation..."
            style={{
              width: "100%",
              minHeight: "160px",
              boxSizing: "border-box",
              background: "transparent",
              color: "#ffffff",
              border: "none",
              outline: "none",
              resize: "vertical",
              fontSize: "16px",
              lineHeight: "1.6",
            }}
          />

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: "14px",
            }}
          >
            <button
              onClick={analyzeSituation}
              disabled={loading}
              style={{
                padding: "12px 20px",
                background: loading ? "#555" : "#ffffff",
                color: "#000000",
                border: "none",
                borderRadius: "7px",
                fontWeight: 600,
                cursor: loading ? "wait" : "pointer",
              }}
            >
              {loading
                ? "Analyzing..."
                : "Understand my situation →"}
            </button>
          </div>
        </div>

        {/* ERROR */}

        {error && (
          <div
            style={{
              marginTop: "20px",
              padding: "16px",
              border: "1px solid #555",
              borderRadius: "8px",
              color: "#ff8b8b",
            }}
          >
            {error}
          </div>
        )}

        {/* RESULT */}

        {caseData && typeof caseData === "object" && (
          <div style={{ marginTop: "45px" }}>

            {/* GOAL */}

            {caseData.goal && (
              <section
                style={{
                  padding: "24px",
                  border: "1px solid #343941",
                  borderRadius: "10px",
                  background: "#101419",
                }}
              >
                <div
                  style={{
                    fontSize: "12px",
                    color: "#8b929c",
                    letterSpacing: "0.1em",
                  }}
                >
                  PRIMARY OBJECTIVE
                </div>

                <h2
                  style={{
                    margin: "10px 0 0",
                    fontSize: "25px",
                    fontWeight: 500,
                  }}
                >
                  {caseData.goal}
                </h2>
              </section>
            )}

            <Section
              title="What I Understand"
              items={caseData.context}
            />

            <Section
              title="Hard Constraints"
              items={caseData.constraints}
            />

            <Section
              title="Critical Timeline"
              items={caseData.deadlines}
            />

            <Section
              title="Dependencies"
              items={caseData.dependencies}
            />

            <Section
              title="Missing Information"
              items={caseData.missing_information}
            />

            <Section
              title="Options & Trade-offs"
              items={caseData.options}
            />

            <Section
              title="Risks & Trade-offs"
              items={caseData.risks_and_tradeoffs}
            />

            <Section
              title="Your Next Actions"
              items={caseData.immediate_actions}
            />

          </div>
        )}

        {/* RAW RESPONSE FALLBACK */}

        {caseData && typeof caseData !== "object" && (
          <div
            style={{
              marginTop: "30px",
              padding: "20px",
              background: "#11151a",
              border: "1px solid #292d33",
              borderRadius: "10px",
              whiteSpace: "pre-wrap",
              lineHeight: "1.6",
            }}
          >
            {caseData}
          </div>
        )}
      </div>
    </div>
  )
}

export default CrisisAction
