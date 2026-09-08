import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Draft Coach · 你的 BP 搭档",
  description: "结合阵容、英雄熟练度与个人战绩的英雄联盟选角助手。",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
