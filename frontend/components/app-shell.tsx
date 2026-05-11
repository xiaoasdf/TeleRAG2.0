import { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(181,82,45,0.14),transparent_24%),linear-gradient(180deg,#f0e4d2_0%,#f7f1e7_45%,#ede4d8_100%)]">
      <div className="mx-auto max-w-7xl px-4 py-10 md:px-8">{children}</div>
    </div>
  );
}
