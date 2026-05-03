"use client";

import { BrainCircuit, BriefcaseBusiness, FileText, KeyRound, LogIn } from "lucide-react";
import { useEffect, useState } from "react";

import { createJobFromText, createResume, login, register } from "@/lib/api";

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
      setNotice({ kind: "success", text: `Resume saved: ${document.id} (${document.language ?? "unknown"})` });
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
      setNotice({ kind: "success", text: `Vacancy saved: ${job.title}` });
    } catch (error) {
      setNotice({ kind: "error", text: error instanceof Error ? error.message : "Vacancy save failed" });
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
        Neural extraction status is stored as pending for M2, where Qwen/Ollama will produce structured JSON.
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
