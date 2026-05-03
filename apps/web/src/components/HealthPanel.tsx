"use client";

import { Activity, Database, FlaskConical, Server } from "lucide-react";
import { useEffect, useState } from "react";

import type { HealthResponse } from "@/lib/api";
import { getHealth } from "@/lib/api";

type HealthState =
  | { status: "loading" }
  | { status: "ready"; data: HealthResponse }
  | { status: "error"; message: string };

export function HealthPanel() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    getHealth()
      .then((data) => setHealth({ status: "ready", data }))
      .catch((error: Error) => setHealth({ status: "error", message: error.message }));
  }, []);

  const apiStatus =
    health.status === "ready" ? health.data.status : health.status === "loading" ? "checking" : "offline";
  const databaseStatus = health.status === "ready" ? health.data.database : "pending";
  const environment = health.status === "ready" ? health.data.environment : "local";
  const mlflow = health.status === "ready" ? health.data.mlflow_tracking_uri : "http://localhost:5000";
  const llm =
    health.status === "ready" && health.data.llm_provider === "ollama"
      ? health.data.llm_model
      : health.status === "ready"
        ? health.data.llm_provider
        : "checking";

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <StatusTile icon={Server} label="API" value={apiStatus} active={apiStatus === "ok"} />
      <StatusTile icon={Database} label="Database" value={databaseStatus} active={databaseStatus === "ok"} />
      <StatusTile icon={Activity} label="Environment" value={environment} active />
      <StatusTile icon={FlaskConical} label="Neural LLM" value={llm} active={health.status === "ready"} />
      <StatusTile icon={FlaskConical} label="MLflow" value={mlflow.replace("http://", "")} active />
    </section>
  );
}

type StatusTileProps = {
  icon: typeof Server;
  label: string;
  value: string;
  active: boolean;
};

function StatusTile({ icon: Icon, label, value, active }: StatusTileProps) {
  return (
    <div className="rounded-lg border border-ink/10 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-cloud text-moss">
          <Icon aria-hidden="true" size={18} strokeWidth={2} />
        </div>
        <span
          className={`h-2.5 w-2.5 rounded-full ${active ? "bg-moss" : "bg-clay"}`}
          aria-label={active ? "Available" : "Unavailable"}
        />
      </div>
      <p className="mt-4 text-xs font-semibold uppercase tracking-[0.12em] text-ink/45">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}
