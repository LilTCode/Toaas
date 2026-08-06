import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function parseError(error) {
  const d = error.response?.data;
  if (!d) return error.message || "Something went wrong.";
  if (typeof d === "string") return d;
  if (d.detail) return d.detail;
  return Object.entries(d).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`).join(" | ");
}

export default function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    email: "", password: "", username: "", role: "student",
    first_name: "", last_name: "", programme: "software_engineering",
    current_level: 100, current_semester: 1,
  });
  const [otp, setOtp] = useState("");
  const [pendingOtp, setPendingOtp] = useState(false);
  const [msg, setMsg] = useState("");

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const doLogin = async (email, password) => {
    const r = await api.post("accounts/login/", { email, password });
    localStorage.setItem("toaas_access_token", r.data.access);
    localStorage.setItem("toaas_user", JSON.stringify(r.data.user));
    const role = r.data.user?.role;
    if (role === "administrator") navigate("/dashboard/admin");
    else if (role === "advisor") navigate("/dashboard/advisor");
    else navigate("/dashboard/student");
  };

  const demoLogin = async () => {
    setMsg("Signing in with demo account…");
    try { await doLogin("student@demo.edu", "demo1234"); }
    catch (e) { setMsg(parseError(e)); }
  };

  const submit = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      if (mode === "register") {
        if (pendingOtp) {
          await api.post("accounts/verify-otp/", { email: form.email, otp_code: otp });
          await doLogin(form.email, form.password);
          return;
        }
        await api.post("accounts/register/", form);
        setPendingOtp(true);
        setMsg("✅ Registered! Enter the OTP sent to your email.");
      } else {
        await doLogin(form.email, form.password);
      }
    } catch (err) {
      setMsg(parseError(err));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f3f1e8] p-4 sm:p-8">
      <form onSubmit={submit} className="w-full max-w-md space-y-5 rounded-3xl border-[3px] border-black bg-white p-7 shadow-[8px_8px_0_0_#000]">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-black">
                {pendingOtp ? "Verify OTP" : mode === "register" ? "Create account" : "Sign in"}
              </h2>
              <button type="button" onClick={() => { setMode(mode === "register" ? "login" : "register"); setPendingOtp(false); setOtp(""); setMsg(""); }}
                className="rounded-xl border-[2px] border-black bg-white px-4 py-2 text-xs font-black text-black shadow-[3px_3px_0_0_#000] active:shadow-none active:translate-x-[3px] active:translate-y-[3px] transition-all">
                {mode === "register" ? "← Login" : "Register →"}
              </button>
            </div>

            {mode === "register" && !pendingOtp && (
              <>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Input label="First name" name="first_name" value={form.first_name} onChange={change} required />
                  <Input label="Last name" name="last_name" value={form.last_name} onChange={change} required />
                </div>
                <Input label="Matric Number" name="username" placeholder="e.g. 125/22/1/0072" value={form.username} onChange={change} required />
                {form.role === "student" && (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Select label="Programme" name="programme" value={form.programme} onChange={change} options={[["computer_science", "B.Sc. Computer Science"], ["software_engineering", "B.Sc. Software Engineering"], ["cyber_security", "B.Sc. Cyber Security"]]} />
                    <Select label="Level" name="current_level" value={form.current_level} onChange={change} options={[[100, "100 Level"], [200, "200 Level"], [300, "300 Level"], [400, "400 Level"]]} />
                  </div>
                )}
              </>
            )}

            {pendingOtp && (
              <Input label="OTP Code (6 digits)" placeholder="000000" value={otp} onChange={(e) => setOtp(e.target.value)} required />
            )}

            <Input label="Email address" name="email" type="email" placeholder="you@university.edu" value={form.email} onChange={change} required />
            <Input label="Password" name="password" type="password" placeholder="Min 8 characters" value={form.password} onChange={change} required />

            {mode === "register" && !pendingOtp && (
              <Select label="Account role" name="role" value={form.role} onChange={change} options={[["student", "Student"], ["advisor", "Academic Advisor"], ["administrator", "Administrator"]]} />
            )}

            <button type="submit" className="w-full rounded-2xl border-[3px] border-black bg-[#ca8a04] py-4 text-base font-black text-black shadow-[6px_6px_0_0_#000] active:shadow-none active:translate-x-[6px] active:translate-y-[6px] transition-all hover:bg-[#eab308]">
              {pendingOtp ? "Verify & Continue" : mode === "register" ? "Register" : "Login"}
            </button>

            {mode !== "register" && (
              <button type="button" onClick={demoLogin} className="w-full rounded-2xl border-[3px] border-black bg-white py-4 text-base font-black text-black shadow-[6px_6px_0_0_#000] active:shadow-none active:translate-x-[6px] active:translate-y-[6px] transition-all hover:bg-gray-100">
                🎮 Demo Student Login
              </button>
            )}

            {msg && (
              <div className="rounded-2xl border-[2px] border-black bg-[#fef9c3] p-4 text-sm font-bold text-black shadow-[3px_3px_0_0_#000]">
                {msg}
              </div>
            )}
      </form>
    </div>
  );
}

/* ── Reusable Brutalist inputs ── */
function Input({ label, name, value, onChange, placeholder, type = "text", required }) {
  return (
    <label className="block text-sm font-black text-black uppercase">
      {label}
      <input
        name={name} type={type} value={value} onChange={onChange} placeholder={placeholder} required={required}
        className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-base font-bold text-black shadow-[4px_4px_0_0_#000] outline-none focus:bg-[#fef9c3] transition-all placeholder:font-normal placeholder:text-gray-400"
      />
    </label>
  );
}

function Select({ label, name, value, onChange, options }) {
  return (
    <label className="block text-sm font-black text-black uppercase">
      {label}
      <select
        name={name} value={value} onChange={onChange}
        className="mt-1.5 block w-full rounded-xl border-[2px] border-black bg-white px-4 py-3 text-base font-bold text-black shadow-[4px_4px_0_0_#000] outline-none focus:bg-[#fef9c3] transition-all">
        {options.map(([val, label]) => <option key={val} value={val}>{label}</option>)}
      </select>
    </label>
  );
}
