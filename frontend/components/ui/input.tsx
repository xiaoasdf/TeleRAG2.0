import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "flex h-11 w-full rounded-xl border border-border bg-white px-4 py-2 text-sm outline-none placeholder:text-muted focus-visible:ring-2 focus-visible:ring-accent",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
