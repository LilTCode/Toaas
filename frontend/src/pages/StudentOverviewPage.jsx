import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

const COGNITIVE_DIMS = [
  "abstract_reasoning", "logical_reasoning", "theoretical_knowledge",
  "quantitative_calculation", "practical_application",
];

const DIM_LABELS = {
  abstract_reasoning: "Abstract", logical_reasoning: "Logical",
  theoretical_knowledge: "Theoretical", quantitative_calculation: "Quantitative",
  practical_application: "Practical",
};

const DIM_COLORS = {
  abstract_reasoning: "#8b5cf6", logical_reasoning: "#3b82f6",
  theoretical_knowledge: "#10b981", quantitative_calculation: "#f59e0b",
  practical_application: "#ef4444",
};

function generateProfileInsight(cognitive) {
  if (!cognitive) return null;
  const dims = COGNITIVE_DIMS.map((d) => ({ key: d, label: DIM_LABELS[d], value: cognitive[d] || 0 }));
  dims.sort((a, b) => a.value - b.value);
  const weakest = dims[0];
  const secondWeakest = dims[1];
  const strongest = dims[dims.length - 1];
  const secondStrongest = dims[dims.length - 2];
  return `Your cognitive profile shows strength in ${strongest.label} (${Math.round(strongest.value)}%) and ${secondStrongest.label} (${Math.round(secondStrongest.value)}%). Recommendations are selected to complement your strengths while gradually building your weaker areas — ${weakest.label} (${Math.round(weakest.value)}%) and ${secondWeakest.label} (${Math.round(secondWeakest.value)}%).`;
}

function MiniBarChart({ profile }) {
  if (!profile) return <p className="text-sm font-bold text-gray-400">No data</p>;
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

export default function StudentOverviewPage() {
  const [profile, setProfile] = useState(null);
  const [activities, setActivities] = useState([]);
  const [recommendation, setRecommendation] = useState(null);
  const [cognitive, setCognitive] = useState(null);
  const [transcript, setTranscript] = useState([]);

  const load = async () => {
    try {
      const [p, a, r, c, t] = await Promise.all([
        api.get("accounts/profile/"),
        api.get("advisories/activity/"),
        api.get("advisories/recommendations/"),
        api.get("advisories/profile/"),
        api.get("courses/transcript/"),
      ]);
      setProfile(p.data);
      setActivities(a.data || []);
      setRecommendation(r.data[0] || null);
      setCognitive(c.data);
      setTranscript(t.data || []);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  const gpa = (() => {
    if (!transcript.length) return "0.00";
    const total = transcript.reduce((s, e) => s + (e.credit_points || 0), 0);
    return (total / transcript.length).toFixed(2);
  })();

  const carryoverCount = transcript.filter((e) => e.status === "carryover" || e.status === "failed").length;
  const credits = transcript.filter((e) => e.status === "passed").reduce((s, e) => s + (e.course?.credit_units || 0), 0);

  const gpaColor = parseFloat(gpa) >= 3.0 ? "text-green-700" : parseFloat(gpa) >= 2.0 ? "text-amber-700" : "text-red-700";

  const timeGreeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();

  const studentName = profile?.first_name || "Student";

  return (
    <div className="space-y-7">
      {/* Greeting */}
      <section className="flex flex-col gap-6 rounded-3xl border-[3px] border-black bg-black px-6 py-7 text-white shadow-[8px_8px_0_0_#000] sm:px-8 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-black uppercase tracking-wider text-[#facc15]">
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
          </p>
          <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">{timeGreeting}, {studentName}.</h1>
          <p className="mt-3 max-w-xl text-sm font-bold leading-6 text-gray-300">
            {profile ? `${profile.current_level} Level · ${profile.current_semester === 1 ? "First" : "Second"} Semester · ${profile.session} Session` : ""}
          </p>
        </div>
        <Link to="/dashboard/student/recommendations" className="rounded-xl border-[2px] border-[#facc15] bg-[#facc15] px-5 py-3 text-center text-sm font-black text-black shadow-[4px_4px_0_0_#000] transition-all hover:bg-white active:shadow-none">
          Review My Plan →
        </Link>
      </section>

      {/* Stats */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Current CGPA", gpa, gpaColor, gpaColor],
          ["Credits Earned", credits, "text-black", "text-black"],
          ["Carryover Courses", carryoverCount, carryoverCount > 0 ? "text-amber-700" : "text-green-700", carryoverCount > 0 ? "text-amber-700" : "text-green-700"],
          ["Plan Status", recommendation?.review_status ? (recommendation.review_status === "accepted" ? "Accepted" : "Pending review") : "No plan yet", "text-black", "text-black"],
        ].map(([label, value, color]) => (
          <article key={label} className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
            <p className="text-xs font-black uppercase text-gray-500">{label}</p>
            <p className={`mt-3 text-3xl font-black tracking-tight ${color}`}>{value}</p>
          </article>
        ))}
      </section>

      {/* Main grid */}
      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.8fr]">
        {/* Recent activity */}
        <article className="rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
          <div className="border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
            <h2 className="text-lg font-black text-black">Recent Activity</h2>
            <p className="mt-1 text-sm font-bold text-gray-600">Your latest workspace updates</p>
          </div>
          <div className="p-5">
            {activities.length === 0 ? (
              <p className="text-sm font-bold text-gray-400">No activity yet. Start by adding your results.</p>
            ) : (
              <div className="space-y-4">
                {activities.slice(0, 6).map((a) => (
                  <div key={a.id} className="flex gap-3">
                    <span className="mt-1.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border-[2px] border-black bg-[#ca8a04] text-[10px] font-black text-black">✓</span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-bold text-black">{a.action}</p>
                      {a.detail && <p className="text-xs font-medium text-gray-500">{a.detail}</p>}
                    </div>
                    <p className="text-[10px] font-bold text-gray-400">{new Date(a.created_at).toLocaleDateString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </article>

        {/* Cognitive profile */}
        <article className="rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
          <div className="border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
            <h2 className="text-lg font-black text-black">Cognitive Profile</h2>
            <p className="mt-1 text-sm font-bold text-gray-600">Based on your passed results</p>
          </div>
          <div className="p-5">
            {cognitive ? (
              <MiniBarChart profile={cognitive} />
            ) : (
              <p className="text-sm font-bold text-gray-400">Add results to build your cognitive profile.</p>
            )}
            <Link to="/dashboard/student/profile" className="mt-5 inline-block text-sm font-black text-[#ca8a04] underline underline-offset-4">View full profile →</Link>
          </div>
        </article>
      </section>

      {/* Bottom actions */}
      <section className="grid gap-6 xl:grid-cols-2">
        <article className="rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000]">
          <h2 className="text-lg font-black text-black">Academic Insight</h2>
          {cognitive && (
            <div className="mt-4 mb-5 border-b-[2px] border-dashed border-gray-200 pb-5">
              <MiniBarChart profile={cognitive} />
            </div>
          )}
          <blockquote className="border-l-[4px] border-[#ca8a04] pl-4 text-base font-bold leading-7 text-gray-700">
            {generateProfileInsight(cognitive) || recommendation?.explanation || "Add your results to build your cognitive profile and generate a recommendation plan."}
          </blockquote>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="rounded-xl border-[2px] border-black bg-black px-4 py-2.5 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all" to="/dashboard/student/chat">Ask the assistant</Link>
            <Link className="rounded-xl border-[2px] border-black bg-white px-4 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all" to="/dashboard/student/messages">Contact advisor</Link>
            <Link className="rounded-xl border-[2px] border-black bg-[#fef9c3] px-4 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-white" to="/dashboard/student/messages">Contact Support</Link>
          </div>
        </article>
        <article className="rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000]">
          <h2 className="text-lg font-black text-black">Quick Links</h2>
          <div className="mt-4 space-y-3">
            <Link className="flex items-center gap-3 rounded-2xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/transcript">Add results</Link>
            <Link className="flex items-center gap-3 rounded-2xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/recommendations">Generate recommendations</Link>
            <Link className="flex items-center gap-3 rounded-2xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/chat">Chat with AI</Link>
            <Link className="flex items-center gap-3 rounded-2xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/profile">View cognitive profile</Link>
            <Link className="flex items-center gap-3 rounded-2xl border-[2px] border-black bg-[#fef9c3] px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-white" to="/dashboard/student/messages">Contact Admin / Support</Link>
          </div>
        </article>
      </section>
    </div>
  );
}