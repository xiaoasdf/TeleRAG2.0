"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogDismiss,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  AlertDialogConfirm
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { deleteKnowledgeBase } from "@/lib/api";

export function DeleteKnowledgeBaseDialog({
  kbId,
  kbName,
  redirectHome = false
}: {
  kbId: string;
  kbName: string;
  redirectHome?: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    try {
      setPending(true);
      setError(null);
      await deleteKnowledgeBase(kbId);
      if (redirectHome) {
        router.push("/");
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除知识库失败");
    } finally {
      setPending(false);
    }
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">删除</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>确认删除知识库</AlertDialogTitle>
          <AlertDialogDescription>
            将永久删除“{kbName}”及其文档和索引文件。该操作不可恢复。
          </AlertDialogDescription>
        </AlertDialogHeader>
        {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
        <AlertDialogFooter>
          <AlertDialogDismiss disabled={pending}>取消</AlertDialogDismiss>
          <AlertDialogConfirm onClick={handleDelete} disabled={pending}>
            {pending ? "删除中..." : "确认删除"}
          </AlertDialogConfirm>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
