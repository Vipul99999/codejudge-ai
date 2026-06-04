import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeJudge AI",
  description: "Static code, reasoning, and AI-response evaluation platform."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

