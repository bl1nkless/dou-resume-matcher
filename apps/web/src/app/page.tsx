import {
  ArrowRight,
  BookOpenCheck,
  BriefcaseBusiness,
  ClipboardCheck,
  FileText,
  Gauge,
  MessageSquareText
} from "lucide-react";

import { HealthPanel } from "@/components/HealthPanel";
import { M1Workspace } from "@/components/M1Workspace";

const pipeline = [
  {
    title: "Candidate profile",
    state: "M1",
    icon: FileText,
    detail: "CV text, raw documents, user-owned records"
  },
  {
    title: "Vacancy intake",
    state: "M1",
    icon: BriefcaseBusiness,
    detail: "Pasted DOU vacancy text and URL fallback"
  },
  {
    title: "Evidence map",
    state: "M2",
    icon: ClipboardCheck,
    detail: "Rules-baseline requirement-to-CV evidence with confidence"
  },
  {
    title: "Verdict engine",
    state: "M2",
    icon: Gauge,
    detail: "Score components, gaps, feedback, and opportunity verdict"
  }
];

const reportSections = [
  "Score components",
  "Requirement evidence",
  "Gap severity",
  "CV actions",
  "Interview battlecard",
  "Feedback"
];

export default function Home() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-20 border-r border-ink/10 bg-white/70 px-4 py-5 backdrop-blur lg:block">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-ink text-lg font-black text-paper">
          RH
        </div>
        <nav className="mt-8 flex flex-col gap-3" aria-label="Workspace">
          {[FileText, BriefcaseBusiness, Gauge, MessageSquareText].map((Icon, index) => (
            <button
              key={index}
              className="flex h-11 w-11 items-center justify-center rounded-md text-ink/55 transition hover:bg-cloud hover:text-ink"
              aria-label={`Workspace section ${index + 1}`}
            >
              <Icon size={19} strokeWidth={2} />
            </button>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-20">
        <header className="border-b border-ink/10 bg-paper/90 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
            <div>
              <h1 className="text-xl font-semibold leading-tight sm:text-2xl">DOU Job Search Copilot</h1>
              <p className="mt-1 text-sm text-ink/60">Local ML workspace foundation</p>
            </div>
            <button className="inline-flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-paper shadow-sm transition hover:bg-moss">
              Start M1
              <ArrowRight size={16} strokeWidth={2.2} />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-7xl px-5 py-6 sm:px-8">
          <HealthPanel />

          <M1Workspace />

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="rounded-lg border border-ink/10 bg-white shadow-panel">
              <div className="flex flex-col gap-4 border-b border-ink/10 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold">Analysis pipeline</h2>
                  <p className="mt-1 text-sm text-ink/58">M2 baseline with product and ML milestones aligned.</p>
                </div>
                <div className="flex items-center gap-2 rounded-md bg-cloud px-3 py-2 text-sm font-semibold text-moss">
                  <BookOpenCheck size={16} strokeWidth={2.2} />
                  Spec-linked
                </div>
              </div>

              <div className="grid gap-0 divide-y divide-ink/10">
                {pipeline.map((item) => (
                  <div key={item.title} className="grid gap-4 p-5 sm:grid-cols-[44px_1fr_auto] sm:items-center">
                    <div className="flex h-11 w-11 items-center justify-center rounded-md bg-paper text-clay">
                      <item.icon size={19} strokeWidth={2.1} />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold">{item.title}</h3>
                      <p className="mt-1 text-sm text-ink/58">{item.detail}</p>
                    </div>
                    <span className="w-fit rounded-md border border-ink/10 px-2.5 py-1 text-xs font-semibold text-ink/60">
                      {item.state}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-ink/10 bg-ink p-5 text-paper shadow-panel">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Report shell</h2>
                <span className="rounded-md bg-paper/10 px-2.5 py-1 text-xs font-semibold text-paper/75">
                  Preview
                </span>
              </div>

              <div className="mt-5 rounded-lg bg-paper p-4 text-ink">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-moss">Tailor first</p>
                    <p className="mt-2 text-4xl font-bold tracking-normal">76%</p>
                  </div>
                  <div className="h-16 w-16 rounded-full border-[10px] border-flax border-r-cloud" />
                </div>
                <div className="mt-5 grid grid-cols-3 gap-2">
                  {["Skills", "Evidence", "Gaps"].map((label, index) => (
                    <div key={label} className="rounded-md bg-cloud px-3 py-2">
                      <p className="text-xs font-semibold text-ink/50">{label}</p>
                      <p className="mt-1 text-sm font-bold">{[78, 71, 72][index]}%</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-5 grid gap-2">
                {reportSections.map((section) => (
                  <div key={section} className="flex items-center justify-between rounded-md bg-paper/8 px-3 py-2">
                    <span className="text-sm font-medium text-paper/85">{section}</span>
                    <ArrowRight size={15} strokeWidth={2.2} className="text-paper/45" />
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
