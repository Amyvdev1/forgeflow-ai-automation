import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const workflows = [
  {
    id: "customer-triage",
    name: "Customer triage",
    description: "Structure an incoming request for human review.",
    prompt: "Identify the clearest next action.",
    tags: ["support", "review"],
    enabled: true
  }
];

function jsonResponse(payload: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(payload) });
}

describe("ForgeFlow dashboard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((path: string) => {
      if (path === "/api/workflows") return jsonResponse(workflows);
      if (path === "/api/runs") return jsonResponse([]);
      return jsonResponse({
        id: "run-1",
        workflow_id: "customer-triage",
        workflow_name: "Customer triage",
        status: "completed",
        execution_mode: "deterministic",
        input: "Need help with a delayed export.",
        result: {
          summary: "A support request needs human review.",
          priority: "high",
          detected_signals: ["support"],
          recommended_next_action: "Review with the support owner.",
          review_checkpoint: "Confirm the customer context."
        },
        error_message: null,
        created_at: "2026-09-03T00:00:00Z"
      });
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("loads a workflow and presents its explicit execution mode", async () => {
    render(<App />);

    expect(screen.getByText("Reliable automation, designed for review")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: /customer triage/i })).toBeInTheDocument());
    expect(screen.getByText("deterministic preview")).toBeInTheDocument();
    expect(screen.getByText(/does not send anything externally/i)).toBeInTheDocument();
  });

  it("submits an explicit deterministic workflow run", async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => expect(screen.getByRole("button", { name: /customer triage/i })).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /run workflow/i }));

    await waitFor(() => expect(screen.getByText("A support request needs human review.")).toBeInTheDocument());
    expect(fetch).toHaveBeenCalledWith(
      "/api/workflows/customer-triage/runs",
      expect.objectContaining({ method: "POST" })
    );
  });
});
