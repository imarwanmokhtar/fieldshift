# Field Shift: farmer onboarding

Two parts:

1. The 28 questions to ask the farmer, and what each one feeds.
2. A copy-paste prompt for your AI coding agent to build the one-question-at-a-time wizard.

Location is a single map pin. Weather and region are not asked, because they come from NASA and partner data using the pin's coordinates.

If your "Field Shift Egypt Data Research Plan" PPTX lists specific engine inputs, add or remove rows below so every engine input has a question.

---

## Part 1: Questions

Rules for every question:
- Plain farmer language, one idea per question.
- Every question except the three marked **required** has a "Don't know / Skip" option. Missing answers become "unknown" in the engine and lower the confidence of the result. They never block the farmer.
- Units: feddan and kirat (offer hectare too).
- Seasons: Winter is about November to April. Summer is about May to October.

### A. Your field (3)

| # | id | Question | Answer type / options | Feeds |
| --- | --- | --- | --- | --- |
| 1 | `pin` **required** | Drop a pin on your field | Map pin, "Use my location", or typed latitude/longitude | Region, climate, and extracting satellite pixels (NDVI, POWER, ERA5, IMERG, SMAP) |
| 2 | `field_name` | What do you call this field? | Short text, optional | Display only |
| 3 | `area` **required** | How big is this field? | Number plus unit: feddan / kirat / hectare | Total water demand, income estimates |

### B. Your soil (6)

| # | id | Question | Answer type / options | Feeds |
| --- | --- | --- | --- | --- |
| 4 | `soil_texture` | When wet, how does the soil feel? | Sticky and heavy (clay) / Smooth, holds shape (loam) / Gritty, falls apart (sandy) / Mixed / Don't know | Water holding, infiltration |
| 5 | `drainage` | After irrigation, how fast does the water sink in? | Within hours / About a day / Several days (stays on top) / Don't know | Drainage, waterlogging, root disease risk |
| 6 | `salinity` | Do you see white salt crust or patchy, poor growth? | Never / Some spots / Large areas / Don't know | Salinity risk, crop tolerance filter |
| 7 | `soil_issues` | Which soil problems have you seen? | Multi-select: Hard layer / Deep cracks when dry / Waterlogging / Erosion by water or wind / Weeds taking over / Low fertility / None | Risk flags |
| 8 | `organic_inputs` | Do you add manure or compost? | Every season / Once a year / Rarely / Never | Organic matter trend |
| 9 | `soil_test` | Do you have a soil test result? | No / Yes, then optional pH, salinity (EC), organic matter %, N, P, K | Calibrates the soil estimates |

### C. Your water (6)

| # | id | Question | Answer type / options | Feeds |
| --- | --- | --- | --- | --- |
| 10 | `water_source` | Where does your irrigation water come from? | Multi-select: Nile canal / Groundwater well / Drainage reuse / Rain only / Other | Water availability, salinity risk |
| 11 | `water_reliability` | Does water arrive when your crop needs it? | Always / Mostly / Often late or short / Rarely | Drought resilience weighting |
| 12 | `irrigation_method` | How do you irrigate? | Flood / Furrow / Sprinkler / Drip / Pivot / Other | Water-use efficiency |
| 13 | `irrigation_interval` | How many days between irrigations? | Two numbers: summer every __ days, winter every __ days | Actual water use vs crop demand |
| 14 | `water_quality` | How is your irrigation water quality? | Good / Slightly salty / Salty / Looks polluted / Don't know | Crop tolerance filter |
| 15 | `water_cost` | Is the cost of water or pumping a heavy burden? | Not at all / Somewhat / Heavy / Water is free / Don't know | Income vs water trade-off |

### D. Your field's history (6)

| # | id | Question | Answer type / options | Feeds |
| --- | --- | --- | --- | --- |
| 16 | `last_crop` | What did you grow most recently? | Crop (list below) plus the season it was grown in: Winter / Summer | Existing rotation (strategy 1) |
| 17 | `prev_crop` | And what did you grow before that? | Crop (list below) plus season: Winter / Summer | Existing rotation, pest cycles |
| 18 | `bare_periods` | How long is the field usually empty between crops? | Never / Under 1 month / 1 to 3 months / More than 3 months | Bare-field periods, cover crop chances |
| 19 | `yield_vs_expected` | How were your last yields compared with neighbors or past years? | Better / About the same / Worse / Don't know | Soil health signal |
| 20 | `pest_issues` | Which problems have you had? | Multi-select: Insects / Fungal disease / Weeds / Nematodes / Birds or rodents / None | Pest-cycle disruption value |
| 21 | `fertilizer_level` | How much chemical fertilizer do you use? | None / Low / Medium / High / Don't know | Nutrient balance, nitrogen-fixing benefit |

Crop list for questions 16 and 17: Wheat, Rice, Maize, Cotton, Berseem (clover), Sugar beet, Faba bean, Onion, Potato, Tomato, Other vegetables, Fruit trees, Sorghum, Sesame, Peanut, Left empty (fallow), Other (text). Adjust to your pilot region.

Older rotation history can come from the satellite NDVI time series at the pin, so you don't need to ask the farmer for it.

### E. Your goals (7)

| # | id | Question | Answer type / options | Feeds |
| --- | --- | --- | --- | --- |
| 22 | `priorities` **required** | What matters most to you? Pick up to 3, in order | Save water / Higher income / Better soil / Lower costs / Lower risk / Fodder for animals | Strategy ranking weights |
| 23 | `livestock` | Do you keep animals that need fodder? | No / Cattle or buffalo / Sheep or goats / Poultry | Forage value of crops |
| 24 | `market` | Where do you usually sell? | Multi-select: Government procurement / Cooperative / Trader / Local market / Contract / Own use only | Market suitability |
| 25 | `risk_tolerance` | Would you try a new crop? | Stick to what I know / Small trial first / Ready to change | How bold the suggested strategies are |
| 26 | `equipment` | What do you have available? | Multi-select: Tractor / Planter / Harvester / Sprayer / Pump / Hand labor only | Feasibility filter |
| 27 | `crop_filter` | Any crops you definitely want, or definitely not? | Two multi-selects: Include / Exclude, from the crop list | Hard constraints |
| 28 | `horizon` | How far ahead are you planning? | Next season only / 2 to 3 years / 5+ years | Strategy length |

---

## Part 2: Prompt for your AI agent

Copy everything inside the block below.

````
You are working in my existing Next.js (App Router, TypeScript) project "Field Shift" that already has: a landing page, Supabase auth (sign up, log in, log out), Tailwind, shadcn/ui, a protected /dashboard that is currently empty, and a shared BrutalButton component with a sliding hover effect. Read the existing code first and reuse its components, colors and conventions.

GOAL
Build a farmer onboarding wizard at /onboarding that asks ONE question per screen, shows a progress bar and a "N / TOTAL" counter, saves answers to Supabase as the user goes, and ends back on the dashboard. Do not build any insights, result maps, weather features, or the Python engine. Only collect the data.

QUESTIONS
Create a single typed config file at src/lib/onboarding/questions.ts exporting an ordered array of questions. The wizard renders purely from this config, so adding or removing a question never needs UI changes. TOTAL is questions.length (never hard-code 28). Each question has:
- id (string), section (string), title (farmer-friendly question), help (optional one-line hint), type, options (if applicable), required (boolean, default false), allowUnknown (boolean, default true), showIf (optional function of current answers).
Supported types: "single", "multi", "number", "numberWithUnit", "text", "mapPin", "rank", "twoNumbers", "soilTest", "cropAndSeason".
Strings must be structured as { en: string, ar?: string } so Arabic can be added later; only English is required now.

Use exactly these 28 questions, in this order (full wording, options and units are in Part 1 of onboarding-questions-and-agent-prompt.md, which I have attached/pasted; follow it):
A. Your field: pin, field_name, area
B. Your soil: soil_texture, drainage, salinity, soil_issues, organic_inputs, soil_test
C. Your water: water_source, water_reliability, irrigation_method, irrigation_interval, water_quality, water_cost
D. History: last_crop, prev_crop, bare_periods, yield_vs_expected, pest_issues, fertilizer_level
E. Goals: priorities, livestock, market, risk_tolerance, equipment, crop_filter, horizon
Required: pin, area, priorities. Every other question shows a "Don't know / Skip" button that stores the value "unknown" and moves on.
Do NOT ask for governorate, district or village, and do NOT ask any weather questions. The map pin is the only location input; region and weather will be derived from its coordinates later by the data engine.

UI / UX
- One question per screen, centered, large type, generous spacing, mobile-first (works at 360px width).
- Top of screen: a section label (small uppercase, e.g. "B. YOUR SOIL"), the counter "07 / 28" in a monospace font, and a progress bar directly under it.
- Progress bar: full width, 16px tall, 3px solid black border, light-green track, dark-green fill, square corners, hard 4px black shadow. The fill width animates smoothly to (currentIndex + 1) / TOTAL. Add role="progressbar" with aria-valuenow, aria-valuemin, aria-valuemax and an aria-label.
- Answer options are big brutalist tiles/buttons (3px black border, flat fill, hard shadow). Selected state: dark-green fill with paper-colored text and a check mark. Selecting does not auto-advance (to avoid mistakes); the user presses Next, and Enter is a shortcut for Next.
- Bottom action bar: "Back" (secondary) and "Next" (primary) using the existing BrutalButton with the sliding hover effect. On the last question Next becomes "Finish". Next is disabled until a required question is answered. Add a quiet "Skip / Don't know" text button for skippable questions.
- Keyboard: Enter = Next, number keys 1-9 pick the matching option on single/multi questions, arrow keys move between options.
- Transitions: sliding horizontally between questions (forward slides left, back slides right), 200-250ms. Respect prefers-reduced-motion by using an instant swap instead.
- Colors (use the existing CSS variables/tokens, do not invent new ones): light green for backgrounds and highlights, dark green for fills and primary actions, black for text, borders and hard shadows, paper/off-white for neutral surfaces. Modern brutalism: thick borders, flat colors, hard offset shadows, no gradients, no blur, no rounded corners. Keep WCAG AA contrast.
- Special inputs:
  - mapPin: a Leaflet map (react-leaflet, OpenStreetMap tiles, no API key), centered by default on the Nile Delta in Egypt (around 31.0 N, 31.4 E, Dakahlia) at a zoom level where individual fields are findable, with a satellite-friendly zoom range. Click or drag to place a marker, plus a "Use my location" button (browser geolocation, handle denial gracefully) and manual latitude/longitude inputs. Store { lat, lng } with 5 decimals. Load the map client-side only (dynamic import, ssr: false). The question is required, so Next stays disabled until a pin is placed.
  - numberWithUnit (area): number input plus unit select (feddan, kirat, hectare). Store the raw value, the unit, and a normalized value in hectares.
  - twoNumbers (irrigation_interval): two labeled inputs (summer days, winter days), validated 1 to 60.
  - cropAndSeason (last_crop, prev_crop): a crop picker (tiles) plus a Winter / Summer toggle. Store { crop, season }. "Left empty (fallow)" is a valid crop. Show a one-line hint that Winter is about November to April and Summer is about May to October.
  - rank (priorities): choose up to 3 and keep their order; show the rank numbers on the tiles.
  - soilTest: first a Yes/No; if Yes, reveal optional fields (pH, salinity EC, organic matter %, N, P, K). All optional. No photo upload.
  - multi with a "None" option: choosing "None" clears other choices, and choosing any other clears "None".
- Validation: friendly inline messages, never blocking on optional questions. Numbers must be positive and sane (area > 0).
- A final summary screen after the last question: list the answers grouped by section with an "Edit" link that jumps back to that question, then a "Save and go to dashboard" button. Do not show the progress counter on this screen.

STATE AND PERSISTENCE
- Use React state in a small client component, but save to Supabase after every Next press (debounced upsert) so a farmer can close the tab and resume exactly where they stopped.
- Table (create with a SQL migration file in supabase/migrations, and also show me the SQL):

  create table public.field_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references auth.users(id) on delete cascade,
    answers jsonb not null default '{}'::jsonb,
    current_step int not null default 0,
    status text not null default 'in_progress' check (status in ('in_progress','completed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
  );
  alter table public.field_profiles enable row level security;
  create policy "own select" on public.field_profiles for select using (auth.uid() = user_id);
  create policy "own insert" on public.field_profiles for insert with check (auth.uid() = user_id);
  create policy "own update" on public.field_profiles for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
  create policy "own delete" on public.field_profiles for delete using (auth.uid() = user_id);
  -- keep updated_at fresh with a trigger

  One profile per user for now (one field). Leave a comment that multi-field support will change user_id to non-unique and add a field id later.
- answers is a flat object keyed by question id. Store "unknown" for skipped questions. Never store anything outside this table.
- Use the existing Supabase server/browser clients. Verify the user server-side with supabase.auth.getUser(). Never use the service role key in client code.

ROUTING
- /onboarding is protected (redirect to /login if signed out).
- After sign-up or log-in, if the user has no completed profile, redirect to /onboarding (resume at current_step if in progress). If completed, go to /dashboard.
- /dashboard stays mostly empty: if the profile is not completed, show a card "Finish your farm setup" with a button to /onboarding; if completed, show a card "Setup complete" with a short summary (field size, last crop, top priority) and an "Edit answers" button that reopens the wizard on the summary screen. No insights yet.

CODE QUALITY
- Strict TypeScript. Derive the answer types from the config where practical.
- Small components: ProgressHeader, QuestionShell, one input component per type, SummaryScreen, and a useOnboarding hook for state, navigation and saving.
- Accessible: real labels, visible focus rings (thick black outline), aria-live for validation errors, proper fieldset/legend for choice groups.
- No new UI libraries except react-leaflet and leaflet. Use shadcn/ui primitives where they fit and style them to the brutalist theme.

DELIVERABLES
1. All new and changed files, listed first.
2. The SQL migration.
3. A short "how to test" list: sign up, place a pin, answer a few questions, close the tab, come back and resume, skip an optional question, finish, see the dashboard summary.
4. Anything you assumed.

Do not add: insights, charts, weather or region questions, the Python engine, Arabic translations, photo uploads, or multi-field support. Ask me before adding anything outside this list.
````

---

## Tips for using it

- Paste Part 1 into the agent's context together with the prompt, since the prompt refers to it for the full wording and options.
- If time is short, cut these first: `field_name`, `organic_inputs`, `water_cost`, `equipment`, `horizon`. The engine still works without them.
- Test the wizard on your phone before the demo. Most farmers will use one.
