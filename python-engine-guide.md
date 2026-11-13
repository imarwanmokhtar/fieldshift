# Field Shift: Python engine, frontend connection, and LLM explanations

Status check: landing page, auth and onboarding are done. This guide covers the engine, how the web app talks to it, and how the LLM writes the farmer-facing text.

I have not opened the data portals you linked, so endpoint names, product versions and field names below come from my own knowledge. Verify each one with a single test call before building on it (see the checklist at the end).

---

## 1. The big picture

```
Farmer finishes onboarding
        |
Next.js  POST /api/analyze  (server route, checks login)
        |  creates a row in `analyses` (status = pending)
        |  calls the engine (server to server, secret key)
        v
Python engine (FastAPI)
   1. loads the farmer's answers from Supabase
   2. fetches NASA / Copernicus / GAEZ data for the pin
   3. computes features (heat, water demand, NDVI, suitability)
   4. builds and scores 3+ rotation strategies  (deterministic)
   5. builds an "evidence pack" (JSON)
   6. sends the pack to the LLM -> plain-language text
   7. saves everything to `analyses` (status = done)
        |
Next.js results page polls / subscribes until done, then shows
the strategy cards in the farmer's language
```

**Golden rule: the engine computes, the LLM only explains.** All numbers, scores and rankings come from Python. The LLM gets a fixed JSON pack and may only rephrase it. This keeps results explainable and checkable, which is what the challenge asks for, and it stops the LLM inventing figures.

---

## 2. What to use from each data source

Be honest about resolution. Delta fields are small and canal-irrigated, so the strongest field-level signals are Sentinel-2 NDVI and NASA POWER. SMAP and IMERG are coarse context layers.

| Source | Use it for | How to get it | Resolution caveat |
| --- | --- | --- | --- |
| **NASA POWER** | Temperature, radiation, humidity, wind, rainfall. Gives heat-stress days, growing degree days, water demand (ET0) | Free REST API, no key, point query | Coarse grid (about 0.5 degree), so use for climate, not field detail |
| **Copernicus Data Space (Sentinel-2)** | NDVI time series at the pin: crop cycles, bare periods, vigor trend, cross-check of the farmer's last crops | Free account, then the Sentinel Hub Statistical API (OAuth client credentials) | 10 m. Best field-level signal |
| **FAO GAEZ** | Crop suitability and yield potential per crop at the pin | Download the suitability rasters for Egypt, sample them with `rasterio` | Coarse (about 10 km). Precompute, do not call live |
| **SMAP** (Earthdata) | Regional soil-moisture trend and anomalies | `earthaccess` library, free Earthdata login | 9 km. Context only; irrigation dominates in the Delta |
| **GPM / IMERG** (Earthdata) | Rainfall trend and extreme events | `earthaccess` library | 10 km. Rain is minor in the Delta, so keep it optional |

Practical advice:
- **Live per request:** NASA POWER only (fast, no key). Cache by rounded coordinates.
- **Live but cached:** Sentinel-2 NDVI statistics for the pin. Cache the result per pin.
- **Precomputed for the Dakahlia area:** GAEZ, SMAP and IMERG. Do these tonight and store the results as small GeoTIFF or Parquet files in the repo. Do not depend on large downloads during the demo.
- If you run short on time, cut IMERG first, then SMAP. POWER, NDVI and GAEZ are enough for a strong result.

Accounts and keys to get tonight:
- NASA Earthdata login (for `earthaccess`)
- Copernicus Data Space account and an OAuth client (id and secret)
- An LLM API key
- Supabase service role key (server only, never in Next.js client code)

---

## 3. Engine folder structure

```
engine/
  app/
    main.py            # FastAPI app and /analyze endpoint
    settings.py        # env vars
    schemas.py         # pydantic models: profile, features, strategy, evidence pack
    db.py              # Supabase client (service role)
    pipeline.py        # run_analysis(): orchestrates steps 1-7
    data/
      power.py         # NASA POWER client
      ndvi.py          # Copernicus Sentinel Hub NDVI client
      raster.py        # sample GAEZ / SMAP / IMERG precomputed rasters
      cache.py         # simple disk or SQLite cache
    features.py        # climate + NDVI + water features
    crops.json         # crop knowledge table
    strategies.py      # candidate rotations + scoring
    evidence.py        # builds the evidence pack
    llm.py             # prompt, call, validation, fallback text
  data/                # precomputed rasters (GAEZ, SMAP, IMERG)
  tests/
  requirements.txt
  Dockerfile
```

`requirements.txt` starting point: `fastapi`, `uvicorn`, `httpx`, `pandas`, `numpy`, `pydantic`, `rasterio`, `supabase`, `anthropic`, `earthaccess`, `python-dotenv`.

---

## 4. Pipeline steps with code

### 4.1 NASA POWER (live, no key)

```python
# app/data/power.py
import httpx, pandas as pd

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M"

def fetch_power(lat: float, lng: float, start="20150101", end="20251231") -> pd.DataFrame:
    r = httpx.get(URL, params={
        "parameters": PARAMS, "community": "AG",
        "latitude": round(lat, 2), "longitude": round(lng, 2),
        "start": start, "end": end, "format": "JSON",
    }, timeout=90)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["properties"]["parameter"])
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df.mask(df == -999)          # -999 is POWER's missing value
```

Features to compute from it (`features.py`):
- Hot days per year (for example `T2M_MAX > 35`) and the yearly trend of that count
- Monthly mean temperature and the 10-year trend
- Growing degree days per season window (winter and summer)
- Reference evapotranspiration (ET0) with the FAO-56 Penman-Monteith or the Hargreaves method (the `pyet` package or a short function). Multiply by crop coefficients to get crop water demand per season
- Rainfall totals (small in the Delta, say so in the output)

### 4.2 Sentinel-2 NDVI from Copernicus (live, cached)

Flow:
1. Get a token from the Copernicus identity server with your client id and secret (client credentials grant).
2. Call the Sentinel Hub Statistical API for a small polygon around the pin (for example 60 m square) for the last 2 to 3 years, with a 10-day aggregation and a cloud mask.
3. Return a clean series of `(date, mean NDVI)`.

Then derive:
- **Season peaks:** find the NDVI peaks per year. Two peaks in a year usually means two crop cycles; compare the timing with the farmer's `last_crop` and `prev_crop` answers.
- **Bare periods:** consecutive days below about 0.2 NDVI. This gives the "bare field" months the challenge highlights.
- **Vigor trend:** compare peak NDVI across seasons for the same crop type.
- **Mismatch flag:** if the farmer says wheat last winter but NDVI shows no winter peak, record it as a data gap, not as an error.

Cache the series per pin and test the call with a single request first. Cloud gaps are normal, so interpolate but mark interpolated stretches.

### 4.3 GAEZ, SMAP, IMERG (precomputed rasters)

1. Download the GAEZ crop suitability rasters (irrigated, the relevant input level) for your candidate crops and clip them to Egypt or the Delta.
2. For SMAP, use `earthaccess` to fetch a few years of daily or monthly soil moisture for the Dakahlia bounding box, aggregate to monthly mean and anomaly, and save as one small GeoTIFF or Parquet.
3. IMERG: same idea, monthly totals. Optional.
4. At request time, sample the nearest cell for the pin:

```python
# app/data/raster.py
import rasterio

def sample(path: str, lat: float, lng: float):
    with rasterio.open(path) as src:
        val = next(src.sample([(lng, lat)]))[0]
        return None if src.nodata is not None and val == src.nodata else float(val)
```

If the GAEZ download is hard to automate in time, hand-enter a suitability score per crop for the Dakahlia area in `crops.json` and label it clearly as an approximation.

### 4.4 Crop knowledge table

`crops.json` holds the agronomy that no satellite gives you. Build it from FAO-56, FAO ECOCROP, and your own research plan. The values below are illustrative placeholders, so replace them and have an agronomist or your plan confirm them.

```json
{
  "berseem": {
    "season": "winter",
    "kc_mid": 1.15,
    "season_days": 150,
    "n_fixing": true,
    "organic_matter": "high",
    "deep_root": false,
    "salinity_tolerance": "medium",
    "heat_sensitivity": "low",
    "forage_value": "high",
    "income_index": 0.5,
    "pest_break_for": ["cereals"]
  }
}
```

### 4.5 Strategies and scoring

Build at least three strategies, as the challenge requires:
1. **Current rotation:** repeat the farmer's `last_crop` and `prev_crop` pattern. This is the baseline.
2. **Soil-focused:** adds a nitrogen-fixing or cover crop in the empty period.
3. **Water-saving:** replaces the highest-demand crop with a lower-demand one.
4. Optional: **income-focused** or **fodder-focused**, depending on the farmer's priorities.

Filter candidates first with hard constraints: crops the farmer excluded, salinity the crop cannot tolerate, equipment missing, a season window that does not fit.

Score each strategy from 0 to 100 on these criteria, each with the numbers that produced it:
- Water demand (crop ET from POWER, compared with the farmer's water reliability)
- Heat-stress exposure (hot days in the crop's sensitive stage)
- Soil benefit (nitrogen fixing, organic matter, fewer bare days from NDVI, pest-cycle break)
- Income and market fit
- Feasibility and risk

Turn the farmer's ranked priorities into weights:

```python
CRITERIA_FOR_PRIORITY = {
    "save_water": "water", "higher_income": "income", "better_soil": "soil",
    "lower_costs": "cost", "lower_risk": "risk", "fodder": "forage",
}
RANK_WEIGHTS = [0.40, 0.25, 0.15]      # remaining 0.20 is spread over the other criteria

def weights_from_priorities(priorities: list[str], all_criteria: list[str]) -> dict:
    w = {c: 0.0 for c in all_criteria}
    for rank, p in enumerate(priorities[:3]):
        w[CRITERIA_FOR_PRIORITY[p]] += RANK_WEIGHTS[rank]
    rest = [c for c in all_criteria if w[c] == 0.0]
    for c in rest:
        w[c] = 0.20 / max(len(rest), 1)
    return w
```

Also compute a **confidence** level per strategy: start high, lower it for each "unknown" answer, each missing data layer, each interpolated NDVI stretch, and each coarse-resolution input. Show it in the UI and send it to the LLM.

Keep the "farmer picked another crop" explanation in this layer too. It is the same scoring, run on the farmer's choice and compared side by side, so the pros and cons come from numbers and not from the LLM.

---

## 5. The evidence pack (what the engine sends onward)

One JSON document per analysis. It is also what you store and show in the UI.

```json
{
  "field": {"lat": 31.04, "lng": 31.38, "area_feddan": 3, "area_ha": 1.26},
  "farmer_priorities": ["save_water", "better_soil", "higher_income"],
  "data_quality": {
    "unknown_answers": ["soil_test", "water_cost"],
    "layers_used": ["nasa_power", "sentinel2_ndvi", "gaez"],
    "layers_unavailable": ["smap"],
    "notes": ["Climate data is about 50 km resolution", "NDVI cloud gaps filled in 3 periods"]
  },
  "observations": {
    "hot_days_per_year": {"mean": 42, "trend_per_year": 1.1},
    "bare_field_days_per_year": 95,
    "peak_ndvi_by_season": [{"season": "winter-2025", "peak": 0.71}]
  },
  "strategies": [
    {
      "id": "current",
      "name": "Current rotation",
      "sequence": ["wheat (winter)", "maize (summer)"],
      "scores": {"overall": 58, "water": 45, "soil": 40, "heat": 60, "income": 75, "risk": 55},
      "evidence": ["Maize needs about X mm of irrigation water in summer", "95 bare days per year"],
      "benefits": ["Familiar to the farmer", "Stable market"],
      "gaps": ["Soil nitrogen not measured"],
      "risks": ["Heat days are rising"],
      "confidence": "medium"
    }
  ]
}
```

Every number the LLM may mention must already be in this pack.

---

## 6. Connecting the engine to the frontend

### 6.1 Database table

```sql
create table public.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  status text not null default 'pending' check (status in ('pending','running','done','failed')),
  result jsonb,            -- the evidence pack
  narrative jsonb,         -- the LLM text per strategy
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.analyses enable row level security;
create policy "own select" on public.analyses for select using (auth.uid() = user_id);
create policy "own insert" on public.analyses for insert with check (auth.uid() = user_id);
-- no update policy: only the engine (service role) updates rows
```

### 6.2 Next.js route (server side only)

The browser never talks to Python. The Next.js route checks the login, creates the row, then calls the engine with a secret.

```ts
// app/api/analyze/route.ts
import { createClient } from "@/lib/supabase/server";

export async function POST() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return new Response("Unauthorized", { status: 401 });

  const { data: analysis, error } = await supabase
    .from("analyses").insert({ user_id: user.id }).select("id").single();
  if (error) return new Response(error.message, { status: 500 });

  // The engine answers 202 immediately and keeps working in the background.
  await fetch(`${process.env.ENGINE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": process.env.ENGINE_API_KEY! },
    body: JSON.stringify({ analysis_id: analysis.id, user_id: user.id }),
  });

  return Response.json({ id: analysis.id });
}
```

### 6.3 FastAPI endpoint

```python
# app/main.py
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel
from .settings import settings
from .pipeline import run_analysis

app = FastAPI()

class AnalyzeRequest(BaseModel):
    analysis_id: str
    user_id: str

@app.post("/analyze", status_code=202)
def analyze(req: AnalyzeRequest, bg: BackgroundTasks, x_api_key: str = Header(...)):
    if x_api_key != settings.ENGINE_API_KEY:
        raise HTTPException(401, "bad key")
    bg.add_task(run_analysis, req.analysis_id, req.user_id)
    return {"status": "accepted"}

@app.get("/health")
def health():
    return {"ok": True}
```

In `run_analysis`:
1. Mark the row `running`.
2. Load the `field_profiles` row with the service role key and check that it belongs to `user_id`.
3. Run the pipeline and the LLM step.
4. Write `result` and `narrative`, set `done`. On any exception, set `failed` with a short `error`.

### 6.4 Results page

Poll the row every 2 seconds until it is `done` or `failed`, and show a progress message meanwhile ("Reading satellite data", "Comparing strategies", "Writing your summary"). Supabase Realtime on the row works too, but polling is simpler and safe for a hackathon.

```ts
useEffect(() => {
  const t = setInterval(async () => {
    const { data } = await supabase.from("analyses").select("status,result,narrative,error").eq("id", id).single();
    if (data && (data.status === "done" || data.status === "failed")) { setAnalysis(data); clearInterval(t); }
  }, 2000);
  return () => clearInterval(t);
}, [id]);
```

### 6.5 Hosting

- Deploy the engine on Render, Railway or Fly.io with a small Dockerfile. Set the environment variables there.
- Free tiers sleep when idle. Hit `/health` a few minutes before your demo and before judging.
- If hosting is a problem, run it on a laptop and expose it with a Cloudflare or ngrok tunnel. Keep the same `ENGINE_URL` variable in Next.js.
- Cache everything. A repeated pin must return in seconds.

---

## 7. The LLM step

### 7.1 Rules for the prompt

- The model only rephrases the evidence pack. It must not add facts, numbers or advice that are not in the pack.
- Write for a farmer: short sentences, no jargon. Explain NDVI or evapotranspiration in a few words if mentioned.
- For each strategy, write the same five parts: why it was suggested, supporting evidence, benefits, information gaps, risks needing local review.
- State uncertainty and confidence plainly.
- Always end with a reminder that this supports, and does not replace, local expertise.
- Write in the farmer's language (`en` or `ar`).
- Return JSON only, in a fixed schema.

### 7.2 Code

```python
# app/llm.py
import json, re, anthropic
from pydantic import BaseModel, ValidationError

client = anthropic.Anthropic()     # reads ANTHROPIC_API_KEY

SYSTEM = """You explain crop-rotation analysis results to a farmer.
Use ONLY the facts and numbers in the DATA. Never add numbers, crops, prices or advice that are not in it.
Write short, simple sentences with no jargon. If you use a technical term, explain it in a few words.
For every strategy return: summary (2 sentences), why, evidence (list), benefits (list), gaps (list), risks (list).
Mention uncertainty and the confidence level honestly. Do not oversell any option.
Finish with one sentence reminding the farmer to review the options with a local agricultural expert.
Reply in the requested language. Return only valid JSON matching the schema."""

class StrategyText(BaseModel):
    id: str
    summary: str
    why: str
    evidence: list[str]
    benefits: list[str]
    gaps: list[str]
    risks: list[str]

class Narrative(BaseModel):
    overview: str
    strategies: list[StrategyText]
    reminder: str

def narrate(pack: dict, lang: str = "en") -> dict:
    schema = Narrative.model_json_schema()
    msg = client.messages.create(
        model="claude-sonnet-5-5",      # check the current model name in your console
        max_tokens=3000,
        temperature=0.2,
        system=SYSTEM,
        messages=[{"role": "user", "content":
            f"Language: {lang}\nSCHEMA: {json.dumps(schema)}\nDATA: {json.dumps(pack, ensure_ascii=False)}"}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    try:
        return Narrative.model_validate_json(raw).model_dump()
    except ValidationError:
        return fallback_text(pack, lang)

def fallback_text(pack: dict, lang: str) -> dict:
    # Build plain text straight from the pack with templates, so the UI never shows an empty result.
    ...
```

### 7.3 Guardrails worth the 20 minutes

- **Number check:** after the call, extract the numbers from the generated text and confirm each appears in the pack. If not, retry once, then use the fallback text.
- **Fallback:** template text built from the same pack, so a failed or slow LLM never breaks the demo.
- **Arabic:** Egyptian farmers will likely prefer it. Ask the LLM for `ar` when the user picks Arabic, and test the right-to-left layout on the results page.
- **No private data:** send only the evidence pack. Do not send the user's email or id to the LLM.
- **Cost and speed:** one call per analysis, cached by a hash of the pack.

---

## 8. Build order for the two days

1. **Tonight:** accounts and keys; one successful POWER call; start the GAEZ downloads; create the `analyses` table.
2. **First 3 hours tomorrow (vertical slice):** FastAPI returns a hard-coded evidence pack; Next.js route, polling and results page show it; the LLM turns it into text. You now have the full path working, even with fake data.
3. Replace fake data with real POWER features and real scoring.
4. Add Sentinel-2 NDVI (bare periods and last-crop cross-check).
5. Add GAEZ suitability, then SMAP if time allows.
6. Add the "farmer chose another crop" comparison and the scenario slider (hotter or drier, re-run the scoring on shifted POWER values).
7. Last 6 hours: polish the UI, rehearse the demo, record the video, write the data and limits slide.

---

## 9. Prompt for your AI coding agent

Copy the block below. Attach this file as context.

````
Build the Python engine for my Field Shift project, following python-engine-guide.md exactly. Work in a new /engine folder with FastAPI. Also add the Next.js pieces listed below to my existing Next.js + Supabase app (reuse its Supabase clients, colors and BrutalButton).

ENGINE
- Structure and files as in section 3 of the guide. Strict typing with pydantic.
- POST /analyze (202, header X-API-Key) runs run_analysis in a background task. GET /health.
- run_analysis: mark the analyses row running; load the field_profiles row with the Supabase service role and verify it belongs to the user; run the pipeline; call the LLM step; save result and narrative; set done, or set failed with a short error.
- Implement now: NASA POWER client with disk caching and -999 handling; climate features (hot days and trend, monthly means, growing degree days, ET0 with FAO-56 or Hargreaves, rainfall totals); crops.json with illustrative placeholder values clearly marked TODO-verify; strategy generation (current rotation from last_crop and prev_crop, a soil-focused one, a water-saving one, and an optional income or fodder one); hard-constraint filtering; weighted 0-100 scoring from the farmer's ranked priorities; a confidence level per strategy; the evidence pack as in section 5; the "farmer chose another crop" comparison using the same scoring.
- Implement as clean stubs with the final function signatures and TODOs, returning realistic mock data, so I can replace them one by one: Sentinel-2 NDVI via Copernicus (token, statistical API call, cache), GAEZ/SMAP/IMERG raster sampling with rasterio.
- LLM step as in section 7: Claude via the anthropic SDK, JSON-only output validated with pydantic, the number-check guardrail, one retry, and template fallback text. Support lang "en" and "ar".
- Settings from environment variables: ENGINE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, COPERNICUS_CLIENT_ID, COPERNICUS_CLIENT_SECRET. Provide .env.example, requirements.txt, a Dockerfile, and a README with run and test commands.
- Tests: scoring, weights_from_priorities, the evidence pack schema, and the number-check guardrail.

NEXT.JS
- Add the analyses table migration from section 6.1.
- Add app/api/analyze/route.ts as in section 6.2, using ENGINE_URL and ENGINE_API_KEY (server-only env vars).
- On the onboarding summary screen, after "Save", call this route and go to /dashboard/results/[id].
- Build the results page: poll the analyses row every 2 seconds with progress messages; when done, show one card per strategy with a score bar and the five parts (why, evidence, benefits, gaps, risks), a confidence badge, and the closing reminder. Use the existing light green, dark green and black brutalist style. If status is failed, show a friendly error with a retry button. Support right-to-left when the language is Arabic.
- On the dashboard, show a "View my analysis" card when a done analysis exists, and a "Run analysis" button otherwise.

RULES
- The browser never calls the engine. Never expose the service role key, engine key or LLM key to the client.
- The LLM may not add facts: all numbers come from the evidence pack.
- Do not add anything not listed. Ask me before adding extras.

DELIVERABLES
List the files created or changed, the SQL, how to run the engine locally, how to test the full flow end to end, and every assumption you made.
````

---

## 10. Verify before you build on it

Run each of these once tonight and fix anything that differs from this guide.

- [ ] POWER daily point call returns data for a Dakahlia coordinate (check the parameter names and the -999 handling).
- [ ] Copernicus token request and one Statistical API call for a small polygon return NDVI values (check the evalscript, the cloud mask and the quota).
- [ ] `earthaccess.login()` works and a search for the SMAP soil moisture product over the Delta returns granules (check the product name and version on the SMAP page).
- [ ] GAEZ rasters for your crops are downloadable for Egypt, and you know which suitability layer and input level you chose.
- [ ] The LLM model name in the code matches a model your account can use.
- [ ] Your engine can read and write Supabase with the service role key, and a normal user cannot update `analyses`.
