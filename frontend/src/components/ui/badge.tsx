import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "good" | "warn" | "bad";
};

const tones = {
  neutral: "border-slate-300 bg-slate-50 text-slate-700",
  good: "border-teal-200 bg-teal-50 text-teal-800",
  warn: "border-amber-200 bg-amber-50 text-amber-800",
  bad: "border-rose-200 bg-rose-50 text-rose-800"
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-1 text-xs font-medium", tones[tone], className)} {...props} />;
}

