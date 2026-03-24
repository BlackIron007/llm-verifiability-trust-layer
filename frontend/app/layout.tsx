import "./globals.css";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  weight: ["300", "400", "500", "600"],
});

export const metadata = {
  title: "TrustLayer — AI Response Verification",
  description:
    "Verify any AI response instantly. TrustLayer extracts claims, cross-references evidence, and scores trust in real time.",
  openGraph: {
    title: "TrustLayer — AI Response Verification",
    description:
      "Verify any AI response instantly. Extract claims, cross-reference evidence, and score trust.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-background text-text font-sans">{children}</body>
    </html>
  );
}