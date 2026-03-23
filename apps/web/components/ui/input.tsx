import * as React from "react";

import { cn } from "@/lib/utils";

function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "flex h-12 w-full rounded-2xl border border-[color:var(--color-line-strong)] bg-white/85 px-4 text-sm text-[color:var(--color-ink)] shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus-visible:border-[color:var(--color-accent)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-accent-soft)] placeholder:text-[color:var(--color-muted)]",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
