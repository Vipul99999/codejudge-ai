"use client";

import { useMemo, useState } from "react";
import { Play, RotateCcw, ShieldCheck } from "lucide-react";
import { CodeEditor } from "@/components/CodeEditor";
import { Dashboard } from "@/components/Dashboard";
import { ResultPanel } from "@/components/ResultPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { postEvaluation } from "@/lib/api";
import { dashboardModule, modules } from "@/lib/modules";
import type { Language, ModuleKey } from "@/lib/schemas";
import { useEvaluationStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const sampleCode = `def two_sum(nums, target):
    seen = {}
    for i, value in enumerate(nums):
        needed = target - value
        if needed in seen:
            return [seen[needed], i]
        seen[value] = i
    return []`;

const sampleCodeB = `function twoSum(nums, target) {
  for (let i = 0; i <= nums.length; i++) {
    for (let j = i + 1; j < nums.length; j++) {
      if (nums[i] + nums[j] === target) return [i, j];
    }
  }
  return [];
}`;

const rubricDefault = JSON.stringify(
  [
    { name: "correctness", weight: 0.4, score: 82 },
    { name: "efficiency", weight: 0.2, score: 76 },
    { name: "clarity", weight: 0.2, score: 88 },
    { name: "reasoning", weight: 0.15, score: 79 },
    { name: "safety", weight: 0.05, score: 94 },
  ],
  null,
  2,
);

function extractScore(result: Record<string, unknown>) {
  const score =
    result.overall_score ?? result.score ?? result.weighted_score ?? result.confidence_score;
  return typeof score === "number" ? Math.round(score) : undefined;
}

export default function Home() {
  const { activeModule, setActiveModule, language, setLanguage, history, addHistory } =
    useEvaluationStore();
  const [showDashboard, setShowDashboard] = useState(false);
  const [code, setCode] = useState(sampleCode);
  const [solutionB, setSolutionB] = useState(sampleCodeB);
  const [prompt, setPrompt] = useState(
    "Write a robust two-sum implementation and explain edge cases.",
  );
  const [aiResponse, setAiResponse] = useState(
    "The function uses a hash map, handles missing pairs by returning an empty list, and runs in O(n) time.",
  );
  const [problem, setProblem] = useState(
    "Evaluate whether a two-sum solution is correct for duplicates and empty arrays.",
  );
  const [reasoning, setReasoning] = useState(
    "1. Assume nums is a finite list.\n2. Track seen values because complements identify a pair.\n3. Empty input returns no pair.\n4. Complexity is O(n).",
  );
  const [datasetTopic, setDatasetTopic] = useState("Array solution evaluation");
  const [rubric, setRubric] = useState(rubricDefault);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const active = useMemo(
    () => modules.find((module) => module.key === activeModule) ?? modules[0],
    [activeModule],
  );
  const ActiveIcon = active.icon;
  const DashboardIcon = dashboardModule.icon;

  function resetSamples() {
    setCode(sampleCode);
    setSolutionB(sampleCodeB);
    setResult(null);
    setError(null);
  }

  function payloadFor(module: ModuleKey) {
    if (module === "compare") return { language, solution_a: code, solution_b: solutionB };
    if (module === "llm-evaluate") return { prompt, ai_response: aiResponse, language };
    if (module === "reasoning") return { problem, reasoning };
    if (module === "dataset")
      return {
        topic: datasetTopic,
        language,
        count: 6,
        difficulty: "mixed",
        tags: ["ai-evaluation", "benchmarking"],
      };
    if (module === "rubric") return { categories: JSON.parse(rubric) as unknown };
    return { language, code };
  }

  async function runEvaluation() {
    setIsLoading(true);
    setError(null);
    try {
      const next = await postEvaluation(activeModule, payloadFor(activeModule));
      setResult(next);
      addHistory({
        module: activeModule,
        score: extractScore(next),
        summary: active.label,
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown evaluator failure");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-panel">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-ink">CodeJudge AI</h1>
              <p className="text-sm text-slate-500">
                Professional static evaluation for code, prompts, reasoning, and datasets.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="good">No code execution</Badge>
            <Badge>Rule-based engine</Badge>
            <Select
              value={language}
              onChange={(event) => setLanguage(event.target.value as Language)}
              aria-label="Language"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </Select>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1500px] gap-4 px-4 py-4 lg:grid-cols-[300px_1fr]">
        <aside className="rounded-lg border border-line bg-white p-3 lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)] lg:overflow-auto">
          <div className="grid gap-1">
            {modules.map((module) => {
              const Icon = module.icon;
              const selected = activeModule === module.key && !showDashboard;
              return (
                <button
                  key={module.key}
                  className={cn(
                    "flex w-full items-start gap-3 rounded-md px-3 py-3 text-left transition hover:bg-slate-50 focus:outline-none focus-visible:shadow-focus",
                    selected ? "bg-teal-50 text-teal-950" : "text-ink",
                  )}
                  onClick={() => {
                    setActiveModule(module.key);
                    setShowDashboard(false);
                  }}
                >
                  <Icon className="mt-0.5 h-5 w-5 shrink-0" />
                  <span>
                    <span className="block text-sm font-semibold">{module.label}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-500">
                      {module.description}
                    </span>
                  </span>
                </button>
              );
            })}
            <button
              className={cn(
                "mt-2 flex w-full items-center gap-3 rounded-md border border-line px-3 py-3 text-left transition hover:bg-slate-50 focus:outline-none focus-visible:shadow-focus",
                showDashboard ? "bg-amber-50 text-amber-950" : "text-ink",
              )}
              onClick={() => setShowDashboard(true)}
            >
              <DashboardIcon className="h-5 w-5" />
              <span className="text-sm font-semibold">{dashboardModule.label}</span>
            </button>
          </div>
        </aside>

        <section className="grid gap-4">
          {showDashboard ? (
            <Dashboard />
          ) : (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <ActiveIcon className="h-5 w-5 text-teal" />
                    <h2 className="text-lg font-semibold text-ink">{active.label}</h2>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">{active.description}</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={resetSamples}>
                    <RotateCcw className="h-4 w-4" /> Reset
                  </Button>
                  <Button onClick={runEvaluation} disabled={isLoading}>
                    <Play className="h-4 w-4" /> Run Evaluation
                  </Button>
                </div>
              </div>

              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)]">
                <div className="grid gap-4">
                  {activeModule === "llm-evaluate" ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Prompt And AI Response</CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-3">
                        <Textarea
                          value={prompt}
                          onChange={(event) => setPrompt(event.target.value)}
                          aria-label="Prompt"
                        />
                        <Textarea
                          value={aiResponse}
                          onChange={(event) => setAiResponse(event.target.value)}
                          aria-label="AI Response"
                          className="min-h-52"
                        />
                      </CardContent>
                    </Card>
                  ) : null}

                  {activeModule === "reasoning" ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Problem And Reasoning</CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-3">
                        <Textarea
                          value={problem}
                          onChange={(event) => setProblem(event.target.value)}
                          aria-label="Problem"
                        />
                        <Textarea
                          value={reasoning}
                          onChange={(event) => setReasoning(event.target.value)}
                          aria-label="Reasoning"
                          className="min-h-60"
                        />
                      </CardContent>
                    </Card>
                  ) : null}

                  {activeModule === "dataset" ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Dataset Topic</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Textarea
                          value={datasetTopic}
                          onChange={(event) => setDatasetTopic(event.target.value)}
                          aria-label="Dataset Topic"
                        />
                      </CardContent>
                    </Card>
                  ) : null}

                  {activeModule === "rubric" ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Rubric Categories JSON</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Textarea
                          value={rubric}
                          onChange={(event) => setRubric(event.target.value)}
                          aria-label="Rubric JSON"
                          className="min-h-80 font-mono"
                        />
                      </CardContent>
                    </Card>
                  ) : null}

                  {!["llm-evaluate", "reasoning", "dataset", "rubric"].includes(activeModule) ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>
                          {activeModule === "compare" ? "Solution A" : "Submission"}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <CodeEditor value={code} language={language} onChange={setCode} />
                      </CardContent>
                    </Card>
                  ) : null}

                  {activeModule === "compare" ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Solution B</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <CodeEditor value={solutionB} language={language} onChange={setSolutionB} />
                      </CardContent>
                    </Card>
                  ) : null}
                </div>

                <div className="grid gap-4">
                  <ResultPanel result={result} error={error} isLoading={isLoading} />
                  <Card>
                    <CardHeader>
                      <CardTitle>Local History</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-2">
                      {history.length ? (
                        history.slice(0, 6).map((entry) => (
                          <div
                            key={entry.id}
                            className="flex items-center justify-between gap-3 rounded-md border border-line bg-slate-50 px-3 py-2 text-sm"
                          >
                            <span className="truncate">{entry.summary}</span>
                            <span className="shrink-0 text-slate-500">{entry.score ?? "n/a"}</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-slate-500">No local evaluations yet.</p>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
