import * as React from "react";

import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-32 w-full rounded-[24px] border border-[color:var(--color-line-strong)] bg-white/85 px-4 py-3 text-sm leading-6 text-[color:var(--color-ink)] shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus-visible:border-[color:var(--color-accent)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-accent-soft)] placeholder:text-[color:var(--color-muted)]",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
