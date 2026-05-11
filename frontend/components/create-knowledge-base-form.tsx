"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FilePlus2 } from "lucide-react";

import { SelectedFileList } from "@/components/selected-file-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createKnowledgeBase } from "@/lib/api";

export function CreateKnowledgeBaseForm() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileCountLabel = useMemo(() => {
    if (!files.length) return "还未选择文件";
    return `已选择 ${files.length} 个文件`;
  }, [files]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!files.length) {
      setError("请先选择至少一个文件。");
      return;
    }
    try {
      setPending(true);
      setError(null);
      const kb = await createKnowledgeBase({ name, files });
      router.push(`/kb/${kb.kb_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建知识库失败");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>创建知识库</CardTitle>
        <CardDescription>支持多次添加文件，并在正式上传前删除任意待上传项。</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-5" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium">知识库名称</label>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="例如：项目资料" />
          </div>

          <div className="space-y-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium">待上传文件</p>
                <p className="text-sm text-muted">{fileCountLabel}</p>
              </div>
              <Button type="button" variant="secondary" onClick={() => inputRef.current?.click()}>
                <FilePlus2 className="mr-2 size-4" />
                添加文件
              </Button>
            </div>
            <input
              ref={inputRef}
              type="file"
              multiple
              hidden
              onChange={(event) => {
                const incoming = Array.from(event.target.files || []);
                setFiles((current) => current.concat(incoming));
                event.target.value = "";
              }}
            />
            <SelectedFileList files={files} onRemove={(index) => setFiles((current) => current.filter((_, i) => i !== index))} />
          </div>

          {error ? <p className="text-sm text-destructive">{error}</p> : null}

          <Button type="submit" disabled={pending} size="lg">
            {pending ? "上传并构建中..." : "上传并构建"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
