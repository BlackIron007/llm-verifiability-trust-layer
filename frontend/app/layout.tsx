import "./globals.css";

export const metadata = {
  title: "LLM Trust Layer",
  description: "Verifiability and Trust Layer for LLMs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-background text-text">{children}</body>
    </html>
  );
}