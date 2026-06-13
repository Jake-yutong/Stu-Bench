import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import Page from "../app/page";


test("renders the Stu-Bench workbench title", () => {
  render(<Page />);
  expect(screen.getByText("Stu-Bench Demo")).toBeInTheDocument();
  expect(screen.getByText("Student API")).toBeInTheDocument();
  expect(screen.getByText("Judge API")).toBeInTheDocument();
});
