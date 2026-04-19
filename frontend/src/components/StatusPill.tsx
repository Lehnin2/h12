import type { ReactNode } from "react";

interface StatusPillProps {
  tone?: "neutral" | "good" | "warn" | "danger";
  children: ReactNode;
}

export function StatusPill({ tone = "neutral", children }: StatusPillProps) {
  return <span className={`status-pill status-pill--${tone}`}>{children}</span>;
}

