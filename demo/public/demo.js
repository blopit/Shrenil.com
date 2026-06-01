import { runClientMock } from "./demo-mock.js";

const SAMPLES = {
  booking:
    "Hi! We're a family of 4 looking to stay Dec 12–15. Is your 2-bedroom available and what's the total with cleaning fee?",
  maintenance:
    "The unit AC stopped working last night — it's pretty warm in here. Can someone come tomorrow morning?",
  urgent:
    "URGENT: We're locked out of the rental and there's no one at the office. Please call ASAP.",
};

const STAGE_ORDER = ["classify-intent", "plan-tasks", "draft-response"];

const $ = (sel) => document.querySelector(sel);
const messageEl = $("#guestMessage");
const outputEl = $("#outputJson");
const statusEl = $("#status");
const runBtn = $("#runBtn");
const steps = [...document.querySelectorAll("#pipelineSteps li")];

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

function setStepState(stageId, state) {
  const li = steps.find((el) => el.dataset.stage === stageId);
  if (!li) return;
  li.classList.remove("pending", "running", "done");
  li.classList.add(state);
}

function resetSteps() {
  STAGE_ORDER.forEach((id) => setStepState(id, "pending"));
}

async function checkHealth() {
  try {
    const res = await fetch("/api/demo/health");
    const data = await res.json();
    if (!data.liveAvailable) {
      setStatus("Mock works in-browser. Live LLM: cd demo && npm start, set OPENAI_API_KEY in demo/.env");
    } else {
      setStatus("Demo server connected — mock (free) or live gpt-4o-mini available.");
    }
    return data;
  } catch {
    setStatus("Mock runs in-browser (no server). For live LLM: cd demo && npm install && npm start");
    return null;
  }
}

document.querySelectorAll(".sample").forEach((btn) => {
  btn.addEventListener("click", () => {
    messageEl.value = SAMPLES[btn.dataset.sample] || "";
  });
});

runBtn.addEventListener("click", async () => {
  const guestMessage = messageEl.value.trim();
  if (!guestMessage) {
    setStatus("Enter a guest message first.", true);
    return;
  }

  const mode = document.querySelector('input[name="mode"]:checked')?.value || "mock";
  runBtn.disabled = true;
  resetSteps();
  setStepState(STAGE_ORDER[0], "running");
  setStatus(`Running ${mode} pipeline…`);
  outputEl.textContent = "…";

  try {
    let data;
    const useClientMock = mode === "mock";

    if (useClientMock) {
      resetSteps();
      let idx = 0;
      const clientData = await runClientMock(guestMessage, (stageId, st) => {
        if (st === "running") {
          STAGE_ORDER.forEach((id, i) => {
            if (i < idx) setStepState(id, "done");
            else if (id === stageId) setStepState(id, "running");
            else setStepState(id, "pending");
          });
        } else {
          setStepState(stageId, "done");
          idx = STAGE_ORDER.indexOf(stageId) + 1;
          if (idx < STAGE_ORDER.length) setStepState(STAGE_ORDER[idx], "running");
        }
      });
      data = {
        mode: "mock",
        result: {
          classification: clientData.result.classification,
          plan: clientData.result.plan,
          response: clientData.result.response,
        },
      };
    } else {
      const res = await fetch("/api/demo/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ guestMessage, mode }),
      });
      data = await res.json();
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      STAGE_ORDER.forEach((id) => setStepState(id, "done"));
    }

    const hitl = data.result?.response?.approvalRequired;
    outputEl.textContent = JSON.stringify(
      {
        mode: data.mode,
        classification: data.result.classification,
        plan: data.result.plan,
        response: data.result.response,
        humanInTheLoop: hitl ? "Approval required before send" : "Auto-send eligible",
      },
      null,
      2,
    );

    setStatus(
      `Done (${data.mode}) · ~${data.result?.plan?.estimatedToolCalls ?? "?"} tool calls · ${
        hitl ? "escalate to human" : "draft ready"
      }`,
    );
  } catch (e) {
    setStatus(e.message, true);
    outputEl.textContent = String(e.message);
    resetSteps();
  } finally {
    runBtn.disabled = false;
  }
});

resetSteps();
checkHealth();
