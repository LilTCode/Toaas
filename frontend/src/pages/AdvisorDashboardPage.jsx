import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import usePolling from "../hooks/usePolling";

const COGNITIVE_DIMS = [
  "abstract_reasoning", "logical_reasoning", "theoretical_knowledge",
  "quantitative_calculation", "practical_application",
];
const DIM_LABELS = {
  abstract_reasoning: "Abstract", logical_reasoning: "Logical",
  theoretical_knowledge: "Theoretical", quantitative_calculation: "Quantitative",
  practical_application: "Practical",
};

function MiniHistogram({ profile }) {
  if (!profile) return null;
  const maxVal = Math.max(...COGNITIVE_DIMS.map((d) => profile[d] || 0), 1);
  return (
    <div className="flex items-end gap-[3px] h-10">
      {COGNITIVE_DIMS.map((d) => {
        const h = Math.max(((profile[d] || 0) / maxVal) * 100, 4);
        return (
          <div key={d} className="w-4 rounded-t border-[1.5px] border-black bg-[#ca8a04] transition-all duration-500" style={{ height: `${Math.min(h, 100)}%` }} title={`${DIM_LABELS[d]}: ${Math.round(profile[d] || 0)}%`} />
        );
      })}
    </div>
  );
}

const programmeColor = (prog) => {
  const map = { computer_science: "bg-blue-100 text-blue-800", software_engineering: "bg-emerald-100 text-emerald-800", cyber_security: "bg-purple-100 text-purple-800" };
  return map[prog] || "bg-gray-100 text-gray-800";
};

export default function AdvisorDashboardPage() {
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [replies, setReplies] = useState([]);
  const [replyText, setReplyText] = useState("");
  const [replying, setReplying] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [contactSubject, setContactSubject] = useState("");
  const [contactBody, setContactBody] = useState("");
  const [contactSending, setContactSending] = useState(false);
  const [contactMsg, setContactMsg] = useState("");
  const [adminMessages, setAdminMessages] = useState([]);
  const [selectedAdminMsg, setSelectedAdminMsg] = useState(null);
  const endRef = useRef(null);
  const [advisorName, setAdvisorName] = useState("");

  const loadStudents = async () => {
    try { const r = await api.get("advisories/students/"); setStudents(r.data); } catch { /* ignore */ }
  };
  const loadMessages = async () => {
    try {
      const r = await api.get("advisories/staff/messages/");
      setMessages(r.data);
      return r.data;
    } catch { return null; }
  };
  const loadAdminMessages = async () => {
    try { const r = await api.get("advisories/staff/my-messages/"); setAdminMessages(r.data); } catch { /* ignore */ }
  };

  useEffect(() => {
    loadStudents(); loadMessages(); loadAdminMessages();
    const user = JSON.parse(localStorage.getItem("toaas_user") || "{}");
    setAdvisorName(user.first_name ? `${user.first_name} ${user.last_name}` : "Advisor");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [replies]);

  // Pull new student replies into the open thread without a manual refresh.
  usePolling(async () => {
    const fresh = await loadMessages();
    loadAdminMessages();
    if (!fresh || !selected) return;
    const thread = fresh.find((m) => m.id === selected.id);
    if (!thread) return;
    setSelected(thread);
    setReplies((prev) =>
      (thread.replies?.length ?? 0) === prev.length ? prev : thread.replies || []
    );
  }, 5000);

  const selectMessage = (msg) => { setSelected(msg); setReplies(msg.replies || []); setReplyText(""); };
  const sendReply = async () => {
    if (!replyText.trim() || !selected) return; setReplying(true);
    try {
      const r = await api.post(`advisories/staff/messages/${selected.id}/reply/`, { content: replyText });
      setReplies((prev) => [...prev, r.data]); setReplyText("");
      const updated = await api.get("advisories/staff/messages/"); setMessages(updated.data);
    } finally { setReplying(false); }
  };

  const sendContact = async (e) => {
    e.preventDefault();
    if (!contactSubject.trim() || !contactBody.trim()) return;
    setContactSending(true); setContactMsg("");
    try {
      await api.post("advisories/staff/contact-admin/", { subject: contactSubject, body: contactBody });
      setContactMsg("Message sent to admin.");
      setContactSubject(""); setContactBody("");
      setTimeout(() => setShowContact(false), 1500);
    } catch { setContactMsg("Failed to send."); }
    finally { setContactSending(false); }
  };

  const signOut = () => { localStorage.clear(); navigate("/auth"); };

  return (
    <div className="min-h-screen bg-[#f3f1e8] p-4 lg:p-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        {/* Header with welcome */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-black uppercase tracking-wider text-[#ca8a04]">TO-AAS</p>
            <h1 className="text-3xl font-black tracking-tight text-black">Welcome, {advisorName}.</h1>
            <p className="text-sm font-bold text-gray-500">{students.length} registered students · {messages.filter(m => !m.read).length} unread messages</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setShowContact(true)} className="rounded-xl border-[2px] border-black bg-[#fef9c3] px-4 py-2 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-white">Contact Admin</button>
            <button onClick={signOut} className="rounded-xl border-[2px] border-black bg-white px-4 py-2 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] active:shadow-none transition-all hover:bg-red-50">Sign out</button>
          </div>
        </div>

        {/* Student Cards Grid */}
        <section>
          <h2 className="mb-3 text-lg font-black text-black">Registered Students</h2>
          {students.length === 0 ? (
            <div className="rounded-3xl border-[3px] border-dashed border-black bg-white p-10 text-center shadow-[8px_8px_0_0_#000]">
              <p className="text-sm font-bold text-gray-400">No students registered yet.</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {students.map((s) => (
                <article key={s.id} className="overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[6px_6px_0_0_#000] transition-all hover:shadow-[4px_4px_0_0_#000]">
                  <div className="flex items-start gap-4 p-5">
                    <div className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-full border-[2px] border-black bg-[#fef9c3] text-lg font-black text-black">
                      {s.profile_photo ? <img src={s.profile_photo} alt="" className="h-full w-full object-cover" /> : (s.first_name?.[0] || "S") + (s.last_name?.[0] || "")}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-black text-black truncate">{s.full_name || s.email}</p>
                      <p className="text-xs font-bold text-gray-500">{s.username}</p>
                      <span className={`mt-1 inline-block rounded-full border-[1.5px] border-black px-2 py-0.5 text-[10px] font-black ${programmeColor(s.programme)}`}>{s.programme_display?.replace("B.Sc. ", "") || s.programme}</span>
                      <p className="mt-1 text-xs font-bold text-gray-500">{s.current_level}L · CGPA: <span className={s.cgpa >= 3.0 ? "text-green-700" : s.cgpa >= 2.0 ? "text-amber-700" : "text-red-700"}>{s.cgpa.toFixed(2)}</span></p>
                    </div>
                  </div>
                  <div className="border-t-[2px] border-black px-5 py-3">
                    <div className="flex items-center justify-between">
                      <MiniHistogram profile={s.cognitive_profile} />
                      <button onClick={() => navigate(`/dashboard/advisor/student/${s.id}`)} className="rounded-lg border-[2px] border-black bg-black px-3 py-1.5 text-[10px] font-black text-white shadow-[2px_2px_0_0_#000] active:shadow-none transition-all hover:bg-gray-800">See More</button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {/* Messaging Section */}
        <h2 className="text-lg font-black text-black">Communications</h2>
        <div className="flex gap-2 mb-3">
          <span className="rounded-xl border-[2px] border-black bg-black px-3 py-1 text-[10px] font-black text-white">Student Messages</span>
          {adminMessages.length > 0 && (
            <span className="rounded-xl border-[2px] border-black bg-[#fef9c3] px-3 py-1 text-[10px] font-black text-black">Admin Feedback ({adminMessages.length})</span>
          )}
        </div>
        <section className="flex min-h-[400px] flex-col overflow-hidden rounded-3xl border-[3px] border-black bg-white shadow-[8px_8px_0_0_#000] lg:flex-row">
          {/* Inbox */}
          <aside className="border-b-[3px] border-black lg:w-80 lg:border-b-0 lg:border-r-[3px] lg:rounded-bl-3xl overflow-hidden">
            <div className="border-b-[3px] border-black bg-[#fef9c3] p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-black text-black">Inbox</h3>
                <div className="flex gap-1">
                  <button onClick={loadMessages} title="Refresh student messages" className="rounded-lg border-[2px] border-black px-2 py-0.5 text-[10px] font-black hover:bg-black hover:text-white transition-all">S</button>
                  <button onClick={loadAdminMessages} title="Refresh admin feedback" className="rounded-lg border-[2px] border-black px-2 py-0.5 text-[10px] font-black hover:bg-black hover:text-white transition-all">A</button>
                </div>
              </div>
              <p className="mt-1 text-xs font-bold text-gray-600">
                {selectedAdminMsg ? "Admin feedback" : `${messages.filter(m => !m.read).length} unread student messages`}
              </p>
            </div>
            <div className="max-h-[400px] overflow-y-auto divide-y-[2px] divide-black">
              {/* Tab: Student messages or Admin feedback */}
              <div className="flex border-b-[2px] border-black">
                <button
                  onClick={() => setSelectedAdminMsg(null)}
                  className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wider transition-all ${!selectedAdminMsg ? "bg-black text-white" : "text-gray-500 hover:text-black"}`}
                >Students</button>
                <button
                  onClick={() => setSelectedAdminMsg(adminMessages[0] || null)}
                  className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wider transition-all ${selectedAdminMsg ? "bg-black text-white" : "text-gray-500 hover:text-black"}`}
                >Admin</button>
              </div>
              {!selectedAdminMsg ? (
                messages.length === 0 ? <p className="p-5 text-sm font-bold text-gray-400">No messages.</p> : messages.map((m) => (
                  <button key={m.id} onClick={() => selectMessage(m)} className={`w-full p-4 text-left transition-all ${selected?.id === m.id ? "bg-[#fef9c3]" : "bg-white hover:bg-gray-50"}`}>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-black text-black truncate">{m.student_name}</p>
                      <div className="flex items-center gap-2">
                        {!m.read && <span className="h-2 w-2 rounded-full bg-[#ca8a04]" />}
                        <span className="text-[10px] font-bold text-gray-400">{new Date(m.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <p className="mt-0.5 text-xs font-bold text-gray-600 truncate">{m.subject}</p>
                    <p className="text-xs text-gray-400 truncate">{m.body}</p>
                  </button>
                ))
              ) : (
                adminMessages.length === 0 ? <p className="p-5 text-sm font-bold text-gray-400">No messages to admin.</p> :
                adminMessages.map((m) => (
                  <button key={m.id} onClick={() => setSelectedAdminMsg(m)} className={`w-full p-4 text-left transition-all ${selectedAdminMsg?.id === m.id ? "bg-[#fef9c3]" : "bg-white hover:bg-gray-50"}`}>
                    <p className="text-sm font-black text-black truncate">{m.subject}</p>
                    <p className="mt-0.5 text-xs text-gray-400 truncate">{m.body}</p>
                    <span className="text-[10px] font-bold text-gray-400">{new Date(m.created_at).toLocaleDateString()}</span>
                    {m.reply_count > 0 && <span className="ml-2 rounded-full border-[2px] border-black bg-green-100 px-2 py-0.5 text-[10px] font-black text-green-800">{m.reply_count} reply</span>}
                  </button>
                ))
              )}
            </div>
          </aside>
          {/* Chat */}
          <section className="flex flex-1 flex-col">
            {selected && !selectedAdminMsg ? (
              <>
                <header className="border-b-[3px] border-black bg-black p-5 text-white">
                  <p className="text-xs font-black uppercase tracking-wider text-[#facc15]">{selected.student_name}</p>
                  <h3 className="mt-1 text-lg font-black">{selected.subject}</h3>
                </header>
                <div className="flex-1 space-y-4 overflow-y-auto bg-[#f3f1e8] p-6">
                  <div className="flex justify-end">
                    <div className="max-w-[75%] rounded-2xl border-[2px] border-black bg-[#ca8a04] px-5 py-3 text-sm font-bold text-black shadow-[4px_4px_0_0_#000]">
                      <p className="text-[10px] font-black uppercase tracking-wider text-black/60">{selected.student_name}</p>
                      <p className="mt-1">{selected.body}</p>
                    </div>
                  </div>
                  {replies.map((r) => (
                    <div key={r.id} className={`flex ${r.sender_type === "staff" ? "justify-start" : "justify-end"}`}>
                      <div className={`max-w-[75%] rounded-2xl border-[2px] border-black px-5 py-3 text-sm font-bold shadow-[4px_4px_0_0_#000] ${r.sender_type === "staff" ? "bg-white text-black" : "bg-[#ca8a04] text-black"}`}>
                        <p className="text-[10px] font-black uppercase tracking-wider text-gray-500">{r.sender_name || (r.sender_type === "staff" ? "You" : "Student")}</p>
                        <p className="mt-1">{r.content}</p>
                      </div>
                    </div>
                  ))}
                  <div ref={endRef} />
                </div>
                <div className="border-t-[3px] border-black bg-white px-4 py-3">
                  <div className="flex gap-3">
                    <input value={replyText} onChange={(e) => setReplyText(e.target.value)} placeholder="Type your reply…" className="min-w-0 flex-1 rounded-xl border-[2px] border-black px-4 py-2.5 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
                    <button onClick={sendReply} disabled={replying || !replyText.trim()} className="rounded-xl border-[2px] border-black bg-black px-5 py-2.5 text-sm font-black text-white shadow-[3px_3px_0_0_#000] active:shadow-none transition-all disabled:opacity-50">{replying ? "…" : "Reply"}</button>
                  </div>
                </div>
              </>
            ) : selectedAdminMsg ? (
              <>
                <header className="border-b-[3px] border-black bg-black p-5 text-white">
                  <p className="text-xs font-black uppercase tracking-wider text-[#facc15]">To: Admin</p>
                  <h3 className="mt-1 text-lg font-black">{selectedAdminMsg.subject}</h3>
                </header>
                <div className="flex-1 space-y-4 overflow-y-auto bg-[#f3f1e8] p-6">
                  <div className="flex justify-end">
                    <div className="max-w-[75%] rounded-2xl border-[2px] border-black bg-[#ca8a04] px-5 py-3 text-sm font-bold text-black shadow-[4px_4px_0_0_#000]">
                      <p className="text-[10px] font-black uppercase tracking-wider text-black/60">You (Advisor)</p>
                      <p className="mt-1">{selectedAdminMsg.body}</p>
                    </div>
                  </div>
                  {(selectedAdminMsg.replies || []).map((r) => (
                    <div key={r.id} className="flex justify-start">
                      <div className="max-w-[75%] rounded-2xl border-[2px] border-black bg-white px-5 py-3 text-sm font-bold text-black shadow-[4px_4px_0_0_#000]">
                        <p className="text-[10px] font-black uppercase tracking-wider text-gray-500">{r.sender_name || "Admin"}</p>
                        <p className="mt-1">{r.content}</p>
                      </div>
                    </div>
                  ))}
                  <div ref={endRef} />
                </div>
              </>
            ) : (
              <div className="flex flex-1 items-center justify-center p-10 text-center">
                <div>
                  <p className="text-4xl">💬</p>
                  <p className="mt-4 text-lg font-black text-black">Communications</p>
                  <p className="mt-2 text-sm font-bold text-gray-500">Switch between Student and Admin tabs to view messages.</p>
                </div>
              </div>
            )}
          </section>
        </section>
      </div>

      {/* Contact Admin Modal */}
      {showContact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4" onClick={() => setShowContact(false)}>
          <div className="w-full max-w-lg rounded-3xl border-[3px] border-black bg-white shadow-[12px_12px_0_0_#000]" onClick={(e) => e.stopPropagation()}>
            <div className="border-b-[3px] border-black bg-black p-5 text-white">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-black">Contact Admin / Support</h3>
                <button onClick={() => setShowContact(false)} className="grid h-8 w-8 place-items-center rounded-xl border-[2px] border-white text-sm font-black">✕</button>
              </div>
            </div>
            <form onSubmit={sendContact} className="p-5 space-y-4">
              {contactMsg && (
                <div className="rounded-2xl border-[2px] border-black bg-[#fef9c3] p-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">{contactMsg}</div>
              )}
              <div>
                <label className="text-xs font-black uppercase text-black">Subject</label>
                <input value={contactSubject} onChange={(e) => setContactSubject(e.target.value)} placeholder="e.g. Need admin approval" required
                  className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
              </div>
              <div>
                <label className="text-xs font-black uppercase text-black">Message</label>
                <textarea value={contactBody} onChange={(e) => setContactBody(e.target.value)} rows={4} placeholder="Describe your issue…" required
                  className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-sm font-bold text-black shadow-[3px_3px_0_0_#000] outline-none focus:bg-[#fef9c3]" />
              </div>
              <div className="flex justify-end gap-3">
                <button type="button" onClick={() => setShowContact(false)} className="rounded-xl border-[2px] border-black bg-white px-4 py-2 text-sm font-black text-black shadow-[3px_3px_0_0_#000]">Cancel</button>
                <button type="submit" disabled={contactSending} className="rounded-xl border-[2px] border-black bg-black px-4 py-2 text-sm font-black text-white shadow-[3px_3px_0_0_#000] disabled:opacity-50">{contactSending ? "Sending…" : "Send"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
