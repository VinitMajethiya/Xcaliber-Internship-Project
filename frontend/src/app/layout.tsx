import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Insight Copilot | AI Business Intelligence Analyst',
  description: 'A reasoning, tool-using analyst agent built with LangGraph for exploring and discovering insights in Global Superstore sales data.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0b0f19] text-gray-100 antialiased flex flex-col">
        {children}
      </body>
    </html>
  );
}
