import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import Page from "../app/page";


beforeEach(() => {
  global.fetch = vi.fn(async (url: RequestInfo | URL) => {
    const textUrl = String(url);
    if (textUrl.endsWith("/api/episodes")) {
      return new Response(
        JSON.stringify({
          episodes: [
            {
              episode_id: "demo-001",
              question_id: 104614,
              intervention_id: 10,
              problem_preview: "Rounding question",
              scaffold_turns: 1,
            },
          ],
        }),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/episodes/demo-001")) {
      return new Response(
        JSON.stringify({
          episode_id: "demo-001",
          problem: {
            text: "Rounding question",
            answer_options: [{ label: "A", text: "Only Alex" }],
          },
          lcs: {
            scs: { visible_learner_profile: "Year 7 learner" },
            scaffold_sequence: [{ message: "Tutor hint" }],
          },
        }),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/runs")) {
      return new Response(
        JSON.stringify({
          run_id: "run-demo",
          results: [
            {
              episode_id: "demo-001",
              status: "succeeded",
              generated_trajectory: [
                {
                  turn_index: 1,
                  tutor_message: "Tutor hint",
                  student_response: "I would inspect the next digit.",
                },
              ],
              judge_scores: {
                overall_realism: 78,
                judge_rationale: "Mock judge rationale",
              },
            },
          ],
        }),
        { status: 200 },
      );
    }
    return new Response("{}", { status: 200 });
  }) as typeof fetch;
});

afterEach(() => {
  cleanup();
});


test("loads episode summaries from the backend", async () => {
  render(<Page />);
  expect(screen.getByText("Stu-Bench Demo")).toBeInTheDocument();
  expect(screen.getByLabelText("Student provider")).toBeInTheDocument();
  expect(screen.getByLabelText("Judge provider")).toBeInTheDocument();
  expect(screen.getByLabelText("Testing mode")).toBeInTheDocument();
  expect(screen.getAllByText("Episode").length).toBeGreaterThan(0);
  expect(screen.getByText("Results")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Run selected" })).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());
});


test("runs the selected mock episode and renders trajectory and scores", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Run selected" }));

  await waitFor(() =>
    expect(screen.getByText("Student: I would inspect the next digit.")).toBeInTheDocument(),
  );
  expect(screen.getByText("Mock judge rationale")).toBeInTheDocument();
  expect(screen.getByText("78")).toBeInTheDocument();
});
