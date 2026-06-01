// Deterministic mock — same stage IDs as guest-triage.json, zero API cost.

function lower(s) {
  return String(s || "").toLowerCase();
}

export async function runMockPipeline(spec, input, progress = {}) {
  const msg = lower(input.guestMessage);
  const state = { ...input };
  progress.stages = {};

  for (const stage of spec.pipeline) {
    progress.currentStage = stage.id;
    progress.updatedAt = Date.now();
    await delay(350);

    let value;
    if (stage.id === "classify-intent") {
      const urgent = /urgent|asap|locked out|no heat|leak|flood|emergency/.test(msg);
      const booking = /book|reserv|check.?in|check.?out|availability|available|dates/.test(msg);
      const maintenance = /broken|repair|fix|maintenance|wifi|ac |heat/.test(msg);
      let intent = "general_question";
      if (urgent) intent = "urgent_ops";
      else if (booking) intent = "booking_inquiry";
      else if (maintenance) intent = "maintenance_request";
      value = {
        intent,
        urgency: urgent ? "high" : booking ? "medium" : "low",
        needsHuman: urgent || /refund|charge|legal|complaint/.test(msg),
        confidence: urgent ? 0.72 : 0.88,
      };
    } else if (stage.id === "plan-tasks") {
      const intent = state.classification?.intent || "general_question";
      const tasks = [
        { id: "t1", agent: "triage", action: "log_inquiry", tool: "ops_log" },
      ];
      if (intent === "booking_inquiry") {
        tasks.push({ id: "t2", agent: "booking", action: "check_calendar", tool: "calendar_api" });
        tasks.push({ id: "t3", agent: "comms", action: "draft_availability_reply", tool: "llm_draft" });
      } else if (intent === "maintenance_request") {
        tasks.push({ id: "t2", agent: "ops", action: "create_ticket", tool: "maintenance_queue" });
        tasks.push({ id: "t3", agent: "comms", action: "acknowledge_eta", tool: "llm_draft" });
      } else if (intent === "urgent_ops") {
        tasks.push({ id: "t2", agent: "ops", action: "page_on_call", tool: "sms_escalation" });
        tasks.push({ id: "t3", agent: "comms", action: "hold_auto_reply", tool: "llm_draft" });
      } else {
        tasks.push({ id: "t2", agent: "comms", action: "draft_faq_reply", tool: "llm_draft" });
      }
      value = { tasks, estimatedToolCalls: tasks.length };
    } else if (stage.id === "draft-response") {
      const needsHuman = state.classification?.needsHuman;
      const intent = state.classification?.intent;
      let draft =
        "Thanks for reaching out — I've logged your message and will follow up shortly with next steps.";
      if (intent === "booking_inquiry") {
        draft =
          "Thanks for your interest! I'll check availability for your dates and send confirmed options within the hour.";
      } else if (intent === "maintenance_request") {
        draft =
          "Sorry about the issue — I've opened a maintenance ticket and will confirm a visit window as soon as possible.";
      } else if (intent === "urgent_ops") {
        draft =
          "We received your urgent message and are escalating to the on-call operator now. Someone will contact you within 15 minutes.";
      }
      value = {
        draft,
        approvalRequired: needsHuman || state.classification?.urgency === "high",
        suggestedTags: [intent, state.classification?.urgency].filter(Boolean),
      };
    }

    if (stage.outputKey) state[stage.outputKey] = value;
    progress.stages[stage.id] = { status: "done", at: Date.now(), output: value, mode: "mock" };
  }

  progress.currentStage = null;
  return state;
}

function delay(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
