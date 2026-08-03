import { useMemo } from "react";
import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import CountUp from "react-countup";

const statCards = [
  { label: "Courses Analysed", value: 42 },
  { label: "Cognitive Dimensions", value: 5 },
  { label: "Active Students", value: 340 },
];

const features = [
  { title: "Transcript-Driven Analysis", desc: "Upload your results and our greedy algorithm builds a cognitive profile based on each course's cognitive demand weights.", icon: "📊" },
  { title: "Smart Course Recommendations", desc: "Courses are ranked by cognitive profile compatibility, carryover priority, prerequisite completion, and unit load policy.", icon: "🎯" },
  { title: "AI Academic Assistant", desc: "Get instant explanations of your recommendations, prerequisites, and semester plan via the built-in chatbot.", icon: "🤖" },
  { title: "Advisor Collaboration", desc: "Send messages to your advisor, receive threaded replies, and keep your academic plan in sync.", icon: "💬" },
  { title: "Cognitive Profile Visualisation", desc: "See your strengths in logical reasoning, abstract reasoning, quantitative ability, and more.", icon: "🧠" },
  { title: "PDF Report Generation", desc: "Download a formatted advisory report with your recommended courses, cognitive profile, and compatibility scores.", icon: "📄" },
];

const workflow = [
  { title: "Register", detail: "Create account with your matric number and institutional email. Verify via OTP sent to your inbox." },
  { title: "Add Results", detail: "Enter your grades manually or upload your transcript. Courses auto-populate based on your programme, level, and semester." },
  { title: "Get Profiled", detail: "The greedy algorithm analyses each passed course against its cognitive demand values to build your 5-dimension learning profile." },
  { title: "Receive Recommendations", detail: "Courses are scored by profile-fit score, prioritising carryovers and prerequisites within the 15–24 unit policy." },
  { title: "Review & Collaborate", detail: "Chat with the AI assistant about your plan, then message your advisor for human review and approval." },
  { title: "Enrol Confidently", detail: "Accept your recommended plan, download the advisory report, and register with the confidence of data-backed decisions." },
];

export default function HomePage() {
  const { scrollYProgress } = useScroll();
  const heroX = useTransform(scrollYProgress, [0, 0.4], [0, -15]);
  const heroY = useTransform(scrollYProgress, [0, 0.4], [0, 15]);

  const fadeUp = useMemo(() => ({ hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0 } }), []);

  return (
    <div id="home" className="relative overflow-hidden bg-slate-950 text-slate-100">
      {/* Glow blobs */}
      <div className="pointer-events-none absolute inset-0 opacity-60">
        <div className="absolute -left-20 top-24 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute right-0 top-1/3 h-80 w-80 rounded-full bg-emerald-400/10 blur-3xl" />
        <div className="absolute left-1/3 bottom-0 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        {/* HERO */}
        <motion.div initial={{ opacity: 0, y: 36 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9 }} className="mb-12 grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-8">
            <motion.span initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.15 }} className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-slate-900/60 px-4 py-2 text-sm text-cyan-200 shadow-lg shadow-cyan-500/10 backdrop-blur">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 shadow-[0_0_20px_rgba(56,189,248,0.5)]" />
              FYP · Academic Advisory System
            </motion.span>
            <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, delay: 0.25 }} className="space-y-6">
              <h1 className="max-w-3xl text-5xl font-semibold leading-tight tracking-tight text-white sm:text-6xl">
                Turn your transcript into a <span className="bg-gradient-to-r from-cyan-300 via-emerald-300 to-sky-400 bg-clip-text text-transparent">smart course plan</span> with cognitive profiling.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-slate-300">
                TO-AAS analyses your academic results using a greedy matching algorithm, builds your cognitive learning profile across five dimensions, and recommends the optimal course selection — all linked to your programme, level, and semester.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/auth" className="group inline-flex items-center justify-center rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 px-7 py-3 text-sm font-semibold text-slate-950 shadow-[0_20px_70px_rgba(16,185,129,0.18)] transition duration-300 hover:-translate-y-0.5">Create Student Account</Link>
                <Link to="/auth" className="inline-flex items-center justify-center rounded-full border border-cyan-500/30 bg-slate-900/80 px-7 py-3 text-sm font-semibold text-slate-100 transition duration-300 hover:border-cyan-300 hover:bg-slate-800">Sign In</Link>
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 32 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, delay: 0.35 }} className="grid gap-4 sm:grid-cols-3">
              {statCards.map((s) => (
                <div key={s.label} className="rounded-[1.75rem] border border-white/10 bg-slate-950/80 p-5 shadow-lg backdrop-blur-xl">
                  <p className="text-sm uppercase tracking-[0.32em] text-slate-400">{s.label}</p>
                  <div className="mt-4 flex items-end gap-3">
                    <span className="text-4xl font-semibold text-white"><CountUp end={s.value} duration={1.8} enableScrollSpy redraw={true} /></span>
                    <span className="text-sm text-slate-500">+</span>
                  </div>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Right panel - system architecture preview */}
          <motion.div style={{ x: heroX, y: heroY }} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1.1 }} className="relative overflow-hidden rounded-[2.5rem] border border-white/10 bg-slate-950/60 p-6 shadow-[0_40px_120px_rgba(15,23,42,0.55)] backdrop-blur-xl">
            <div className="grid gap-5">
              <div className="rounded-[2rem] border border-white/10 bg-slate-900/95 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.35em] text-cyan-300/70">System Pipeline</p>
                    <p className="mt-2 text-lg font-semibold text-white">Greedy Algorithm Flow</p>
                  </div>
                  <div className="rounded-full bg-emerald-400/10 px-3 py-1 text-xs uppercase tracking-[0.3em] text-emerald-300">v1.0</div>
                </div>
                <div className="mt-5 space-y-3">
                  <div className="flex items-center gap-3 rounded-2xl border border-cyan-500/20 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-800 text-xs font-bold text-cyan-300">1</span>
                    <span>Transcript entries → Weighted cognitive scores</span>
                  </div>
                  <div className="flex items-center gap-3 rounded-2xl border border-cyan-500/20 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-800 text-xs font-bold text-cyan-300">2</span>
                    <span>Course demand vectors → Profile-fit ranking</span>
                  </div>
                  <div className="flex items-center gap-3 rounded-2xl border border-cyan-500/20 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-800 text-xs font-bold text-cyan-300">3</span>
                    <span>Carryover priority + 15–24 unit constraint</span>
                  </div>
                  <div className="flex items-center gap-3 rounded-2xl border border-cyan-500/20 bg-slate-950/90 px-4 py-3 text-sm text-slate-300">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-800 text-xs font-bold text-cyan-300">4</span>
                    <span>Compatibility score output → Recommended plan</span>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-[2rem] border border-white/10 bg-slate-900/90 p-4 text-center">
                  <p className="text-2xl font-bold text-cyan-300">5</p>
                  <p className="mt-1 text-xs text-slate-400">Dimensions</p>
                </div>
                <div className="rounded-[2rem] border border-white/10 bg-slate-900/90 p-4 text-center">
                  <p className="text-2xl font-bold text-emerald-300">15–24</p>
                  <p className="mt-1 text-xs text-slate-400">Unit Policy</p>
                </div>
                <div className="rounded-[2rem] border border-white/10 bg-slate-900/90 p-4 text-center">
                  <p className="text-2xl font-bold text-sky-300">OTP</p>
                  <p className="mt-1 text-xs text-slate-400">Email Verified</p>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* FEATURES */}
        <motion.section id="features" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }} variants={fadeUp} transition={{ duration: 0.8 }} className="mb-20 rounded-[3rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_40px_120px_rgba(15,23,42,0.5)] backdrop-blur-xl">
          <div className="grid gap-10 lg:grid-cols-[0.6fr_1.4fr]">
            <div className="space-y-6">
              <p className="text-sm uppercase tracking-[0.32em] text-cyan-300/70">Core features</p>
              <h2 className="text-4xl font-semibold text-white">What TO-AAS does for you.</h2>
              <p className="max-w-xl text-slate-400">Every feature is built around a single goal: helping you make data-informed course decisions with advisor oversight.</p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {features.map((f) => (
                <motion.div key={f.title} whileHover={{ y: -8, scale: 1.01 }} transition={{ type: "spring", stiffness: 220, damping: 18 }} className="group rounded-[2rem] border border-white/10 bg-slate-900/90 p-6 shadow-[0_20px_80px_rgba(15,23,42,0.35)] backdrop-blur-xl">
                  <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-cyan-400/10 text-2xl">{f.icon}</div>
                  <h3 className="mt-5 text-xl font-semibold text-white">{f.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{f.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.section>

        {/* WORKFLOW */}
        <motion.section id="workflow" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }} variants={fadeUp} transition={{ duration: 0.8 }} className="mb-20">
          <div className="rounded-[3rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_40px_120px_rgba(15,23,42,0.45)] backdrop-blur-xl">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.32em] text-cyan-300/70">Workflow</p>
                <h2 className="text-4xl font-semibold text-white">From registration to enrolment.</h2>
              </div>
              <div className="rounded-3xl border border-cyan-500/10 bg-slate-900/80 px-5 py-4 text-sm text-slate-300">
                <p className="font-semibold text-white">6-step process</p>
                <p className="mt-1">Data-driven decisions at every stage.</p>
              </div>
            </div>
            <div className="mt-10 overflow-hidden rounded-[2.5rem] border border-white/10 bg-slate-900/70 p-6 shadow-[0_30px_90px_rgba(15,23,42,0.35)]">
              <div className="relative">
                <div className="absolute left-0 top-6 h-1 w-4/5 rounded-full bg-gradient-to-r from-cyan-400 via-emerald-400 to-sky-400 opacity-30" />
                <div className="flex gap-4 overflow-x-auto pb-4">
                  {workflow.map((step, i) => (
                    <motion.div key={step.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.6, delay: i * 0.08 }} className="min-w-[16rem] rounded-[2rem] border border-white/10 bg-slate-950/95 p-6 shadow-lg">
                      <div className="flex h-12 w-12 items-center justify-center rounded-3xl border border-cyan-400/20 bg-slate-900/90 text-xl text-cyan-300">{i + 1}</div>
                      <h3 className="mt-4 text-xl font-semibold text-white">{step.title}</h3>
                      <p className="mt-3 text-sm leading-6 text-slate-400">{step.detail}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.section>

        {/* CONTACT */}
        <motion.section id="contact" initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.2 }} variants={fadeUp} transition={{ duration: 0.8 }} className="mb-24 rounded-[3rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_40px_120px_rgba(15,23,42,0.45)] backdrop-blur-xl">
          <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
            <div className="space-y-6">
              <p className="text-sm uppercase tracking-[0.32em] text-cyan-300/70">Get started</p>
              <h2 className="text-4xl font-semibold text-white">Ready to plan smarter?</h2>
              <p className="max-w-xl text-slate-400">
                TO-AAS is a Final Year Project demonstration. Register with your matric number and institutional email, add your results, and receive a data-backed course recommendation.
              </p>
              <Link to="/auth" className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg">Create your account →</Link>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-[2rem] border border-white/10 bg-slate-900/90 p-6 text-center">
                <p className="text-sm uppercase tracking-[0.32em] text-slate-500">Register</p>
                <p className="mt-4 text-2xl font-bold text-white">1 min</p>
                <p className="mt-2 text-xs text-slate-400">With OTP verification</p>
              </div>
              <div className="rounded-[2rem] border border-white/10 bg-slate-900/90 p-6 text-center">
                <p className="text-sm uppercase tracking-[0.32em] text-slate-500">Analyse</p>
                <p className="mt-4 text-2xl font-bold text-white">Instant</p>
                <p className="mt-2 text-xs text-slate-400">Greedy algorithm</p>
              </div>
              <div className="rounded-[2rem] border border-white/10 bg-slate-900/90 p-6 text-center">
                <p className="text-sm uppercase tracking-[0.32em] text-slate-500">Support</p>
                <p className="mt-4 text-2xl font-bold text-white">AI + Advisor</p>
                <p className="mt-2 text-xs text-slate-400">Dual-layer guidance</p>
              </div>
            </div>
          </div>
        </motion.section>
      </div>
    </div>
  );
}
