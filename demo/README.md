# Guest triage orchestration demo

Minimal 3-stage LLM pipeline (classify → plan → draft) using the same `runPipeline` pattern as [Infinite-Summoner](https://github.com/blopit/Infinite-Summoner) `frontend/forge-engine/runPipeline.js`.

## Run locally

```bash
cd demo
npm install
npm start
```

Open http://localhost:3099

- **Mock mode** — no API key, deterministic outputs (~1s)
- **Live mode** — set `OPENAI_API_KEY` in `demo/.env` (uses `gpt-4o-mini`, typically &lt; $0.01 per run)

## Deploy

Serve the `demo/` folder behind any Node host, or run alongside your static site with a reverse proxy to port 3099.
