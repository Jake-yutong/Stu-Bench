export function formatMathText(text: string): string {
  return text
    .replace(/\\begin\{tabular\}\{[^}]*\}/g, "")
    .replace(/\\end\{tabular\}/g, "")
    .replace(/\\color\{gold\}\\bigstar/g, "star")
    .replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, "$1/$2")
    .replace(/\\bigstar/g, "star")
    .replace(/\\space/g, " ")
    .replace(/\\\(/g, "")
    .replace(/\\\)/g, "")
    .replace(/\\\\/g, "\n")
    .replace(/&/g, " ")
    .split("\n")
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n");
}
