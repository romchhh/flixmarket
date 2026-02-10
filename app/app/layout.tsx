import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import ShopLayoutClient from "@/components/ShopLayoutClient";

export const metadata: Metadata = {
  title: "Flix Market",
  description: "Каталог та профіль",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="uk">
      <head>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body className="min-h-screen text-gray-900 antialiased">
        <ShopLayoutClient>{children}</ShopLayoutClient>
      </body>
    </html>
  );
}
