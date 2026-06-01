// Linear pipeline dispatcher — adapted from Infinite-Summoner/frontend/forge-engine/runPipeline.js

import { renderPrompt } from "./renderPrompt.js";

export async function runPipeline(spec, input, ctx, progress = {}) {
  if (!spec?.pipeline?.length) throw new Error("runPipeline: spec.pipeline required");
  const state = { ...(input || {}) };

  for (const stage of spec.pipeline) {
    if (stage.runIf) {
      const value = resolveStateKey(state, stage.runIf);
      const passes = stage.runIfEquals !== undefined ? value === stage.runIfEquals : !!value;
      if (!passes) continue;
    }

    progress.currentStage = stage.id;
    progress.updatedAt = Date.now();

    const exec = STAGE_EXECUTORS[stage.type];
    if (!exec) throw new Error(`Unknown stage type: ${stage.type}`);
    const value = await exec({ spec, stage, state, ctx, progress });
    if (stage.outputKey) state[stage.outputKey] = value;

    progress.stages = progress.stages || {};
    progress.stages[stage.id] = { status: "done", at: Date.now(), output: value };
  }

  progress.currentStage = null;
  progress.updatedAt = Date.now();
  return state;
}

const STAGE_EXECUTORS = {
  "llm.prompt": llmPromptStage,
};

function resolveStateKey(state, key) {
  const path = String(key).split(".");
  let cur = state;
  for (const seg of path) {
    if (cur == null || typeof cur !== "object") return undefined;
    cur = cur[seg];
  }
  return cur;
}

function buildVars(stage, state) {
  const vars = {};
  for (const [k, v] of Object.entries(state)) {
    if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
      vars[k] = String(v);
    }
  }
  if (stage.inputs) {
    for (const [localName, stateKey] of Object.entries(stage.inputs)) {
      const v = resolveStateKey(state, stateKey);
      vars[localName] = v == null ? "" : typeof v === "string" ? v : JSON.stringify(v);
    }
  }
  return vars;
}

function buildMessages(spec, stage, state) {
  const { system, user } = renderPrompt(spec, stage.promptId, buildVars(stage, state));
  const messages = [];
  if (system) messages.push({ role: "system", content: system });
  if (user) messages.push({ role: "user", content: user });
  return messages;
}

async function llmPromptStage({ spec, stage, state, ctx }) {
  if (typeof ctx.chatJson !== "function") {
    throw new Error("ctx.chatJson required for llm.prompt");
  }
  const messages = buildMessages(spec, stage, state);
  return ctx.chatJson(messages, stage.modelOpts || {});
}
