import { API_BASE_URL } from "@/lib/constants";
import { KnowledgeBase, QueryResponse } from "@/lib/types";

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload as T;
}

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  return parseResponse<{ status: string; service: string }>(response);
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const response = await fetch(`${API_BASE_URL}/knowledge-bases`, { cache: "no-store" });
  return parseResponse<KnowledgeBase[]>(response);
}

export async function getKnowledgeBase(kbId: string): Promise<KnowledgeBase> {
  const response = await fetch(`${API_BASE_URL}/knowledge-bases/${kbId}`, { cache: "no-store" });
  return parseResponse<KnowledgeBase>(response);
}

export async function getKnowledgeBaseStatus(kbId: string): Promise<KnowledgeBase> {
  const response = await fetch(`${API_BASE_URL}/knowledge-bases/${kbId}/status`, { cache: "no-store" });
  return parseResponse<KnowledgeBase>(response);
}

export async function createKnowledgeBase(input: { name: string; files: File[] }): Promise<KnowledgeBase> {
  const formData = new FormData();
  formData.append("name", input.name);
  input.files.forEach((file) => formData.append("files", file, file.name));
  const response = await fetch(`${API_BASE_URL}/knowledge-bases`, {
    method: "POST",
    body: formData
  });
  return parseResponse<KnowledgeBase>(response);
}

export async function deleteKnowledgeBase(kbId: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/knowledge-bases/${kbId}`, {
    method: "DELETE"
  });
  return parseResponse<{ message: string }>(response);
}

export async function queryKnowledgeBase(kbId: string, question: string): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/knowledge-bases/${kbId}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ question })
  });
  return parseResponse<QueryResponse>(response);
}
