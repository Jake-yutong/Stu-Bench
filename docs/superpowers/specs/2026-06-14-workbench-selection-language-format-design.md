# Workbench Selection, Language, and Formatting Design

## Goal

Improve the Stu-Bench demo so pre-experiments can select multiple episodes, limit the tested count, switch UI language between English and Chinese, and display math-heavy Eedi questions without exposing raw LaTeX control syntax.

## Scope

- Add multi-select episode controls in the setup panel.
- Add a numeric test count control. Manual checkbox selection takes priority; if nothing is checked, the run uses the first N episodes.
- Add a local UI language toggle for English and Chinese labels.
- Preserve benchmark data exactly. Question text, answer options, SCS, scaffolds, model outputs, and judge text are not translated.
- Normalize common LaTeX wrappers in question and option display, including inline `\(...\)` and simple `tabular` blocks.

## Architecture

The frontend remains local-state driven. `EpisodeWorkbench` owns selection, count, language, and active preview state. A small formatter component renders question text and option text after deterministic normalization. A local translation dictionary maps stable UI keys to English and Chinese labels.

No backend schema change is needed because `RunConfig.episode_ids` already accepts multiple ids. The frontend will send an ordered array of episode ids.

## UX

The setup panel shows a compact language selector, a test count input, and a scrollable episode checkbox list. The episode preview follows the first selected episode, or the first episode in the count-limited list when no boxes are checked. Status labels remain short to avoid layout overflow.

## Formatting Rules

The formatter is intentionally conservative:

- Strip inline math wrappers `\(` and `\)`.
- Strip `\begin{tabular}{...}` and `\end{tabular}`.
- Convert tabular column separators `&` to spaced text.
- Convert LaTeX row separators `\\` to line breaks.
- Convert `\color{gold}\bigstar` to `star`.
- Collapse repeated spaces while preserving line breaks.

## Testing

Frontend tests cover:

- Manual multi-selection sends multiple episode ids.
- Test count sends the first N ids when no manual selection exists.
- Chinese language mode changes UI labels.
- Raw LaTeX table syntax is not displayed in question text or options.

Verification also includes TypeScript, backend tests, and visual regression screenshots.
