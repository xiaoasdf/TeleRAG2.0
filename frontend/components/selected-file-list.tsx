"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function SelectedFileList({
  files,
  onRemove
}: {
  files: File[];
  onRemove: (index: number) => void;
}) {
  if (!files.length) {
    return <div className="rounded-[1.5rem] border border-dashed border-border p-6 text-sm text-muted">暂未选择文件。</div>;
  }

  return (
    <div className="space-y-3">
      {files.map((file, index) => (
        <div
          key={`${file.name}-${file.size}-${index}`}
          className="flex items-center justify-between gap-4 rounded-[1.25rem] border border-border bg-white/80 px-4 py-3"
        >
          <div className="min-w-0">
            <p className="truncate font-medium">{file.name}</p>
            <p className="text-sm text-muted">{formatBytes(file.size)}</p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={() => onRemove(index)}>
            <X className="mr-1 size-4" />
            移除
          </Button>
        </div>
      ))}
    </div>
  );
}
