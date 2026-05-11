"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { getKnowledgeBaseStatus, queryKnowledgeBase } from "@/lib/api";
import { STATUS_LABELS } from "@/lib/constants";
import { KnowledgeBase, QueryResponse } from "@/lib/types";

export function QueryPanel({ initialKb }: { initialKb: KnowledgeBase }) {
  const [kb, setKb] = useState(initialKb);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!["pending", "running"].includes(kb.status)) return;
    let cancelled = false;

    async function poll() {
      try {
        const next = await getKnowledgeBaseStatus(kb.kb_id);
        if (cancelled) return;
        setKb(next);
        if (["pending", "running"].includes(next.status)) {
          window.setTimeout(poll, 2000);
        }
      } catch {
        if (!cancelled) {
          window.setTimeout(poll, 3000);
        }
      }
    }

    const timer = window.setTimeout(poll, 2000);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [kb.kb_id, kb.status]);

  const statusHint = useMemo(() => {
    if (kb.status === "ready") return "知识库已可用，可以开始提问。";
    if (kb.status === "failed") return kb.error_message || "知识库构建失败。";
    return `知识库正在${STATUS_LABELS[kb.status]}，页面会自动刷新状态。`;
  }, [kb]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      setError("问题不能为空。");
      return;
    }
    try {
      setPending(true);
      setError(null);
      const response = await queryKnowledgeBase(kb.kb_id, question.trim());
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提问失败");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <Card>
        <CardHeader>
          <CardTitle>提问</CardTitle>
          <CardDescription>{statusHint}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <Textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="请输入你想问的问题。"
              disabled={kb.status !== "ready" || pending}
            />
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <Button type="submit" disabled={kb.status !== "ready" || pending}>
              {pending ? "生成中..." : "开始提问"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>回答</CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="whitespace-pre-wrap text-sm leading-7 text-foreground">{result.answer}</div>
            ) : (
              <p className="text-sm text-muted">提交问题后，这里会显示模型生成的回答。</p>
            )}
            {result?.thinking ? (
              <div className="mt-6 rounded-[1.25rem] bg-black/5 p-4 text-sm text-muted">
                <p className="mb-2 font-medium text-foreground">思考过程</p>
                <div className="whitespace-pre-wrap leading-7">{result.thinking}</div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>来源</CardTitle>
          </CardHeader>
          <CardContent>
            {result?.sources.length ? (
              <div className="space-y-3">
                {result.sources.map((source) => (
                  <div key={source.chunk_id} className="rounded-[1.25rem] border border-border bg-white/80 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">
                          {source.source}
                          {source.page ? `（第 ${source.page} 页）` : ""}
                        </p>
                        <p className="text-xs text-muted">{source.chunk_id}</p>
                      </div>
                      <div className="text-xs text-muted">score={source.score.toFixed(4)}</div>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted">{source.snippet}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted">暂无来源结果。</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
