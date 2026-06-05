"use client";

import dynamic from "next/dynamic";
import { Textarea } from "@/components/ui/textarea";
import type { Language } from "@/lib/schemas";

const Monaco = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[360px] items-center justify-center rounded-lg border border-line bg-white text-sm text-slate-500">
      Loading editor
    </div>
  ),
});

type Props = {
  value: string;
  language: Language;
  onChange: (value: string) => void;
  minHeight?: number;
};

export function CodeEditor({ value, language, onChange, minHeight = 360 }: Props) {
  const monacoLanguage = language === "cpp" ? "cpp" : language;

  return (
    <div
      className="monaco-shell overflow-hidden rounded-lg border border-line bg-white"
      style={{ minHeight }}
    >
      <Monaco
        height={minHeight}
        language={monacoLanguage}
        value={value}
        theme="vs"
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbersMinChars: 3,
          scrollBeyondLastLine: false,
          wordWrap: "on",
          tabSize: 2,
          padding: { top: 12, bottom: 12 },
        }}
        onChange={(next) => onChange(next ?? "")}
      />
      <noscript>
        <Textarea value={value} onChange={(event) => onChange(event.target.value)} />
      </noscript>
    </div>
  );
}
