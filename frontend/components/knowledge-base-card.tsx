import Link from "next/link";
import { Files, MessageSquare } from "lucide-react";

import { DeleteKnowledgeBaseDialog } from "@/components/delete-kb-dialog";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { KnowledgeBase } from "@/lib/types";

export function KnowledgeBaseCard({ kb }: { kb: KnowledgeBase }) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="space-y-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">{kb.name}</h3>
              <StatusBadge status={kb.status} />
            </div>
            <p className="text-xs text-muted">{kb.kb_id}</p>
          </div>
          <DeleteKnowledgeBaseDialog kbId={kb.kb_id} kbName={kb.name} />
        </div>
        <div className="grid gap-2 text-sm text-muted sm:grid-cols-2">
          <div className="flex items-center gap-2">
            <Files className="size-4" />
            <span>{kb.files.length} 个文件</span>
          </div>
          <div className="flex items-center gap-2">
            <MessageSquare className="size-4" />
            <span>{new Date(kb.created_at).toLocaleString("zh-CN")}</span>
          </div>
        </div>
        {kb.error_message ? <p className="text-sm text-destructive">{kb.error_message}</p> : null}
        <Button asChild className="w-full">
          <Link href={`/kb/${kb.kb_id}`}>进入问答</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
