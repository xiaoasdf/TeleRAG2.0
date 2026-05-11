export type KnowledgeBaseStatus = "pending" | "running" | "ready" | "failed";

export type KnowledgeBase = {
  kb_id: string;
  name: string;
  status: KnowledgeBaseStatus;
  created_at: string;
  files: string[];
  error_message: string | null;
  documents: number | null;
  chunks: number | null;
};

export type SourceItem = {
  source: string;
  chunk_id: string;
  score: number;
  snippet: string;
  page: number | null;
};

export type QueryResponse = {
  answer: string;
  thinking: string;
  sources: SourceItem[];
};
