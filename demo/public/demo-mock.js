// Browser mock — mirrors demo/orchestration/mockPipeline.js (no server required)

export async function runClientMock(guestMessage, onStage) {
  const msg = String(guestMessage).toLowerCase();
  const state = { guestMessage };

  const stages = [
    {
      id: "classify-intent",
      key: "classification",
      run() {
        const urgent = /urgent|asap|locked out|no heat|leak|flood|emergency/.test(msg);
        const booking = /book|reserv|check.?in|check.?out|availability|available|dates/.test(msg);
        const maintenance = /broken|repair|fix|maintenance|wifi|ac |heat/.test(msg);
        let intent = "general_question";
        if (urgent) intent = "urgent_ops";
        else if (booking) intent = "booking_inquiry";
        else if (maintenance) intent = "maintenance_request";
        return {
          intent,
          urgency: urgent ? "high" : booking ? "medium" : "low",
          needsHuman: urgent || /refund|charge|legal|complaint/.test(msg),
          confidence: urgent ? 0.72 : 0.88,
        };
      },
    },
    {
      id: "plan-tasks",
      key: "plan",
      run() {
        const intent = state.classification.intent;
        const tasks = [{ id: "t1", agent: "triage", action: "log_inquiry", tool: "ops_log" }];
        if (intent === "booking_inquiry") {
          tasks.push(
            { id: "t2", agent: "booking", action: "check_calendar", tool: "calendar_api" },
            { id: "t3", agent: "comms", action: "draft_availability_reply", tool: "llm_draft" },
          );
        } else if (intent === "maintenance_request") {
          tasks.push(
            { id: "t2", agent: "ops", action: "create_ticket", tool: "maintenance_queue" },
            { id: "t3", agent: "comms", action: "acknowledge_eta", tool: "llm_draft" },
          );
        } else if (intent === "urgent_ops") {
          tasks.push(
            { id: "t2", agent: "ops", action: "page_on_call", tool: "sms_escalation" },
            { id: "t3", agent: "comms", action: "hold_auto_reply", tool: "llm_draft" },
          );
        } else {
          tasks.push({ id: "t2", agent: "comms", action: "draft_faq_reply", tool: "llm_draft" });
        }
        return { tasks, estimatedToolCalls: tasks.length };
      },
    },
    {
      id: "draft-response",
      key: "response",
      run() {
        const { needsHuman, intent, urgency } = state.classification;
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
        return {
          draft,
          approvalRequired: needsHuman || urgency === "high",
          suggestedTags: [intent, urgency],
        };
      },
    },
  ];

  for (const stage of stages) {
    onStage(stage.id, "running");
    await new Promise((r) => setTimeout(r, 320));
    state[stage.key] = stage.run();
    onStage(stage.id, "done");
  }

  return { mode: "mock-client", result: state };
}
