import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "DOU Job Search Copilot",
  description: "Evidence-based job search workspace for Ukrainian IT candidates"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
