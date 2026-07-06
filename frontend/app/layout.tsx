import type { Metadata } from "next";
import { sourceSerif } from "./fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "Beige Claude UI",
  description: "Warm cocoa + gold chat interface",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={sourceSerif.variable}>
      <body className="bg-cocoa text-cream antialiased">{children}</body>
    </html>
  );
}
