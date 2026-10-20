import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/shell/Sidebar";

export const metadata: Metadata = {
  title: "ShelfSense AI — Planogram Designer Studio",
  description: "Retail planogram designer and product catalogue management platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-[#0d0f12]">
      <body className="h-full flex text-gray-100 bg-[#0d0f12] overflow-hidden antialiased">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
