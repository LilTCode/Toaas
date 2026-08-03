import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  abstract_reasoning: "high",
  logical_reasoning: "high",
  theoretical_knowledge: "medium",
  quantitative_calculation: "medium",
  practical_application: "high",
};

const roleOptions = [
  { value: "student", label: "Student Dashboard", description: "Academic planning and recommendations" },
  { value: "administrator", label: "Administrator Dashboard", description: "Programme and course controls" },
  { value: "advisor", label: "Advisor Dashboard", description: "Student review and guidance" },
];

function gradeToGpa(grade) {
  const map = { A: 4.0, B: 3.0, C: 2.0, D: 1.0 };
  return map[grade] || 2.0;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [cognitiveProfile, setCognitiveProfile] = useState(null);
  const [courses, setCourses] = useState([]);
  const [transcriptEntries, setTranscriptEntries] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [assessment, setAssessment] = useState(() => {
    const saved = localStorage.getItem("toaas_assessment");
    return saved ? JSON.parse(saved) : initialAssessment;
  });
  const [transcriptForm, setTranscriptForm] = useState({ courseId: "", semester: "First", grade: "A", status: "passed" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeRole, setActiveRole] = useState("student");

  const loadDashboardData = async () => {
    try {
      const [profileResponse, cognitiveResponse, recommendationsResponse, courseResponse, transcriptResponse] = await Promise.all([
        api.get("accounts/profile/"),
        api.get("advisories/profile/"),
        api.get("advisories/recommendations/"),
        api.get("courses/course/"),
        api.get("courses/transcript/"),
      ]);

      setProfile(profileResponse.data);
      setActiveRole(profileResponse.data?.role || "student");
      setCognitiveProfile(cognitiveResponse.data);
      setRecommendations(recommendationsResponse.data || []);
      setCourses(courseResponse.data || []);
      setTranscriptEntries(transcriptResponse.data || []);
    } catch (error) {
      setMessage("Unable to load dashboard data yet. Please verify your account and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("toaas_access_token");
    if (!token) {
      navigate("/auth");
      return;
    }

    loadDashboardData();
  }, [navigate]);

  const handleAssessmentChange = (event) => {
    const { name, value } = event.target;
    setAssessment((current) => ({ ...current, [name]: value }));
  };

  const handleAssessmentSubmit = (event) => {
    event.preventDefault();
    localStorage.setItem("toaas_assessment", JSON.stringify(assessment));
    setMessage("Self-assessment saved for your next advisory review.");
  };

  const handleTranscriptSubmit = async (event) => {
    event.preventDefault();
    try {
      await api.post("courses/transcript/", {
        course_id: transcriptForm.courseId,
        semester: transcriptForm.semester,
        grade: transcriptForm.grade,
        status: transcriptForm.status,
        credit_points: gradeToGpa(transcriptForm.grade),
      });
      setMessage("Transcript update saved.");
      setTranscriptForm({ courseId: "", semester: "First", grade: "A", status: "passed" });
      await loadDashboardData();
    } catch (error) {
      setMessage("Please select a registered course before saving your transcript.");
    }
  };

  const handleGenerateRecommendations = async () => {
    try {
      setGenerating(true);
      const response = await api.post("advisories/recommendations/generate/");
      setRecommendations((current) => [response.data, ...current]);
      setMessage("Recommendation generated successfully.");
      await loadDashboardData();
    } catch (error) {
      setMessage("The recommendation engine could not be reached yet.");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadReport = () => {
    const report = [
      "TO-AAS Advisory Report",
      `Student: ${profile?.email || "student"}`,
      `Cognitive profile: ${JSON.stringify(cognitiveProfile || {})}`,
      `Assessment: ${JSON.stringify(assessment)}`,
      `Transcript entries: ${transcriptEntries.length}`,
      `Recommended courses: ${recommendations[0]?.selected_courses?.length || 0}`,
      recommendations[0]?.explanation || "No recommendation generated yet.",
    ].join("\n\n");

    const blob = new Blob([report], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "advisory-report.txt";
    link.click();
    URL.revokeObjectURL(url);
    setMessage("Advisory report downloaded.");
  };

  const gpa = useMemo(() => {
    if (!transcriptEntries.length) return "0.00";
    const total = transcriptEntries.reduce((sum, entry) => sum + (entry.credit_points || 0), 0);
    return (total / transcriptEntries.length).toFixed(2);
  }, [transcriptEntries]);

  const stats = [
    { label: "Recommended Courses", value: recommendations[0]?.selected_courses?.length || 0 },
    { label: "Transcript Entries", value: transcriptEntries.length },
    { label: "Estimated GPA", value: gpa },
  ];

  const actions = [
    "Upload your latest transcript",
    "Review course recommendations",
    "Complete your self-assessment",
    "Share this plan with your advisor",
  ];

  const studentView = (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-2xl">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Student dashboard</p>
            <h1 className="text-4xl font-semibold text-slate-900">Your academic advisory workspace</h1>
            <p className="max-w-2xl text-slate-600 sm:text-lg">
              Track your progress, build your cognitive profile, and request advisor-ready recommendations for the next semester.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              className="rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              onClick={handleGenerateRecommendations}
              type="button"
              disabled={generating}
            >
              {generating ? "Generating..." : "Request recommendations"}
            </button>
            <button
              className="rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              onClick={handleDownloadReport}
              type="button"
            >
              Save report
            </button>
          </div>
        </div>

        {message ? <p className="mt-4 rounded-2xl bg-slate-100 px-4 py-3 text-sm text-slate-700">{message}</p> : null}

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {stats.map((item) => (
            <div key={item.label} className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-6 shadow-sm">
              <p className="text-3xl font-semibold text-slate-900">{item.value}</p>
              <p className="mt-2 text-sm text-slate-600">{item.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6 rounded-[2rem] border border-slate-200 bg-slate-950 p-8 text-white shadow-2xl">
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-300">Advisory snapshot</p>
            <h2 className="text-3xl font-semibold">What to do next</h2>
            <p className="text-slate-300">
              Your academic plan is active. Complete the self-assessment, add transcript evidence, and generate recommendations from the engine.
            </p>
          </div>

          <div className="space-y-4">
            {actions.map((item) => (
              <div key={item} className="rounded-3xl bg-slate-900/80 p-4">
                <p className="text-sm text-slate-200">• {item}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">Academic profile</h2>
            <p className="mt-2 text-sm text-slate-600">
              {profile ? `Signed in as ${profile.email}` : "Loading profile..."}
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-sm text-slate-500">Current cognitive profile</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {cognitiveProfile ? (
                Object.entries(cognitiveProfile).filter(([key]) => key !== "updated_at").map(([key, value]) => (
                  <div key={key} className="rounded-2xl bg-white p-3 shadow-sm">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{key.replace(/_/g, " ")}</p>
                    <p className="mt-1 font-semibold text-slate-900">{value}%</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-600">Generate recommendations to populate this profile.</p>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Self-assessment questionnaire</h2>
          <p className="mt-2 text-sm text-slate-600">These answers guide the advisory engine so it can tailor recommendations to your learning style.</p>
          <form className="mt-6 space-y-4" onSubmit={handleAssessmentSubmit}>
            {assessmentQuestions.map((item) => (
              <label key={item.key} className="block text-sm font-medium text-slate-700">
                {item.label}
                <select
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none"
                  name={item.key}
                  value={assessment[item.key]}
                  onChange={handleAssessmentChange}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>
            ))}
            <button className="rounded-2xl bg-sky-600 px-4 py-3 text-sm font-semibold text-white" type="submit">
              Save self-assessment
            </button>
          </form>
        </div>

        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Manual transcript entry</h2>
          <p className="mt-2 text-sm text-slate-600">Add a result for a course to build a richer academic profile.</p>
          <form className="mt-6 space-y-4" onSubmit={handleTranscriptSubmit}>
            <label className="block text-sm font-medium text-slate-700">
              Course
              <select
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none"
                value={transcriptForm.courseId}
                onChange={(event) => setTranscriptForm((current) => ({ ...current, courseId: event.target.value }))}
                required
              >
                <option value="">Select a course</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>{course.code} - {course.title}</option>
                ))}
              </select>
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                Semester
                <select
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none"
                  value={transcriptForm.semester}
                  onChange={(event) => setTranscriptForm((current) => ({ ...current, semester: event.target.value }))}
                >
                  <option value="First">First</option>
                  <option value="Second">Second</option>
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Grade
                <select
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none"
                  value={transcriptForm.grade}
                  onChange={(event) => setTranscriptForm((current) => ({ ...current, grade: event.target.value }))}
                >
                  <option value="A">A</option>
                  <option value="B">B</option>
                  <option value="C">C</option>
                  <option value="D">D</option>
                </select>
              </label>
            </div>
            <button className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white" type="submit">
              Save transcript entry
            </button>
          </form>
        </div>
      </section>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">Recommended courses</h2>
            <p className="mt-2 text-sm text-slate-600">The engine ranks courses against your current cognitive profile and transcript evidence.</p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-700">{recommendations.length ? `${recommendations[0].selected_courses.length} matches` : "Waiting for generation"}</span>
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          {!recommendations.length && !loading ? (
            <div className="rounded-3xl border border-dashed border-slate-200 p-6 text-sm text-slate-600">
              No recommendations yet. Click the request button to generate your first advisory plan.
            </div>
          ) : (
            recommendations.map((recommendation) => (
              <div key={recommendation.id} className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{recommendation.selected_courses?.[0]?.code || "Course"}</p>
                    <p className="text-sm text-slate-600">{recommendation.selected_courses?.[0]?.title || "No course title"}</p>
                  </div>
                  <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">Recommended</span>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-600">{recommendation.explanation}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {recommendation.selected_courses?.slice(0, 3).map((course) => (
                    <span key={course.id} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">{course.code}</span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );

  const adminView = (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-2xl">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Administrator workspace</p>
        <h1 className="mt-3 text-4xl font-semibold text-slate-900">Programme and course management</h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          Configure rules, manage departments, update cognitive demand values, and monitor the quality of course recommendations.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            { label: "Departments", value: "6" },
            { label: "Active Courses", value: "24" },
            { label: "Student Records", value: "184" },
          ].map((item) => (
            <div key={item.label} className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
              <p className="text-3xl font-semibold text-slate-900">{item.value}</p>
              <p className="mt-2 text-sm text-slate-600">{item.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Recommendation controls</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>• Configure recommendation rules and departmental regulations.</li>
            <li>• Maintain prerequisite relationships across course levels.</li>
            <li>• Monitor recommendation accuracy and update demand values.</li>
          </ul>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">System oversight</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>• Review student activity and generated recommendations.</li>
            <li>• Monitor chatbot activity and advisory logs.</li>
            <li>• Keep recommendation database and reports up to date.</li>
          </ul>
        </div>
      </section>
    </div>
  );

  const advisorView = (
    <div className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-2xl">
        <p className="text-sm uppercase tracking-[0.3em] text-sky-600">Academic advisor workspace</p>
        <h1 className="mt-3 text-4xl font-semibold text-slate-900">Review and guide student decisions</h1>
        <p className="mt-3 max-w-2xl text-slate-600">
          Examine cognitive profiles, review transcript evidence, and approve or adjust course recommendations with professional guidance.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {[
            { label: "Assigned Students", value: "12" },
            { label: "Pending Reviews", value: "4" },
            { label: "Advice Notes", value: "18" },
          ].map((item) => (
            <div key={item.label} className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
              <p className="text-3xl font-semibold text-slate-900">{item.value}</p>
              <p className="mt-2 text-sm text-slate-600">{item.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Student review queue</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>• Review recommendations against academic performance.</li>
            <li>• Approve or adjust course selections for the upcoming semester.</li>
            <li>• Add advisor notes and send guidance to students.</li>
          </ul>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Collaboration tools</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>• View AI conversations and recommendation explanations.</li>
            <li>• Continue advisory conversations with students directly.</li>
            <li>• Monitor the effectiveness of recommendations over time.</li>
          </ul>
        </div>
      </section>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-100 p-4 lg:p-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 lg:flex-row">
        <aside className="w-full rounded-[2rem] border border-slate-200 bg-slate-950 p-6 text-white shadow-2xl lg:w-72">
          <div className="space-y-2">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-300">TO-AAS</p>
            <h2 className="text-2xl font-semibold">Academic portal</h2>
            <p className="text-sm text-slate-400">{profile?.email || "Student account"}</p>
          </div>

          <div className="mt-8 space-y-3">
            {roleOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setActiveRole(option.value)}
                className={`w-full rounded-[1.25rem] border px-4 py-4 text-left transition ${activeRole === option.value ? "border-sky-400 bg-slate-800" : "border-slate-800 bg-slate-900/70 hover:border-slate-600"}`}
              >
                <p className="text-sm font-semibold text-white">{option.label}</p>
                <p className="mt-1 text-sm text-slate-400">{option.description}</p>
              </button>
            ))}
          </div>

          <div className="mt-8 rounded-[1.5rem] border border-slate-800 bg-slate-900/80 p-4 text-sm text-slate-300">
            <p className="font-semibold text-white">Role-based navigation</p>
            <p className="mt-2">Switch between student, administrator, and advisor views for a complete academic system experience.</p>
          </div>
        </aside>

        <main className="flex-1">
          {loading ? <div className="rounded-[2rem] border border-slate-200 bg-white p-8 text-slate-600 shadow-sm">Loading dashboard...</div> : null}
          {!loading && activeRole === "student" ? studentView : null}
          {!loading && activeRole === "administrator" ? adminView : null}
          {!loading && activeRole === "advisor" ? advisorView : null}
        </main>
      </div>

      <AssistantPopup />
    </div>
  );
}
