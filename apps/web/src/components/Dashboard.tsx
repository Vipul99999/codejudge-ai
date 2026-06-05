"use client";

import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchBenchmarks } from "@/lib/api";
import type { BenchmarkSummary } from "@/lib/schemas";

function flatten(records: Record<string, number>[]) {
  return records.flatMap((record) =>
    Object.entries(record).map(([name, value]) => ({ name, value })),
  );
}

export function Dashboard() {
  const [summary, setSummary] = useState<BenchmarkSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      setSummary(await fetchBenchmarks());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load benchmarks");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const modules = useMemo(() => flatten(summary?.module_distribution ?? []), [summary]);
  const complexity = useMemo(() => flatten(summary?.complexity_distribution ?? []), [summary]);
  const bugs = useMemo(() => flatten(summary?.common_bug_categories ?? []), [summary]);

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Benchmark Dashboard</h2>
          <p className="text-sm text-slate-500">Local metrics gathered from evaluator API calls.</p>
        </div>
        <Button variant="secondary" onClick={refresh}>
          <RefreshCw className="h-4 w-4" /> Refresh
        </Button>
      </div>
      {error ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          {error}
        </div>
      ) : null}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Evaluations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{summary?.evaluations_performed ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Average Score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{summary?.average_score ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Bug Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{bugs.length}</p>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        {[
          ["Module Usage", modules, "#0f766e"],
          ["Complexity Distribution", complexity, "#b45309"],
          ["Common Bug Categories", bugs, "#be123c"],
        ].map(([title, data, fill]) => (
          <Card key={String(title)}>
            <CardHeader>
              <CardTitle>{String(title)}</CardTitle>
            </CardHeader>
            <CardContent className="h-72">
              {Array.isArray(data) && data.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      angle={-35}
                      textAnchor="end"
                      interval={0}
                      height={70}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="value" fill={String(fill)} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center rounded-md border border-dashed border-line text-sm text-slate-500">
                  No data yet
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
