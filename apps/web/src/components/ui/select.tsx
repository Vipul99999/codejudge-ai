import * as React from "react";
import { cn } from "@/lib/utils";

export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "h-10 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:border-teal focus:shadow-focus",
      className,
    )}
    {...props}
  />
));
Select.displayName = "Select";
