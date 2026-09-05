import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Supply Chain Intelligence — BlackSwan",
  description:
    "AI-powered supply chain decomposition and risk analysis. A council of LLM personas identifies every component, sub-component, and raw material in a product's supply chain.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-mono bg-[#0A0A0A] text-[#F5F5F5] antialiased min-h-screen">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[#2A2A2A] bg-[#0A0A0A]/90 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-[#7CB9E8] flex items-center justify-center text-[#0A0A0A] font-bold text-sm">
                SC
              </div>
              <span className="text-sm font-semibold text-[#F5F5F5] hidden sm:block">
                Supply Chain Intelligence
              </span>
            </a>

            <div className="flex items-center gap-4">
              <span className="text-[10px] uppercase tracking-widest text-[#6B7280]">
                BlackSwan
              </span>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="pt-14">{children}</main>
      </body>
    </html>
  );
}
