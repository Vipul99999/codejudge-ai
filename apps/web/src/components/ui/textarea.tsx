import * as React from "react";
import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "min-h-32 w-full resize-y rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-teal focus:shadow-focus",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
