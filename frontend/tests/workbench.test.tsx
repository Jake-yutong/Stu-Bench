import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import Page from "../app/page";

let providerTestBodies: Array<Record<string, unknown>> = [];
let runBodies: Array<Record<string, unknown>> = [];
let releaseRunCompletion: (() => void) | null = null;

beforeEach(() => {
  let eventsCalls = 0;
  let lastRunEpisodeIds: string[] = ["demo-001"];
  releaseRunCompletion = null;
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
      const runBody = JSON.parse(String(init?.body));
      runBodies.push(runBody);
      lastRunEpisodeIds = runBody.episode_ids as string[];
      return new Response(
        JSON.stringify({
          run_id: "run-demo",
          status: "queued",
          total: lastRunEpisodeIds.length,
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
      const firstResult = {
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
          lrs: 0.78,
          isf: 0.76,
          ma: 0.74,
          su: 0.8,
          ktc: 0.72,
          occ: 0.83,
          judge_rationale: "Mock judge rationale",
          formula_metrics: {
            kts: 0.72,
            uptake: 0.8,
            over_improve: 0.17,
            status: "judge_estimated",
          },
        },
      };
      const secondResult = {
        episode_id: "demo-002",
        status: "succeeded",
        generated_trajectory: [
          {
            turn_index: 1,
            tutor_message: "Tutor hint for rounding",
            student_response: "I would round to the nearest ten.",
          },
        ],
        judge_scores: {
          lrs: 0.91,
          isf: 0.9,
          ma: 0.88,
          su: 0.9,
          ktc: 0.88,
          occ: 0.91,
          judge_rationale: "Second judge rationale",
          formula_metrics: {
            kts: 0.88,
            uptake: 0.9,
            over_improve: 0.09,
            status: "judge_estimated",
          },
        },
      };
      if (lastRunEpisodeIds.length > 1) {
        if (eventsCalls === 1) {
          return new Response(
            JSON.stringify({
              run_id: "run-demo",
              status: "running",
              total: 2,
              completed: 0,
              current_episode_id: "demo-001",
              results: [],
            }),
            { status: 200 },
          );
        }
        if (eventsCalls === 2) {
          return new Response(
            JSON.stringify({
              run_id: "run-demo",
              status: "running",
              total: 2,
              completed: 1,
              current_episode_id: "demo-002",
              results: [firstResult],
            }),
            { status: 200 },
          );
        }

        return new Promise<Response>((resolve) => {
          releaseRunCompletion = () =>
            resolve(
              new Response(
                JSON.stringify({
                  run_id: "run-demo",
                  status: "completed",
                  total: 2,
                  completed: 2,
                  current_episode_id: null,
                  results: [firstResult, secondResult],
                }),
                { status: 200 },
              ),
            );
        });
      }
      return new Response(
        JSON.stringify(
          eventsCalls === 1
            ? {
                run_id: "run-demo",
                status: "running",
                total: 1,
                completed: 0,
                current_episode_id: "demo-001",
                results: [],
              }
            : {
                run_id: "run-demo",
                status: "completed",
                total: 1,
                completed: 1,
                current_episode_id: null,
                results: [firstResult],
              },
        ),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/runs/run-demo/export.json")) {
      return new Response(
        JSON.stringify({
          run_id: "run-demo",
          results: [
            {
              episode_id: "demo-001",
              status: "succeeded",
              generated_trajectory: [],
              judge_scores: {
                lrs: 0.78,
                isf: 0.76,
                ma: 0.74,
                su: 0.8,
                ktc: 0.72,
                occ: 0.83,
                judge_rationale: "Mock judge rationale",
                formula_metrics: {
                  kts: 0.72,
                  uptake: 0.8,
                  over_improve: 0.17,
                  status: "judge_estimated",
                },
              },
            },
          ],
        }),
        { status: 200 },
      );
    }
    if (textUrl.endsWith("/api/runs/run-demo")) {
      return new Response(
        JSON.stringify({
          run_id: "run-demo",
          results:
            lastRunEpisodeIds.length > 1
              ? [
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
                      lrs: 0.78,
                      isf: 0.76,
                      ma: 0.74,
                      su: 0.8,
                      ktc: 0.72,
                      occ: 0.83,
                      judge_rationale: "Mock judge rationale",
                      formula_metrics: {
                        kts: 0.72,
                        uptake: 0.8,
                        over_improve: 0.17,
                        status: "judge_estimated",
                      },
                    },
                  },
                  {
                    episode_id: "demo-002",
                    status: "succeeded",
                    generated_trajectory: [
                      {
                        turn_index: 1,
                        tutor_message: "Tutor hint for rounding",
                        student_response: "I would round to the nearest ten.",
                      },
                    ],
                    judge_scores: {
                      lrs: 0.91,
                      isf: 0.9,
                      ma: 0.88,
                      su: 0.9,
                      ktc: 0.88,
                      occ: 0.91,
                      judge_rationale: "Second judge rationale",
                      formula_metrics: {
                        kts: 0.88,
                        uptake: 0.9,
                        over_improve: 0.09,
                        status: "judge_estimated",
                      },
                    },
                  },
                ]
              : [
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
                      lrs: 0.78,
                      isf: 0.76,
                      ma: 0.74,
                      su: 0.8,
                      ktc: 0.72,
                      occ: 0.83,
                      judge_rationale: "Mock judge rationale",
                      formula_metrics: {
                        kts: 0.72,
                        uptake: 0.8,
                        over_improve: 0.17,
                        status: "judge_estimated",
                      },
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
  vi.useRealTimers();
  cleanup();
});

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
  });
}


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
  expect(screen.getByText("LRS")).toBeInTheDocument();
  expect(screen.getByText("0.780")).toBeInTheDocument();
  expect(screen.getByText("OCC")).toBeInTheDocument();
  expect(screen.queryByText("Trajectory")).not.toBeInTheDocument();
  expect(screen.queryByText("OverImprove")).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Export CSV" })).toHaveAttribute(
    "href",
    "http://localhost:8000/api/runs/run-demo/export.csv",
  );
  fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
  await waitFor(() => expect(screen.getByRole("dialog", { name: "Export JSON" })).toBeInTheDocument());
  expect(screen.getByText(/\"run_id\": \"run-demo\"/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Close" }));
  expect(screen.queryByRole("dialog", { name: "Export JSON" })).not.toBeInTheDocument();
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


test("fills local vLLM defaults for SFT and DPO student presets", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

  const studentProvider = screen.getByLabelText("Student provider");
  const baseUrlInputs = screen.getAllByLabelText("Base URL") as HTMLInputElement[];
  const modelInputs = screen.getAllByLabelText("Model") as HTMLInputElement[];

  fireEvent.change(studentProvider, { target: { value: "local-vllm-sft" } });
  expect(baseUrlInputs[0].value).toBe("http://127.0.0.1:8010/v1");
  expect(modelInputs[0].value).toBe("eedi-stud-sft-8b");

  fireEvent.change(studentProvider, { target: { value: "local-vllm-dpo" } });
  expect(baseUrlInputs[0].value).toBe("http://127.0.0.1:8010/v1");
  expect(modelInputs[0].value).toBe("eedi-stud-dpo-8b");

  fireEvent.click(screen.getByRole("button", { name: "Test connections" }));

  await waitFor(() => expect(providerTestBodies).toHaveLength(2));
  expect(providerTestBodies[0]).toEqual(
    expect.objectContaining({
      preset: "local-vllm-dpo",
      base_url: "http://127.0.0.1:8010/v1",
      model: "eedi-stud-dpo-8b",
    }),
  );
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


test("streams multi-episode progress and displays the active result scores", async () => {
  render(<Page />);
  await waitFor(() => expect(screen.getByText("x 0 1 2")).toBeInTheDocument());

  vi.useFakeTimers();
  await act(async () => {
    fireEvent.change(screen.getByLabelText("Test count"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Run selected" }));
  });
  await flushAsyncWork();

  expect(screen.getByText("running: 0/2")).toBeInTheDocument();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  await flushAsyncWork();

  expect(screen.getByText("running: 1/2")).toBeInTheDocument();
  expect(screen.getAllByText("Rounding question").length).toBeGreaterThan(0);
  expect(screen.getByText("Student: I would inspect the next digit.")).toBeInTheDocument();
  expect(screen.getByText("Mock judge rationale")).toBeInTheDocument();
  expect(screen.getByText("0.780")).toBeInTheDocument();

  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(releaseRunCompletion).toBeTruthy();
  await act(async () => {
    releaseRunCompletion?.();
  });
  await flushAsyncWork();

  expect(screen.getByText("completed: 2/2")).toBeInTheDocument();
  expect(screen.getByText("Student: I would round to the nearest ten.")).toBeInTheDocument();
  expect(screen.getByText("Second judge rationale")).toBeInTheDocument();
  expect(screen.getAllByText("0.910").length).toBeGreaterThan(0);
});
