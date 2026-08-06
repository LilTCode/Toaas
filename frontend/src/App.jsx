import { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import HomePage from "./pages/HomePage";
import AuthPage from "./pages/AuthPage";
import StudentDashboardPage from "./pages/StudentDashboardPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import AdvisorDashboardPage from "./pages/AdvisorDashboardPage";
import AdvisorStudentDetailPage from "./pages/AdvisorStudentDetailPage";
import StudentOverviewPage from "./pages/StudentOverviewPage";
import StudentProfilePage from "./pages/StudentProfilePage";
import StudentRecommendationsPage from "./pages/StudentRecommendationsPage";
import StudentChatPage from "./pages/StudentChatPage";
import StudentMessagesPage from "./pages/StudentMessagesPage";
import StudentTranscriptPage from "./pages/StudentTranscriptPage";
import StudentLayout from "./components/StudentLayout";
import ErrorBoundary from "./components/ErrorBoundary";

function AppContent() {
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (location.hash) {
      const element = document.getElementById(location.hash.replace("#", ""));
      if (element) {
        setTimeout(() => element.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
      }
    } else if (location.pathname === "/") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [location]);

  const isStudentWorkspace = location.pathname.startsWith("/dashboard/student");
  const isAuthPage = location.pathname.startsWith("/auth");
  const isDashboardPage = location.pathname.startsWith("/dashboard");

  // For auth and student workspace we use the page's own background
  // For admin/advisor we use their own background too
  const useCustomBg = isAuthPage || isDashboardPage;

  return (
    <div className={`min-h-screen ${useCustomBg ? "" : "bg-slate-950 text-slate-100"}`}>
      {!useCustomBg && (
        <header className={`sticky top-0 z-50 transition-all duration-500 ${scrolled ? "border-b border-slate-800/60 bg-slate-950/95 backdrop-blur-2xl shadow-2xl" : "bg-slate-950/40"}`}>
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.4em] text-cyan-300/80">TO-AAS</p>
              <p className="text-xs text-slate-400">Academic Advisory System</p>
            </div>
            <nav className="flex flex-wrap items-center gap-3 text-sm text-slate-200">
              <Link className="transition hover:text-white" to={{ pathname: "/", hash: "#home" }}>Home</Link>
              <Link className="transition hover:text-white" to={{ pathname: "/", hash: "#features" }}>Features</Link>
              <Link className="transition hover:text-white" to={{ pathname: "/", hash: "#workflow" }}>How It Works</Link>
              <Link className="transition hover:text-white" to={{ pathname: "/", hash: "#contact" }}>Contact</Link>
              <Link className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-slate-100 transition hover:border-cyan-300 hover:bg-cyan-400/10" to="/auth">Sign In</Link>
            </nav>
          </div>
        </header>
      )}
      <main className={useCustomBg ? "" : "overflow-hidden"}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/dashboard/student" element={<Navigate to="/dashboard/student/overview" replace />} />
          <Route path="/dashboard/student/overview" element={<StudentLayout><StudentOverviewPage /></StudentLayout>} />
          <Route path="/dashboard/student/profile" element={<StudentLayout><StudentProfilePage /></StudentLayout>} />
          <Route path="/dashboard/student/recommendations" element={<StudentLayout><StudentRecommendationsPage /></StudentLayout>} />
          <Route path="/dashboard/student/chat" element={<StudentLayout><ErrorBoundary title="Chatbot temporarily unavailable" message="The AI assistant could not be loaded right now. Your other dashboard pages are unaffected."><StudentChatPage /></ErrorBoundary></StudentLayout>} />
          <Route path="/dashboard/student/messages" element={<StudentLayout><StudentMessagesPage /></StudentLayout>} />
          <Route path="/dashboard/student/transcript" element={<StudentLayout><StudentTranscriptPage /></StudentLayout>} />
          <Route path="/dashboard/admin" element={<AdminDashboardPage />} />
          <Route path="/dashboard/advisor" element={<AdvisorDashboardPage />} />
          <Route path="/dashboard/advisor/student/:studentId" element={<AdvisorStudentDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
