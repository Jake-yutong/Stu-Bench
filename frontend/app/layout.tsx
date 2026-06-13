import "./globals.css";

export const metadata = {
  title: "Stu-Bench Demo",
  description: "Local-first learner simulation benchmark workbench",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
