// Job: GODMODE Frontend. Purpose: Root layout that loads global styles and wraps pages in the app shell.
import "./globals.css";
import Shell from "./Shell";

export const metadata = { title: "GODMODE Command Center" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><Shell>{children}</Shell></body></html>;
}
