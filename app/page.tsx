"use client";

import { FormEvent, useMemo, useState } from "react";

type Forecast = {
  question: string;
  probability: number;
  confidence: "Low" | "Medium" | "High";
  reasoning: string[];
};

const EXAMPLES = [
  "Will the S&P 500 finish higher this month?",
  "Will a major AI lab release a new flagship model this quarter?",
  "Will the Lakers win their next game?"
];

function scoreForecast(question: string, evidence: string, prior: number): Forecast {
  const text = `${question} ${evidence}`.toLowerCase();
  const positive = ["growth", "increase", "ahead", "strong", "likely", "win", "approved", "launch", "higher"];
  const negative = ["decline", "delay", "weak", "unlikely", "loss", "blocked", "lower", "risk", "miss"];
  const positiveHits = positive.filter((word) => text.includes(word)).length;
  const negativeHits = negative.filter((word) => text.includes(word)).length;
  const evidenceWeight = Math.min(18, evidence.trim().length / 35);
  const raw = prior + (positiveHits - negativeHits) * 6 + (positiveHits >= negativeHits ? evidenceWeight : -evidenceWeight);
  const probability = Math.max(5, Math.min(95, Math.round(raw)));
  const signalCount = positiveHits + negativeHits;
  const confidence = evidence.length > 220 && signalCount >= 3 ? "High" : evidence.length > 80 ? "Medium" : "Low";

  return {
    question,
    probability,
    confidence,
    reasoning: [
      `Started from a ${prior}% base-rate prior supplied by you.`,
      `${positiveHits} positive and ${negativeHits} negative directional signals were detected in the evidence.`,
      confidence === "Low"
        ? "The evidence is thin, so this forecast should be updated as new information arrives."
        : "The evidence has enough detail to support a directional adjustment, but uncertainty remains."
    ]
  };
}

export default function Home() {
  const [question, setQuestion] = useState(EXAMPLES[0]);
  const [evidence, setEvidence] = useState("");
  const [prior, setPrior] = useState(50);
  const [forecast, setForecast] = useState<Forecast | null>(null);

  const ringStyle = useMemo(
    () => ({ background: `conic-gradient(#6ee7b7 ${forecast?.probability ?? 0}%, #1d293d 0)` }),
    [forecast]
  );

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setForecast(scoreForecast(question.trim(), evidence.trim(), prior));
  }

  return (
    <main>
      <nav>
        <div className="brand"><span>◉</span> Forecast Lab</div>
        <div className="status">Transparent MVP · No API key required</div>
      </nav>

      <section className="hero">
        <p className="eyebrow">AI-assisted probabilistic thinking</p>
        <h1>Turn uncertain questions into a clear forecast.</h1>
        <p className="lede">Set a base rate, add evidence, and generate an explainable probability you can challenge and update.</p>
      </section>

      <section className="workspace">
        <form onSubmit={submit} className="panel formPanel">
          <label>Prediction question</label>
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Will X happen by Y date?" />

          <div className="examples">
            {EXAMPLES.map((example) => (
              <button type="button" key={example} onClick={() => setQuestion(example)}>{example}</button>
            ))}
          </div>

          <label>Evidence and context</label>
          <textarea value={evidence} onChange={(e) => setEvidence(e.target.value)} placeholder="Paste known facts, recent developments, arguments for and against, or assumptions…" />

          <div className="priorRow">
            <div>
              <label>Base-rate prior</label>
              <p>Your probability before considering the evidence.</p>
            </div>
            <strong>{prior}%</strong>
          </div>
          <input className="range" type="range" min="5" max="95" value={prior} onChange={(e) => setPrior(Number(e.target.value))} />
          <button className="primary" type="submit">Generate forecast</button>
        </form>

        <aside className="panel resultPanel">
          {!forecast ? (
            <div className="empty">
              <div className="emptyIcon">↗</div>
              <h2>Your forecast appears here</h2>
              <p>The model uses a deliberately simple, inspectable scoring method so the MVP works immediately without external services.</p>
            </div>
          ) : (
            <div className="result">
              <p className="eyebrow">Current forecast</p>
              <h2>{forecast.question}</h2>
              <div className="probabilityWrap">
                <div className="ring" style={ringStyle}><div><strong>{forecast.probability}%</strong><span>YES</span></div></div>
                <div><span className={`badge ${forecast.confidence.toLowerCase()}`}>{forecast.confidence} confidence</span><p>Estimated chance the event occurs.</p></div>
              </div>
              <h3>Why this estimate</h3>
              <ol>{forecast.reasoning.map((item) => <li key={item}>{item}</li>)}</ol>
              <div className="warning">This is a decision-support tool, not financial, medical, or legal advice.</div>
            </div>
          )}
        </aside>
      </section>

      <footer>Built for fast deployment on Vercel · Next.js App Router</footer>
    </main>
  );
}
