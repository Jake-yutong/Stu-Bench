import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import Page from "../app/page";


test("renders the three-column Stu-Bench workbench controls", () => {
  render(<Page />);
  expect(screen.getByText("Stu-Bench Demo")).toBeInTheDocument();
  expect(screen.getByLabelText("Student provider")).toBeInTheDocument();
  expect(screen.getByLabelText("Judge provider")).toBeInTheDocument();
  expect(screen.getByLabelText("Testing mode")).toBeInTheDocument();
  expect(screen.getByText("Episode")).toBeInTheDocument();
  expect(screen.getByText("Results")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Run selected" })).toBeInTheDocument();
});
