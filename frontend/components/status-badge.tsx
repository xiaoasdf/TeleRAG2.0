import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS } from "@/lib/constants";
import { KnowledgeBaseStatus } from "@/lib/types";

export function StatusBadge({ status }: { status: KnowledgeBaseStatus }) {
  const variant =
    status === "ready" ? "success" : status === "failed" ? "destructive" : status === "running" ? "warning" : "default";
  return <Badge variant={variant}>{STATUS_LABELS[status]}</Badge>;
}
