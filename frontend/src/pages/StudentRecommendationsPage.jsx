import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

const DIM_LABELS = {
  abstract_reasoning: "Abstract",
  logical_reasoning: "Logical",
  theoretical_knowledge: "Theoretical",
  quantitative_calculation: "Quantitative",
  practical_application: "Practical",
};
const DIM_COLORS = {
  abstract_reasoning: "#8b5cf6", logical_reasoning: "#3b82f6",
  theoretical_knowledge: "#10b981", quantitative_calculation: "#f59e0b",
  practical_application: "#ef4444",
};
const COGNITIVE_DIMS = Object.keys(DIM_LABELS);

function MiniBarChart({ profile }) {
  if (!profile) return null;
  const maxV = Math.max(...COGNITIVE_DIMS.map((d) => profile[d] || 0), 1);
  return (
    <div className="flex gap-2">
      {COGNITIVE_DIMS.map((d) => {
        const val = Math.round(profile[d] || 0);
        const h = Math.max((val / maxV) * 100, 6);
        return (
          <div key={d} className="flex flex-1 flex-col items-center justify-end">
            <span className="text-[10px] font-black text-black">{val}%</span>
            <div className="mt-1 w-full rounded-t border-[2px] border-black transition-all duration-500"
              style={{ height: `${Math.min(h, 120)}px`, backgroundColor: DIM_COLORS[d] }}
            />
            <span className="mt-1.5 text-[9px] font-black uppercase text-gray-600 text-center leading-tight">{DIM_LABELS[d]}</span>
          </div>
        );
      })}
    </div>
  );
}

const printDimLabels = {
  abstract_reasoning: "Abstract\nReasoning",
  logical_reasoning: "Logical\nReasoning",
  theoretical_knowledge: "Theoretical\nKnowledge",
  quantitative_calculation: "Quantitative\nCalculation",
  practical_application: "Practical\nApplication",
};

function recalcCompatibility(cognitive, course) {
  if (!cognitive || !course?.cognitive_dims) return null;
  const dims = Object.keys(course.cognitive_dims);
  if (!dims.length) return null;
  const diff = dims.reduce((s, d) => s + Math.abs((cognitive[d] || 0) - (course.cognitive_dims[d] || 0)), 0) / dims.length;
  return Math.max(0, Math.round(100 - diff));
}

function generateProfileInsight(cognitive) {
  if (!cognitive) return null;
  const DIM_LABELS_SHORT = { abstract_reasoning: "Abstract", logical_reasoning: "Logical", theoretical_knowledge: "Theoretical", quantitative_calculation: "Quantitative", practical_application: "Practical" };
  const dims = Object.keys(DIM_LABELS_SHORT).map((d) => ({ key: d, label: DIM_LABELS_SHORT[d], value: cognitive[d] || 0 }));
  dims.sort((a, b) => a.value - b.value);
  const weakest = dims[0];
  const secondWeakest = dims[1];
  const strongest = dims[dims.length - 1];
  const secondStrongest = dims[dims.length - 2];
  return `Your cognitive profile shows strength in ${strongest.label} (${Math.round(strongest.value)}%) and ${secondStrongest.label} (${Math.round(secondStrongest.value)}%). Recommendations are selected to complement your strengths while gradually building your weaker areas — ${weakest.label} (${Math.round(weakest.value)}%) and ${secondWeakest.label} (${Math.round(secondWeakest.value)}%).`;
}

export default function StudentRecommendationsPage() {
  const [plan, setPlan] = useState(null);
  const [cognitive, setCognitive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    try {
      const [r, c] = await Promise.all([
        api.get("advisories/recommendations/"),
        api.get("advisories/profile/"),
      ]);
      setPlan(r.data[0] || null);
      setCognitive(c.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const generate = async () => {
    setSaving(true); setMsg("");
    try {
      const r = await api.post("advisories/recommendations/generate/");
      setPlan(r.data);
      const c = await api.get("advisories/profile/");
      setCognitive(c.data);
      setMsg("Recommendation generated successfully.");
    } catch (e) { setMsg("Could not generate. Add results first."); }
    finally { setSaving(false); }
  };

  const acknowledge = async () => {
    if (!plan) return;
    setSaving(true); setMsg("");
    try {
      const r = await api.post(`advisories/recommendations/${plan.id}/acknowledge/`);
      setPlan(r.data);
      setMsg("Plan reviewed and acknowledged.");
    } finally { setSaving(false); }
  };

  const printPDF = async () => {
    try {
      const [profRes, cogRes] = await Promise.all([
        api.get("accounts/profile/"),
        api.get("advisories/profile/"),
      ]);
      const profile = profRes.data;
      const cog = cogRes.data;

      const courses = plan?.rule_snapshot?.courses || plan?.selected_courses || [];
      const deferred = plan?.rule_snapshot?.deferred_courses || [];
      const totalUnits = plan?.rule_snapshot?.total_units || courses.reduce((s, c) => s + (c.credit_units || 0), 0);

      const dims = [
        { key: "abstract_reasoning", label: "Abstract Reasoning", value: cog.abstract_reasoning || 0 },
        { key: "logical_reasoning", label: "Logical Reasoning", value: cog.logical_reasoning || 0 },
        { key: "theoretical_knowledge", label: "Theoretical Knowledge", value: cog.theoretical_knowledge || 0 },
        { key: "quantitative_calculation", label: "Quantitative Calculation", value: cog.quantitative_calculation || 0 },
        { key: "practical_application", label: "Practical Application", value: cog.practical_application || 0 },
      ];

      const reviewStatus = plan?.review_status === "accepted" ? "Accepted by Advisor" :
        plan?.student_acknowledged ? "Awaiting Advisor Review" : "Pending Student Acknowledgment";
      const barColor = (v) => v >= 70 ? "#15803d" : v >= 50 ? "#ca8a04" : "#dc2626";

      const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Recommended Registration Plan</title>
<style>
  @page { margin: 18mm 16mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #1a1a1a;
    background: #fff;
    line-height: 1.5;
    padding: 0;
  }
  .watermark {
    position: fixed;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-30deg);
    font-size: 90px; font-weight: 900;
    color: rgba(0,0,0,0.03);
    letter-spacing: 12px;
    z-index: -1;
    white-space: nowrap;
  }
  .header {
    border-bottom: 3px solid #ca8a04;
    padding-bottom: 14px;
    margin-bottom: 22px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }
  .header h1 {
    font-size: 20px;
    font-weight: 900;
    color: #000;
    letter-spacing: -0.3px;
    line-height: 1.2;
  }
  .header .sub {
    font-size: 9px;
    font-weight: 800;
    text-transform: uppercase;
    color: #ca8a04;
    letter-spacing: 2px;
  }
  .header .date {
    font-size: 10px;
    font-weight: 700;
    color: #666;
    text-align: right;
  }
  .section-title {
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #ca8a04;
    margin-bottom: 10px;
    padding-bottom: 4px;
    border-bottom: 2px solid #eee;
  }
  .info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin-bottom: 22px;
    background: #f8f7f2;
    border: 2px solid #000;
    padding: 14px 16px;
  }
  .info-item label {
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    color: #999;
    display: block;
    letter-spacing: 0.8px;
  }
  .info-item p {
    font-size: 13px;
    font-weight: 800;
    color: #000;
    margin-top: 2px;
  }
  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 22px;
  }
  .card {
    border: 2px solid #000;
    padding: 14px 16px 18px;
    background: #fff;
  }

  /* --- Histogram --- */
  .histogram {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    height: 160px;
    padding: 0 4px;
    gap: 6px;
    border-bottom: 2px solid #000;
  }
  .bar-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
    justify-content: flex-end;
  }
  .bar {
    width: 100%;
    max-width: 52px;
    min-height: 4px;
    border: 2px solid #000;
    transition: none;
    position: relative;
  }
  .bar-label {
    font-size: 7px;
    font-weight: 800;
    text-align: center;
    color: #555;
    margin-top: 6px;
    line-height: 1.2;
    white-space: pre-line;
  }
  .bar-value {
    font-size: 12px;
    font-weight: 900;
    text-align: center;
    margin-bottom: 3px;
  }
  .legend {
    display: flex;
    gap: 14px;
    margin-top: 8px;
    justify-content: center;
    font-size: 8px;
    font-weight: 700;
    color: #666;
  }
  .legend span { display: flex; align-items: center; gap: 4px; }
  .legend .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid #000; }

  /* --- Table --- */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10px;
  }
  thead th {
    background: #000;
    color: #fff;
    font-size: 8px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 7px 8px;
    text-align: left;
    border: 1px solid #000;
  }
  tbody td {
    padding: 7px 8px;
    border-bottom: 1px solid #ddd;
    font-weight: 600;
    color: #1a1a1a;
    vertical-align: middle;
  }
  tbody tr:last-child td { border-bottom: none; }
  .carryover-badge {
    display: inline-block;
    font-size: 7px;
    font-weight: 800;
    background: #fef3c7;
    border: 1.5px solid #000;
    padding: 1px 6px;
    border-radius: 20px;
    color: #92400e;
    margin-left: 4px;
  }
  .compat-pill {
    display: inline-block;
    font-weight: 800;
    padding: 2px 8px;
    border: 1.5px solid #000;
    border-radius: 4px;
    font-size: 10px;
    min-width: 36px;
    text-align: center;
  }
  .deferred-title {
    font-size: 13px;
    font-weight: 800;
    color: #92400e;
    margin-top: 18px;
    margin-bottom: 6px;
  }
  .deferred-table td {
    background: #fffbeb;
  }
  .footer {
    margin-top: 30px;
    padding-top: 12px;
    border-top: 2px solid #000;
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    font-weight: 700;
    color: #666;
  }
  .footer strong { color: #000; }
  .page-break { page-break-before: always; }
</style>
</head>
<body>
<div class="watermark">COURSE PLAN</div>

<div class="header">
  <div>
    <div class="sub">Course Planning System</div>
    <h1>Recommended Registration Plan</h1>
  </div>
  <div class="date">
    Generated: ${new Date(plan?.generated_at || Date.now()).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}<br>
    Status: <strong style="color:#000">${reviewStatus}</strong>
  </div>
</div>

<div class="info-grid">
  <div class="info-item">
    <label>Student Name</label>
    <p>${profile.last_name || ""} ${profile.first_name || ""}</p>
  </div>
  <div class="info-item">
    <label>Matriculation No.</label>
    <p>${profile.username || ""}</p>
  </div>
  <div class="info-item">
    <label>Programme</label>
    <p>${profile.programme || ""}</p>
  </div>
  <div class="info-item">
    <label>Current Level</label>
    <p>${profile.current_level || ""}</p>
  </div>
  <div class="info-item">
    <label>Semester</label>
    <p>${profile.current_semester || ""}</p>
  </div>
  <div class="info-item">
    <label>Session</label>
    <p>${profile.session || ""}</p>
  </div>
</div>

<div class="two-col">
  <div class="card">
    <div class="section-title">Cognitive Profile</div>
    <div class="histogram">
      ${dims.map(d => {
        const v = Math.round(d.value);
        const h = Math.max(v * 1.5, 6);
        return `<div class="bar-wrapper">
          <div class="bar-value" style="color:${barColor(v)}">${v}%</div>
          <div class="bar" style="height:${h}px; background:${barColor(v)}"></div>
          <div class="bar-label">${printDimLabels[d.key] || d.label}</div>
        </div>`;
      }).join("")}
    </div>
    <div class="legend">
      <span><span class="dot" style="background:#15803d"></span> Strong (≥70%)</span>
      <span><span class="dot" style="background:#ca8a04"></span> Moderate (50–69%)</span>
      <span><span class="dot" style="background:#dc2626"></span> Weak (<50%)</span>
    </div>
  </div>

  <div class="card">
    <div class="section-title">Plan Summary</div>
    <table style="margin-top:4px">
      <tbody>
        <tr><td style="font-weight:800;width:50%;padding:5px 0;border:none">Courses Recommended</td><td style="font-weight:900;font-size:20px;padding:5px 0;border:none">${courses.length}</td></tr>
        <tr><td style="font-weight:800;padding:5px 0;border:none">Total Credit Units</td><td style="font-weight:900;font-size:20px;padding:5px 0;border:none">${totalUnits}</td></tr>
        ${deferred.length > 0 ? `<tr><td style="font-weight:800;padding:5px 0;border:none">Deferred Carryovers</td><td style="font-weight:900;font-size:18px;padding:5px 0;border:none;color:#92400e">${deferred.length}</td></tr>` : ""}
        <tr><td style="font-weight:800;padding:5px 0;border:none">Student Acknowledged</td><td style="font-weight:900;padding:5px 0;border:none;font-size:14px">${plan?.student_acknowledged ? "Yes" : "No"}</td></tr>
        <tr><td style="font-weight:800;padding:5px 0;border:none">Advisor Decision</td><td style="font-weight:900;padding:5px 0;border:none;text-transform:capitalize;font-size:14px">${plan?.review_status === "accepted" ? "Accepted" : plan?.review_status === "rejected" ? "Rejected" : "Pending"}</td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="section-title">Recommended Courses</div>
<table>
  <thead>
    <tr>
      <th style="width:44px">Code</th>
      <th>Course Title</th>
      <th style="width:44px;text-align:center">Units</th>
      <th style="width:64px;text-align:center">Compatibility</th>
    </tr>
  </thead>
  <tbody>
    ${courses.length === 0 ? '<tr><td colspan="4" style="text-align:center;padding:20px;font-weight:700;color:#999">No courses in plan</td></tr>' :
      courses.map(c => `<tr>
        <td style="font-weight:900;font-size:10px">${c.code || ""}</td>
        <td>${c.title || ""}${c.carryover ? '<span class="carryover-badge">CARRYOVER</span>' : ""}</td>
        <td style="text-align:center;font-weight:800">${c.credit_units || ""}</td>
        <td style="text-align:center"><span class="compat-pill" style="background:${(c.compatibility ?? 50) >= 70 ? "#dcfce7" : (c.compatibility ?? 50) >= 50 ? "#fef9c3" : "#fee2e2"}">${c.compatibility ?? "—"}%</span></td>
      </tr>`).join("")}
  </tbody>
</table>

${deferred.length > 0 ? `
<div class="deferred-title">Deferred to Future Semesters</div>
<table class="deferred-table">
  <thead>
    <tr>
      <th style="width:44px">Code</th>
      <th>Course Title</th>
      <th style="width:44px;text-align:center">Units</th>
      <th>Cognitive Focus</th>
    </tr>
  </thead>
  <tbody>
    ${deferred.map(c => `<tr>
      <td style="font-weight:900;font-size:10px">${c.code || ""}</td>
      <td>${c.title || ""}</td>
      <td style="text-align:center;font-weight:800">${c.credit_units || ""}</td>
      <td style="font-size:9px">${c.dominant_dim ? c.dominant_dim.replace(/_/g, " ") : ""}</td>
    </tr>`).join("")}
  </tbody>
</table>` : ""}

<div class="footer">
  <div>
    Generated by <strong>Cognitive Course Planning System</strong><br>
    ${profile.last_name || ""} ${profile.first_name || ""} · ${profile.current_level || ""}
  </div>
  <div style="text-align:right">
    Print date: ${new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}<br>
    Page 1 of 1
  </div>
</div>
</body>
</html>`;

      const w = window.open("", "_blank");
      w.document.write(html);
      w.document.close();
      w.focus();
      setTimeout(() => { w.print(); }, 400);
    } catch (e) {
      setMsg("Could not generate PDF. Try again.");
    }
  };

  const courses = plan?.rule_snapshot?.courses || plan?.selected_courses || [];
  const deferred = plan?.rule_snapshot?.deferred_courses || [];
  if (loading) return <p className="text-sm font-bold text-gray-500">Loading recommendations…</p>;

  const statusLabel = plan?.review_status === "accepted" ? "Accepted" : "Pending Review";
  const statusColor = plan?.review_status === "accepted" ? "text-green-600" : "text-[#ca8a04]";

  return (
    <div className="space-y-7">
      {/* Header */}
      <section className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-black uppercase tracking-wider text-[#ca8a04]">Course Planning</p>
          <h1 className="mt-1 text-3xl font-black tracking-tight text-black">Recommended Registration Plan</h1>
          <p className="mt-2 max-w-2xl text-sm font-bold text-gray-600">
            Carryover courses are auto-included and prioritised first, then balanced by your cognitive profile. Add new results on the Transcript page and regenerate to update the plan.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={generate} disabled={saving}
            className="rounded-2xl border-[3px] border-black bg-[#ca8a04] px-5 py-3 text-sm font-black text-black shadow-[4px_4px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">
            {saving ? "Working..." : "Generate Plan"}
          </button>
          {plan && (
            <button onClick={printPDF}
              className="rounded-2xl border-[3px] border-black bg-white px-5 py-3 text-sm font-black text-black shadow-[4px_4px_0_0_#000] active:shadow-none transition-all">
              Print PDF
            </button>
          )}
        </div>
      </section>

      {msg && (
        <div className="rounded-2xl border-[2px] border-black bg-[#fef9c3] p-4 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">
          {msg}
        </div>
      )}

      {!plan ? (
        <section className="rounded-3xl border-[3px] border-dashed border-black bg-white p-14 text-center shadow-[8px_8px_0_0_#000]">
          <p className="text-4xl">📋</p>
          <h2 className="mt-4 text-xl font-black text-black">No recommendation plan yet</h2>
          <p className="mt-2 text-sm font-bold text-gray-500">Add your results on the Transcript page, then generate your first course plan.</p>
        </section>
      ) : (
        <>
          {/* Stats */}
          <section className="grid gap-4 sm:grid-cols-4">
            <div className="rounded-2xl border-[3px] border-black bg-black p-5 text-white shadow-[6px_6px_0_0_#000]">
              <p className="text-xs font-black uppercase text-[#facc15]">Recommended Load</p>
              <p className="mt-2 text-3xl font-black">{plan.rule_snapshot?.total_units || 0} units</p>
              <p className="mt-3 text-xs font-bold text-gray-300">15–24 unit policy</p>
            </div>
            <div className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
              <p className="text-xs font-black uppercase text-gray-500">Review Status</p>
              <p className={`mt-2 text-3xl font-black capitalize ${statusColor}`}>{statusLabel}</p>
            </div>
            <div className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
              <p className="text-xs font-black uppercase text-gray-500">Courses Selected</p>
              <p className="mt-2 text-3xl font-black text-black">{courses.length}</p>
            </div>
            <div className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
              <p className="text-xs font-black uppercase text-gray-500">Your Review</p>
              <p className={`mt-2 text-3xl font-black ${plan.student_acknowledged ? "text-green-600" : "text-[#ca8a04]"}`}>
                {plan.student_acknowledged ? "Done" : "Pending"}
              </p>
            </div>
          </section>

          {/* Cognitive profile for context */}
          {cognitive && (
            <section className="rounded-3xl border-[3px] border-black bg-white p-5 shadow-[8px_8px_0_0_#000]">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-black text-black">Your Cognitive Profile</h2>
                  <p className="text-xs font-bold text-gray-500">Used to match courses to your strengths</p>
                </div>
                <Link to="/dashboard/student/profile" className="text-xs font-black text-[#ca8a04] underline underline-offset-4">View full</Link>
              </div>
              <div className="mt-4">
                <MiniBarChart profile={cognitive} />
              </div>
              <blockquote className="mt-4 border-l-[3px] border-[#ca8a04] pl-3 text-xs font-bold leading-5 text-gray-600">
                {generateProfileInsight(cognitive)}
              </blockquote>
            </section>
          )}

          {/* Course list */}
          <section className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
            <div className="border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
              <h2 className="text-lg font-black text-black">Optimised Course Selection</h2>
              <p className="mt-1 text-sm font-bold text-gray-600">Ranked by cognitive profile compatibility</p>
            </div>
            <div className="divide-y-[2px] divide-black">
              {courses.map((c) => (
                <article className="flex gap-4 p-5" key={c.id || c.code}>
                  <div className="grid h-12 w-16 shrink-0 place-items-center rounded-xl border-[2px] border-black bg-[#fef9c3] text-xs font-black text-black shadow-[2px_2px_0_0_#000]">{c.code}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-black text-black">{c.title}</h3>
                      {c.carryover && <span className="rounded-full border-[2px] border-black bg-amber-100 px-2 py-0.5 text-[10px] font-black text-amber-800">⚠️ Carryover</span>}
                    </div>
                    <p className="mt-1 text-sm font-bold text-gray-500">{c.explanation || c.description}</p>
                  </div>
                   <div className="text-right">
                    {(() => {
                      const liveCompat = recalcCompatibility(cognitive, c);
                      const displayCompat = liveCompat ?? c.compatibility;
                      const compatColor = displayCompat >= 70 ? "text-green-700" : displayCompat >= 50 ? "text-amber-700" : "text-red-700";
                      return <p className={`text-xl font-black ${compatColor}`}>{displayCompat ?? "—"}%</p>;
                    })()}
                    <p className="text-xs font-bold text-gray-500">{c.credit_units} units</p>
                  </div>
                </article>
              ))}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t-[2px] border-black bg-[#fef9c3] p-5">
              <p className="text-sm font-bold text-gray-600">
                {plan.review_status === "accepted"
                  ? "✅ Accepted by your advisor. You can proceed with registration."
                  : plan.student_acknowledged
                    ? "Waiting for advisor review."
                    : "Review this plan and acknowledge once you've reviewed it."}
              </p>
              <div className="flex gap-2">
                {!plan.student_acknowledged && (
                  <button disabled={saving} onClick={acknowledge}
                    className="rounded-xl border-[2px] border-black bg-black px-4 py-2 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all">
                    {saving ? "..." : "OK — I've Reviewed"}
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* Deferred carryovers */}
          {deferred.length > 0 && (
            <section className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
              <div className="border-b-[3px] border-black bg-amber-50 px-6 py-4">
                <h2 className="text-lg font-black text-amber-800">Deferred to Future Semesters</h2>
                <p className="mt-1 text-sm font-bold text-amber-700">
                  {deferred.length} carryover course(s) deferred to avoid overwhelming your weaker cognitive areas.
                  You will focus on them in subsequent semesters.
                </p>
              </div>
              <div className="divide-y-[2px] divide-black">
                {deferred.map((c) => (
                  <article className="flex items-center gap-4 p-4" key={c.id}>
                    <div className="grid h-10 w-14 shrink-0 place-items-center rounded-xl border-[2px] border-black bg-amber-100 text-xs font-black text-amber-800 shadow-[2px_2px_0_0_#000]">
                      {c.code}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-black text-black">{c.title}</h3>
                      <p className="mt-0.5 text-xs font-bold text-gray-500">
                        {c.credit_units} units · {c.dominant_dim ? `Focus: ${c.dominant_dim.replace(/_/g, " ")}` : ""}
                      </p>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
