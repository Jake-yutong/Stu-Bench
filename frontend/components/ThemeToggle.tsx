"use client";

export function ThemeToggle({ label = "Toggle theme" }: { label?: string }) {
  function toggleTheme() {
    const current = document.documentElement.dataset.theme;
    document.documentElement.dataset.theme = current === "dark" ? "light" : "dark";
  }

  return (
    <button type="button" onClick={toggleTheme}>
      {label}
    </button>
  );
}
