import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import Page from "../app/page";

let providerTestBodies: Array<Record<string, unknown>> = [];
let runBodies: Array<Record<string, unknown>> = [];

beforeEach(() => {
  let eventsCalls = 0;
  providerTestBodies = [];
  runBodies = [];
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
              problem_preview: "Table question",
              scaffold_turns: 1,
            },
            {
              episode_id: "demo-002",
              question_id: 104615,
              intervention_id: 11,
              problem_preview: "Rounding question",
              scaffold_turns: 2,
            },
            {
              episode_id: "demo-003",
              question_id: 104616,
              intervention_id: 12,
              problem_preview: "Fraction question",
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
            text:
              "\\begin{tabular}{llll} \\( x \\) & \\( 0 \\) & \\( 1 \\) & \\( 2 \\) \\\\ \\( y \\) & \\( 5 \\) & \\(\\space\\) & \\(\\color{gold}\\bigstar\\) \\end{tabular}",
            answer_options: [
              { label: "A", text: "\\( 38 \\)" },
              { label: "B", text: "\\( \\frac{11}{16} \\)" },
            ],
          },
          lcs: {
            scs: { visible_learner_profile: "Year 7 learner" },
            scaffold_sequence: [{ message: "Tutor hint" }],
          },
        }),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/episodes/demo-002") || textUrl.endsWith("/api/episodes/demo-003")) {
      const episodeId = textUrl.endsWith("demo-002") ? "demo-002" : "demo-003";
      return new Response(
        JSON.stringify({
          episode_id: episodeId,
          problem: {
            text: episodeId === "demo-002" ? "Rounding question" : "Fraction question",
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
      runBodies.push(JSON.parse(String(init?.body)));
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
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());
});


test("runs the selected mock episode and renders trajectory and scores", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

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
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Test connections" }));

  await waitFor(() => expect(screen.getByText("Student API: connection ok")).toBeInTheDocument());
  expect(screen.getByText("Judge API: connection ok")).toBeInTheDocument();
});


test("uses the provider default base URL when switching presets", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

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


test("sends manually selected episode ids", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

  fireEvent.click(screen.getByLabelText("demo-001"));
  fireEvent.click(screen.getByLabelText("demo-002"));
  fireEvent.click(screen.getByRole("button", { name: "Run selected" }));

  await waitFor(() => expect(runBodies).toHaveLength(1));
  expect(runBodies[0].episode_ids).toEqual(["demo-001", "demo-002"]);
});


test("uses the first N episodes when no manual selection exists", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

  fireEvent.change(screen.getByLabelText("Test count"), { target: { value: "2" } });
  fireEvent.click(screen.getByRole("button", { name: "Run selected" }));

  await waitFor(() => expect(runBodies).toHaveLength(1));
  expect(runBodies[0].episode_ids).toEqual(["demo-001", "demo-002"]);
});


test("switches interface labels to Chinese", async () => {
  render(<Page />);
  fireEvent.change(screen.getByLabelText("Language"), { target: { value: "zh" } });

  expect(screen.getByText("测试模式")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "测试连接" })).toBeInTheDocument();
});


test("formats latex-heavy question text for display", async () => {
  render(<Page />);

  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());
  expect(screen.getByText("y 5 star")).toBeInTheDocument();
  expect(screen.queryByText(/begin\{tabular\}/)).not.toBeInTheDocument();
  expect(screen.queryByText(/\\\(/)).not.toBeInTheDocument();
  expect(screen.getByText("A. 38")).toBeInTheDocument();
  expect(screen.getByText("B. 11/16")).toBeInTheDocument();
});
