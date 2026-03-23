import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-all outline-none disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--color-background)]",
  {
    variants: {
      variant: {
        default:
          "bg-[color:var(--color-ink)] px-4 py-2 text-[color:var(--color-paper)] shadow-[0_12px_30px_rgba(20,27,45,0.12)] hover:-translate-y-0.5",
        secondary:
          "border border-[color:var(--color-line-strong)] bg-[color:var(--color-panel)] px-4 py-2 text-[color:var(--color-ink)] hover:bg-white/90",
        ghost:
          "px-3 py-2 text-[color:var(--color-muted)] hover:bg-white/60 hover:text-[color:var(--color-ink)]",
        danger:
          "bg-[color:var(--color-accent-warm)] px-4 py-2 text-white shadow-[0_12px_24px_rgba(213,92,50,0.22)] hover:-translate-y-0.5",
      },
      size: {
        default: "h-11",
        sm: "h-9 px-3 text-xs",
        lg: "h-12 px-5 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

export { Button, buttonVariants };
