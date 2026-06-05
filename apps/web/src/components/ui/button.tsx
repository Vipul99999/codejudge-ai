import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium transition focus:outline-none focus-visible:shadow-focus disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-ink text-white hover:bg-black",
        secondary: "border border-line bg-white text-ink hover:bg-slate-50",
        ghost: "text-ink hover:bg-slate-100",
        danger: "bg-berry text-white hover:bg-rose-800",
      },
      size: {
        default: "h-10 px-4",
        icon: "h-10 w-10 px-0",
        sm: "h-8 px-3 text-xs",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  ),
);
Button.displayName = "Button";
