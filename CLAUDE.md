# CLAUDE.md — Field Shift Engine (terminal-first)

> You are the AI coding agent building the **Python engine** for *Field Shift: Adapting Farms with NASA Data* (NASA Space Apps Challenge 2026).
> The engine is a **colored interactive terminal app**. The Next.js/Supabase web app comes **after** the engine works (Part 14).
> **Companion file: `DATA.md`** — every data source, schema, seed table, validation rule and quality flag. Read it before any task that loads, validates, joins or scores data. It is part of your specification.
> This file replaces the engine-related parts of the earlier full-project `CLAUDE.md` (v2) until the engine is finished.

---

## PART 0 — RULES FOR YOU (READ FIRST)

1. **Ask the human first** (use your question tool) before Phase 0: (a) operating system and terminal (Windows Terminal / PowerShell / macOS / Linux / Git Bash), (b) Python version available, (c) whether the machine has internet access to `power.larc.nasa.gov`, (d) whether real field coordinates exist yet (otherwise the illustrative pilot point is used and everything is labelled illustrative). Record answers in `DECISIONS.md`.
2. **Work phase by phase** (Part 11). Do not start a phase until the previous one's acceptance criteria pass. Run `pytest -q` and `ruff check .` before declaring a phase done.
3. **Never invent data.** No made-up climate, soil, crop, price or yield values. Unknown stays unknown, is shown as unknown, and lowers confidence. Test fixtures may be synthetic but must be named `synthetic` and never reach the demo path.
4. **Provenance everywhere.** Every number shown to the user carries its source, status badge and (for datasets) period and resolution. See `DATA.md` §0.2 and §13.
5. **Support, don't replace.** The tool helps a farmer *explore* options. It never promises yields, never gives exact irrigation amounts, never calls a rotation "the best". Wording rules are in Part 8.4.
6. **Transparent over clever.** Deterministic code, simple formulas written out in this file, bands instead of false-precision decimals. No ML, no LLM in the engine.
7. **Small, typed, tested modules.** Pure functions in `analysis/`; network only in `data/` and `scripts/`; terminal I/O only in `ui/`.
8. **Don't silently deviate.** If a spec here is ambiguous or impossible, pick the simplest reading, write it in `DECISIONS.md`, continue. Keep this file and `DATA.md` current when contracts change.
9. **Demo safety.** The demo must run offline from files in `FieldShift_Data/`. Live fetching is an explicit user choice, never an implicit step.

---

## PART 1 — WHAT WE ARE BUILDING

### 1.1 One-paragraph description
A terminal application that interviews the user (a farmer, extension officer or team member) with colored arrow-key menus and typed prompts, joins **NASA POWER climate history**, **soil information**, a **sourced crop reference table** and the user's **farm profile and ranked priorities**, and then **compares the existing rotation with at least two alternative rotation strategies**. For each strategy it explains *why it was listed, what evidence supports it, what benefits it may offer, where information gaps exist, and what needs local review*, with confidence and data-quality flags. It exports a JSON result (for the future web app) and a Markdown report.

### 1.2 Source of truth
| Document | Role |
|---|---|
| Team PPTX *Field Shift – Egypt Data Research Plan* (pilot Dakahlia) | **How the engine works**: pipeline, datasets, inputs, scoring principles, metadata rules. Summarised in this file and `DATA.md`. |
| NASA challenge text | What the deliverable must show (≥3 strategies incl. existing; why/evidence/benefits/gaps/risks; uncertainty; supports not replaces expertise). |
| `DATA.md` | Data facts, seed tables, validation, flags. |

### 1.3 Reconciling the three sources (decisions already made)
| Topic | PPTX says | Challenge says | Decision |
|---|---|---|---|
| Number of strategies | "Compare two candidate rotation strategies" | "at least three, including the existing rotation" | Existing + **≥ 2 alternatives** = ≥ 3. The UI enforces it. |
| Datasets in MVP | POWER → FAO crop calendar & water → HWSD soil; SMAP & MODIS optional | many NASA datasets suggested | MVP = POWER + crop table + soil. SMAP/MODIS = Phase 9. SRTM/GPM/GRACE/ECOSTRESS/future climate = out of scope for the engine MVP (web-app phase). |
| Output style | "Transparent scores with caveats", "avoid false precision" | explain evidence and uncertainty | Indicators with units and definitions + **bands** (Good / Moderate / Poor / Unknown). A relative overall band is shown, never a decimal "score". |
| Water | reference crop-water need vs rainfall context | water demand | Engine estimates ETc = Kc × ET0 (Hargreaves–Samani) from local POWER temperatures and FAO-56 Kc (an *addition* beyond the PPTX, always labelled `estimated`). |
| Rotation rules | "apply only where supported" | pest-cycle interruption, N-fixing, etc. | Rules live in `rotation_rules.yaml`; unsupported rules are **notes only** and change no score. |
| Language | Arabic section in the plan | farmer-friendly | Engine UI in English now. All strings in `i18n/en.yaml` so Arabic can be added for the web app (terminals render right-to-left text unreliably). |

### 1.4 Non-goals
Yield forecasting · exact irrigation schedules · pest/disease modelling · market/price scoring (no data) · wind, dust-storm, flash-flood or local-frost warnings (need local met sources) · live demo API calls · user accounts · web UI.

---

## PART 2 — PRINCIPLES FROM THE PPTX (ENFORCE IN CODE)

1. Pipeline order: **COLLECT → VALIDATE → JOIN → COMPARE → EXPLAIN**. Each stage is a module with a clear input and output.
2. **No silent gap filling.** Missing stays missing; indicators depending on it become `unknown`.
3. **Raw vs cleaned** are separate folders; cleaned is regenerated from raw by code.
4. **Metadata required for each dataset:** source name + URL, version, retrieval date, time coverage, spatial resolution/grid cell, units, missing-value code.
5. **Do not mix incompatible units or resolutions.** Convert explicitly and log it.
6. **Location rules:** store latitude, longitude, CRS and selection date; record whether each source is point, gridded or field-measured.
7. **Let users rank priorities;** don't assume one goal fits everyone.
8. **Show missing or uncertain inputs** next to results.
9. **Collect only what the prototype needs;** no names, phones or addresses.
10. **A single indicator never produces a verdict.** Show a preliminary level, the reason, the action to check, the source.
11. **Every output displays source, update date and accuracy limits.**

---

## PART 3 — TECH STACK AND SETUP

| Need | Choice | Why |
|---|---|---|
| Python | **3.11+** | modern typing |
| Packaging | `pyproject.toml` (setuptools or hatch), `src/` layout, console script `fieldshift` | |
| CLI commands | **Typer** | subcommands, `--help`, completion |
| Colored output | **Rich** (panels, tables, rules, progress, status, themes) | |
| **Interactive prompts** | **questionary** (built on prompt_toolkit): `select` (arrow keys), `checkbox` (space), `text`, `confirm`, `autocomplete` | same feel as Claude Code's multiple-choice question UI, with free-text "Other" |
| Models/validation | **Pydantic v2** | |
| Data | pandas, numpy | |
| HTTP | httpx (timeouts, retries) | only in `data/` |
| Config/seed files | PyYAML | |
| Tests/lint | pytest, pytest-cov, ruff | |
| Optional later | rasterio (HWSD helper), earthaccess (SMAP/MODIS) | Phase 9 only |

`pyproject.toml` dependencies:
```toml
[project]
name = "fieldshift"
requires-python = ">=3.11"
dependencies = ["typer>=0.12", "rich>=13.7", "questionary>=2.0", "pydantic>=2.6",
                "pandas>=2.1", "numpy>=1.26", "httpx>=0.27", "pyyaml>=6.0"]
[project.optional-dependencies]
dev = ["pytest>=8", "pytest-cov", "ruff"]
geo = ["rasterio", "earthaccess"]
[project.scripts]
fieldshift = "fieldshift.cli:app"
```
Terminal notes: use **Windows Terminal or PowerShell** on Windows. In Git Bash (mintty) prompt_toolkit needs `winpty fieldshift`. Support `NO_COLOR`, `--plain` (no colors, numbered prompts) and `--ascii` (ASCII symbols) for limited terminals and CI. Minimum width 80 columns; adapt tables when narrower.

---

## PART 4 — REPOSITORY LAYOUT

```
fieldshift-engine/
  CLAUDE.md  DATA.md  README.md  DECISIONS.md  pyproject.toml
  config/
    app.yaml            # pilot point, slots, default period, thresholds file refs
    thresholds.yaml     # generic hot/cold thresholds, plausibility ranges (Part 7.3)
    bands.yaml          # indicator band cut-offs (Part 7.8)
  FieldShift_Data/      # exact structure in DATA.md §3 (raw/ cleaned/ metadata/ references/ README.md)
  runs/                 # one folder per analysis: profile.json, result.json, report.md, run.log
  src/fieldshift/
    __main__.py  cli.py
    models.py           # Pydantic: Location, Soil, FarmProfile, Priorities, Strategy, Indicator, RunResult…
    config.py
    ui/
      theme.py          # palette, rich Theme, symbols (+ASCII fallback), badges
      prompter.py       # Prompter protocol + QuestionaryPrompter + ScriptedPrompter + PlainPrompter
      questions.py      # Question catalog (Part 6.5)
      wizard.py         # state machine for the interview
      screens.py        # banner, section headers, summary tables, progress stages
      results.py        # result screens (Part 6.7)
    data/
      power.py          # URL builder, download, raw save, parse, clean
      provenance.py     # DataSource, StatusBadge, QualityFlag, retrieval_log writer
      validate.py       # V-* checks from DATA.md §12
      crops.py          # crop_reference.yaml loader + validator
      soil.py           # soil record loader/merger (farmer test over HWSD record)
      smap.py modis.py  # optional, Phase 9
    analysis/
      seasons.py        # slots, crop windows, cross-year handling
      et0.py            # Ra, Hargreaves–Samani ET0
      water.py          # Kc curve, ETc, rain coverage, access match
      climate.py        # exposure and fit indicators
      soilfit.py        # pH and salinity fit
      rotation.py       # strategy building, rule notes
      priorities.py     # rank → weights, indicator→priority mapping
      compare.py        # bands, composite, tie handling, equal-weights check
      explain.py        # why / evidence / benefits / gaps / local review
      confidence.py
    export/
      json_export.py  markdown_export.py
    i18n/en.yaml        # every user-visible string and indicator definition
  scripts/              # offline helpers (e.g. extract_hwsd.py) — never imported at runtime
  tests/                # unit + scripted-wizard + golden tests, fixtures/ (synthetic only)
```

---

## PART 5 — PIPELINE (PPTX slide 4) → MODULES

| Stage | What happens | Module(s) | Output |
|---|---|---|---|
| 1 COLLECT | read local files or (if chosen) download POWER; load crop table; load soil record; read farm profile | `data/power.py`, `crops.py`, `soil.py`, wizard | raw files + loaded objects + retrieval log |
| 2 VALIDATE | checks V-POWER/V-CROP/V-SOIL/V-PROFILE/V-META; flags; no filling | `data/validate.py` | `QualityFlag[]`, validated cleaned tables |
| 3 JOIN | location × season windows × crop requirements × farm history/priorities | `analysis/seasons.py`, `rotation.py` | per-(crop, slot, historical year) records |
| 4 COMPARE | indicators → bands → priority results → relative overall band for existing vs alternatives | `climate.py`, `water.py`, `soilfit.py`, `compare.py` | `Strategy[]` with indicators |
| 5 EXPLAIN | why / evidence / benefits / gaps / local review, limitations, confidence | `explain.py`, `confidence.py`, `export/*` | `RunResult` JSON + Markdown + screens |

---

## PART 6 — THE INTERACTIVE COLORED TERMINAL (core requirement)

### 6.1 Goal
The user enters **all required data in the terminal**, either by **choosing from an arrow-key menu** or **typing text/numbers**, exactly like answering questions in Claude Code: a short header chip, a question, a list of options with a one-line hint each, an "Other (type your own)" escape where it makes sense, and clear colors. No config files needed to run an analysis.

### 6.2 Prompt abstraction (do this first — it makes everything testable)
```python
# ui/prompter.py
@dataclass
class Option:  label: str; value: Any; hint: str = ""; disabled: str | None = None
@dataclass
class Question:
    id: str; header: str; prompt: str
    kind: Literal["select","multi","text","number","confirm"]
    options: list[Option] = field(default_factory=list)
    default: Any = None
    allow_other: bool = False       # adds "✎ Other (type your own)"
    allow_unknown: bool = False     # adds "I don't know / skip" -> Answer.unknown
    allow_back: bool = True         # adds "← Back"
    unit: str | None = None; min: float | None = None; max: float | None = None
    validate: Callable[[Any], str | None] | None = None   # return error text or None
    help: str = ""                  # shown dim under the question
    min_select: int = 0             # for multi
@dataclass
class Answer: value: Any; kind: Literal["menu","typed","unknown","default","back","quit"]
class Prompter(Protocol):
    def ask(self, q: Question) -> Answer: ...
```
Implementations:
* `QuestionaryPrompter` — interactive (default when stdin is a TTY).
* `PlainPrompter` — numbered menus and `input()` (for `--plain`, non-colored, or limited terminals).
* `ScriptedPrompter(answers: dict[str, Any])` — replays answers by `Question.id` (tests, `fieldshift demo`, `--answers file.json`). Unknown id → test failure.
Non-TTY without `--answers/--profile` → print a clear error and exit code 2.

### 6.3 Look and feel
**Palette** (define once in `ui/theme.py`; Rich `Theme` + questionary `Style`):
| Role | Color | Used for |
|---|---|---|
| brand | cyan `#00D7FF` bold | title, question mark `?`, section rules, header chips |
| ok / selected | green `#5FD75F` | pointer `❯`, chosen answer, ✔, "Good" band |
| warn | yellow `#FFD75F` | ▲ placeholder, warnings, "Moderate" band |
| error | red `#FF5F5F` | ✖, validation errors, "Poor" band, `missing` |
| muted | grey `#808080` | hints, definitions, instructions |
| NASA | blue `#5F87FF` | `NASA POWER` badges |
| FAO | teal `#00AF87` | FAO / crop-table badges |
| farmer | magenta `#D75FD7` | values typed by the user |
| estimate | orange `#FF8700` | engine estimates (`estimated`) |
| unknown | dim italic grey | "unknown" band |

questionary style:
```python
Style([("qmark","fg:#00d7ff bold"),("question","bold"),("answer","fg:#5fd75f bold"),
       ("pointer","fg:#5fd75f bold"),("highlighted","fg:#5fd75f bold"),("selected","fg:#5fd75f"),
       ("instruction","fg:#808080 italic"),("disabled","fg:#808080 italic"),("separator","fg:#808080")])
```
Option rows are formatted text: bold label + dim `— hint` (use `Choice(title=[("class:text", label), ("class:instruction", "  — "+hint)])` so it works across questionary versions).
**Symbols** (with ASCII fallback): `✔ ok`, `✖ error`, `▲ warning`, `● extracted`, `○ general fact`, `◆ farmer`, `❯ pointer`, `← back`, `✎ other`, `━ progress`.
**Status badges** (from `DATA.md` §0.2) are rendered by one function `badge(status)` and reused everywhere.
**Layout:** header chip + step counter + progress bar on one line; blank line; question; dim help line; options. Never print raw dicts/JSON to the user.

### 6.4 Interaction rules
* ↑/↓ move, Enter selects, Space toggles (multi), typing filters long lists (autocomplete for crop pickers).
* Every select has `← Back` (state machine goes to the previous question) unless `allow_back=False`.
* **Ctrl+C** never crashes: show a menu `[Resume] [Save draft & quit] [Quit without saving]`. Draft saved to `runs/draft.json` after every answered question; offer "Resume draft?" at start.
* Numeric input: accepts `31.04`, `31,04` (decimal comma) and Arabic-Indic digits (`٣١٫٠٤`); show unit; validate range with a friendly message ("pH is usually between 3 and 10").
* "I don't know" is a **first-class answer** where allowed: store `unknown`, add the flag from the catalog, and say so in the summary — never substitute a default silently.
* Show the **why we ask** line (`help`) for non-obvious questions, e.g. "Salinity needs a field EC measurement — a soil database cannot replace it."
* Echo each answer after it is given in green so the transcript reads like a form.
* Accessibility: respects `NO_COLOR`; every status is conveyed by a word or symbol, never by color alone.

### 6.5 Question catalog (implement in `ui/questions.py`; ids are stable API)
| id | Header chip | Prompt | Kind & choices | Validation / notes | Maps to | If unknown → flag |
|---|---|---|---|---|---|---|
| `start` | START | What would you like to do? | select: **New analysis** · Resume saved draft (if exists) · Load a saved profile · Run the demo (pilot point) · Data tools (fetch / validate / view crops) · Quit | | – | – |
| `loc_mode` | LOCATION | How do you want to set the field location? | select: **Use the pilot point near Mansoura, Dakahlia (31.04°N, 31.38°E — illustrative)** · Type latitude and longitude · Load a field boundary file (disabled: "coming later") | | location | – |
| `lat` | LOCATION | Latitude of the field (decimal degrees, e.g. 31.04) | number | −90…90; outside Egypt box (DATA.md §2) → confirm | location.latitude | – |
| `lon` | LOCATION | Longitude of the field (decimal degrees, e.g. 31.38) | number | −180…180 | location.longitude | – |
| `loc_name` | LOCATION | Give this location a short name (optional) | text, skippable | ≤ 40 chars | location.name | – |
| `coords_real` | LOCATION | Are these the real coordinates of your field? | confirm (default No) — only if pilot point | No → flag `coordinates_illustrative` | location.coordinates_illustrative | – |
| `prev_crop` | FARM | What crop did you grow **last season**? | select from crop table + Fallow + Other (type) + I don't know | Other → flag `crop_not_in_reference` (indicators unknown for it) | farm.previous_crop | `history_unknown` |
| `prev_season` | FARM | In which season was that? | select: Winter (Nov–Apr) · Summer (May–Oct) · I'm not sure | decides the first slot of the rotation | farm.previous_crop_season | `season_unknown` |
| `has_earlier` | FARM | Do you know the crops before that? | confirm | yes → `prev2_a`, `prev2_b` | – | – |
| `prev2_a`, `prev2_b` | FARM | What did you grow 2 / 3 seasons ago? | select (same list) + skip | optional | farm.previous_2_crops | – |
| `irrigation` | WATER | What is your main irrigation source? | select: Nile canal / surface water · Groundwater well · Canal + well · Rain only (no irrigation) · Other · I don't know | | farm.irrigation_source | `irrigation_unknown` |
| `water_avail` | WATER | How much irrigation water can you count on? | select: Limited · Moderate · High · I'm not sure | help: "Rainfall is not the same as irrigation availability." | farm.water_availability | skip water-access comparison |
| `soil_test` | SOIL | Do you have a recent soil test for this field? | confirm | yes → `soil_*` questions; no → regional data or unknown | farm.soil_test_available | – |
| `soil_texture` | SOIL | Soil texture class | select: 12 USDA classes + I don't know | | soil_test.texture | `soil_partial` |
| `soil_ph` | SOIL | Soil pH | number 3–10, skippable | | soil_test.ph | `soil_partial` |
| `soil_oc` | SOIL | Organic carbon | number ≥ 0 + unit select (% · g/kg · other → text) | store the unit string | soil_test.organic_carbon | `soil_partial` |
| `soil_ec` | SOIL | Salinity: electrical conductivity (ECe) in dS/m | number ≥ 0, skippable | help: field/lab EC; HWSD is no substitute | soil_test.ec_dsm | `salinity_unassessed` |
| `soil_depth` | SOIL | Rooting/sampling depth (cm) | number 0–300, skippable | | soil_test.depth_cm | – |
| `soil_date` | SOIL | Date of the test (YYYY-MM-DD) | text, skippable | valid date, not in the future | soil_test.date | – |
| `area` | FARM | Field area in hectares (optional) | number > 0, skippable | not used in scoring | farm.area_ha | – |
| `prio_rank` | PRIORITIES | Which matters **most** to you? (then next, then next…) | repeated select over: Reduce water use · Support soil health · Improve climate resilience · Maintain productivity; each round removes the chosen item; last option "Stop here — treat the rest as equal" | produces an ordered list | priorities.ranking | – |
| `budget_market` | PRIORITIES | Do budget or market limits matter? | select: No constraint · Low-cost inputs matter · Market / cash value matters · Food or fodder for my own use | **not scored** → flag `priority_unscored` + shown as a note | priorities.budget_market | – |
| `data_mode` | DATA | Where should climate data come from? | select: **Saved local files (offline)** · Download fresh NASA POWER data now (internet needed) · Auto (local if present, else download) | default Auto if files exist else Download | analysis.data_mode | – |
| `period` | DATA | Which years of climate history? | select: 2020–2025 (default from the research plan) · 2011–2025 (15 years — better for variability) · Custom range | custom: two numbers, start < end ≤ current year | analysis.period | – |
| `horizon` | DATA | How many years should each rotation cover? | select: 1 · **2** · 3 | | analysis.horizon_years | – |
| `strat_source` | STRATEGIES | How do you want to choose alternatives to compare? | select: **Ready-made templates (recommended)** · Build my own · Let the engine propose candidates (experimental — Phase 8) | | strategies.mode | – |
| `existing_edit` | STRATEGIES | This is your existing rotation. Is it right? | confirm + (if no) per-slot crop selects | shown as a sequence line | strategies.existing | `baseline_assumed` |
| `templates` | STRATEGIES | Pick **at least 2** alternatives to compare with your rotation | multi (checkbox) with the hypothesis as hint; `min_select=2` | template ids from `rotation_templates.yaml` | strategies.candidates | – |
| `custom_*` | STRATEGIES | Year _y_ · Winter/Summer crop | select crop (autocomplete) per slot; then `custom_name` text | at least 2 custom strategies | strategies.candidates | – |
| `review` | REVIEW | Everything look right? | select: **Run the analysis** · Edit a section · Save profile and exit | summary table first (Part 6.6) | – | – |
| `after_run` | RESULTS | What next? | select: Save report (Markdown + JSON) · Change priorities and re-run · Add another strategy · View data-quality details · Exit | | – | – |

### 6.6 Screens
**Banner** (every start): Rich `Panel`, brand color. Include the support-not-replace statement.
**Step header:** `[ LOCATION ]  Step 2 of 7  ━━━━━━──────` (chips colored by section).
**Summary before running:** a Rich table `Field | Your answer | Source/status` with colored badges (farmer `◆`, pilot default `▲ illustrative`, unknown red) and a "Flags" list underneath.
**Run progress:** five stages shown with Rich `Progress`/`status`; each stage prints one line (`✔ COLLECT  POWER 2020-01-01→2025-12-31, 2192 days, 0 missing`; `▲ VALIDATE  crop table: 11 placeholder values`).
Mock (plain text; colors per the palette):
```
╭─ FIELD SHIFT · Rotation Explorer ─────────────────────── engine v0.1.0 ─╮
│ NASA Space Apps 2026 · Egypt pilot (Dakahlia)                           │
│ This tool supports your decisions. It does not replace your own          │
│ experience or local agricultural experts.                                │
╰──────────────────────────────────────────────────────────────────────────╯
[ LOCATION ]  Step 1 of 7  ━━━━──────────────
? How do you want to set the field location?
 ❯ Use the pilot point near Mansoura — 31.04°N 31.38°E (illustrative)
   Type latitude and longitude
   Load a field boundary file (coming later)
   ← Back
  ↑/↓ move · Enter choose · Ctrl+C menu
```

### 6.7 Result screens (`ui/results.py`)
1. **Data used & quality** — table of datasets (name · type point/grid/field · resolution · period · retrieved · badge) and the active quality flags with plain-language explanations.
2. **Climate summary** — per season (winter, summer): mean/min/max temperature, rainfall total, hot-day count, cold/frost days; with `NASA POWER` badge, period, number of complete windows.
3. **Strategy comparison** — one table, **existing rotation first**, then alternatives:
`Strategy | Sequence | Water demand | Climate exposure | Soil | Overall (relative)` using colored band words (`Good`/`Moderate`/`Poor`/`Unknown`) plus a small bar `●●●○○`. Under the table: "Order under your priorities / under equal weights — stable? yes/no" and "too close to call" notes.
4. **Strategy detail** (select a strategy): five blocks named exactly as in the challenge — **Why it was listed · Evidence · Possible benefits (vs your existing rotation) · Information gaps · Risks needing local review** — then an indicator table (name · value (range across years) · unit · band · definition) and the crop rows used with status badges.
5. **Limits and next steps** — always shown: the PPTX methodological notes (DATA.md §11.6) and the "Check locally" list.

### 6.8 Demo mode
`fieldshift demo` runs the whole flow with a `ScriptedPrompter` over the pilot point and a sample profile (DATA.md §9.2), using files already in `FieldShift_Data/`. If required data files are missing it says exactly which ones and how to create them (`fieldshift fetch power --pilot`).

---

## PART 7 — ANALYSIS SPECIFICATION

All functions are pure and deterministic. Units in names (`_mm`, `_c`, `_days`). Definitions below appear in `i18n/en.yaml` and in the UI.

### 7.1 Season windows (`analysis/seasons.py`)
* Slots: `winter` (months 11,12,1,2,3,4) and `summer` (5–10). Rotation sequence for horizon *N* years = `2N` consecutive slots. The first slot is the one **after** `previous_crop_season` (winter if unknown, with flag `season_unknown`). The **existing rotation** is a **one-year cycle** (one winter crop + one summer crop) repeated over the horizon. Build it from `previous_crop` (in its slot) and ask for the other slot via `existing_edit` ("What do you usually grow in the other season?": a crop, Fallow, or Nothing). Never guess an empty slot. `previous_2_crops` are **not** used to build the cycle; they are kept as history context for rotation-rule notes (same family across seasons, past problems). A user who really follows a 2-year pattern can enter all four slots in `existing_edit`.
* **Crop window** for crop *c* in historical year *Y*: sowing date = midpoint of `sowing_window` in year *Y*; end = sowing + `growth_duration_days` − 1. Windows may cross the year end (e.g. 15 Nov → 23 Apr).
* A window counts only if it lies **entirely inside** the climate period and has **no missing values**; otherwise it is dropped (never filled). Record `n_windows`; if `< 3` → flag `few_windows`.
* Aggregate across years with **median, minimum and maximum**; show the range.
* Overlap with the previous crop's window (> 0 days) → note `season_overlap`.
* `fallow`: no window; counts as bare (note only).

### 7.2 ET0 and ETc (`analysis/et0.py`, `water.py`)
**Extraterrestrial radiation** (FAO-56 Eq. 21), latitude φ in radians, `J` = day of year:
```
dr = 1 + 0.033·cos(2πJ/365)
δ  = 0.409·sin(2πJ/365 − 1.39)
ωs = arccos(−tanφ·tanδ)
Ra[MJ m⁻² d⁻¹] = (24·60/π)·0.0820·dr·[ωs·sinφ·sinδ + cosφ·cosδ·sinωs]
Ra[mm d⁻¹] = 0.408·Ra[MJ m⁻² d⁻¹]
```
**Hargreaves–Samani ET0** (FAO-56 Eq. 52): `ET0 = 0.0023·(Tmean + 17.8)·√(Tmax − Tmin)·Ra[mm/d]` with `Tmean = (Tmax + Tmin)/2`. If `Tmax < Tmin` or a value is missing → ET0 = NaN (day invalid). Always tag results `et0_estimated`. (It is a temperature-based estimate; note this in the definition.)
**Kc curve** per day *d* of the window with stage lengths `ini, dev, mid, late` and `Kc_ini, Kc_mid, Kc_end` (midpoint-linear rule):
```
initial :  Kc = Kc_ini
develop :  Kc = Kc_ini + (Kc_mid − Kc_ini)·(i − 0.5)/dev      i = 1..dev
mid     :  Kc = Kc_mid
late    :  Kc = Kc_mid + (Kc_end − Kc_mid)·(i − 0.5)/late      i = 1..late
```
If `stage_days` is missing but `growth_duration_days` exists → split by `defaults.stage_split_if_missing` (0.15/0.25/0.40/0.20, rounded, remainder to `mid`) and flag `stage_split_assumed`. If `kc` or duration is missing → `etc` is `unknown`.
**ETc** = Σ over days of `Kc_d × ET0_d` (mm per window). **Rainfall in window** = Σ `rain_mm`.
**Rain coverage %** = `min(100, 100 × rain / ETc)`.
Definition text: "Estimated crop water need (ETc) — the water a healthy crop could lose to evaporation and transpiration over its season. It is **not** an irrigation schedule: it ignores losses in canals, fields and (for flooded rice) percolation."
Rice: always attach `rice_gross_water_underestimated`.
If `water_requirement_mm_ref` exists: show it beside ETc and flag a difference > 30 % (`etc_vs_reference_gap`).

### 7.3 Generic exposure and fit indicators (`analysis/climate.py`)
Thresholds in `config/thresholds.yaml` (generic, **not crop-specific**, heuristics — label them):
```yaml
hot_day_tmax_c: 35
cold_day_tmin_c: 5
frost_day_tmin_c: 0
plausible: {t_c: [-10, 55], rain_mm_day: [0, 200], solar_mj_m2_day: [0, 40]}
min_windows: 3
```
Per crop window (median/min/max over years):
| Indicator id | Definition | Unit | Needs |
|---|---|---|---|
| `heat_days` | days with Tmax ≥ 35 °C | days | POWER |
| `cold_days` | days with Tmin ≤ 5 °C | days | POWER |
| `frost_days` | days with Tmin ≤ 0 °C | days | POWER |
| `rain_window_mm` | rainfall total in the window | mm | POWER |
| `temp_in_range_pct` | % of window days with Tmean inside the crop's suitable temperature range | % | crop `temperature_c.topmn/topmx` |
| `days_above_tmax` | days with Tmax > crop `tmax` | days | crop `tmax` |
| `days_below_tmin` | days with Tmin < crop `tmin` | days | crop `tmin` |
Fit indicators are `unknown` when the crop range is `missing`; exposure indicators are always computed. Always print "generic threshold" next to exposure counts.

### 7.4 Water indicators (`analysis/water.py`)
| Indicator id | Definition | Unit |
|---|---|---|
| `etc_window_mm` | ETc per crop window (median, range) | mm/season (estimated) |
| `etc_year_mm` | Σ ETc over one year of the sequence (existing rotation = reference) | mm/year (estimated) |
| `rain_coverage_pct` | share of ETc met by rainfall | % |
| `irrigation_dependence` | band from coverage: ≥ 75 % low · 25–75 % moderate · < 25 % high | band |
| `water_demand_rel` | `etc_year_mm / max(etc_year_mm among compared strategies)`: ≤ 0.75 Good · 0.75–0.90 Moderate · > 0.90 Poor; if spread < 5 % all "Similar" | band (relative) |
| `water_vs_access` | `irrigation_dependence` × farmer `water_availability`: (high dep, limited) Poor · (high, moderate) Moderate · (high, high) Good · (moderate, limited) Moderate · (moderate, moderate/high) Good · (low, any) Good · unknown availability → Unknown | band |

### 7.5 Soil indicators (`analysis/soilfit.py`)
Soil record = farmer test over HWSD record over `missing` (DATA.md §6.5).
* `ph_fit`: Good if pH within crop `soil_ph_range`; Moderate if within 0.5 outside; else Poor. `Unknown` if either missing.
* `salinity_fit` (needs EC and crop `salinity_threshold_ece_dsm`): EC ≤ threshold → Good ("below crop threshold"); threshold < EC ≤ 2 × threshold → Moderate; > 2 × threshold → Poor. Cut-offs are heuristics (flag `heuristic_band`). `Unknown` + flag `salinity_unassessed` if EC missing.
* Texture and AWC are **shown as context** (no score) in the MVP.

### 7.6 Rotation rules (`analysis/rotation.py`)
Load `rotation_rules.yaml`. For each rule: if triggered, emit a **note** (`rule_unsupported` flag if `supported: false`). Only rules with `supported: true` and an `effect_if_supported`/score may change the `soil_health` priority result. In the MVP `R_HIGH_WATER_SUMMER` and `R_SEASON_OVERLAP` are the only supported ones, and neither adds a score. Report `n_fixer_present`, `family_repeat_count`, `bare_slots` as plain facts either way.

### 7.7 Priorities → weights → overall (`analysis/priorities.py`, `compare.py`)
**Rank-order-centroid weights** for *n* ranked priorities (`n` = 3…4, plus equal weights for anything the user skipped): `w_i = (1/n)·Σ_{k=i..n} 1/k` → n=4: 0.5208, 0.2708, 0.1458, 0.0625.
**Priority ← indicators mapping (explicit, shown to the user):**
| Priority | Indicators used (those that are not Unknown) |
|---|---|
| `reduce_water_use` | `water_demand_rel`, `irrigation_dependence`, `water_vs_access` |
| `support_soil_health` | `ph_fit`, `salinity_fit`, supported rotation-rule effects |
| `improve_climate_resilience` | `heat_days`, `frost_days`/`cold_days`, crop `drought_sensitivity` (low = Good), `days_above_tmax` |
| `maintain_productivity` | `temp_in_range_pct`, `days_above_tmax`, `ph_fit`, `salinity_fit` — a **suitability** proxy, *not yield* |
| `budget_market` | none (flag `priority_unscored`) |
**Band → number** (internal only): Good 1.0, Moderate 0.5, Poor 0.0. Season bands for exposure indicators come from `config/bands.yaml` (heuristics, listed in the UI definitions):
```yaml
heat_days:  {good_max: 2,  moderate_max: 10}     # median days per window
cold_days:  {good_max: 5,  moderate_max: 20}
frost_days: {good_max: 0,  moderate_max: 3}
temp_in_range_pct: {good_min: 70, moderate_min: 40}
days_above_tmax:   {good_max: 2,  moderate_max: 10}
days_below_tmin:   {good_max: 0,  moderate_max: 3}
```
**Priority result** = mean of its available indicator numbers (across seasons of the sequence). `Unknown` if none available.
**Overall (relative)** = `Σ w_p·score_p / Σ w_p` over priorities with data. Display as a band: ≥ 0.67 Good · 0.34–0.67 Moderate · < 0.34 Poor. Rules:
* If the weight share of priorities with data is < 50 % → show **"Not enough data for an overall comparison"** and list what to add (soil test, EC, crop temperature ranges…).
* Adjacent strategies whose overall numbers differ by < 0.05 are **"too close to call"** (do not rank them).
* Also compute the order under **equal weights**; report `ranking_stable = same order` and say so.
* Wording: "relative comparison among these strategies in this data period — not a yield forecast".

### 7.8 Confidence (`analysis/confidence.py`)
Per strategy, start `high` and apply effects from DATA.md §13 (placeholder/missing crop values, soil unknown/regional only, short record, assumed baseline, `stage_split_assumed`, `et0_estimated` counts as a note, etc.). Floor `low`. Print the flags that set the level.

### 7.9 Explanation blocks (`analysis/explain.py`)
Five blocks per strategy (challenge wording): `why_suggested`, `evidence`, `benefits`, `information_gaps`, `risks_for_local_review`.
* **why_suggested**: the template's `hypothesis` (for templates) or "chosen by you" (custom) or "your current practice" (existing), plus 1–3 data-based statements ("summer water demand is lower than your existing summer crop in the data period (estimated)").
* **evidence**: list of `{indicator, value_range, unit, dataset_badge, period, n_windows, status}`; every statement in `why_suggested`/`benefits` must cite ≥ 1 evidence item.
* **benefits (vs existing)**: only where a band improves or a numeric difference is ≥ 10 % (e.g. `etc_year_mm`), always hedged ("may", "in the data period").
* **information_gaps**: every flag active for that strategy translated to a sentence + what would fix it.
* **risks_for_local_review** (always present): varieties and seed availability · sowing dates · pests and diseases · market prices and costs · irrigation water allocation and any local regulation on the crop (e.g. area limits for rice — verify current rules) · soil test and field EC · equipment. Add triggered items (`salinity_unassessed`, `soil_unknown`, `rice_gross_water_underestimated`, `season_overlap`).

---

## PART 8 — OUTPUTS

### 8.1 `runs/<YYYYMMDD-HHMMSS>/`
`profile.json` · `result.json` · `report.md` · `run.log` (+ copies of the data-quality summary). Never overwrite raw data.

### 8.2 `result.json` (schema_version 1) — the contract for the future web app
```json
{
  "schema_version": 1, "engine_version": "0.1.0", "run_id": "20261030-101500",
  "created_at": "...", "disclaimer": "Supports, does not replace, farmer judgment and local expertise.",
  "profile": {"...": "sanitised, no personal data"},
  "data_sources": [{"id": "NASA_POWER_DAILY", "name": "...", "url": "...", "version": "...", "retrieved": "...",
                    "period": "2020-01-01/2025-12-31", "resolution": "...", "spatial_type": "gridded", "units": {...},
                    "missing_value_rule": "...", "status": "extracted"}],
  "quality_flags": [{"code": "soil_unknown", "text_key": "flag.soil_unknown", "severity": "warn"}],
  "climate_summary": {"winter": {"...": "..."}, "summer": {"...": "..."}, "n_complete_windows": {"winter": 5, "summer": 6}},
  "crops_used": [{"crop_id": "wheat", "fields": {"kc": {"v": {}, "status": "extracted", "src": "FAO56_T12"}}}],
  "strategies": [{
    "id": "existing", "kind": "existing|template|custom|proposed", "name": "...",
    "sequence": [{"slot": "winter", "year": 1, "crop_id": "wheat"}],
    "indicators": [{"id": "etc_window_mm", "label": "...", "median": 0.0, "min": 0.0, "max": 0.0, "unit": "mm",
                    "band": "Moderate", "status": "estimated", "definition_key": "ind.etc_window_mm",
                    "dataset": "NASA POWER + FAO-56", "n_windows": 5}],
    "priority_results": {"reduce_water_use": {"band": "Good", "indicators": ["water_demand_rel"]}},
    "overall": {"band": "Moderate", "value": 0.52, "basis": "3 of 4 priorities had data", "suppressed": false},
    "confidence": "low", "flags": ["stage_split_assumed"],
    "why_suggested": [], "evidence": [], "benefits": [], "information_gaps": [], "risks_for_local_review": []
  }],
  "comparison": {"order": ["rec-1", "existing"], "too_close": [["rec-1", "rec-2"]],
                 "order_equal_weights": ["rec-1", "existing"], "ranking_stable": true},
  "limitations": [], "local_review": []
}
```
`value` of `overall` is kept in JSON for the web app but **not printed as a decimal** in the terminal.

### 8.3 `report.md`
Header + disclaimer · inputs table with provenance · data sources table · quality flags · climate summary · crop rows used (with badges) · strategy comparison table · five blocks per strategy · limitations and methodology notes (DATA.md §11.6) · reproduction (versions, commands, SHA-256 of raw files).

### 8.4 Wording rules (enforced by a test that scans all strings in `i18n/en.yaml` and the report)
* Use *may, could, in the data period, estimated*. State the dataset and period next to every statement.
* **Banned phrases:** "will increase yield", "guaranteed", "best rotation", "optimal rotation", "optimal strategy", "you should irrigate", "recommended irrigation of … mm", "proven". Don't give irrigation volumes or dates.
* Say **suitability / exposure / water demand (estimated)**, never "yield".
* Always end result screens with: "Check these locally with an agronomist or extension officer."

---

## PART 9 — CLI COMMANDS (`cli.py`, Typer)

| Command | Purpose |
|---|---|
| `fieldshift` | interactive main menu → wizard (default) |
| `fieldshift run --profile P [--period 2020-2025] [--offline\|--fetch] [--out DIR] [--plain] [--json]` | non-interactive run from a profile |
| `fieldshift demo` | scripted demo on the pilot point (offline) |
| `fieldshift init-data` | create the `FieldShift_Data/` skeleton and write seed files from DATA.md (`crop_reference.yaml`, `rotation_templates.yaml`, `rotation_rules.yaml`, `data_dictionary.csv`, `links.md`) |
| `fieldshift fetch power [--pilot \| --lat --lon] [--start --end]` | download POWER, save raw + request sidecar, append retrieval log |
| `fieldshift validate [--climate\|--crops\|--soil\|--all]` | run V-* checks; table of results; exit code 1 on errors |
| `fieldshift climate [--pilot \| --lat --lon]` | seasonal climate summary |
| `fieldshift crops [--status]` | crop table with status badges and fill-in checklist (DATA.md §7.5) |
| `fieldshift explain <indicator>` | print a definition from `i18n/en.yaml` |
| `fieldshift theme` | show the palette, badges, symbols (for visual QA) |
Global flags: `--plain`, `--no-color`, `--ascii`, `--data-dir`, `--verbose`. Exit codes: 0 ok · 1 data/validation error · 2 usage or non-TTY without answers · 130 cancelled.

---

## PART 10 — TESTING

**Rules:** all tests offline and fast; prompts via `ScriptedPrompter`; no network.
**Unit tests (with these exact vectors — computed from the FAO-56 equations above; verify independently once):**
* `Ra` at latitude 31.04°, `J` = 15 / 105 / 196 / 288 → **20.463 / 36.663 / 40.605 / 27.005 MJ m⁻² d⁻¹** (±0.01).
* Hargreaves ET0 at φ=31.04: J=15, Tmax 19, Tmin 8 → **1.993 mm/d**; J=105, 28/14 → **4.995**; J=196, 36/22 → **6.672**; J=288, 29/16 → **3.682** (±0.01).
* Kc sum with the midpoint rule: wheat (20/50/60/30; 0.30/1.15/0.25) → **132.25** → ETc at constant ET0 = 3 mm/d = **396.75 mm**; cotton (30/50/60/55; 0.35/1.15/0.70) → **167.875** → **503.625 mm** at ET0 = 3.
* ROC weights: n=3 → 0.6111/0.2778/0.1111; n=4 → 0.5208/0.2708/0.1458/0.0625; n=5 → 0.4567/0.2567/0.1567/0.0900/0.0400; sums = 1.
* Window logic: winter crop sown 15 Nov for 160 days crosses the year end; windows past the data end are dropped; `n_windows` correct; **missing days drop the window** (never filled).
* POWER parser on a **synthetic** CSV fixture: header block with `-BEGIN HEADER-`/`-END HEADER-`; both `YEAR,DOY` and `YEAR,MO,DY` layouts; `-999` → NaN; unit/missing-code checks; gap detection.
* Validators: seed crop table passes with warnings; mutated stage sum → `stage_sum_mismatch`; bad pH → error.
* Unknown propagation: missing crop `tmax` ⇒ `days_above_tmax` Unknown ⇒ priority computed from remaining indicators ⇒ flags present; all-unknown priority excluded and weights renormalised; < 50 % weight share ⇒ overall suppressed.
* Tie handling (< 0.05) and equal-weights stability.
* Wording test: banned phrases absent from every string.
**Wizard tests:** scripted answers for (a) pilot path with soil unknown, (b) farmer soil test path, (c) Back navigation, (d) Ctrl+C draft save/resume, (e) `min_select=2` enforcement, (f) invalid number then valid.
**Golden test:** a small **synthetic** climate fixture + the seed crop table + a fixed profile ⇒ fixed `result.json` (kept in `tests/golden/`, regenerated only intentionally).
**Visual QA:** `fieldshift theme` and a Rich `Console(record=True)` export for screens; a snapshot test that the comparison table renders in 80 columns.

---

## PART 11 — BUILD PHASES (do in order)

Mapping to the team's 3-day data sprint and priority list (POWER → FAO crops → HWSD → SMAP → MODIS): the data work (Day 1–2 of the PPTX) runs **in parallel** with Phases 0–4 by the human data researcher; you consume what they produce.

### Phase 0 — Scaffold and theme
Create the layout, `pyproject.toml`, config files, `ui/theme.py`, `fieldshift theme`, `fieldshift --help`, ruff/pytest setup, `DECISIONS.md` (with the answers from Part 0.1).
**Done when:** `pip install -e ".[dev]"` works; `fieldshift theme` prints the colored palette, all badges and symbols; plain/ASCII variants render; tests run.

### Phase 1 — Models, provenance, data skeleton
`models.py`, `data/provenance.py` (`DataSource`, `StatusBadge`, `QualityFlag`, retrieval-log writer), `config.py`, `fieldshift init-data` writing every seed file from `DATA.md` (§3, §7.3, §8.1, §8.2, §14).
**Done when:** `init-data` creates the exact folder tree; all seed files load; flags and statuses render as colored badges.

### Phase 2 — Crop table loader and validator
`data/crops.py`, V-CROP checks, `fieldshift crops --status` (table of crops × fields with badges; counts of `placeholder`/`missing`; the §7.5 fill-in checklist).
**Done when:** seed table loads; validator catches the injected errors in tests; the screen makes it obvious what the data researcher still has to fill.

### Phase 3 — **Interactive wizard (the visible core)**
`ui/prompter.py` (3 implementations), `ui/questions.py` (catalog 6.5), `ui/wizard.py` state machine, `ui/screens.py` (banner, chips, progress, summary), draft save/resume, profile JSON export (`runs/<id>/profile.json`), scripted tests.
**Done when:** `fieldshift` walks the whole interview with arrow-key menus and typed input in color; Back, Ctrl+C menu and "I don't know" work; the summary screen shows provenance badges and flags; `fieldshift demo` replays it with scripted answers; non-TTY exits with code 2 and a helpful message. *(No analysis needed yet.)*

### Phase 4 — NASA POWER (priority 1)
`data/power.py` (URL builder from profile, download with retries, raw + `.request.json`, parser per DATA.md §5.4, cleaned daily CSV, seasonal summary), `data/validate.py` (V-POWER), `fieldshift fetch power`, `validate --climate`, `climate`.
**Done when:** offline tests pass on the synthetic fixture; with internet, `fetch power --pilot` stores a real raw CSV and sidecar and `climate --pilot` prints the summary; the human then writes the confirmed facts into `DATA.md` §5.3 (assumptions → verified).

### Phase 5 — Soil (priority 3)
`data/soil.py`: load `soil_<locid>.json`, merge with the farmer's test (precedence in DATA.md §6.5), V-SOIL checks, `salinity_unassessed` logic; wizard soil questions feed it.
**Done when:** pilot soil shows `unknown` with the right flags; entering a test in the wizard changes the status to `◆ farmer`.

### Phase 6 — Analysis
`seasons.py`, `et0.py`, `water.py`, `climate.py`, `soilfit.py`, `rotation.py`, `priorities.py`, `compare.py`, `confidence.py` per Part 7, plus the equal-weights check and tie handling.
**Done when:** all Part 10 vectors pass; given a synthetic climate and the seed table, the engine returns the existing rotation + ≥ 2 alternatives with indicators, bands, flags and confidence; unknowns propagate correctly.

### Phase 7 — Explanations, results screens, export
`explain.py`, `ui/results.py` (Part 6.7), `export/json_export.py`, `export/markdown_export.py`, wording test, `run` command, `after_run` menu.
**Done when:** the full interactive run ends with the five-block detail for every strategy, the "Check locally" list and saved `result.json` + `report.md`; the wording test passes; the report reproduces from `profile.json` with `fieldshift run`.

### Phase 8 — Extensions (SHOULD)
* Engine-proposed candidates: enumerate sequences from crops allowed per slot (no identical crop in consecutive same-type slots), compute indicators, show the **top 2–3 as "candidates to explore"** (never "best"); tie handling applies.
* Sowing-date sensitivity: compute indicators for the start/mid/end of each sowing window and show the spread.
* Priority sensitivity: perturb ranking weights (fixed seed) and report order stability.

### Phase 9 — Optional datasets (only after Phase 7 is stable)
`data/smap.py` and `data/modis.py` per DATA.md §10: context panels (soil-moisture trend, seasonal greenness) with quality flags and honest resolution caveats; never core score terms.

### Phase 10 — Hand-off to the web app
Expose `run_analysis(profile) -> RunResult` as a library function; add a thin FastAPI wrapper (`/recommend`, `/crops`, `/datasets`, `/health`) returning `result.json`; keep the schema versioned; add Arabic strings in `i18n/ar.yaml` for the web UI.
**Done when:** the same `profile.json` produces identical `result.json` from the CLI and the API.

**If time is short (48 h):** MUST = Phases 0–7; SHOULD = 8; STRETCH = 9–10. A working Phase 3 + 4 + 6 + 7 on the pilot point is already a complete demo.

---

## PART 12 — GUARDRAILS

**Never**
* invent climate/soil/crop values, prices or yields; fill gaps; interpolate missing days.
* present satellite/model grid values as field measurements, or HWSD as a soil test.
* print raw JSON, stack traces or internal codes to the user (log them to `run.log`).
* call external services in the demo path or at import time.
* use banned phrases (Part 8.4) or give irrigation amounts/dates.
* hide `placeholder`/`missing` statuses to make output look cleaner.
* store personal data.
**Always**
* show source, status badge, period and resolution next to numbers; keep flags visible.
* keep functions pure and unit-tested; log every download to `retrieval_log.jsonl`.
* handle Ctrl+C, non-TTY, narrow terminals, missing files with a clear message and the command that fixes it.
* write `DECISIONS.md` entries for every ambiguity you resolved.

---

## PART 13 — DEFINITION OF DONE (engine v0.1)

- [ ] `fieldshift` runs an end-to-end interview in color with menus and typed input; Back, Ctrl+C menu, draft resume, "I don't know" all work.
- [ ] The pilot point runs offline from `FieldShift_Data/` and is labelled illustrative.
- [ ] Real NASA POWER data can be fetched, validated and stored raw + cleaned with a retrieval log.
- [ ] The result compares the **existing rotation with ≥ 2 alternatives**, each with *why, evidence, benefits, information gaps, local-review risks*, indicators with units, bands, confidence and flags.
- [ ] Unknown inputs stay unknown, propagate correctly, and the UI says what to add to unlock more.
- [ ] Priorities are ranked by the user; mapping to indicators is visible; equal-weights stability and ties are reported.
- [ ] `result.json` (schema v1) and `report.md` are produced and reproducible from `profile.json`.
- [ ] All Part 10 tests pass; `ruff check .` clean; wording test passes.
- [ ] `DATA.md` §5.3, §6.1 assumptions updated after the first real download/extraction; remaining placeholders listed in the report.

---

## PART 14 — LATER: WEB APP (do not start yet)

Next.js + Supabase UI calling a FastAPI wrapper around `run_analysis`. Reuse `result.json`, the i18n keys, the quality-flag catalogue and the wording rules. Add Arabic/RTL, maps and charts, scenario sliders and the extra NASA datasets (SRTM, GPM, GRACE, ECOSTRESS, future climate) as later layers. The earlier full-project spec (v2) remains the reference for that stage.

---

## PART 15 — WHAT ONLY HUMANS CAN SUPPLY (ask for these; do not guess)

1. Real field coordinates (and ideally a real soil test with EC) for at least one field.
2. Crop-table fill-ins and citations (DATA.md §7.5): GIEWS sowing windows, EcoCrop temperature ranges, FAO water needs, drought sensitivity, pH ranges; verification of FAO-56 and salinity values; an Arabic speaker's check of crop names.
3. HWSD extraction for the pilot point and confirmation of attribute names/units (DATA.md §6.1, §6.3).
4. First-run confirmation of the NASA POWER response format (DATA.md §5.3).
5. Review of the rotation templates (DATA.md §8.1) and citations to switch any rotation rule to `supported: true`.
6. Decisions on SMAP product and Earthdata access if Phase 9 is attempted.
