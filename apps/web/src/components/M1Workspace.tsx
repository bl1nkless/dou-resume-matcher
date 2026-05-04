"use client";

import { BrainCircuit, BriefcaseBusiness, FileText, Gauge, KeyRound, LogIn } from "lucide-react";
import { useEffect, useState } from "react";

import {
  AnalysisReportResponse,
  createAnalysis,
  createCandidateProfile,
  createJobFromText,
  createResume,
  login,
  register,
  submitAnalysisFeedback
} from "@/lib/api";

type Notice = { kind: "idle" | "success" | "error"; text: string };

const sampleResume =
  "Junior Python Backend Developer. Built FastAPI REST API with PostgreSQL, SQLAlchemy, Docker basics and pytest. Looking for backend roles with API and database work.";

const sampleVacancy =
  "Junior Python Developer\nRequirements: Python, Django or FastAPI, REST API, PostgreSQL, Git, English Intermediate. Responsibilities: develop backend services, write tests, work with database models.";

export function M1Workspace() {
  const [email, setEmail] = useState("demo@resumehunt.local");
  const [password, setPassword] = useState("local-demo-password");
  const [token, setToken] = useState("");
  const [resumeText, setResumeText] = useState(sampleResume);
  const [vacancyText, setVacancyText] = useState(sampleVacancy);
  const [resumeDocumentId, setResumeDocumentId] = useState("");
  const [candidateProfileId, setCandidateProfileId] = useState("");
  const [jobId, setJobId] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisReportResponse | null>(null);
  const [notice, setNotice] = useState<Notice>({ kind: "idle", text: "Ready for M1 API calls." });

  useEffect(() => {
    setToken(window.localStorage.getItem("resume_hunt_token") ?? "");
  }, []);

  async function authenticate(mode: "register" | "login") {
    setNotice({ kind: "idle", text: mode === "register" ? "Creating account..." : "Logging in..." });
    try {
      const response = mode === "register" ? await register(email, password) : await login(email, password);
      window.localStorage.setItem("resume_hunt_token", response.access_token);
      setToken(response.access_token);
      setNotice({ kind: "success", text: "Token saved locally for this browser session." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Auth failed" });
    }
  }

  async function submitResume() {
    if (!token) {
      setNotice({ kind: "error", text: "Log in first, then submit CV text." });
      return;
    }
    try {
      const document = await createResume(token, resumeText);
      const profile = await createCandidateProfile(token, document.id, "Junior Python Backend Developer");
      setResumeDocumentId(document.id);
      setCandidateProfileId(profile.id);
      setNotice({
        kind: "success",
        text: `CV profile ready: ${profile.estimated_seniority ?? "unknown"} (${document.language ?? "unknown"})`
      });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Resume save failed" });
    }
  }

  async function submitVacancy() {
    if (!token) {
      setNotice({ kind: "error", text: "Log in first, then submit vacancy text." });
      return;
    }
    try {
      const job = await createJobFromText(token, vacancyText);
      setJobId(job.id);
      setNotice({ kind: "success", text: `Vacancy parsed: ${job.title}` });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Vacancy save failed" });
    }
  }

  async function runAnalysis() {
    if (!token) {
      setNotice({ kind: "error", text: "Log in first, then run analysis." });
      return;
    }
    if (!candidateProfileId || !jobId) {
      setNotice({ kind: "error", text: "Save a CV profile and vacancy before analysis." });
      return;
    }
    try {
      setNotice({ kind: "idle", text: "Running rules-baseline analysis..." });
      const report = await createAnalysis(token, candidateProfileId, jobId);
      setAnalysis(report);
      setNotice({ kind: "success", text: `Analysis complete: ${formatVerdict(report.verdict)}` });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Analysis failed" });
    }
  }

  async function submitFeedback(eventValue: Record<string, unknown>) {
    if (!token || !analysis) {
      return;
    }
    try {
      await submitAnalysisFeedback(token, analysis.id, "verdict_rating", eventValue);
      setNotice({ kind: "success", text: "Feedback saved for model evaluation." });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Feedback save failed" });
    }
  }

  return (
    <section className="mt-6 rounded-lg border border-ink/10 bg-white shadow-panel">
      <div className="grid gap-0 divide-y divide-ink/10 xl:grid-cols-[0.85fr_1.15fr] xl:divide-x xl:divide-y-0">
        <form
          className="p-5"
          onSubmit={(event) => {
            event.preventDefault();
            void authenticate("login");
          }}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-cloud text-moss">
              <KeyRound size={18} strokeWidth={2.2} />
            </div>
            <div>
              <h2 className="text-lg font-semibold">M1 account</h2>
              <p className="text-sm text-ink/58">JWT auth for user-scoped CV and vacancy records.</p>
            </div>
          </div>

          <label className="mt-5 block text-sm font-semibold text-ink/70" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="mt-2 w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm outline-none transition focus:border-moss"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label className="mt-4 block text-sm font-semibold text-ink/70" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="mt-2 w-full rounded-md border border-ink/15 bg-paper px-3 py-2 text-sm outline-none transition focus:border-moss"
            value={password}
            type="password"
            onChange={(event) => setPassword(event.target.value)}
          />

          <div className="mt-5 grid grid-cols-2 gap-3">
            <button
              className="inline-flex items-center justify-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-semibold text-paper transition hover:bg-moss"
              type="button"
              onClick={() => void authenticate("register")}
            >
              <KeyRound size={16} />
              Register
            </button>
            <button
              className="inline-flex items-center justify-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink transition hover:bg-cloud"
              type="submit"
            >
              <LogIn size={16} />
              Login
            </button>
          </div>

          <div
            className={`mt-5 rounded-md px-3 py-2 text-sm ${
              notice.kind === "success"
                ? "bg-moss/10 text-moss"
                : notice.kind === "error"
                  ? "bg-clay/10 text-clay"
                  : "bg-cloud text-ink/65"
            }`}
          >
            {notice.text}
          </div>
        </form>

        <div className="grid gap-0 divide-y divide-ink/10 lg:grid-cols-2 lg:divide-x lg:divide-y-0">
          <IngestionPanel
            icon={FileText}
            title="CV paste"
            value={resumeText}
            onChange={setResumeText}
            onSubmit={submitResume}
            buttonLabel="Save CV"
          />
          <IngestionPanel
            icon={BriefcaseBusiness}
            title="Vacancy paste"
            value={vacancyText}
            onChange={setVacancyText}
            onSubmit={submitVacancy}
            buttonLabel="Save vacancy"
          />
        </div>
      </div>

      <div className="flex items-center gap-3 border-t border-ink/10 px-5 py-3 text-sm text-ink/58">
        <BrainCircuit size={17} className="text-clay" />
        M2 rules-baseline extraction now stores skills, gaps, scores, and grounded recommendations.
      </div>

      <div className="grid gap-0 border-t border-ink/10 lg:grid-cols-[0.85fr_1.15fr] lg:divide-x lg:divide-ink/10">
        <div className="p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-cloud text-moss">
              <Gauge size={18} strokeWidth={2.2} />
            </div>
            <div>
              <h3 className="text-base font-semibold">Fit analysis</h3>
              <p className="text-sm text-ink/58">Runs deterministic evidence mapping before LLM recommendations.</p>
            </div>
          </div>
          <div className="mt-4 grid gap-2 text-xs text-ink/58">
            <StateRow label="Resume document" value={resumeDocumentId} />
            <StateRow label="Candidate profile" value={candidateProfileId} />
            <StateRow label="Vacancy" value={jobId} />
          </div>
          <button
            className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-semibold text-paper transition hover:bg-moss"
            type="button"
            onClick={() => void runAnalysis()}
          >
            <Gauge size={16} />
            Run analysis
          </button>
        </div>

        <AnalysisPanel analysis={analysis} onFeedback={submitFeedback} />
      </div>
    </section>
  );
}

type IngestionPanelProps = {
  icon: typeof FileText;
  title: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  buttonLabel: string;
};

function IngestionPanel({ icon: Icon, title, value, onChange, onSubmit, buttonLabel }: IngestionPanelProps) {
  return (
    <div className="p-5">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-md bg-paper text-clay">
          <Icon size={18} strokeWidth={2.2} />
        </div>
        <h3 className="text-base font-semibold">{title}</h3>
      </div>
      <textarea
        className="mt-4 h-44 w-full resize-none rounded-md border border-ink/15 bg-paper p-3 text-sm leading-6 outline-none transition focus:border-moss"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      <button
        className="mt-3 w-full rounded-md bg-moss px-3 py-2 text-sm font-semibold text-white transition hover:bg-ink"
        type="button"
        onClick={onSubmit}
      >
        {buttonLabel}
      </button>
    </div>
  );
}

function StateRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md bg-paper px-3 py-2">
      <span>{label}</span>
      <span className="max-w-[13rem] truncate font-mono text-[11px] text-ink/70">{value || "not created"}</span>
    </div>
  );
}

function AnalysisPanel({
  analysis,
  onFeedback
}: {
  analysis: AnalysisReportResponse | null;
  onFeedback: (eventValue: Record<string, unknown>) => void;
}) {
  if (!analysis) {
    return (
      <div className="p-5">
        <div className="rounded-md border border-dashed border-ink/15 bg-paper p-4 text-sm text-ink/58">
          Analysis results will appear here after a CV profile and vacancy are saved.
        </div>
      </div>
    );
  }

  const overall = Math.round(((analysis.score_json?.overall_score as number | undefined) ?? 0) * 100);
  const scoreItems = [
    ["Skills", analysis.score_json?.skill_match_score],
    ["Evidence", analysis.score_json?.experience_evidence_score],
    ["Gaps", analysis.score_json?.gap_severity_score]
  ];

  return (
    <div className="p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-moss">{formatVerdict(analysis.verdict)}</p>
          <p className="mt-1 text-sm text-ink/58">{analysis.model_version}</p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold">{overall}%</p>
          <p className="text-xs font-semibold text-ink/45">overall score</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {scoreItems.map(([label, value]) => (
          <div key={label} className="rounded-md bg-cloud px-3 py-2">
            <p className="text-xs font-semibold text-ink/50">{label}</p>
            <p className="mt-1 text-sm font-bold">{Math.round(((value as number | undefined) ?? 0) * 100)}%</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-2">
        {analysis.evidence.slice(0, 4).map((item) => (
          <div key={item.id} className="flex items-center justify-between gap-3 rounded-md bg-paper px-3 py-2">
            <span className="text-sm font-medium">{item.requirement_text}</span>
            <span className="rounded-md bg-white px-2 py-1 text-xs font-semibold text-ink/60">
              {item.evidence_level}
            </span>
          </div>
        ))}
      </div>

      {analysis.gaps.length > 0 ? (
        <div className="mt-3 rounded-md bg-clay/10 px-3 py-2 text-sm text-clay">
          {analysis.gaps[0].gap_type}: {analysis.gaps[0].gap_text}
        </div>
      ) : null}

      <div className="mt-4 border-t border-ink/10 pt-4">
        <p className="text-xs font-semibold uppercase tracking-normal text-ink/45">Feedback</p>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {[
            ["Useful", 1],
            ["Unsure", 0],
            ["Wrong", -1]
          ].map(([label, value]) => (
            <button
              key={label}
              className="rounded-md border border-ink/10 px-3 py-2 text-sm font-semibold text-ink/70 transition hover:bg-cloud"
              type="button"
              onClick={() =>
                onFeedback({
                  rating: value,
                  label,
                  overall_score: analysis.score_json?.overall_score,
                  source: "workspace_quick_feedback"
                })
              }
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function formatVerdict(verdict: string | null) {
  if (!verdict) {
    return "No verdict";
  }
  return verdict
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}
