"use client";

import { Download, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { downloadText } from "@/lib/utils";

type Props = {
  result: Record<string, unknown> | null;
  error: string | null;
  isLoading: boolean;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function scoreTone(score: number) {
  if (score >= 80) return "good";
  if (score >= 60) return "warn";
  return "bad";
}

function renderValue(value: unknown): React.ReactNode {
  if (Array.isArray(value)) {
    return (
      <div className="space-y-3">
        {value.map((item, index) => (
          <div key={index} className="rounded-md border border-line bg-slate-50 p-3">
            {renderValue(item)}
          </div>
        ))}
      </div>
    );
  }

  if (isRecord(value)) {
    return (
      <dl className="grid gap-2 text-sm">
        {Object.entries(value).map(([key, entry]) => (
          <div key={key} className="grid gap-1 sm:grid-cols-[170px_1fr]">
            <dt className="font-medium capitalize text-slate-600">{key.replaceAll("_", " ")}</dt>
            <dd className="break-words text-ink">{renderValue(entry)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  if (typeof value === "number") {
    return <Badge tone={scoreTone(value)}>{value}</Badge>;
  }

  return <span>{String(value)}</span>;
}

export function ResultPanel({ result, error, isLoading }: Props) {
  const exportRecord = result?.export;
  const jsonExport =
    isRecord(exportRecord) && typeof exportRecord.json === "string" ? exportRecord.json : null;
  const csvExport =
    isRecord(exportRecord) && typeof exportRecord.csv === "string" ? exportRecord.csv : null;

  return (
    <Card className="min-h-[520px]">
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <div>
          <CardTitle>Evaluation Report</CardTitle>
          <p className="mt-1 text-sm text-slate-500">Deterministic static-analysis output.</p>
        </div>
        <div className="flex gap-2">
          {jsonExport ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => downloadText("codejudge-export.json", jsonExport)}
            >
              <Download className="h-4 w-4" /> JSON
            </Button>
          ) : null}
          {csvExport ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => downloadText("codejudge-export.csv", csvExport, "text/csv")}
            >
              <Download className="h-4 w-4" /> CSV
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="rounded-md border border-line bg-slate-50 p-4 text-sm text-slate-600">
            Running evaluator...
          </div>
        ) : null}
        {error ? (
          <div className="flex gap-3 rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Evaluation failed</p>
              <p className="mt-1 break-words">{error}</p>
            </div>
          </div>
        ) : null}
        {!isLoading && !error && result ? (
          <div className="space-y-4">{renderValue(result)}</div>
        ) : null}
        {!isLoading && !error && !result ? (
          <div className="rounded-md border border-dashed border-line p-6 text-sm text-slate-500">
            Run an evaluator to generate a structured report.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
