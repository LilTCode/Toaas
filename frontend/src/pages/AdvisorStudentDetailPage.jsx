import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../services/api";

const COGNITIVE_DIMS = [
  "abstract_reasoning", "logical_reasoning", "theoretical_knowledge",
  "quantitative_calculation", "practical_application",
];
const DIM_LABELS_SHORT = {
  abstract_reasoning: "Abstract", logical_reasoning: "Logical",
  theoretical_knowledge: "Theoretical", quantitative_calculation: "Quantitative",
  practical_application: "Practical",
};
const DIM_COLORS = {
  abstract_reasoning: "#8b5cf6", logical_reasoning: "#3b82f6",
  theoretical_knowledge: "#10b981", quantitative_calculation: "#f59e0b",
  practical_application: "#ef4444",
};

const Y_MAX = 50;
const Y_TICKS = [0, 10, 20, 30, 40, 50];

function BarChart({ profile }) {
  if (!profile) return <p className="text-sm font-bold text-gray-400">No cognitive data.</p>;
  const CHART_H = 224;
  const LABEL_W = 30;
  const BAR_AREA_H = CHART_H - 3;
  return (
    <div>
      <div className="flex" style={{ height: CHART_H }}>
        {/* Y-axis labels */}
        <div className="w-[30px] shrink-0 flex flex-col justify-between pt-0 pb-0">
          {[...Y_TICKS].reverse().map((tick) => (
            <span key={tick} className="text-[10px] font-black text-gray-500 leading-none -mt-1">{tick}</span>
          ))}
        </div>
        {/* Grid + bars */}
        <div className="flex-1 relative ml-0.5">
          {/* Grid lines */}
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
            {[...Y_TICKS].reverse().map((tick) => (
              <div key={tick} className="border-t border-dashed border-gray-300" />
            ))}
          </div>
          {/* Bars — absolute inset-0 gives explicit height so pixel values work */}
          <div className="absolute inset-0 flex items-end gap-1.5 border-l-[3px] border-b-[3px] border-black">
            {COGNITIVE_DIMS.map((d) => {
              const val = profile[d] || 0;
              const hPx = Math.max(Math.round((val / Y_MAX) * BAR_AREA_H), 3);
              return (
                <div key={d} className="flex-1 flex flex-col items-center self-stretch justify-end min-w-0 pb-[3px]">
                  <span className="text-[10px] font-black text-black leading-none mb-0.5">{Math.round(val)}</span>
                  <div className="w-full rounded-t border-[2px] border-black transition-all shrink-0" style={{ height: hPx, backgroundColor: DIM_COLORS[d] }} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
      {/* X-axis labels */}
      <div className="flex ml-[34px]">
        {COGNITIVE_DIMS.map((d) => (
          <div key={d} className="flex-1 text-center">
            <span className="text-[9px] font-black text-black">{DIM_LABELS_SHORT[d]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdvisorStudentDetailPage() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("ai_history");
  const [replyText, setReplyText] = useState("");
  const [sending, setSending] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get(`advisories/students/${studentId}/`);
        setData(r.data);
      } catch { /* ignore */ } finally { setLoading(false); }
    })();
  }, [studentId]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [activeTab, data?.chat_history, data?.advisor_messages]);

  const sendMessage = async () => {
    if (!replyText.trim()) return; setSending(true);
    try {
      await api.post("advisories/staff/send-message/", {
        student_id: parseInt(studentId), subject: "Advisor guidance", body: replyText,
      });
      setReplyText("");
      const r = await api.get(`advisories/students/${studentId}/`);
      setData(r.data);
    } finally { setSending(false); }
  };

  const reviewRecommendation = async (decision) => {
    setReviewing(true);
    try {
      const r = await api.post(`advisories/students/${studentId}/review-recommendation/`, { decision });
      setData(prev => ({ ...prev, recommendation: r.data }));
    } catch { /* ignore */ } finally { setReviewing(false); }
  };

  if (loading) return <div className="min-h-screen bg-[#f3f1e8] flex items-center justify-center"><p className="text-sm font-bold text-gray-500">Loading student details…</p></div>;
  if (!data) return <div className="min-h-screen bg-[#f3f1e8] flex items-center justify-center"><p className="text-sm font-bold text-red-500">Student not found.</p></div>;

  const { student, cognitive_profile, transcript, carryovers, chat_history, advisor_messages } = data;
  const programmeColor = (prog) => {
    const map = { computer_science: "bg-blue-100 text-blue-800", software_engineering: "bg-emerald-100 text-emerald-800", cyber_security: "bg-purple-100 text-purple-800" };
    return map[prog] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="min-h-screen bg-[#f3f1e8] p-4 lg:p-8">
      <div className="mx-auto max-w-7xl">
        {/* Back button + header */}
        <div className="mb-6 flex items-center justify-between">
          <button onClick={() => navigate("/dashboard/advisor")} className="rounded-xl border-[2px] border-black bg-black px-4 py-2 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-gray-800">← Back to Dashboard</button>
          <p className="text-xs font-black uppercase tracking-wider text-[#ca8a04]">Student Detail View</p>
        </div>

        {/* TOP: Student Info Cards */}
        <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
          <div className="space-y-5">
            {/* Info card */}
            <div className="rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
              <div className="border-b-[3px] border-black bg-black p-4 text-white">
                <h3 className="text-sm font-black uppercase tracking-wider text-[#facc15]">Student Profile</h3>
              </div>
              <div className="p-5 space-y-4">
                <div className="flex items-center gap-4">
                  <div className="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-full border-[3px] border-black bg-[#fef9c3] text-2xl font-black text-black">
                    {student.profile_photo ? <img src={student.profile_photo} alt="" className="h-full w-full object-cover" /> : (student.first_name?.[0] || "S") + (student.last_name?.[0] || "")}
                  </div>
                  <div>
                    <p className="text-lg font-black text-black">{student.full_name || student.email}</p>
                    <p className="text-sm font-bold text-gray-500">{student.username}</p>
                    <span className={`mt-1 inline-block rounded-full border-[1.5px] border-black px-2.5 py-0.5 text-xs font-black ${programmeColor(student.programme)}`}>{student.programme_display?.replace("B.Sc. ", "") || student.programme}</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 sm:gap-4">
                  <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-3">
                    <p className="text-[10px] font-black uppercase text-gray-500">Level</p>
                    <p className="mt-1 text-lg font-black text-black">{student.current_level}L</p>
                  </div>
                  <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-3">
                    <p className="text-[10px] font-black uppercase text-gray-500">Semester</p>
                    <p className="mt-1 text-lg font-black text-black">{student.current_semester === 1 ? "First" : "Second"}</p>
                  </div>
                  <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-3">
                    <p className="text-[10px] font-black uppercase text-gray-500">CGPA</p>
                    <p className={`mt-1 text-lg font-black ${student.cgpa >= 3.0 ? "text-green-700" : student.cgpa >= 2.0 ? "text-amber-700" : "text-red-700"}`}>{student.cgpa.toFixed(2)}</p>
                  </div>
                  <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-3">
                    <p className="text-[10px] font-black uppercase text-gray-500">Session</p>
                    <p className="mt-1 text-lg font-black text-black">{student.session}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendation Plan Review */}
            {data.recommendation && (
              <div className="rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
                <div className="border-b-[3px] border-black bg-black px-5 py-3 text-white">
                  <h3 className="text-sm font-black uppercase tracking-wider text-[#facc15]">Recommendation Plan</h3>
                </div>
                <div className="p-5 space-y-4">
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-2">
                      <p className="text-[10px] font-black uppercase text-gray-500">Units</p>
                      <p className="text-lg font-black text-black">{data.recommendation.rule_snapshot?.total_units || 0}</p>
                    </div>
                    <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-2">
                      <p className="text-[10px] font-black uppercase text-gray-500">Courses</p>
                      <p className="text-lg font-black text-black">{data.recommendation.rule_snapshot?.course_count || 0}</p>
                    </div>
                    <div className="rounded-xl border-[2px] border-black bg-[#fef9c3] p-2">
                      <p className="text-[10px] font-black uppercase text-gray-500">Student</p>
                      <p className="text-lg font-black text-black">{data.recommendation.student_acknowledged ? "Seen ✓" : "Pending"}</p>
                    </div>
                  </div>

                  <div className="rounded-xl border-[2px] border-black p-3">
                    <p className="text-[10px] font-black uppercase text-gray-500 mb-1">Status</p>
                    <p className={`text-lg font-black ${data.recommendation.review_status === "accepted" ? "text-green-700" : data.recommendation.review_status === "rejected" ? "text-red-700" : "text-amber-700"}`}>
                      {data.recommendation.review_status === "accepted" ? "Accepted" : data.recommendation.review_status === "rejected" ? "Rejected" : "Pending Review"}
                    </p>
                    <p className="text-[9px] font-bold text-gray-400 mt-1">You can change this decision at any time.</p>
                  </div>

                  {/* Recommended courses list */}
                  {(data.recommendation.rule_snapshot?.courses || []).length > 0 && (
                    <div>
                      <p className="text-xs font-black uppercase text-gray-500 mb-2">Recommended Courses</p>
                      <div className="max-h-36 overflow-y-auto space-y-1.5">
                        {(data.recommendation.rule_snapshot.courses || []).map((c) => (
                          <div key={c.id || c.code} className="flex items-center justify-between rounded-lg border-[1.5px] border-black px-3 py-1.5 text-xs font-bold">
                            <span className="text-black">{c.code} — {c.title}</span>
                            <span className="text-gray-500">{c.credit_units} units</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button onClick={() => reviewRecommendation("rejected")} disabled={reviewing}
                      className="flex-1 rounded-xl border-[2px] border-black bg-white px-3 py-2 text-xs font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">
                      {reviewing ? "..." : data.recommendation.review_status === "rejected" ? "✓ Rejected" : "Reject"}
                    </button>
                    <button onClick={() => reviewRecommendation("accepted")} disabled={reviewing}
                      className="flex-1 rounded-xl border-[2px] border-black bg-black px-3 py-2 text-xs font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">
                      {reviewing ? "..." : data.recommendation.review_status === "accepted" ? "✓ Accepted" : "Accept"}
                    </button>
                  </div>

                  {data.recommendation.reviewed_by_name && (
                    <p className="text-[10px] font-bold text-gray-500">
                      Reviewed by: {data.recommendation.reviewed_by_name}
                      {data.recommendation.reviewed_at && ` · ${new Date(data.recommendation.reviewed_at).toLocaleDateString()}`}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Cognitive Profile Histogram */}
            <div className="rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
              <div className="border-b-[3px] border-black bg-[#fef9c3] px-5 py-3">
                <h3 className="text-sm font-black text-black">Cognitive Profile</h3>
              </div>
              <div className="p-5">
                <BarChart profile={cognitive_profile} />
              </div>
            </div>

            {/* Carryovers */}
            {carryovers?.length > 0 && (
              <div className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
                <div className="border-b-[3px] border-black bg-red-50 px-5 py-3">
                  <h3 className="text-sm font-black text-red-800">Carryover Courses ({carryovers.length})</h3>
                </div>
                <div className="divide-y-[2px] divide-black">
                  {carryovers.map((co) => (
                    <div key={co.id} className="flex items-center justify-between gap-3 px-5 py-3">
                      <div className="min-w-0">
                        <p className="text-sm font-black text-black truncate">{co.course_code}</p>
                        <p className="text-xs font-bold text-gray-500 truncate">{co.course_title} · {co.credit_units} units</p>
                      </div>
                      <span className="shrink-0 rounded-full border-[2px] border-red-300 bg-red-50 px-2 py-0.5 text-[10px] font-black text-red-700">{co.grade || "F"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transcript summary */}
            <div className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
              <div className="border-b-[3px] border-black bg-[#fef9c3] px-5 py-3">
                <h3 className="text-sm font-black text-black">Transcript Summary</h3>
              </div>
              <div className="divide-y-[2px] divide-black max-h-48 overflow-y-auto">
                {transcript?.length === 0 ? <p className="p-5 text-sm font-bold text-gray-400">No entries.</p> : transcript.map((e) => (
                  <div key={e.id} className="flex items-center justify-between gap-3 px-5 py-2.5">
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-black truncate">{e.course_code}</p>
                      <p className="text-xs text-gray-500">Sem {e.semester}</p>
                    </div>
                    <span className={`shrink-0 text-sm font-black ${e.grade === "A" ? "text-green-600" : e.grade === "F" ? "text-red-600" : "text-black"}`}>{e.grade}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM: Conversation & Messaging */}
        <div className="mt-6 overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000]">
          <header className="border-b-[3px] border-black bg-black p-5 text-white">
            <div className="flex items-center gap-3">
              <div className="grid h-12 w-12 shrink-0 place-items-center overflow-hidden rounded-full border-[2px] border-white/30 bg-[#fef9c3] text-sm font-black text-black">
                {student.profile_photo ? <img src={student.profile_photo} alt="" className="h-full w-full object-cover" /> : (student.first_name?.[0] || "S") + (student.last_name?.[0] || "")}
              </div>
              <div>
                <p className="text-sm font-black">{student.full_name || student.email}</p>
                <p className="text-xs font-bold text-gray-300">{student.username} · {student.current_level}L · {student.programme_display?.replace("B.Sc. ", "")}</p>
              </div>
            </div>
          </header>

          {/* Tabs */}
          <div className="flex border-b-[2px] border-black bg-gray-50">
            <button onClick={() => setActiveTab("ai_history")} className={`flex-1 py-3 text-xs font-black uppercase tracking-wider transition-all ${activeTab === "ai_history" ? "bg-black text-white" : "text-gray-500 hover:text-black"}`}>AI Conversations</button>
            <button onClick={() => setActiveTab("advisor_chat")} className={`flex-1 py-3 text-xs font-black uppercase tracking-wider transition-all ${activeTab === "advisor_chat" ? "bg-black text-white" : "text-gray-500 hover:text-black"}`}>Advisor Messages</button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto bg-[#f3f1e8] p-4 space-y-4 min-h-[350px] max-h-[500px]">
            {activeTab === "ai_history" ? (
              chat_history.length === 0 ? <p className="text-center text-sm font-bold text-gray-400 py-8">No AI conversations yet.</p> :
              chat_history.map((conv) => (
                <div key={conv.conversation_id} className="space-y-3">
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500">Conversation · {new Date(conv.created_at).toLocaleDateString()}</p>
                  {conv.messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.sender_role === "student" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] rounded-2xl border-[2px] border-black px-4 py-2.5 text-sm font-bold shadow-[3px_3px_0_0_#000] ${msg.sender_role === "student" ? "bg-[#ca8a04] text-black" : "bg-white text-black"}`}>
                        <p className="text-[9px] font-black uppercase tracking-wider text-gray-500 mb-0.5">{msg.sender_role === "student" ? "Student" : "AI Assistant"}</p>
                        <p>{msg.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ))
            ) : (
              advisor_messages.length === 0 ? <p className="text-center text-sm font-bold text-gray-400 py-8">No advisor messages yet.</p> :
              advisor_messages.map((m) => (
                <div key={m.id} className="space-y-3">
                  <div className="flex justify-end">
                    <div className="max-w-[80%] rounded-2xl border-[2px] border-black bg-[#ca8a04] px-4 py-2.5 text-sm font-bold shadow-[3px_3px_0_0_#000]">
                      <p className="text-[9px] font-black uppercase tracking-wider text-black/60">Student</p>
                      <p className="mt-1">{m.body}</p>
                      <p className="mt-1 text-[10px] font-bold text-black/50">{new Date(m.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  {m.replies?.map((r) => (
                    <div key={r.id} className="flex justify-start">
                      <div className="max-w-[80%] rounded-2xl border-[2px] border-black bg-white px-4 py-2.5 text-sm font-bold shadow-[3px_3px_0_0_#000]">
                        <p className="text-[9px] font-black uppercase tracking-wider text-gray-500">{r.sender_name || "Staff"}</p>
                        <p className="mt-1">{r.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ))
            )}
            <div ref={endRef} />
          </div>

          {/* Quick message input */}
          <div className="border-t-[3px] border-black bg-white px-4 py-3">
            <div className="flex gap-3">
              <input value={replyText} onChange={(e) => setReplyText(e.target.value)} placeholder="Send a message to this student…" className="min-w-0 flex-1 rounded-xl border-[2px] border-black px-4 py-2.5 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
              <button onClick={sendMessage} disabled={sending || !replyText.trim()} className="rounded-xl border-[2px] border-black bg-black px-5 py-2.5 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">{sending ? "…" : "Send"}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
