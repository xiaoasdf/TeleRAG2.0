import { AppShell } from "@/components/app-shell";
import { CreateKnowledgeBaseForm } from "@/components/create-knowledge-base-form";
import { KnowledgeBaseList } from "@/components/knowledge-base-list";
import { Card, CardContent } from "@/components/ui/card";
import { getHealth, listKnowledgeBases } from "@/lib/api";

export default async function HomePage() {
  const [health, knowledgeBases] = await Promise.all([getHealth(), listKnowledgeBases()]);

  return (
    <AppShell>
      <section className="mb-8 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="border-none bg-transparent shadow-none">
          <CardContent className="px-0 pt-0">
            <p className="mb-3 text-sm font-semibold uppercase tracking-[0.24em] text-accent">TeleRAG</p>
            <h1 className="max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
              把文档整理成可随时提问的本地知识库。
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-muted">
              使用 Next.js 正式用户端管理多个知识库，上传多个文档，后台构建索引，并直接进入问答工作台。
            </p>
            <div className="mt-6 inline-flex rounded-full border border-border bg-white/70 px-4 py-2 text-sm text-muted">
              API 状态：{health.service} / {health.status}
            </div>
          </CardContent>
        </Card>
        <CreateKnowledgeBaseForm />
      </section>

      <KnowledgeBaseList items={knowledgeBases} />
    </AppShell>
  );
}
