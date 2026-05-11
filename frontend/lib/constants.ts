import { KnowledgeBaseStatus } from "@/lib/types";

export const STATUS_LABELS: Record<KnowledgeBaseStatus, string> = {
  pending: "等待中",
  running: "构建中",
  ready: "可用",
  failed: "失败"
};

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";
