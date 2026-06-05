import {
  benchmarkSchema,
  endpointByModule,
  type BenchmarkSummary,
  type ModuleKey,
} from "@/lib/schemas";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function postEvaluation(module: ModuleKey, payload: unknown) {
  const response = await fetch(`${API_BASE}${endpointByModule[module]}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return (await response.json()) as Record<string, unknown>;
}

export async function fetchBenchmarks(): Promise<BenchmarkSummary> {
  const response = await fetch(`${API_BASE}/api/benchmarks`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Benchmark API unavailable");
  }
  return benchmarkSchema.parse(await response.json());
}
