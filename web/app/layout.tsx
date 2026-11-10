import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LEGO Sets Explorer",
  description: "Search and explore LEGO sets and themes from Rebrickable data.",
};

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/sets", label: "Sets" },
  { href: "/themes", label: "Themes" },
  { href: "/parts", label: "Parts" },
  { href: "/completed", label: "My Completed Sets" },
  { href: "/my-parts", label: "My Parts" },
  { href: "/build", label: "What Can I Build" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b border-border bg-surface">
          <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
            <Link href="/" className="flex items-center gap-2 font-semibold">
              <span className="inline-block h-5 w-5 rounded-sm bg-accent" />
              LEGO Sets Explorer
            </Link>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
              {NAV.map((item) => (
                <Link key={item.href} href={item.href} className="hover:text-foreground">
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-border py-4 text-center text-xs text-muted">
          LEGO data sourced from{" "}
          <a href="https://rebrickable.com/" className="underline">
            Rebrickable
          </a>
          . CS 348 course project.
        </footer>
      </body>
    </html>
  );
}
