import { Database } from "lucide-react";

import { KnowledgeBaseCard } from "@/components/knowledge-base-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KnowledgeBase } from "@/lib/types";

export function KnowledgeBaseList({ items }: { items: KnowledgeBase[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>知识库列表</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length ? (
          <div className="grid gap-4 md:grid-cols-2">
            {items.map((kb) => (
              <KnowledgeBaseCard key={kb.kb_id} kb={kb} />
            ))}
          </div>
        ) : (
          <div className="rounded-[1.5rem] border border-dashed border-border bg-white/60 p-10 text-center">
            <Database className="mx-auto mb-4 size-10 text-muted" />
            <p className="text-base font-medium">还没有知识库</p>
            <p className="mt-1 text-sm text-muted">先上传文档，系统会在后台构建索引。</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
