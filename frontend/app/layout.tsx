import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "TeleRAG 正式用户端",
  description: "本地知识库上传、构建与问答工作台"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
