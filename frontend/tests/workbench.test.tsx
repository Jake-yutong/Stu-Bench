import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import Page from "../app/page";

let providerTestBodies: Array<Record<string, unknown>> = [];

beforeEach(() => {
  let eventsCalls = 0;
  providerTestBodies = [];
  global.fetch = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
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
          status: "queued",
          total: 1,
          completed: 0,
        }),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/providers/test")) {
      providerTestBodies.push(JSON.parse(String(init?.body)));
      return new Response(JSON.stringify({ ok: true, sample: "connection ok" }), {
        status: 200,
      });
    }
    if (textUrl.endsWith("/api/runs/run-demo/events")) {
      eventsCalls += 1;
      return new Response(
        JSON.stringify(
          eventsCalls === 1
            ? {
                run_id: "run-demo",
                status: "running",
                total: 1,
                completed: 0,
                current_episode_id: "demo-001",
              }
            : {
                run_id: "run-demo",
                status: "completed",
                total: 1,
                completed: 1,
                current_episode_id: null,
              },
        ),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/runs/run-demo")) {
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

  await waitFor(() => expect(screen.getByText("running: 0/1")).toBeInTheDocument());
  await waitFor(() =>
    expect(screen.getByText("Student: I would inspect the next digit.")).toBeInTheDocument(),
  );
  expect(screen.getByText("Mock judge rationale")).toBeInTheDocument();
  expect(screen.getByText("78")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Export CSV" })).toHaveAttribute(
    "href",
    "http://localhost:8000/api/runs/run-demo/export.csv",
  );
  expect(screen.getByRole("link", { name: "Export JSON" })).toHaveAttribute(
    "href",
    "http://localhost:8000/api/runs/run-demo/export.json",
  );
});


test("tests both provider connections", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Test connections" }));

  await waitFor(() => expect(screen.getByText("Student API: connection ok")).toBeInTheDocument());
  expect(screen.getByText("Judge API: connection ok")).toBeInTheDocument();
});


test("uses the provider default base URL when switching presets", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("Rounding question")).toBeInTheDocument());

  fireEvent.change(screen.getByLabelText("Student provider"), { target: { value: "qwen" } });
  fireEvent.change(screen.getByLabelText("Judge provider"), { target: { value: "qwen" } });
  fireEvent.click(screen.getByRole("button", { name: "Test connections" }));

  await waitFor(() => expect(providerTestBodies).toHaveLength(2));
  expect(providerTestBodies).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        preset: "qwen",
        base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      }),
    ]),
  );
  expect(providerTestBodies.every((body) => body.base_url !== "mock://local")).toBe(true);
});
