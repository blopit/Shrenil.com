import express from "express";
import cors from "cors";
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { config as loadEnv } from "dotenv";
import { runPipeline } from "./orchestration/runPipeline.js";
import { runMockPipeline } from "./orchestration/mockPipeline.js";
import { makeOpenAIChatCtx } from "./orchestration/openaiClient.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env"), quiet: true });
loadEnv({ path: join(__dirname, "..", ".env"), quiet: true });

const PORT = Number(process.env.DEMO_PORT || 3099);
const OPENAI_KEY = process.env.OPENAI_API_KEY || "";
const spec = JSON.parse(
  readFileSync(join(__dirname, "orchestration/specs/guest-triage.json"), "utf8"),
);

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(join(__dirname, "public")));

app.get("/api/demo/health", (_, res) => {
  res.json({
    ok: true,
    liveAvailable: OPENAI_KEY.length >= 20,
    spec: spec.id,
    defaultModel: "gpt-4o-mini",
  });
});

app.post("/api/demo/orchestrate", async (req, res) => {
  const guestMessage = String(req.body?.guestMessage || "").trim();
  const mode = req.body?.mode === "live" ? "live" : "mock";
  const propertyContext = String(
    req.body?.propertyContext || "20-unit + 3-unit residential / short-stay portfolio, GTA",
  );

  if (!guestMessage) {
    return res.status(400).json({ error: "guestMessage required" });
  }

  const input = { guestMessage, propertyContext };
  const progress = { stages: {} };

  try {
    let state;
    if (mode === "live") {
      if (!OPENAI_KEY) {
        return res.status(503).json({
          error: "OPENAI_API_KEY not set — use mock mode or add key to demo/.env",
        });
      }
      const ctx = makeOpenAIChatCtx(OPENAI_KEY);
      state = await runPipeline(spec, input, ctx, progress);
      progress.mode = "live";
    } else {
      state = await runMockPipeline(spec, input, progress);
      progress.mode = "mock";
    }

    res.json({
      ok: true,
      mode: progress.mode,
      progress,
      result: {
        classification: state.classification,
        plan: state.plan,
        response: state.response,
      },
    });
  } catch (e) {
    console.error("[demo]", e);
    res.status(500).json({ error: e.message || "orchestration failed" });
  }
});

app.listen(PORT, () => {
  console.log(`[demo] http://localhost:${PORT}  (live=${OPENAI_KEY ? "yes" : "mock only"})`);
});
