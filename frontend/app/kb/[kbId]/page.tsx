import Link from "next/link";
import { ArrowLeft, Files } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { DeleteKnowledgeBaseDialog } from "@/components/delete-kb-dialog";
import { QueryPanel } from "@/components/query-panel";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getKnowledgeBase } from "@/lib/api";

export default async function KnowledgeBasePage({ params }: { params: Promise<{ kbId: string }> }) {
  const { kbId } = await params;
  const kb = await getKnowledgeBase(kbId);

  return (
    <AppShell>
      <section className="mb-8 rounded-[2rem] border border-border bg-card px-6 py-8 shadow-paper md:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-4">
            <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted transition hover:text-foreground">
              <ArrowLeft className="size-4" />
              返回首页
            </Link>
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-3xl font-semibold tracking-tight md:text-5xl">{kb.name}</h1>
                <StatusBadge status={kb.status} />
              </div>
              <p className="text-sm text-muted">{kb.kb_id}</p>
              {kb.error_message ? <p className="text-sm text-destructive">{kb.error_message}</p> : null}
            </div>
          </div>
          <DeleteKnowledgeBaseDialog kbId={kb.kb_id} kbName={kb.name} redirectHome />
        </div>
      </section>

      <section className="mb-6">
        <Card>
          <CardHeader>
            <CardTitle>文档列表</CardTitle>
          </CardHeader>
          <CardContent>
            {kb.files.length ? (
              <div className="grid gap-3 md:grid-cols-2">
                {kb.files.map((file) => (
                  <div key={file} className="flex items-center gap-3 rounded-[1.25rem] border border-border bg-white/80 px-4 py-3">
                    <Files className="size-4 text-muted" />
                    <span className="text-sm">{file}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted">该知识库暂时没有文档。</p>
            )}
          </CardContent>
        </Card>
      </section>

      <QueryPanel initialKb={kb} />
    </AppShell>
  );
}
