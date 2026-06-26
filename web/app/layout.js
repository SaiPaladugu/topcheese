import "./globals.css";

export const metadata = {
  title: "Topcheese044 — Solo Queue Coaching Report",
  description:
    "Data-driven League of Legends solo-queue analysis for Topcheese044#NA1: win/loss differentials, champion pool, matchups, and tilt patterns across 825 ranked games.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
