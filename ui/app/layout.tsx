import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SliceBuddy",
  description: "Beginner-friendly 3D print planning from your STL or 3MF model file.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
