import { formatMathText } from "../lib/formatMathText";

export function FormattedMathText({ text }: { text: string }) {
  const lines = formatMathText(text).split("\n");

  return (
    <span className="formatted-text">
      {lines.map((line) => (
        <span key={line}>{line}</span>
      ))}
    </span>
  );
}
