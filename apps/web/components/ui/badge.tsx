import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]",
  {
    variants: {
      variant: {
        default:
          "border-[color:var(--color-line-strong)] bg-white/80 text-[color:var(--color-muted)]",
        accent:
          "border-transparent bg-[color:var(--color-accent-soft)] text-[color:var(--color-accent)]",
        warm: "border-transparent bg-[color:var(--color-warm-soft)] text-[color:var(--color-accent-warm)]",
        success:
          "border-transparent bg-[color:var(--color-success-soft)] text-[color:var(--color-success)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge };
