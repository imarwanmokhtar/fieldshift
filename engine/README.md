# Field Shift engine (Python / FastAPI)

The engine computes; the LLM only explains. All numbers, scores and rankings come
from this code. The LLM gets a fixed evidence pack and may only rephrase it.

```
Next.js POST /api/analyze ─▶ engine POST /analyze (202) ─▶ background run_analysis()
   1 load field_profiles (service role)       5 build the evidence pack
   2 NASA POWER climate (cached)              6 LLM text (or template text) in ar/en
   3 features: hot days, ET0, crop water      7 save result + narrative to `analyses`
   4 score 3+ rotations from your priorities
```

## Run it on Windows (PowerShell)

```powershell
cd engine
py -m venv .venv
.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements-dev.txt
python -m pytest                    # 15 tests, all offline
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/health. It should show `"ok": true` and `"supabase": true`.

Then in a second terminal at the project root: `npm run dev`. The Next.js app finds
the engine through `ENGINE_URL` and `ENGINE_API_KEY` in `.env.local` (the key must
match `ENGINE_API_KEY` in `engine/.env`).

macOS / Linux: same steps with `python3 -m venv .venv` and `source .venv/bin/activate`.

## One-time setup

1. **Supabase:** run `supabase/migrations/002_analyses.sql` in the Supabase SQL editor.
2. **Secrets:** `engine/.env` (never commit it; copy `.env.example` for a new machine).
   - LLM: set `GEMINI_API_KEY` (Gemini 3.8 Flash, `LLM_PROVIDER=gemini`) or `ANTHROPIC_API_KEY` (Claude). With no key, explanations use built-in templates (English and Arabic).
   - `COPERNICUS_CLIENT_ID` / `SECRET` empty: the Sentinel-2 NDVI layer is skipped.
   - `USE_MOCK_LAYERS=true`: NDVI, SMAP and IMERG return demo values, clearly labelled "mock" in the results.

## Quick checks

```powershell
# Live NASA POWER call for a Dakahlia point (should print a number of days)
python -c "from app.data.power import fetch_power; print(len(fetch_power(31.04, 31.38)))"

# Full analysis of sample answers, no database needed
python -c "from tests.test_engine import ANSWERS; from app.pipeline import analyze_answers; p,n=analyze_answers(ANSWERS,'ar'); print(p.recommended_id); print(n.overview)"
```

## What is real and what is not yet

| Part | Status |
| --- | --- |
| NASA POWER daily climate (live, cached in `.cache/`) | Real. If unreachable, a bundled approximate climatology is used and flagged as low confidence |
| Hot days, temperature trend, ET0 (FAO-56 Penman-Monteith, Hargreaves fallback), rainfall | Real formulas |
| Crop water need, heat stress at the sensitive stage, growing degree days | Real formulas on `crops.json` values |
| `crops.json` agronomy (Kc, dates, tolerances, income/cost indices) | **Illustrative, TODO-verify** with an agronomist or your research plan |
| Strategy generation, constraints, weighted scoring, confidence | Real |
| Evidence pack, LLM step, number check, retry, template fallback | Real |
| Sentinel-2 NDVI (Copernicus Statistical API) | Written but untested: needs your Copernicus OAuth client |
| GAEZ / SMAP / IMERG raster sampling | Code ready; put GeoTIFFs in `data/` (`gaez_<crop>.tif`, `smap_anomaly.tif`, `imerg_trend.tif`) and `pip install -r requirements-data.txt` |

## API

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | none | status, which LLM is active, which keys are set |
| POST | `/analyze` | `X-API-Key` | `{analysis_id, user_id, lang?}` → 202, runs in the background |
| POST | `/compare` | `X-API-Key` | `{user_id, crop, season?}` → the farmer's own crop scored next to their current rotation and the best option |

## Files

```
app/main.py         FastAPI endpoints
app/settings.py     environment variables (.env)
app/schemas.py      pydantic models: profile, strategy, evidence pack, narrative
app/profile.py      onboarding answers -> FarmProfile ("unknown" handling)
app/db.py           Supabase REST with the service role key
app/pipeline.py     run_analysis(): steps 1-7
app/data/power.py   NASA POWER client, cache, fallback, hotter/drier scenario
app/data/ndvi.py    Sentinel-2 NDVI (Copernicus)
app/data/raster.py  GAEZ / SMAP / IMERG raster sampling
app/data/cache.py   disk cache
app/features.py     climate, ET0, crop water/heat, NDVI features
app/crops.json      crop knowledge table (TODO-verify)
app/strategies.py   candidates, constraints, scoring, selection, "my own crop" comparison
app/evidence.py     evidence pack + confidence
app/texts.py        English + Arabic text for every fact
app/llm.py          prompt, call, validation, number check, fallback
```

## Deploy on Vercel (free, no card)

Create a second Vercel project from the same GitHub repo with **Root Directory = `engine`**.
Vercel loads `index.py` (which imports `app.main:app`), reads `requirements.txt`, and
`vercel.json` gives the function up to 90 s. On Vercel the engine runs in sync mode
(`ENGINE_SYNC`, automatic): `/analyze` finishes the analysis before replying. Add the same
environment variables as in `.env`, then set `ENGINE_URL` in the website project to this
project's URL.

## Deploy with Docker (Render / Railway / Fly.io)

`Dockerfile` is ready for Render / Railway / Fly.io. Set the same variables as in
`.env`, then set `ENGINE_URL` in Vercel to the public engine URL. Free tiers sleep:
open `/health` a few minutes before a demo.
