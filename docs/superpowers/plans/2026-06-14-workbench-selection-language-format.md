# Workbench Selection, Language, and Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add multi-episode selection, count-limited runs, English/Chinese UI labels, and deterministic question formatting.

**Architecture:** Keep all changes in the existing Next.js frontend. `EpisodeWorkbench` owns state and run request construction, `FormattedMathText` owns display normalization, and `i18n.ts` owns UI copy. The backend already accepts multiple `episode_ids`.

**Tech Stack:** Next.js, React state, Vitest Testing Library, Playwright visual snapshots.

---

### Task 1: Regression Tests

**Files:**
- Modify: `frontend/tests/workbench.test.tsx`

- [ ] **Step 1: Write failing tests**

Add tests that verify:

```ts
test("sends manually selected episode ids", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());
  fireEvent.click(screen.getByLabelText("demo-002"));
  fireEvent.click(screen.getByRole("button", { name: "Run selected" }));
  await waitFor(() => expect(runBodies[0].episode_ids).toEqual(["demo-001", "demo-002"]));
});

test("uses the first N episodes when no manual selection exists", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());
  fireEvent.click(screen.getByLabelText("demo-001"));
  fireEvent.change(screen.getByLabelText("Test count"), { target: { value: "2" } });
  fireEvent.click(screen.getByRole("button", { name: "Run selected" }));
  await waitFor(() => expect(runBodies[0].episode_ids).toEqual(["demo-001", "demo-002"]));
});

test("switches interface labels to Chinese", async () => {
  render(<Page />);
  fireEvent.change(screen.getByLabelText("Language"), { target: { value: "zh" } });
  expect(screen.getByText("测试模式")).toBeInTheDocument();
});

test("formats latex-heavy question text for display", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2 3")).toBeInTheDocument());
  expect(screen.queryByText(/begin\{tabular\}/)).not.toBeInTheDocument();
  expect(screen.getByText("A. 38")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify red**

Run: `bun run test -- --run tests/workbench.test.tsx`

Expected: fails because controls and formatter do not exist yet.

### Task 2: Formatter and I18n Helpers

**Files:**
- Create: `frontend/lib/i18n.ts`
- Create: `frontend/lib/formatMathText.ts`
- Create: `frontend/components/FormattedMathText.tsx`

- [ ] **Step 1: Implement copy dictionary**

Create English and Chinese UI labels with stable keys for topbar text, language, provider labels, testing mode, episode selection, buttons, statuses, and loading text.

- [ ] **Step 2: Implement text normalizer**

Create `formatMathText(text: string): string` with the rules from the design spec.

- [ ] **Step 3: Implement display component**

Create `FormattedMathText` that splits normalized text on newlines and renders each line without raw LaTeX syntax.

### Task 3: Workbench Controls

**Files:**
- Modify: `frontend/components/EpisodeWorkbench.tsx`
- Modify: `frontend/components/ApiConfigPanel.tsx`
- Modify: `frontend/components/ResultsPanel.tsx`
- Modify: `frontend/components/ThemeToggle.tsx`
- Modify: `frontend/app/globals.css`

- [ ] **Step 1: Add language state**

Add `language` state in `EpisodeWorkbench`, derive `copy`, and pass translated labels to child components.

- [ ] **Step 2: Add multi-select and count state**

Replace `selectedEpisodeId` with `selectedEpisodeIds`, `activeEpisodeId`, and `testCount`. Build run ids with manual selection first, otherwise first `testCount` episodes.

- [ ] **Step 3: Replace question rendering**

Use `FormattedMathText` for `episode.problem.text`, option labels, SCS fallback labels, and scaffold fallback labels where needed.

- [ ] **Step 4: Update styles**

Add compact `.episode-picker`, `.checkbox-row`, `.control-row`, and `.formatted-text` styles with fixed max heights and safe word wrapping.

### Task 4: Verification and Push

**Files:**
- Update visual snapshots if layout changes are intended.

- [ ] **Step 1: Run frontend tests**

Run: `bun run test -- --run`

Expected: all tests pass.

- [ ] **Step 2: Run TypeScript**

Run: `bunx tsc --noEmit`

Expected: exit 0.

- [ ] **Step 3: Run backend tests**

Run: `pytest backend/tests -q`

Expected: all tests pass.

- [ ] **Step 4: Run visual regression**

Run: `bun run visual`

Expected: pass, or update snapshots after inspecting actual images.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add docs/superpowers frontend
git commit -m "feat: improve workbench selection and formatting"
git push
```
