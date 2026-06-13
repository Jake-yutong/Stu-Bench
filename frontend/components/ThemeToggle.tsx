"use client";

export function ThemeToggle() {
  function toggleTheme() {
    const current = document.documentElement.dataset.theme;
    document.documentElement.dataset.theme = current === "dark" ? "light" : "dark";
  }

  return (
    <button type="button" onClick={toggleTheme}>
      Toggle theme
    </button>
  );
}
