import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AssistantPopup from "../components/AssistantPopup";
import api from "../services/api";

const assessmentQuestions = [
  { key: "abstract_reasoning", label: "How comfortable are you with abstract problem solving?" },
  { key: "logical_reasoning", label: "How strong is your logical reasoning when solving technical problems?" },
  { key: "theoretical_knowledge", label: "How much do you enjoy theory-heavy coursework?" },
  { key: "quantitative_calculation", label: "How confident are you with calculations and quantitative analysis?" },
  { key: "practical_application", label: "How much do you prefer hands-on or applied learning?" },
];

const initialAssessment = {
  abstract_reasoning: "high", logical_reasoning: "high", theoretical_knowledge: "medium",
  quantitative_calculation: "medium", practical_application: "high",
};

export default function StudentDashboardPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [cognitive, setCognitive] = useState(null);
  const [courses, setCourses] = useState([]);
  const [transcript, setTranscript] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [activities, setActivities] = useState([]);
  const [assessment, setAssessment] = useState(() => {
    const saved = localStorage.getItem("toaas_assessment");
    return saved ? JSON.parse(saved) : initialAssessment;
  });
  const [transcriptForm, setTranscriptForm] = useState({ courseId: "", semester: "First", grade: "A", status: "passed" });
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const load = async () => {
    try {
      const [p, c, r, co, t, a] = await Promise.all([
        api.get("accounts/profile/"),
        api.get("advisories/profile/"),
        api.get("advisories/recommendations/"),
        api.get("courses/course/"),
        api.get("courses/transcript/"),
        api.get("advisories/activity/"),
      ]);
      setProfile(p.data); setCognitive(c.data); setRecommendations(r.data || []);
      setCourses(co.data || []); setTranscript(t.data || []); setActivities(a.data || []);
    } catch { setMsg("Unable to load dashboard data."); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    const token = localStorage.getItem("toaas_access_token");
    if (!token) { navigate("/auth"); return; }
    load();
  }, [navigate]);

  const gpa = useMemo(() => {
    if (!transcript.length) return "0.00";
    return (transcript.reduce((s, e) => s + (e.credit_points || 0), 0) / transcript.length).toFixed(2);
  }, [transcript]);

  const filteredCourses = courses.filter(c => profile && c.level === profile.current_level && c.semester === profile.current_semester);

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[#f3f1e8]"><p className="text-2xl font-black text-black">Loading…</p></div>;

  return (
    <div className="min-h-screen bg-[#f3f1e8] p-4 lg:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Hero */}
        <section className="flex flex-col gap-6 rounded-3xl border-[3px] border-black bg-black px-6 py-7 text-white shadow-[8px_8px_0_0_#000] sm:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-black uppercase tracking-wider text-[#facc15]">Student Dashboard</p>
            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">Welcome, {profile?.username || "Student"}</h1>
            <p className="mt-3 text-sm font-bold text-gray-300">{profile?.current_level || ""} Level · {profile?.current_semester === 1 ? "First" : "Second"} Semester</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button onClick={async () => { setGenerating(true); try { await api.post("advisories/recommendations/generate/"); await load(); setMsg("Recommendation generated successfully."); } catch { setMsg("Add results first."); } finally { setGenerating(false); } }} disabled={generating}
              className="rounded-xl border-[2px] border-[#facc15] bg-[#facc15] px-5 py-3 text-sm font-black text-black shadow-[4px_4px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">
              {generating ? "Working..." : "Generate"}
            </button>
            <button onClick={() => window.dispatchEvent(new CustomEvent("assistant:open"))} className="rounded-xl border-[2px] border-white bg-black px-5 py-3 text-sm font-black text-white shadow-[4px_4px_0_0_#fff] active:shadow-none transition-all">Chat AI</button>
          </div>
        </section>

        {msg && <div className="mt-5 rounded-2xl border-[2px] border-black bg-[#fef9c3] p-4 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">{msg}</div>}

        {/* Stats */}
        <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ["Current CGPA", gpa], ["Recommended Courses", recommendations[0]?.selected_courses?.length || 0],
            ["Transcript Entries", transcript.length], ["Activities", activities.length],
          ].map(([label, value]) => (
            <article key={label} className="rounded-2xl border-[3px] border-black bg-white p-5 shadow-[6px_6px_0_0_#000]">
              <p className="text-xs font-black uppercase text-gray-500">{label}</p>
              <p className="mt-3 text-3xl font-black text-black">{value}</p>
            </article>
          ))}
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-2">
          {/* Quick Add Result */}
          <form onSubmit={async (e) => { e.preventDefault(); try { await api.post("courses/transcript/", { course_id: transcriptForm.courseId, semester: transcriptForm.semester, grade: transcriptForm.grade, status: transcriptForm.status, credit_points: { A: 5.0, B: 4.0, C: 3.0, D: 2.0, E: 1.0, F: 0.0 }[transcriptForm.grade] || 0 }); setMsg("Result saved."); setTranscriptForm({ courseId: "", semester: "First", grade: "A", status: "passed" }); await load(); } catch { setMsg("Select a course."); } }} className="rounded-3xl border-[3px] border-black bg-white p-6 shadow-[8px_8px_0_0_#000]">
            <h2 className="text-lg font-black text-black">Quick Add Result</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <select value={transcriptForm.courseId} onChange={(e) => setTranscriptForm({ ...transcriptForm, courseId: e.target.value })} className="rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                <option value="">— Course —</option>
                {filteredCourses.map((c) => <option key={c.id} value={c.id}>{c.code}</option>)}
              </select>
              <select value={transcriptForm.grade} onChange={(e) => setTranscriptForm({ ...transcriptForm, grade: e.target.value })} className="rounded-xl border-[2px] border-black px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none">
                {["A","B","C","D","E","F"].map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <button type="submit" className="mt-4 rounded-xl border-[2px] border-black bg-[#ca8a04] px-5 py-2.5 text-sm font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all">Save</button>
          </form>

          {/* Recent Activity */}
          <article className="rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
            <div className="border-b-[3px] border-black bg-[#fef9c3] px-6 py-4">
              <h2 className="text-lg font-black text-black">Recent activity</h2>
            </div>
            <div className="p-5 space-y-3">
              {activities.slice(0, 5).map(a => (
                <div key={a.id} className="flex gap-3">
                  <span className="mt-1 h-2.5 w-2.5 rounded-full bg-[#ca8a04]" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-black">{a.action}</p>
                    {a.detail && <p className="text-xs text-gray-500">{a.detail}</p>}
                  </div>
                  <p className="text-[10px] font-bold text-gray-400">{new Date(a.created_at).toLocaleDateString()}</p>
                </div>
              ))}
              {!activities.length && <p className="text-sm font-bold text-gray-400">No activity yet.</p>}
            </div>
          </article>
        </section>

        {/* Quick links */}
        <section className="mt-6 grid gap-4 sm:grid-cols-3">
          <Link className="rounded-2xl border-[2px] border-black bg-white p-4 text-center font-black text-black shadow-[4px_4px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/transcript">Transcript</Link>
          <Link className="rounded-2xl border-[2px] border-black bg-white p-4 text-center font-black text-black shadow-[4px_4px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/recommendations">Recommendations</Link>
          <Link className="rounded-2xl border-[2px] border-black bg-white p-4 text-center font-black text-black shadow-[4px_4px_0_0_#000] active:shadow-none transition-all hover:bg-[#fef9c3]" to="/dashboard/student/profile">Profile</Link>
        </section>
      </div>
      <AssistantPopup />
    </div>
  );
}
