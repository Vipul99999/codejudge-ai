import { render, screen } from "@testing-library/react";
import React from "react";
import Home from "@/app/page";

vi.mock("@/components/CodeEditor", () => ({
  CodeEditor: ({ value }: { value: string }) =>
    React.createElement("textarea", { readOnly: true, value, "aria-label": "Mock editor" })
}));

vi.mock("@monaco-editor/react", () => ({
  default: () => React.createElement("textarea", { "aria-label": "Monaco mock" })
}));

describe("CodeJudge AI UI", () => {
  it("renders evaluator modules", () => {
    render(<Home />);
    expect(screen.getByText("CodeJudge AI")).toBeInTheDocument();
    expect(screen.getByText("Bug Detector")).toBeInTheDocument();
    expect(screen.getByText("LLM Code Evaluator")).toBeInTheDocument();
  });
});
